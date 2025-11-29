import sys
import io
import os
import base64
import contextlib
import traceback
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pypdf
import json
import zipfile
import requests
import bs4
from app.transcriber import transcribe_audio

DOWNLOAD_DIR = "downloads"

def execute_generated_code(code: str) -> dict:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    def solve_audio_sync(filename):
        import asyncio
        return asyncio.run(transcribe_audio(os.path.join(DOWNLOAD_DIR, filename)))

    # EXPOSE POWERFUL TOOLS TO LLM
    local_scope = {
        "pd": pd, "np": np, "plt": plt, "pypdf": pypdf,
        "json": json, "os": os, "zipfile": zipfile,
        "requests": requests, "bs4": bs4,
        "solve_audio": solve_audio_sync,
        "solution": None
    }
    
    stdout_capture = io.StringIO()
    image_data = None
    plt.clf()

    try:
        with contextlib.redirect_stdout(stdout_capture):
            exec(code, {"__name__": "__main__"}, local_scope)
        
        if plt.get_fignums():
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            image_data = "data:image/png;base64," + base64.b64encode(buf.read()).decode('utf-8')
            plt.clf()

        result = local_scope.get("solution")
        if result == "USE_PLOT": result = image_data

        return {
            "success": True, "result": result, "image": image_data,
            "stdout": stdout_capture.getvalue(), "error": None
        }
    except Exception as e:
        return {
            "success": False, "result": None, "image": None,
            "stdout": stdout_capture.getvalue(), "error": traceback.format_exc()
        }