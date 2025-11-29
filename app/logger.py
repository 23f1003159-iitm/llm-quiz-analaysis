import os
import json
import time
from datetime import datetime
import base64

LOG_DIR = "mission_logs"

class MissionLogger:
    def __init__(self, task_id: str):
        # Create a unique folder for this specific run
        timestamp = datetime.now().strftime('%H-%M-%S')
        # Clean up the URL to make it a valid folder name
        clean_id = str(task_id).replace(":", "").replace("/", "_")[-10:]
        
        self.dir = os.path.join(LOG_DIR, f"{timestamp}_{clean_id}")
        os.makedirs(self.dir, exist_ok=True)
        
        self.log_data = []
        print(f"📝 Logging mission to: {self.dir}")

    def log_step(self, step_name: str, details: dict, screenshot_b64: str = None):
        """Saves text logs and screenshot to disk"""
        entry = {
            "timestamp": time.time(),
            "step": step_name,
            "details": details
        }
        self.log_data.append(entry)
        
        # Save Screenshot if provided
        if screenshot_b64:
            try:
                img_path = os.path.join(self.dir, f"{step_name}.png")
                with open(img_path, "wb") as f:
                    f.write(base64.b64decode(screenshot_b64))
            except Exception as e:
                print(f"⚠️ Failed to save screenshot: {e}")

        # Update the master log file immediately
        try:
            with open(os.path.join(self.dir, "mission_report.json"), "w") as f:
                json.dump(self.log_data, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️ Failed to write log JSON: {e}")
            
    def error(self, error_msg):
        self.log_step("ERROR", {"error": str(error_msg)})