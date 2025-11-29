import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from dotenv import load_dotenv
from app.models import QuizTask
from app.agent import process_quiz_task

load_dotenv()
MY_SECRET = os.getenv("STUDENT_SECRET")

app = FastAPI()

@app.post("/quiz")
async def start_quiz(task: QuizTask, background_tasks: BackgroundTasks):
    print(f"📨 Incoming: {task.url}")
    if task.secret != MY_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
    background_tasks.add_task(process_quiz_task, task.email, task.secret, str(task.url))
    return {"message": "Task accepted", "status": "processing"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)