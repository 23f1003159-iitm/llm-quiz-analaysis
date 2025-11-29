# LLM Quiz God Mode 🤖

An intelligent agent system that uses LLMs to solve web-based quiz challenges by scraping content, downloading files, analyzing data, and submitting answers automatically.

## ✨ Features

- **Smart Scraping**: Automatically extracts text, links, and downloads files from web pages
- **LLM-Powered Analysis**: Uses AI models (GPT-5-nano and Gemini) to understand questions and generate solutions
- **Code Execution Sandbox**: Safely executes generated Python code to process data
- **Mission Logging**: Tracks all operations with screenshots and detailed logs
- **Secure API**: Authentication system to protect against unauthorized access

## 🚀 Quick Start

### Prerequisites

- Python 3.11
- uv (Python package manager)

### Installation

1. **Install dependencies**:
```bash
uv pip install -r requirements.txt
```

2. **Install Playwright browsers**:
```bash
python -m playwright install chromium
```

3. **Configure environment variables**:

Create a `.env` file with:
```env
STUDENT_EMAIL="your_email@example.com"
STUDENT_SECRET="your_secret_password"
AIPIPE_TOKEN="your_aipipe_token"
GEMINI_API_KEY="your_gemini_api_key"
```

### Verification

Run the comprehensive test suite to verify everything is working:

```bash
python run_all_tests.py
```

This will automatically:
- ✅ Check all dependencies are installed
- ✅ Test LLM connectivity
- ✅ Verify code executor
- ✅ Test mission logger
- ✅ Start servers and test API security
- ✅ Test smart scraper functionality

## 📋 Manual Testing (Step by Step)

### Step 1: Check Environment
```bash
python check_step_1.py
```
Verifies all required libraries (fastapi, playwright, pandas, etc.) are installed.

### Step 2: Test Server Security (requires servers running)
```bash
# Terminal 1 - Start main server
python -m uvicorn app.main:app --port 8000

# Terminal 2 - Start test server
python tests/dummy_advanced.py

# Terminal 3 - Run test
python check_step_2.py
```
Tests that the API correctly blocks invalid credentials and accepts valid ones.

### Step 3: Test LLM Connection
```bash
python check_step_3.py
```
Verifies the AI can answer simple questions.

### Step 4: Test Smart Scraper (requires servers running)
```bash
# With servers still running from Step 2
python check_step_4.py
```
Tests that the agent can download files from web pages.

### Step 5: Test Code Executor
```bash
python check_step_5.py
```
Verifies the sandbox can execute generated code safely.

### Step 6: Test Mission Logger
```bash
python check_step_6.py
```
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
