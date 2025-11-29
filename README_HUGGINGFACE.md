---
title: LLM Quiz God Mode
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
---

# LLM Quiz God Mode 🤖

An intelligent agent system that uses LLMs to solve web-based quiz challenges by scraping content, downloading files, analyzing data, and submitting answers automatically.

## Features

- **Smart Scraping**: Automatically extracts text, links, and downloads files from web pages
- **LLM-Powered Analysis**: Uses AI models (GPT-5-nano and Gemini) to understand questions and generate solutions
- **Code Execution Sandbox**: Safely executes generated Python code to process data
- **Mission Logging**: Tracks all operations with screenshots and detailed logs
- **Secure API**: Authentication system to protect against unauthorized access

## Usage

This Space runs a FastAPI server that accepts quiz tasks via POST requests.

### API Endpoint

**POST** `/quiz`

**Request Body:**
```json
{
  "email": "your_email@example.com",
  "secret": "your_secret_key",
  "url": "https://quiz-url.com"
}
```

**Response:**
```json
{
  "message": "Task accepted",
  "status": "processing"
}
```

### Environment Variables

Configure these secrets in your Hugging Face Space settings:

- `STUDENT_EMAIL`: Your email address
- `STUDENT_SECRET`: Authentication secret for API access
- `AIPIPE_TOKEN`: Token for OpenAI models via AIPIPE
- `GEMINI_API_KEY`: Google Gemini API key

## How It Works

1. **Receive Task**: API receives quiz URL via POST request
2. **Observe**: Scraper visits page, extracts text, downloads files
3. **Plan**: LLM analyzes page and identifies the question
4. **Execute**: LLM generates Python code to solve the problem
5. **Submit**: Agent submits answer to quiz server
6. **Log**: All steps recorded with screenshots

## Models Used

The agent uses a fallback strategy:
1. GPT-5-nano (fast, via AIPIPE)
2. GPT-5-nano (retry)
3. Gemini-1.5-flash (deep analysis)

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Client    │────▶│  FastAPI     │────▶│   Agent     │
│             │     │  Server      │     │   System    │
└─────────────┘     └──────────────┘     └─────────────┘
                                                │
                    ┌───────────────────────────┼───────────────────┐
                    ▼                           ▼                   ▼
              ┌──────────┐              ┌─────────────┐     ┌──────────┐
              │ Scraper  │              │     LLM     │     │ Executor │
              │(Playwright)              │(GPT/Gemini) │     │ (Sandbox)│
              └──────────┘              └─────────────┘     └──────────┘
```

## GitHub Repository

Full source code and documentation: [github.com/23f1003159-iitm/llm-quiz-analaysis](https://github.com/23f1003159-iitm/llm-quiz-analaysis)

## License

MIT
