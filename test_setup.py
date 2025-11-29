#!/usr/bin/env python3
"""
Quick test script to verify the LLM Quiz Solver setup.
Run this before deployment to check everything works.
"""

import asyncio
import os
import sys

def print_status(name: str, passed: bool, details: str = ""):
    icon = "✅" if passed else "❌"
    print(f"{icon} {name}: {'PASS' if passed else 'FAIL'} {details}")


def test_imports():
    """Test that all required modules can be imported"""
    required = [
        "fastapi",
        "uvicorn", 
        "httpx",
        "playwright",
        "pandas",
        "numpy",
        "matplotlib",
        "pypdf",
        "bs4",
        "dotenv",
        "pydantic",
        "tenacity"
    ]
    
    all_passed = True
    for module in required:
        try:
            __import__(module)
            print_status(f"Import {module}", True)
        except ImportError as e:
            print_status(f"Import {module}", False, str(e))
            all_passed = False
    
    return all_passed


def test_env_vars():
    """Test that required environment variables are set"""
    from dotenv import load_dotenv
    load_dotenv()
    
    required = ["STUDENT_SECRET", "AIPIPE_TOKEN"]
    optional = ["OPENAI_API_KEY"]
    
    all_required_present = True
    for var in required:
        value = os.getenv(var)
        if value:
            print_status(f"Env {var}", True, "(configured)")
        else:
            print_status(f"Env {var}", False, "(MISSING - required)")
            all_required_present = False
    
    for var in optional:
        value = os.getenv(var)
        if value:
            print_status(f"Env {var}", True, "(configured)")
        else:
            print_status(f"Env {var}", True, "(not set - optional)")
    
    return all_required_present


async def test_llm_connection():
    """Test that LLM API is reachable"""
    from app.llm import ask_llm
    
    try:
        result = await ask_llm("What is 2+2? Reply with just the number.")
        if "4" in result:
            print_status("LLM Connection", True, f"Response: {result[:50]}")
            return True
        else:
            print_status("LLM Connection", False, f"Unexpected: {result[:100]}")
            return False
    except Exception as e:
        print_status("LLM Connection", False, str(e))
        return False


def test_executor():
    """Test code execution sandbox"""
    from app.executor import execute_generated_code
    
    code = """
import pandas as pd
data = {'a': [1, 2, 3], 'b': [4, 5, 6]}
df = pd.DataFrame(data)
solution = int(df['a'].sum())
"""
    
    result = execute_generated_code(code)
    
    if result["success"] and result["result"] == 6:
        print_status("Code Executor", True, f"Result: {result['result']}")
        return True
    else:
        print_status("Code Executor", False, f"Error: {result.get('error', 'Unknown')[:100]}")
        return False


async def test_playwright():
    """Test Playwright browser"""
    from playwright.async_api import async_playwright
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://example.com")
            title = await page.title()
            await browser.close()
            
            if "Example" in title:
                print_status("Playwright Browser", True, f"Title: {title}")
                return True
            else:
                print_status("Playwright Browser", False, f"Unexpected title: {title}")
                return False
    except Exception as e:
        print_status("Playwright Browser", False, str(e))
        return False


async def main():
    print("=" * 60)
    print("LLM Quiz Solver - Setup Verification")
    print("=" * 60)
    print()
    
    results = []
    
    print("📦 Checking imports...")
    results.append(test_imports())
    print()
    
    print("🔐 Checking environment variables...")
    results.append(test_env_vars())
    print()
    
    print("🤖 Testing LLM connection...")
    results.append(await test_llm_connection())
    print()
    
    print("⚙️ Testing code executor...")
    results.append(test_executor())
    print()
    
    print("🌐 Testing Playwright browser...")
    results.append(await test_playwright())
    print()
    
    print("=" * 60)
    if all(results):
        print("🎉 All tests passed! Ready for deployment.")
        return 0
    else:
        print("⚠️ Some tests failed. Please fix before deployment.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
