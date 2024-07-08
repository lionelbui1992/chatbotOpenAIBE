from db import collection_users

def get_user_settings(request):
    data = request.get_json()
    user_id = data.get('user_id')
    user_token = data.get('user_token')
    user = collection_users.find_one({"_id": user_id, "token": user_token})
    if user:
        return {
            "status": "success",
            "message": "User settings retrieved",
            "data": {
                "settings": user['settings']
            }
        }
    else:
        return {
            "status": "error",
            "message": "Invalid user ID or token"
        }
def set_user_settings(request):
    data = request.get_json()
    user_id = data.get('user_id')
    user_token = data.get('user_token')
    user = collection_users.find_one({"_id": user_id, "token": user_token})
    if user:
        collection_users.update_one({'_id': user['_id']}, {'$set': {'settings': data['settings']}})
        return {
            "status": "success",
            "message": "User settings updated",
            "data": {
                "settings": user['settings']
            }
        }
    else:
        return {
            "status": "error",
            "message": "Invalid user ID or token"
        }
