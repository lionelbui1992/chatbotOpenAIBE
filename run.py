import time
from flask import Flask, request, jsonify, current_app
from flask_cors import CORS
from dotenv import load_dotenv
import os

from openai import OpenAI
from config import Config
from models.auth import auth_login
from models.chat import get_chat_completions
from models.models import get_models

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)  # Enable CORS for all domains

# Secret key for session management
app.secret_key = os.getenv('SECRET_KEY')

app.openAIClient = OpenAI(
    api_key=app.config['OPENAI_API_KEY'],
)

@app.route('/', methods=['GET', 'PUT', 'POST', 'OPTIONS'])
def index():
    if request.method == 'OPTIONS':
        return '', 200  # Handle preflight request for CORS
    # Handle GET, PUT, POST requests here
    return jsonify({'message': 'Welcome to the API!'})

# /api
@app.route('/api', methods=['GET', 'PUT', 'POST', 'OPTIONS'])
@app.route('/api/', methods=['GET', 'PUT', 'POST', 'OPTIONS'])
def api():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({'message': 'Welcome to the API!'})

# /api/v1
@app.route('/api/v1', methods=['GET', 'PUT', 'POST', 'OPTIONS'])
@app.route('/api/v1/', methods=['GET', 'PUT', 'POST', 'OPTIONS'])
def api_v1():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({'message': 'Welcome to the API v1!'})

# /auth

@app.route('/api/v1/auth', methods=['GET', 'PUT', 'POST', 'OPTIONS'])
@app.route('/api/v1/auth/', methods=['GET', 'PUT', 'POST', 'OPTIONS'])
def auth():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify(auth_login(request))


# /api/v1/chat
@app.route('/api/v1/chat', methods=['GET', 'PUT', 'POST', 'OPTIONS'])
@app.route('/api/v1/chat/', methods=['GET', 'PUT', 'POST', 'OPTIONS'])
def chat_v1():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({'message': 'Welcome to the Chat API v1!'})

# /api/v1/chat/completions
@app.route('/api/v1/chat/completions', methods=['GET', 'PUT', 'POST', 'OPTIONS'])
@app.route('/api/v1/chat/completions/', methods=['GET', 'PUT', 'POST', 'OPTIONS'])
def chat_completions_v1():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify(get_chat_completions(request))

# /api/v1/models
@app.route('/api/v1/models', methods=['GET', 'PUT', 'POST', 'OPTIONS'])
@app.route('/api/v1/models/', methods=['GET', 'PUT', 'POST', 'OPTIONS'])
def models_v1():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify(get_models(request))
if __name__ == '__main__':
    app.run(debug=True)
