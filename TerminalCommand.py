import subprocess
import os
import threading
import sys
import time
from flask import Flask, request, jsonify

class Terminal:
    def __init__(self):
        # Initialize the Flask app within the class
        self.app = Flask(__name__)
        self.setup_routes()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "command_name": ("STRING", {"multiline": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "execute"
    CATEGORY = "utils"

    # Define allowed commands
    ALLOWED_COMMANDS = {
        'list_files': 'ls -la',
        'check_python_version': 'python --version',
        'start_server': 'python -m http.server',
        # Add more predefined commands as needed
    }

    def setup_routes(self):
        # Define the API route within the class
        @self.app.route('/run', methods=['POST'])
        def run_command():
            data = request.get_json()
            if not data or 'command_name' not in data:
                return jsonify({'error': 'No command_name provided'}), 400

            command_name = data['command_name']
            command = self.ALLOWED_COMMANDS.get(command_name)

            if not command:
                return jsonify({'error': 'Invalid or unauthorized command'}), 400

            try:
                result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
                return jsonify({'output': result.decode('utf-8')}), 200
            except subprocess.CalledProcessError as e:
                return jsonify({'error': e.output.decode('utf-8')}), 400

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

    def start_api(self):
        # Run the Flask app in a separate thread
        self.app.run(host='0.0.0.0', port=7860, threaded=True)

    def execute(self, command_name):
        port = 7860
        self.kill_process_on_port(port)
        print("Starting API...")
        # Start the API server in a new thread
        api_thread = threading.Thread(target=self.start_api, daemon=True)
        api_thread.start()
        print("Waiting for API to start...")
        time.sleep(2)
        # Now execute the command via the API
        import requests
        try:
            response = requests.post(f'http://localhost:{port}/run', json={'command_name': command_name})
            if response.status_code == 200:
                output = response.json().get('output', '')
                return (output,)
            else:
                error = response.json().get('error', 'Unknown error')
                return (f"Error: {error}",)
        except requests.exceptions.ConnectionError:
            return ("Error: Could not connect to the API.",)
