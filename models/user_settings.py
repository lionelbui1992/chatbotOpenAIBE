from flask_jwt_extended import get_jwt_identity
from core.google_sheet import get_google_sheets_data
from core.input_actions import create_user_instructions
from db import collection_users
from bson.objectid import ObjectId

def get_user_settings():
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
        get_google_sheets_data(current_user, google_access_token, google_selected_details)
        instruction_prompt = create_user_instructions(current_user['domain'])
        current_user['settings']['instructions'] = instruction_prompt
    
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
    update_data = request.get_json().get('updateData')
    print(current_user_id, update_data)
    current_user = collection_users.find_one({"_id": ObjectId(current_user_id)})
    data = request.get_json()
    google_access_token = data.get('googleAccessToken')
    google_selected_details = data.get('googleSelectedDetails')
    old_google_selected_details = current_user['settings']['googleSelectedDetails']
    if current_user:
        response_message = {
            "status": "success",
            "message": ""
        }
        try:
            # update new data
            current_user['settings']['googleAccessToken'] = google_access_token
            current_user['settings']['googleSelectedDetails'] = google_selected_details
            collection_users.update_one({'_id': current_user['_id']}, {'$set': {'settings.googleAccessToken': google_access_token}})
            collection_users.update_one({'_id': current_user['_id']}, {'$set': {'settings.googleSelectedDetails': google_selected_details}})
            # update google sheet data if google sheet details are different
            if update_data or old_google_selected_details != google_selected_details:
                get_google_sheets_data(current_user, google_access_token, google_selected_details)
                instruction_prompt = create_user_instructions(current_user['domain'])
                current_user['settings']['instructions'] = instruction_prompt
                collection_users.update_one({'_id': current_user['_id']}, {'$set': {'settings.instructions': instruction_prompt}})
                response_message['data'] = {
                    "instructions": instruction_prompt
                }
                response_message['message'] = "Google settings updated and data retrieved"
            else:
                instruction_prompt = 'You are helpfull assistant'
                current_user['settings']['instructions'] = instruction_prompt
                collection_users.update_one({'_id': current_user['_id']}, {'$set': {'settings.instructions': instruction_prompt}})
                response_message['data'] = {
                    "instructions": instruction_prompt
                }
                response_message['message'] = "Google settings updated"
        except Exception as e:
            print(':::::::::::ERROR - set_user_setting_google ', str(e))
            response_message['status'] = "error"
            response_message['message'] = "An error occurred while updating settings" + str(e)
    else:
        response_message = {
            "status": "error",
            "message": "Invalid user token"
        }
    return response_message
