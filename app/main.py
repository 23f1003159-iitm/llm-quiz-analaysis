import os
import json
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from pydantic import ValidationError
from app.models import QuizTask
from app.agent import process_quiz_task

load_dotenv()
MY_SECRET = os.getenv("STUDENT_SECRET")

app = FastAPI(title="LLM Quiz Solver", version="1.0.0")


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors with HTTP 400"""
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid JSON payload", "details": str(exc)}
    )


@app.exception_handler(json.JSONDecodeError)
async def json_exception_handler(request: Request, exc: json.JSONDecodeError):
    """Handle JSON decode errors with HTTP 400"""
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid JSON format", "details": str(exc)}
    )


@app.post("/quiz")
async def start_quiz(request: Request, background_tasks: BackgroundTasks):
    """
    Main endpoint to receive quiz tasks.
    - Returns 400 for invalid JSON
    - Returns 403 for invalid secret
    - Returns 200 and starts processing for valid requests
    """
    # Parse JSON manually to catch errors
    try:
        body = await request.json()
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    
    # Validate with Pydantic
    try:
        task = QuizTask(**body)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {str(e)}")
    
    # Verify secret
    print(f"📨 Incoming request for: {task.url}")
    if task.secret != MY_SECRET:
        print(f"❌ Invalid secret provided")
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    # Start background processing
    background_tasks.add_task(process_quiz_task, task.email, task.secret, str(task.url))
    return {"message": "Task accepted", "status": "processing"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "secret_configured": bool(MY_SECRET)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)