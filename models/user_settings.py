from flask_jwt_extended import get_jwt_identity
from core.google_sheet import get_google_sheets_data
from db import collection_users
from bson.objectid import ObjectId

def get_user_settings(request):
    current_user_id = get_jwt_identity()
    current_user = collection_users.find_one({"_id": ObjectId(current_user_id)})
    if current_user:
        return {
            "status": "success",
            "message": "User settings retrieved",
            "data": {
                "settings": current_user['settings']
            }
        }
    else:
        return {
            "status": "error",
            "message": "Invalid user ID or token"
        }

def set_user_settings(request):
    current_user_id = get_jwt_identity()
    current_user = collection_users.find_one({"_id": ObjectId(current_user_id)})
    data = request.get_json()
    removed_keys = [
        'token',
        'domain',
        'email',
        'name',
        'user_id'
    ]
    for key in removed_keys:
        data.pop(key, None)
    current_user['settings'] = data

    google_access_token = data.get('googleAccessToken')
    google_selected_details = data.get('googleSelectedDetails')

    if google_access_token and google_selected_details:
        get_google_sheets_data(google_access_token, google_selected_details)
    
    if current_user:
        collection_users.update_one({'_id': current_user['_id']}, {'$set': {'settings': data}})
        return {
            "status": "success",
            "message": "User settings updated",
            "data": {
                "settings": current_user['settings']
            }
        }
    else:
        return {
            "status": "error",
            "message": "Invalid user ID or token"
        }

def set_user_setting_google(request):
    current_user_id = get_jwt_identity()
    print(current_user_id)
    current_user = collection_users.find_one({"_id": ObjectId(current_user_id)})
    data = request.get_json()
    googleAccessToken = data.get('googleAccessToken')
    googleSelectedDetails = data.get('googleSelectedDetails')
    if current_user and googleAccessToken and googleSelectedDetails:
        # only migrate if old data is different from new data
        if current_user['settings'].get('googleAccessToken') != googleAccessToken or current_user['settings'].get('googleSelectedDetails') != googleSelectedDetails:
            try:
                data = get_google_sheets_data(googleAccessToken, googleSelectedDetails)
                current_user['settings']['googleAccessToken'] = googleAccessToken
                current_user['settings']['googleSelectedDetails'] = googleSelectedDetails
                collection_users.update_one({'_id': current_user['_id']}, {'$set': {'settings': current_user['settings']}})
                return {
                    "status": "success",
                    "message": "Google settings updated"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": "An error occurred while retrieving data" + str(e)
                }
    else:
        return {
            "status": "error",
            "message": "Invalid user ID or token"
        }
