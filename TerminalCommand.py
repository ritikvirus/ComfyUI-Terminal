from subprocess import getoutput
import subprocess
import os
import threading
import sys

class Terminal:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "execute"
    CATEGORY = "utils"

    def kill_process_on_port(self, port):
        try:
            # For Unix-like systems
            result = subprocess.check_output(f"lsof -ti:{port}", shell=True)
            pids = result.decode().strip().split('\n')
            for pid in pids:
                if pid:
                    os.kill(int(pid), 9)
        except subprocess.CalledProcessError:
            try:
                # For Windows systems
                result = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True)
                lines = result.decode().strip().split('\n')
                for line in lines:
                    if line:
                        parts = line.strip().split()
                        pid = parts[-1]
                        subprocess.call(f"taskkill /PID {pid} /F", shell=True)
            except Exception as e:
                print(f"Could not kill process on port {port}: {e}")

    def start_api(self):
        # Path to your API script
        api_script = os.path.join(os.path.dirname(__file__), 'api.py')
        subprocess.Popen([sys.executable, api_script])

    def execute(self, text):
        # First kill port 7860 and start the API
        port = 7860
        self.kill_process_on_port(port)
        threading.Thread(target=self.start_api).start()
        # Now execute the command
        out = getoutput(f"{text}")
        return (out,)
