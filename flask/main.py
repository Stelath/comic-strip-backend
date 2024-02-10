from flask import Flask
from flask import send_from_directory

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/api/comic")
def generate_comic():
    return send_from_directory(directory='..', path='test.png')
