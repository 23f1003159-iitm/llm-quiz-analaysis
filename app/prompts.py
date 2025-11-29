# --- ROLE DEFINITIONS ---

PLANNER_SYSTEM_ROLE = """You are a precise task analyzer for automated quiz solving.
Your job is to extract EXACTLY three things from a quiz page:
1. The actual question/task (ignore examples, sample data, or instructions about format)
2. The submission URL where the answer should be POSTed
3. The expected answer format (number, string, list, dict, base64, etc.)

Be extremely careful to distinguish between:
- The ACTUAL task (what needs to be calculated/extracted)
- Example data shown on the page (ignore this)
- Sample JSON payloads (these show format, not actual values)

Always output valid JSON only."""

CODER_SYSTEM_ROLE = """You are an expert Python programmer for data extraction and analysis.
You write clean, self-contained Python scripts that solve data tasks.

CRITICAL RULES:
1. Output ONLY valid Python code - no explanations, no markdown
2. Assign your final answer to the variable `solution`
3. NEVER use requests.post() - only calculate/extract the answer
4. All downloaded files are in the 'downloads/' directory
5. Handle errors gracefully - don't let exceptions crash
6. solution MUST be a value (number, string, list, dict), NOT an error message

Available libraries: pandas, numpy, matplotlib, pypdf, json, os, zipfile, requests, bs4
For audio transcription: solve_audio(filename) returns the transcription"""

# --- DYNAMIC PROMPT GENERATORS ---

def generate_planning_prompt(page_text: str, files: list, links: list) -> str:
    links_str = "\n".join([f"- {l.get('text', '')}: {l.get('href', '')}" for l in links[:15]])
    
    return f"""Analyze this quiz page and extract the task details.

=== PAGE CONTENT ===
{page_text[:12000]}

=== AVAILABLE FILES ===
{files if files else "None downloaded yet"}

=== LINKS ON PAGE ===
{links_str if links_str else "No links found"}

=== YOUR TASK ===
Extract and return JSON with these exact keys:
{{
    "question": "The actual task to perform (what to calculate, extract, or analyze)",
    "submit_url": "The URL to POST the answer to (look for 'submit', 'answer', or POST endpoint)",
    "format_hint": "Expected answer type: number|string|list|dict|base64|json"
}}

IMPORTANT:
- The "question" should be the TASK, not example data
- Look for the submit URL in the instructions (often contains 'submit' or is mentioned after 'POST')
- If no submit URL is explicitly mentioned, look for any URL that seems like an endpoint

Return ONLY the JSON object, nothing else."""


def generate_coding_prompt(
    task: str, 
    files: list, 
    links: list, 
    format_hint: str, 
    previous_error: str = "", 
    server_feedback: str = ""
) -> str:
    links_str = "\n".join([f"  - {l.get('href', '')}" for l in links[:10] if l.get('href')])
    
    prompt = f"""Write Python code to solve this task.

=== TASK ===
{task}

=== AVAILABLE FILES (in 'downloads/' directory) ===
{files if files else "No files - may need to download from links"}

=== AVAILABLE LINKS ===
{links_str if links_str else "No links available"}

=== EXPECTED OUTPUT FORMAT ===
{format_hint}

=== REQUIREMENTS ===
1. Write complete, runnable Python code
2. Assign the final answer to `solution` variable
3. Files are in 'downloads/' directory (e.g., 'downloads/data.csv')
4. Use requests.get() for URLs, NOT requests.post()
5. Handle file not found or parsing errors gracefully
6. For PDFs, use pypdf.PdfReader
7. For Excel files, use pd.read_excel()
8. For CSV, use pd.read_csv()
9. For ZIP files, extract first then process

=== CODE TEMPLATE ===
import pandas as pd
import numpy as np
import json
import os
import requests
from bs4 import BeautifulSoup
import pypdf
import zipfile

# Your code here...

solution = YOUR_ANSWER_HERE  # Must be the actual answer value"""

    if previous_error:
        prompt += f"""

=== PREVIOUS ERROR (fix this) ===
{previous_error[:500]}

Fix the error and try a different approach."""

    if server_feedback:
        prompt += f"""

=== SERVER FEEDBACK (your answer was wrong) ===
{server_feedback}

Recalculate - your previous answer was incorrect."""

    return prompt


def fix_json_prompt(broken_json: str) -> str:
    return f"""Fix this malformed JSON and return ONLY valid JSON.

Broken input:
{broken_json[:2000]}

Return ONLY the corrected JSON object with keys: question, submit_url, format_hint"""