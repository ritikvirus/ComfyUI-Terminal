import subprocess
import os
import threading
import sys
import time
from flask import Flask, request, jsonify

def setup_app():
    app = Flask(__name__)

    @app.route('/run', methods=['POST'])
    def run_command():
        data = request.get_json()
        if not data or 'command' not in data:
            return jsonify({'error': 'No command provided'}), 400

        command = data['command']

        try:
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            return jsonify({'output': result.decode('utf-8')}), 200
        except subprocess.CalledProcessError as e:
            return jsonify({'error': e.output.decode('utf-8')}), 400
        except Exception as e:
            # Log unexpected exceptions
            print(f"Exception occurred while executing command: {e}")
            return jsonify({'error': str(e)}), 500

    return app

class Terminal:
    port = 7860

    def __init__(self):
        pass  # No need to start the API here; we'll handle it in execute()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "command": ("STRING", {"multiline": False}),
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
            # No process running on the port
            pass

    def is_port_in_use(self, port):
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    def start_api(self):
        app = setup_app()
        app.run(host='0.0.0.0', port=self.port, threaded=True, use_reloader=False, debug=False)

    def execute(self, command):
        # First, check if the API is running
        if not self.is_port_in_use(self.port):
            # Kill any process on the port
            self.kill_process_on_port(self.port)
            # Start the API server
            print("Starting API...")
            # Start the API server in a separate process
            command_to_run = [sys.executable, os.path.abspath(__file__), 'start_api']
            subprocess.Popen(command_to_run, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            print("Waiting for API to start...")
            time.sleep(2)
        else:
            print("API already running.")
        # Now execute the command via the API
        import requests
        try:
            response = requests.post(f'http://localhost:{self.port}/run', json={'command': command})
            response.raise_for_status()  # Raise an exception for HTTP errors
            output = response.json().get('output', '')
            return (output,)
        except requests.exceptions.HTTPError as e:
            # Handle HTTP errors
            try:
                error = response.json().get('error', 'Unknown error')
                return (f"Error: {error}",)
            except ValueError:
                # Response wasn't JSON
                return (f"HTTP Error: {response.status_code} {response.reason}",)
        except requests.exceptions.ConnectionError:
            return ("Error: Could not connect to the API.",)
        except Exception as e:
            return (f"Unexpected error: {str(e)}",)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'start_api':
        # Start the Flask app
        app = setup_app()
        app.run(host='0.0.0.0', port=7860, threaded=True, use_reloader=False, debug=False)
