from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS

from jobs_manager import JobManager

app = Flask(__name__)
CORS(app)

job_manager = JobManager()

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route('/api/prompt', methods=['POST'])
def process_prompt():
    # Extract the prompt from the incoming request
    data = request.json  # Assuming the prompt is sent as JSON
    print(data)
    prompt = data.get('prompt')
    
    # Process the prompt (this example just echoes it back)
    response = {"receivedPrompt": prompt, "jobId": job_manager.new_job(prompt)}

    # Return the response as JSON
    return jsonify(response)

@app.route("/api/jobs/<job_id>", methods=['GET'])
def get_job_status(job_id):
    info = job_manager.get_job_info(job_id)
    
    return jsonify(info)
