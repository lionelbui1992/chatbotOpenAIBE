# -*- coding: utf-8 -*-

from flask import jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity
from core.domain import DomainObject
from core.user import User, UserSettings

from db import collection_users, collection_domain

import traceback


def auth_login(request):
    # Get the email and password from the request
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user = User()
    # Check if the email and password are valid
    if not email or not password:
        return {
            "status": "error",
            "message": "Email and password are required"
        }
    try:
        user.load(data)
        if user.login():
            user_data = user.to_dict()
            # remove password
            user_data.pop('password')
            # add tokens
            user_data['settings']['access_token'] = user.access_token
            user_data['settings']['refresh_token'] = user.refresh_token
            return {
                "status": "success",
                "message": "Login successful",
                "data": user_data
            }
        else:
            return {
                "status": "error",
                "message": "Invalid email or password"
            }
    except Exception:
        return {
            "status": "error",
            "message": traceback.format_exc()
        }


def auth_register(request):
    # validate data
    data = request.get_json()
    user = User()
    user.load(data)
    try:
        # Validate the user
        validate_messages = user.validate()
        if validate_messages:
            return {
                "status": "error",
                "message": "Invalid data\n" + "\n".join(validate_messages)
            }
        
        # Save the user
        user.register()

        user_data = user.to_dict()
        # remove password
        user_data.pop('password')
        # add tokens
        user_data['settings']['access_token'] = user.access_token
        user_data['settings']['refresh_token'] = user.refresh_token

        return {
            "status": "success",
            "message": "User registered",
            "data": user_data
        }

    except Exception:
        return {
            "status": "error",
            "message": traceback.format_exc()
        }

def auth_refresh_token():
    current_user_id = get_jwt_identity()
    if not current_user_id:
        return {
            "status": "error",
            "message": "Invalid user ID or token"
        }
    access_token = create_access_token(identity=current_user_id)
    return {
        "status": "success",
        "message": "Token refreshed",
        "data": {
            "access_token": access_token
        }
    }
