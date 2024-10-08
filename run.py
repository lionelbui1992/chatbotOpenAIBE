# -*- coding: utf-8 -*-

from flask import Flask
from flask import json
from flask import redirect
from flask import request
from flask import jsonify

from flask_cors import CORS

from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required

from flask_pymongo import PyMongo

from dotenv import load_dotenv

from openai import OpenAI
import requests

from config import Config

from core.domain import DomainObject
from models.auth import auth_login
from models.auth import auth_refresh_token
from models.auth import auth_register

from models.chat import get_chat_completions

from models.models import get_models

from models.user_settings import get_user_settings
from models.user_settings import set_user_setting_google
from models.user_settings import set_user_settings

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
bcrypt = Bcrypt(app)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 86400  # 1 day
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 2592000  # 30 days
jwt = JWTManager(app)

users = []  # Temporary in-memory user store

# Configure CORS to allow all domains for all routes and methods
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "PUT", "POST", "DELETE", "OPTIONS"], "allow_headers": ["Authorization", "Content-Type"]}})


app.openAIClient = OpenAI(
    api_key=app.config['OPENAI_API_KEY'],
)

app.mongo = PyMongo(app)

@app.after_request
def after_request_func(response):
    if response.is_json:
        data = response.get_json()
        msg = data.get('msg')
        if msg:
            data['message'] = msg
            response.set_data(json.dumps(data))
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
def auth_v1():
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
@jwt_required()
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
    
# /api/v1/user/google
@app.route('/api/v1/user/google', methods=['PUT', 'OPTIONS'])
@app.route('/api/v1/user/google/', methods=['PUT', 'OPTIONS'])
@jwt_required()
def user_settings_google_v1():
    if request.method == 'OPTIONS':
        return '', 200
    data = set_user_setting_google(request)
    if data['status'] == 'success':
        return jsonify(data)
    else:
        return jsonify(data), 401

@app.route('/api/v1/user/auth')
def auth():
    auth_url = (
        f"{Config.GOOGLE_AUTHORIZATION_URL}?response_type=code"
        f"&client_id={Config.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={Config.GOOGLE_REDIRECT_URI}"
        f"&scope=https://www.googleapis.com/auth/drive.metadata.readonly "
        f"https://www.googleapis.com/auth/spreadsheets.readonly"
        f"&access_type=offline"
    )
    return redirect(auth_url)

@app.route('/api/v1/user/oauth2callback')
def oauth2callback():
    code = request.args.get('code')
    data = {
        'code': code,
        'client_id': Config.GOOGLE_CLIENT_ID,
        'client_secret': Config.GOOGLE_CLIENT_SECRET,
        'redirect_uri': Config.GOOGLE_REDIRECT_URI,
        'grant_type': 'authorization_code',
    }
    response = requests.post(Config.GOOGLE_TOKEN_URL, data=data)
    token_response = response.json()
    return jsonify(token_response)

@app.route('/api/v1/user/save', methods=['POST'])
def save_user():
    user_info = request.json
    # Save user information to your database
    print('Received user info:', user_info)
    return jsonify({'message': 'User info saved successfully'})

@app.route('/api/v1/user/saveDetails', methods=['POST'])
def save_details():
    details = request.json
    # Save the selected details to your database
    print('Received selected details:', details)
    return jsonify({'message': 'Selected details saved successfully'})

# domain
@app.route('/api/v1/domain', methods=['GET', 'PUT', 'POST', 'OPTIONS'])
@app.route('/api/v1/domain/', methods=['GET', 'PUT', 'POST', 'OPTIONS'])
def domain_v1():
    if request.method == 'OPTIONS':
        return '', 200
    # call DomainObject methods here: load_all
    try:
        data = DomainObject.load_all()
        domain_list = [{'name': d.name, 'label': d.label} for d in data]
        return jsonify({'status': 'success', 'data': domain_list})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
