from flask_jwt_extended import get_jwt_identity

from core.domain import DomainObject
from core.google_sheet import get_credentials, import_google_sheets_data, pull_google_sheets_data, get_gspread_client
from core.input_actions import create_domain_instructions

from db import collection_users, collection_spreadsheets
from db import truncate_collection

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
    current_user_id         = get_jwt_identity()
    current_user            = collection_users.find_one({"_id": ObjectId(current_user_id)})
    data                    = request.get_json()
    google_access_token     = data.get('googleAccessToken')
    google_selected_details = data.get('googleSelectedDetails')
    creds                   = get_credentials(google_access_token)
    gspread_client          = get_gspread_client(creds)


    # ===================== Clean data ==============================================
    removed_keys = [
        'token',
        'domain',
        'email',
        'name',
        'user_id',
        'googleSelectedDetails',
        'instructions'
    ]

    for key in removed_keys:
        data.pop(key, None)

    if len(google_selected_details) > 0:
        google_selected_details = google_selected_details[0]
    else:
        google_selected_details = {}
    # ===================== End Clean data ==========================================

    # validate from db
    if current_user:
        current_user['settings'] = data
        domain = DomainObject.load(current_user['domain'])
        domain.googleSelectedDetails = google_selected_details
        response_message = {
            "status": "success",
            "message": ""
        }

        # ===================== Update user settings ====================================
        collection_users.update_one({'_id': current_user['_id']}, {'$set': {'settings': data}})
        # ===================== End Update user settings ================================

        instruction_prompt = 'You are helpfull assistant'

        if google_selected_details:
            # ===================== pull data ===============================================
            pull_google_response = pull_google_sheets_data(google_selected_details, gspread_client)
            if pull_google_response['status'] == 'success':
                # ===================== pull data success =======================================
                rows = pull_google_response['data']
                # get column titles, remove empty keys
                column_titles = list(rows[0].keys())
                column_titles = [title for title in column_titles if title]
                domain.columns = column_titles

                # remove old data
                truncate_collection(collection_spreadsheets, domain.name)

                # import data to db
                try:
                    import_google_sheets_data(domain, rows)
                    #  rebuild instructions

                    instruction_prompt = create_domain_instructions(domain)
                    # print('instruction_prompt', instruction_prompt)
                    if (len(rows) > 1):
                        response_message['message'] = 'From spreadsheet, imported ' + str(len(rows) - 1) + ' rows imported'
                    elif len(rows) == 1:
                        response_message['message'] = 'From spreadsheet, imported ' + str(len(rows)) + ' row imported'
                    else:
                        response_message['message'] = 'No data imported'
                except Exception as e:
                    print(':::::::::::ERROR - import_google_sheets_data ', str(e))
                    response_message['status'] = "error"
                    response_message['message'] = "An error occurred while importing data" + str(e)
            else:
                # ===================== pull data error =========================================
                response_message['message'] = pull_google_response['message']
        else:
            domain.columns = []
            # ===================== end pull data ===========================================


        # ===================== Instructions ============================================
        current_user['settings']['instructions'] = instruction_prompt
        domain.instructions = instruction_prompt
        # ===================== End Instructions ========================================

        domain.update()

        response_message['data'] = {
            "instructions": instruction_prompt
        }
        # except Exception as e:
        #     print(':::::::::::ERROR - set_user_setting_google ', str(e))
        #     response_message['status'] = "error"
        #     response_message['message'] = "An error occurred while updating settings" + str(e)
    else:
        response_message = {
            "status": "error",
            "message": "Invalid user token"
        }
    response_message['data'] = {
        "settings": current_user['settings']
    }
    return response_message

def set_user_setting_google(request):
    current_user_id         = get_jwt_identity()
    current_user            = collection_users.find_one({"_id": ObjectId(current_user_id)})
    data                    = request.get_json()
    google_access_token     = data.get('googleAccessToken')
    google_selected_details = data.get('googleSelectedDetails', [])
    creds                   = get_credentials(google_access_token)
    gspread_client          = get_gspread_client(creds)

    # ===================== Clean data ==============================================
    if len(google_selected_details) > 0:
        google_selected_details = google_selected_details[0]
    else:
        google_selected_details = {}
    # ===================== End Clean data ==========================================

    # validate from db
    if current_user:
        domain = DomainObject.load(current_user['domain'])

        domain.googleSelectedDetails = google_selected_details
        response_message = {
            "status": "success",
            "message": ""
        }

        # ===================== Update user google token ================================
        current_user['settings']['googleAccessToken'] = google_access_token
        current_user['settings']['googleSelectedDetails'] = google_selected_details
        collection_users.update_one({'_id': current_user['_id']}, {'$set': {'settings.googleAccessToken': google_access_token}})
        # ===================== End Update user google token ============================

        instruction_prompt = 'You are helpfull assistant'

        if google_selected_details:
            # ===================== pull data ===============================================
            pull_google_response = pull_google_sheets_data(google_selected_details, gspread_client)
            if pull_google_response['status'] == 'success':
                # ===================== pull data success =======================================
                rows = pull_google_response['data']
                # get column titles, remove empty keys
                column_titles = list(rows[0].keys())
                column_titles = [title for title in column_titles if title]
                domain.columns = column_titles

                # remove old data
                truncate_collection(collection_spreadsheets, domain.name)

                # import data to db
                try:
                    import_google_sheets_data(domain, rows)

                    #  rebuild instructions

                    instruction_prompt = create_domain_instructions(domain)
                    # print('instruction_prompt', instruction_prompt)

                    if (len(rows) > 1):
                        response_message['message'] = 'From spreadsheet, imported ' + str(len(rows) - 1) + ' rows imported'
                    elif len(rows) == 1:
                        response_message['message'] = 'From spreadsheet, imported ' + str(len(rows)) + ' row imported'
                    else:
                        response_message['message'] = 'No data imported'
                except Exception as e:
                    print(':::::::::::ERROR - import_google_sheets_data ', str(e))
                    response_message['status'] = "error"
                    response_message['message'] = "An error occurred while importing data" + str(e)
            else:
                # ===================== pull data error =========================================
                response_message['message'] = pull_google_response['message']
        else:
            domain.columns = []
            # ===================== end pull data ===========================================


        # ===================== Instructions ============================================
        current_user['settings']['instructions'] = instruction_prompt
        domain.instructions = instruction_prompt
        # ===================== End Instructions ========================================

        domain.update()

        response_message['data'] = {
            "instructions": instruction_prompt
        }
        # except Exception as e:
        #     print(':::::::::::ERROR - set_user_setting_google ', str(e))
        #     response_message['status'] = "error"
        #     response_message['message'] = "An error occurred while updating settings" + str(e)
    else:
        response_message = {
            "status": "error",
            "message": "Invalid user token"
        }
    return response_message
