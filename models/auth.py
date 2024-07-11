from flask import jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity
from db import collection_users


def auth_login(request):
    # Get the email and password from the request
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    # Check if the email and password are valid
    if not email or not password:
        return {
            "status": "error",
            "message": "Email and password are required"
        }
    user = collection_users.find_one({"email": email, "password": password})
    if user:
        user_id = str(user['_id'])
        access_token = create_access_token(identity=user_id)
        refresh_token = create_refresh_token(identity=user_id)

        # save the token to the user
        collection_users.update_one({'_id': user_id}, {'$set': {'token': access_token}})

        return {
            "status": "success",
            "message": "Login successful",
            "data": {
                "user": {
                    "id": user_id,
                    "domain": str(user['domain']),
                    "email": str(user['email']),
                    "name": str(user['name']),
                    "settings": user['settings']
                },
                "token": access_token,
                "access_token": access_token,
                "refresh_token": refresh_token
            }
        }
    else:
        return {"status": "error", "message": "Invalid email or password"}


def auth_register(request):
    # Get the email and password from the request
    email = f"buiduyet.it1@gmail.com"
    # will be removed
    user = collection_users.find_one({"email": email})
    if user:
        collection_users.delete_one({"_id": user['_id']})
        print(f"Deleted user {user['_id']}")
    # will be removed
    
    data = request.get_json()
    domain = data.get('domain')
    email = data.get('email')
    password = data.get('password')
    re_password = data.get('re_password')

    # validate data
    if not domain:
        return {
            "status": "error",
            "message": "Domain is required"
        }
    if not email or not password:
        return {
            "status": "error",
            "message": "Email and password are required"
        }
    if password != re_password:
        return {
            "status": "error",
            "message": "Passwords do not match"
        }
    # Check if the email is already registered
    user = collection_users.find_one({"email": email})
    if user:
        return {
            "status": "error",
            "message": "Email is already registered"
        }
    # Create a new user
    user = {
        "domain": domain,
        "email": email,
        "name": email,
        "password": password,
        "settings": {
            "user_theme": "system",
            "theme": "light",
            "model": '',
            "instructions": "",
            "speechModel": "tts-1",
            "speechVoice": "echo",
            "speechSpeed": 1,
            "googleAccessToken": "",
            "googleSelectedDetails": [],
            "tag": ["server"]
        }
    }
    result = collection_users.insert_one(user)
    user_id = str(result.inserted_id)
    access_token = create_access_token(identity=user_id)
    refresh_token = create_refresh_token(identity=user_id)
    # save the token to the user
    collection_users.update_one({'_id': user_id}, {'$set': {'token': access_token}})

    return {
        "status": "success",
        "message": "User registered",
        "data": {
            "user": {
                "id": user_id,
                "domain": domain,
                "email": email,
                "name": email,
                "settings": user['settings']
            },
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    }

def auth_refresh_token(request):
    refresh_token = request.cookies.get('refreshToken')
    print(refresh_token)
    if not refresh_token:
        return {
            "status": "error",
            "message": "Missing refresh token"
        }
    current_user_id = get_jwt_identity(refresh_token)
    if not current_user_id:
        return {
            "status": "error",
            "message": "Invalid user ID or token"
        }
    access_token = create_access_token(identity=current_user_id)
    refresh_token = create_refresh_token(identity=current_user_id)
    return {
        "status": "success",
        "message": "Token refreshed",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    }
