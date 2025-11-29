# --- ROLE DEFINITIONS ---

PLANNER_SYSTEM_ROLE = """
You are a Senior Data Forensic Analyst.
Your goal is to parse messy HTML and identify the exact data extraction task.
You are paranoid about "Decoy Data" (example JSONs, sample payloads).
You focus ONLY on the instructions that ask the user to perform a calculation or extraction.
"""

CODER_SYSTEM_ROLE = """
You are a Principal Python Architect.
You write flawless, robust code to extract data, process it, and return the raw result.
You handle all data types (Strings, Ints, Floats, Lists, Dicts) natively.
You NEVER submit data to a server using requests.post(). You only CALCULATE the answer.
"""

# --- DYNAMIC PROMPT GENERATORS ---

def generate_planning_prompt(page_text: str, files: list, links: list) -> str:
    return f"""
    === MISSION BRIEF ===
    [RESOURCES]
    - FILES: {files}
    - LINKS FOUND: {links}
    - PAGE TEXT:
    {page_text[:15000]}
    
    [OBJECTIVE]
    1. THE ACTUAL QUESTION:
       - If page says "Download X", X is the question.
       - If page says "Scrape /data", finding that data is the question.
       - IGNORE "Example JSON" shown on page.
    
    2. THE SUBMISSION URL.
    
    3. THE ANSWER FORMAT (Number, String, List, Dict).
    
    [OUTPUT]
    Return ONLY JSON:
    {{
        "question": "...",
        "submit_url": "...",
        "format_hint": "..."
    }}
    """

def generate_coding_prompt(task: str, files: list, links: list, format_hint: str, previous_error: str = "", server_feedback: str = "") -> str:
    prompt = f"""
    === CODING TASK ===
    GOAL: "{task}"
    FILES: {files} (in 'downloads/')
    LINKS: {links} (Use 'requests' to scrape these if needed)
    EXPECTED FORMAT: {format_hint}
    
    [INSTRUCTIONS]
    Write Python script to calculate the answer.
    
    1. DATA LOADING:
       - Use 'pandas' for CSV/Excel.
       - Use 'requests.get()' for scraping URLs (handle absolute/relative paths).
       - DO NOT use 'requests.post()'. You are forbidden from submitting data.
    
    2. OUTPUT ASSIGNMENT (CRITICAL):
       - Assign final result to `solution`.
       - `solution` MUST BE THE ANSWER VALUE (e.g. 600, "secret_code").
       - `solution` MUST NOT BE A DICT like {{'error': ...}}.
    """

    if previous_error:
        prompt += f"\n\n[PREVIOUS CODE ERROR]: {previous_error}\nFix Logic."

    if server_feedback:
        prompt += f"\n\n[SERVER REJECTED ANSWER]: {server_feedback}\nRe-calculate."

    return prompt

def fix_json_prompt(broken_json: str) -> str:
    return f"Return ONLY valid JSON. Broken string:\n{broken_json}"