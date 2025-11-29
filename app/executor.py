import sys
import io
import os
import base64
import contextlib
import traceback
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import pypdf
import json
import zipfile
import requests
import bs4
from bs4 import BeautifulSoup
import re
import csv
from app.transcriber import transcribe_audio

DOWNLOAD_DIR = "downloads"


def execute_generated_code(code: str) -> dict:
    """
    Execute generated Python code in a sandboxed environment.
    
    Returns dict with:
        - success: bool
        - result: the value of 'solution' variable
        - image: base64 PNG if matplotlib figure was created
        - stdout: captured print output
        - error: traceback if execution failed
    """
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    def solve_audio_sync(filename):
        """Synchronous wrapper for audio transcription"""
        import asyncio
        filepath = os.path.join(DOWNLOAD_DIR, filename) if not filename.startswith(DOWNLOAD_DIR) else filename
        return asyncio.run(transcribe_audio(filepath))
    
    def safe_read_file(filepath):
        """Helper to read files with error handling"""
        full_path = os.path.join(DOWNLOAD_DIR, filepath) if not filepath.startswith(DOWNLOAD_DIR) else filepath
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        return None
    
    def list_downloads():
        """List all files in downloads directory"""
        if os.path.exists(DOWNLOAD_DIR):
            return os.listdir(DOWNLOAD_DIR)
        return []

    # Expose tools to the LLM-generated code
    local_scope = {
        # Data processing
        "pd": pd,
        "np": np,
        "plt": plt,
        "pypdf": pypdf,
        "json": json,
        "csv": csv,
        "re": re,
        
        # File handling
        "os": os,
        "zipfile": zipfile,
        "base64": base64,
        
        # Web/scraping
        "requests": requests,
        "bs4": bs4,
        "BeautifulSoup": BeautifulSoup,
        
        # Custom helpers
        "solve_audio": solve_audio_sync,
        "read_file": safe_read_file,
        "list_downloads": list_downloads,
        "DOWNLOAD_DIR": DOWNLOAD_DIR,
        
        # Output variable
        "solution": None
    }
    
    stdout_capture = io.StringIO()
    image_data = None
    
    # Clear any existing plots
    plt.clf()
    plt.close('all')

    try:
        # Execute the code
        with contextlib.redirect_stdout(stdout_capture):
            exec(code, {"__name__": "__main__", "__builtins__": __builtins__}, local_scope)
        
        # Check if a matplotlib figure was created
        if plt.get_fignums():
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            image_data = "data:image/png;base64," + base64.b64encode(buf.read()).decode('utf-8')
            plt.clf()
            plt.close('all')

        result = local_scope.get("solution")
        
        # Handle special case where solution is meant to be the plot
        if result == "USE_PLOT" and image_data:
            result = image_data

        # Clean up result - ensure it's serializable
        if result is not None:
            try:
                # Test JSON serialization
                json.dumps(result)
            except (TypeError, ValueError):
                # Convert to string if not serializable
                result = str(result)

        return {
            "success": True,
            "result": result,
            "image": image_data,
            "stdout": stdout_capture.getvalue(),
            "error": None
        }
        
    except SyntaxError as e:
        return {
            "success": False,
            "result": None,
            "image": None,
            "stdout": stdout_capture.getvalue(),
            "error": f"SyntaxError: {e}\nLine {e.lineno}: {e.text}"
        }
    except Exception as e:
        return {
            "success": False,
            "result": None,
            "image": None,
            "stdout": stdout_capture.getvalue(),
            "error": traceback.format_exc()
        }
    finally:
        # Cleanup
        plt.close('all')