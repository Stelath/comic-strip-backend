from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route('/api/prompt', methods=['POST'])
def process_prompt():
    # Extract the prompt from the incoming request
    data = request.json  # Assuming the prompt is sent as JSON
    print(data)
    prompt = data.get('prompt')
    
    print(f"Received prompt: {prompt}")
    # Process the prompt (this example just echoes it back)
    response = f"Received prompt: {prompt}"

    # Return the response as JSON
    return jsonify({'response': response})

@app.route("/api/jobs/<job_id>", methods=['GET'])
def get_job_status(job_id):
    # Replace this with your job status logic
    return jsonify({'status': 'completed', 'job_id': job_id})
