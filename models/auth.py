from flask import jsonify
from flask_jwt_extended import create_access_token
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
        # format:
        # {
        #     "status": "success",
        #     "message": "Login successful",
        #     "data": {
        #         "user": {
        #         "id": "",
        #         "email": "",
        #         "name": ""
        #         },
        #         "token": ""
        #     }
        # }

        user_id = str(user['_id'])

        access_token = create_access_token(identity=user_id)

        # save the token to the user
        collection_users.update_one({'_id': user['_id']}, {'$set': {'token': access_token}})

        return {
            "status": "success",
            "message": "Login successful",
            "data": {
                "user": {
                    "id": user_id,
                    "email": str(user['email']),
                    "name": str(user['name']),
                    "settings": user['settings']
                },
                "token": access_token
            }
        }
    else:
        return {"status": "error", "message": "Invalid email or password"}


def auth_register(request):
    # Get the email and password from the request
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
            "sheet_name": "",
            "spreadsheet_id": "",
            "tag": "server"
        }
    }
    result = collection_users.insert_one(user)
    user_id = str(result.inserted_id)
    access_token = create_access_token(identity=user_id)
    
    return {
        "status": "success",
        "message": "User registered",
        "data": {
            "user": {
                "id": user_id,
                "email": email,
                "name": email,
                "settings": {
                    "sheet_name": "",
                    "spreadsheet_id": "",
                    "tag": "server"
                }
            },
            "token": access_token
        }
    }