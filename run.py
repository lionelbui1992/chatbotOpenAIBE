from datetime import timedelta
import time
from flask import Flask, abort, json, request, jsonify, current_app
from flask_cors import CORS
from dotenv import load_dotenv
import os

from openai import OpenAI
from config import Config
from models.auth import auth_login, auth_refresh_token, auth_register
from models.chat import get_chat_completions
from models.models import get_models
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

from models.google import user_google_connect
from models.user_settings import get_user_settings, set_user_settings

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
bcrypt = Bcrypt(app)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15)  # Access token expiration time
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)  # Refresh token expiration time
jwt = JWTManager(app)

users = []  # Temporary in-memory user store

# Configure CORS to allow all domains for all routes and methods
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "PUT", "POST", "DELETE", "OPTIONS"], "allow_headers": ["Authorization", "Content-Type"]}})

# Secret key for session management
# app.secret_key = os.getenv('SECRET_KEY')

app.openAIClient = OpenAI(
    api_key=app.config['OPENAI_API_KEY'],
)

@app.after_request
def after_request_func(response):
    if response.is_json:
        data = response.get_json()
        msg = data.get('msg')
        if msg:
            data['message'] = msg
            response.set_data(json.dumps(data))
    # response.headers.add('Access-Control-Allow-Origin', '*')
    # response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    # response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


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
    return jsonify({'message': 'Welcome to the Auth API v1!'})


# /api/v1/auth/login
@app.route('/api/v1/auth/login', methods=['POST', 'OPTIONS'])
@app.route('/api/v1/auth/login/', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
    auth_data = auth_login(request)
    if auth_data['status'] == 'success':
        return jsonify(auth_data)
    else:
        return jsonify(auth_data), 401


@app.route('/api/v1/auth/register', methods=['POST', 'OPTIONS'])
@app.route('/api/v1/auth/register/', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 200
    auth_data = auth_register(request)
    if auth_data['status'] == 'success':
        return jsonify(auth_data)
    else:
        return jsonify(auth_data), 401

# /api/v1/auth/refreshtoken
@app.route('/api/v1/auth/refreshtoken', methods=['POST', 'OPTIONS'])
@app.route('/api/v1/auth/refreshtoken/', methods=['POST', 'OPTIONS'])
@jwt_required(refresh=True)
def refreshtoken():
    if request.method == 'OPTIONS':
        return '', 200
    data = auth_refresh_token()
    if data['status'] == 'success':
        return jsonify(data)
    else:
        return jsonify(data), 401


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
    data = get_models()
    if data['status'] == 'success':
        return jsonify(data)
    else:
        return jsonify(data), 401

# /api/v1/settings/google
@app.route('/api/v1/settings/google', methods=['GET', 'PUT', 'POST', 'OPTIONS'])
@app.route('/api/v1/settings/google/', methods=['GET', 'PUT', 'POST', 'OPTIONS'])
def settings_google_v1():
    if request.method == 'OPTIONS':
        return '', 200
    data = user_google_connect(request)
    if data['status'] == 'success':
        return jsonify(data)
    else:
        return jsonify(data), 401

# /api/v1/user
@app.route('/api/v1/user', methods=['GET', 'PUT', 'POST', 'OPTIONS'])
@app.route('/api/v1/user/', methods=['GET', 'PUT', 'POST', 'OPTIONS'])
def user_v1():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({'message': 'Welcome to the User API v1!'})

# /api/v1/user/settings
@app.route('/api/v1/user/settings', methods=['GET', 'PUT', 'OPTIONS'])
@app.route('/api/v1/user/settings/', methods=['GET', 'PUT', 'OPTIONS'])
@jwt_required()
def user_settings_v1():
    if request.method == 'OPTIONS':
        return '', 200
    switcher = {
        'GET': get_user_settings,
        'PUT': set_user_settings
    }
    data = switcher[request.method](request)
    if data['status'] == 'success':
        return jsonify(data)
    else:
        return jsonify(data), 401

if __name__ == '__main__':
    app.run(debug=True)
