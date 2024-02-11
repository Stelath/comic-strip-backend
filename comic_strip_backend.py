from flask import Flask, send_from_directory, request, jsonify
# from flask_cors import CORS

import os
from jobs_manager import JobManager

app = Flask(__name__, static_folder='client')
# CORS(app)

job_manager = JobManager()

# Serve React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    app.run(use_reloader=True, port=5000, threaded=True)

@app.route('/api/prompt', methods=['POST'])
def process_prompt():
    # Extract the prompt from the incoming request
    data = request.json  # Assuming the prompt is sent as JSON
    print(data)
    prompt = data.get('prompt')
    num_images = data.get('numImages')
    
    # Process the prompt (this example just echoes it back)
    response = {"receivedPrompt": prompt, "jobID": job_manager.new_job(prompt, num_images)}

    # Return the response as JSON
    return jsonify(response)

@app.route("/api/jobs/<job_id>", methods=['GET'])
def get_job_status(job_id):
    print(f"Getting job status for {job_id}")
    info = job_manager.get_job_info(job_id)
    
    return jsonify(info)

@app.route("/api/images/<job_id>/<path:name>", methods=['GET'])
def get_frame(job_id, name):
    return send_from_directory('generated_comics', os.path.join(job_id, 'frames', name))
