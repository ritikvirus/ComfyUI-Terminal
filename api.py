from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

# Define a list of allowed commands
ALLOWED_COMMANDS = {
    'list_files': 'ls -la',
    'check_python_version': 'python --version',
    'start_server': 'python -m http.server',
    # Add more predefined commands as needed
}

@app.route('/run', methods=['POST'])
def run_command():
    data = request.get_json()
    if not data or 'command_name' not in data:
        return jsonify({'error': 'No command_name provided'}), 400

    command_name = data['command_name']
    command = ALLOWED_COMMANDS.get(command_name)

    if not command:
        return jsonify({'error': 'Invalid or unauthorized command'}), 400

    try:
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return jsonify({'output': result.decode('utf-8')}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({'error': e.output.decode('utf-8')}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
