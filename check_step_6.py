from app.logger import MissionLogger
import os
import shutil

def test_logger():
    print("📝 Testing Mission Logger...")
    
    # 1. Initialize Logger
    task_id = "http://google.com/test_quiz"
    logger = MissionLogger(task_id)
    
    # 2. Log a Fake Step
    print("   Logging a test step...")
    logger.log_step("TEST_STEP", {"message": "Hello World", "status": "ok"})
    
    # 3. Verify Files Exists
    log_dir = logger.dir
    json_path = os.path.join(log_dir, "mission_report.json")
    
    if os.path.exists(json_path):
        print(f"✅ PASSED: Log file created at {json_path}")
        print("\n🎉 Step 6 Complete! Your Agent has a Black Box.")
    else:
        print("❌ FAILED: Log file was not created.")

if __name__ == "__main__":
    test_logger()