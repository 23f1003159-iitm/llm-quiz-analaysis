# LLM Quiz Solver 🤖

An intelligent agent system that uses LLMs to solve web-based quiz challenges by scraping content, downloading files, analyzing data, and submitting answers automatically.

## ✨ Features

- **Smart Scraping**: Automatically extracts text, links, and downloads files from JavaScript-rendered web pages
- **LLM-Powered Analysis**: Uses AI models (GPT-4.1-nano) to understand questions and generate solutions
- **Code Execution Sandbox**: Safely executes generated Python code to process data
- **Mission Logging**: Tracks all operations with screenshots and detailed logs
- **Secure API**: Authentication via secret matching (HTTP 400 for invalid JSON, 403 for invalid secrets)
- **Auto-retry**: Intelligent retry logic with different approaches on failure

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Playwright browsers

### Installation

1. **Clone and setup**:
```bash
git clone <your-repo-url>
cd llm_quiz_god_mode
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. **Install Playwright browsers**:
```bash
python -m playwright install chromium
```

3. **Configure environment variables**:

Create a `.env` file:
```env
STUDENT_SECRET="your_secret_from_google_form"
AIPIPE_TOKEN="your_aipipe_token"
OPENAI_API_KEY="optional_openai_key_for_whisper"
```

### Running the Server

```bash
# Development
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Exposing via ngrok (for public endpoint)

```bash
ngrok http 8000
```

Use the generated HTTPS URL as your API endpoint in the Google Form.

## 📡 API Specification

### POST /quiz

Receives quiz tasks from the evaluation server.

**Request Body:**
```json
{
  "email": "your_email@example.com",
  "secret": "your_secret",
  "url": "https://tds-llm-analysis.s-anand.net/quiz-xxx"
}
```

**Responses:**
- `200 OK`: Task accepted, processing in background
- `400 Bad Request`: Invalid JSON payload
- `403 Forbidden`: Invalid secret

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "secret_configured": true
}
```

## 🧪 Testing

Test with the demo endpoint:
```bash
curl -X POST http://localhost:8000/quiz \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your_email",
    "secret": "your_secret",
    "url": "https://tds-llm-analysis.s-anand.net/demo"
  }'
```

## 📁 Project Structure

```
llm_quiz_god_mode/
├── app/
│   ├── main.py        # FastAPI server with endpoints
│   ├── agent.py       # Main quiz solving logic
│   ├── llm.py         # LLM API integration
│   ├── prompts.py     # System and user prompts
│   ├── executor.py    # Code execution sandbox
│   ├── scraper.py     # Web scraping utilities
│   ├── transcriber.py # Audio transcription (Whisper)
│   ├── logger.py      # Mission logging
│   └── models.py      # Pydantic models
├── downloads/         # Temporary file downloads
├── mission_logs/      # Execution logs and screenshots
├── requirements.txt
├── Dockerfile
└── README.md
```

## 🔧 How It Works

1. **Receive Task**: POST request with quiz URL
2. **Scrape Page**: Load JavaScript-rendered page, extract text/links, download files
3. **Plan**: LLM analyzes page to extract question, submit URL, and format hint
4. **Execute**: LLM generates Python code to solve the task
5. **Submit**: POST answer to the submit URL
6. **Iterate**: Handle response, retry if wrong, proceed to next question if correct

## 📝 Supported Question Types

- CSV/Excel data analysis
- PDF text extraction
- API data fetching
- Web scraping
- Image/chart generation
- Audio transcription
- Mathematical calculations
- JSON manipulation

## ⚠️ Important Notes

- The endpoint must respond within 3 minutes of receiving the original POST
- Answers can be: boolean, number, string, base64 URI, or JSON object
- JSON payload must be under 1MB
- Do not hardcode any URLs - always parse from quiz page
Checks that operations are logged correctly.

## 🎯 Running the Full Agent

### Start the Servers

**Terminal 1 - Main API Server (port 8000)**:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Test Quiz Server (port 8002)**:
```bash
python tests/dummy_advanced.py
```

### Run the Test

**Terminal 3 - Execute Test**:
```bash
python test_dummy_advanced.py
```

This will:
1. Send a quiz task to the agent
2. Agent visits the test page
3. Downloads the CSV file
4. Analyzes the data using LLM
5. Calculates the answer (sum of values)
6. Submits the answer
7. Logs everything to `mission_logs/`

## 📁 Project Structure

```
llm_quiz_god_mode/
├── app/
│   ├── main.py          # FastAPI server
│   ├── agent.py         # Main agent logic with retry and multi-model support
│   ├── llm.py           # LLM interface (AIPIPE + Gemini)
│   ├── scraper.py       # Smart web scraper with Playwright
│   ├── executor.py      # Safe code execution sandbox
│   ├── logger.py        # Mission logging system
│   ├── prompts.py       # LLM prompt templates
│   ├── models.py        # Pydantic data models
│   └── transcriber.py   # Audio transcription (placeholder)
├── tests/
│   ├── dummy_advanced.py # Test quiz server
│   └── data/
│       └── secret.csv    # Test data file
├── check_step_*.py      # Individual verification scripts
├── run_all_tests.py     # Comprehensive test runner
├── test_dummy_advanced.py # Full integration test
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Project configuration
└── .env                 # Environment variables (not in repo)
```

## 🔧 Configuration

### LLM Models

The agent uses a fallback strategy:
1. **GPT-5-nano** (fast, via AIPIPE)
2. **GPT-5-nano** (retry)
3. **Gemini-1.5-flash** (deep analysis)

Configure in `app/agent.py`:
```python
MODELS = ["openai/gpt-5-nano", "openai/gpt-5-nano", "gemini-1.5-flash"]
```

### Timeouts

- Page load: 45 seconds
- Network idle: 10 seconds
- Total mission: 175 seconds

### Downloads

All downloaded files are saved to `downloads/` directory.

### Logs

Mission logs with screenshots are saved to `mission_logs/[timestamp]_[task_id]/`.

## 🛡️ Security

The API uses secret-based authentication:
- Set `STUDENT_SECRET` in `.env`
- All requests must include the correct secret
- Invalid attempts return 403 Forbidden

## 🐛 Troubleshooting

### Import Errors
```bash
uv pip install -r requirements.txt
python -m playwright install chromium
```

### Server Connection Errors
Make sure both servers are running:
- Main server on port 8000
- Test server on port 8002

### LLM Errors
Check your API keys in `.env`:
- `AIPIPE_TOKEN` for GPT models
- `GEMINI_API_KEY` for Gemini models

### Browser Errors
Reinstall Playwright browsers:
```bash
python -m playwright install chromium
```

## 📊 Example Output

```
🚀 Mission Level: http://localhost:8002/test_page
👀 Scraped Text: 423 chars | Links: 2
📋 Question: Read the file and calculate the sum of the 'value' column.
🧠 Format Hint: number
💡 Generated Answer: 600 (Model: openai/gpt-5-nano)
📤 Submitting to http://localhost:8002/submit...
📬 Server said: {'correct': True, 'message': '🎉 You Win! The Agent works!'}
✅ Correct! Mission complete!
```

## 🎓 How It Works

1. **Receive Task**: API receives quiz URL via POST request
2. **Observe**: Scraper visits page, extracts text, downloads files
3. **Plan**: LLM analyzes page and identifies the question
4. **Execute**: LLM generates Python code to solve the problem
5. **Submit**: Agent submits answer to quiz server
6. **Log**: All steps recorded with screenshots

## 🔄 Retry Strategy

- 3 attempts per question with different models
- Incorporates previous errors into next attempt
- Uses server feedback to refine answers

## 📝 License

MIT

## 🤝 Contributing

This is a demonstration project. Feel free to fork and modify!

## 📮 Support

Check the logs in `mission_logs/` for detailed debugging information.

---

**Status**: ✅ All systems operational - Ready to solve quizzes!
