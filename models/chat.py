from bson import ObjectId
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from core.domain import DomainObject
from core.google_sheet import append_google_sheet_column
from core.google_sheet import delete_google_sheet_row
from core.google_sheet import get_credentials
from core.google_sheet import get_gspread_client
from core.google_sheet import get_service
from core.google_sheet import import_google_sheets_data
from core.google_sheet import pull_google_sheets_data
from core.google_sheet import update_many_row_value

from core.input_actions import create_domain_instructions
from core.openai import create_completion, create_embedding
from db import collection_embedded_server
from db import collection_action
from db import collection_attribute
from db import collection_users
from db import collection_spreadsheets
from db import truncate_collection

import json

def update_data_to_db(_id, plot):
    """
    Update data in the database with the given _id and plot.
    """
    collection_embedded_server.update_one(
        {"_id": _id},
        {"$set": {"plot": plot}}
    )
    return collection_embedded_server.find_one({"_id": _id})

def add_data_to_db(title, plot, embedding):
    """
    Add data to the database with the given title, plot, and embedding.
    """
    collection_embedded_server.insert_one(
        {
            "title": title,
            "plot": plot,
            "plot_embedding": embedding,
            "type": "server",
            "row_index": 0,
            "column_count": len(plot)
        }
    )
    return collection_embedded_server.find_one({"title": title})

def embedding_search_attribute(title, domain):
    """
    Search for attributes in the database based on the given title and domain.
    This is filter mapping, not sematic search
    """
    
    info_funtion = collection_attribute.aggregate([
        {
            '$match': {
                'title': title, 
                'domain': domain
            }
        }, {
            '$project': {
                'title': 1, 
                'column_index': 1, 
                'domain': 1
            }
        }
    ])

    # for message in info_funtion:
    #     print('>>>>>>>>>>>> search attribute: ', message.get('column_index', -1))
    
    return info_funtion

def embedding_search_total(search_vector, domain):
    """
    Search for total in the database based on the given searchVector and domain.
    """
    pipeline = [
    {
        '$vectorSearch': {
        'index': 'vector_index', 
        'path': 'plot_embedding', 
        'queryVector': search_vector, 
        'numCandidates': 150, 
        'limit': 1
        }
    }, {
        '$match': {
            'domain': domain
        }
    }, {
        '$project': {
        '_id': 1,
        'title': 1, 
        'total': 1,
        'domain': 1,
        'score': {
            '$meta': 'vectorSearchScore'
        }
        }
    }]
    info_funtion = collection_action.aggregate(pipeline)
    
    return info_funtion

def embedding_search_info(search_vector, domain, limit=100):
    """
    Search for information in the database based on the given search_vector, domain, and limit.
    """
    pipeline = [{
        '$vectorSearch': {
            'index': 'vector_index', 
            'path': 'plot_embedding', 
            'queryVector': search_vector, 
            'numCandidates': 150, 
            'limit': limit
        }
    }, {
        '$match': {
            'domain': domain
        }
    }, {
        '$project': {
            '_id': 1, 
            'plot': 1, 
            'title': 1, 
            'header_column': 1,
            'row_index': 1,
            'column_count': 1,
            'domain': 1,
            'score': {
                '$meta': 'vectorSearchScore'
            }
        }
    },
    {
        '$sort': {
            # sort by score in increasing order
            'score': -1
        }
    }]
    info_funtion = collection_embedded_server.aggregate(pipeline)
    
    return info_funtion

def embedding_search_action(search_vector):
    """
    Search for action in the database based on the given searchVector.
    """
    pipeline = [
    {
        '$vectorSearch': {
        'index': 'vector_index', 
        'path': 'plot_embedding', 
        'queryVector': search_vector, 
        'numCandidates': 150, 
        'limit': 1
        }
    }, {
        '$project': {
        '_id': 1, 
        'title': 1, 
        'score': {
            '$meta': 'vectorSearchScore'
        }
        }
    }]
    action_funtion = collection_action.aggregate(pipeline)
    action = 0
    for message in action_funtion:
        action = message['score']

    return action

def embedding_function(input_text):
    """
    Get the embedding for the given input_text.
    """
    response = create_embedding(input_string = input_text)
    return response.data[0].embedding

def get_chat_completions(request):
    """
    Get the chat completions based on the given request.
    """
    # ===================== End Instructions ========================================
    # Input text -> AI -> RAG -> (JSON) -> Google sheet action/ summary collection/ get information -> RAG -> output messages
    # ===================== Verify user =============================================
    current_user_id = get_jwt_identity()
    current_user = collection_users.find_one({"_id": ObjectId(current_user_id)})
    # ===================== End Verify user =========================================

    if not current_user:
        return {"error": "Invalid user ID or token"}

    # ===================== Input text ==============================================
    data            = request.get_json()
    domain          = DomainObject.load(current_user['domain'])
    input_messages  = data.get('messages', [])
    temp_messages   = []

    if not input_messages:
        return jsonify({"error": "No messages provided"})
    
    # get latest message content text
    input_text      = input_messages[-1].get('content', "")[0].get('text', "")
    # set first item content text from domain instructions
    input_messages[0]['content'][0]['text'] = domain.instructions

    # ===================== End Input text ==========================================


    # ===================== AI Analysis =============================================
    action_info = None
    try:
        action_completion = create_completion(messages=input_messages)
        # convert response to dictionary
        action_info = json.loads(action_completion.choices[0].message.content)
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('Action analysis: ', action_info, type(action_info))
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    except Exception as e:
        # this step can be skipped
        print(':::::::::::ERROR - get_analysis_input_action ', str(e))
        # assistant_message = {
        #     "role": "assistant",
        #     "content": "Sorry, I can't analyze the action, please try again!"
        # }
        # input_messages.append(assistant_message)
    # ===================== End AI Analysis =========================================


    # ===================== RAG =====================================================
    if action_info:
        action_do               = action_info.get('do_action', 'None') # 'Add row', Add column, Delete row, Delete column, Edit cell, Get summary, Get information, None
        action_status           = action_info.get('action_status', 'None') # 'ready_to_process', 'missing_data', 'None'
        action_message          = action_info.get('message', '')
        action_conditions:dict  = action_info.get('mongodb_condition_object', {})
        action_column_values    = action_info.get('column_values', [])
        action_replace_query    = action_info.get('replace_query', '')
        action_row_values       = action_info.get('row_values', [])
        action_url             = action_info.get('url', '')
        google_access_token     = current_user['settings']['googleAccessToken']
        google_selected_details = domain.googleSelectedDetails
        SPREADSHEET_URL         = 'https://docs.google.com/spreadsheets/d/{sheet_id}'.format(sheet_id=google_selected_details['sheetId'])
        creds                   = get_credentials(google_access_token)
        gspread_client          = get_gspread_client(creds)
        service                 = get_service(creds)

        # convert to dictionary if action_conditions is string
        if isinstance(action_conditions, str):
            action_conditions = json.loads(action_conditions)


        # "Add row", "Add column", "Delete row", "Delete column", "Edit cell" or "None", "Get summary", "Get information"
        if action_do == 'Add row' and action_status == 'ready_to_process':
            #  call append_google_sheet_row
            print(action_row_values)
            sheet = gspread_client.open_by_url(SPREADSHEET_URL).worksheet(google_selected_details['title'])
            try:
                # get values from action_row_values (not include key)
                values = [list(row.values()) for row in action_row_values]
                
                sheet.append_rows(values)
                temp_messages.append("Added {total_rows} rows".format(total_rows=len(values)))
            except Exception as e:
                temp_messages.append("Failed to add rows")
                print('>>>>>>>>>>>>>>>>>>>> "Add row" failed ', e)
            finally:
                chat_action_callback(domain, gspread_client)
        if action_do == 'Add column' and action_status == 'ready_to_process':
            print('>>>>>>>>>>>>>>>>>>>> "Add column"')
            for index, column_title in enumerate(action_column_values):
                try:
                    add_column_response = append_google_sheet_column(google_selected_details, gspread_client, column_title)
                    temp_messages.append(f"{index + 1}. Added new column: {column_title}")
                except Exception as e:
                    temp_messages.append(f"{index + 1}. Failed to add new column: {column_title}\n{add_column_response.message}")
                    print('>>>>>>>>>>>>>>>>>>>> "Add column" failed ', e)
            chat_action_callback(domain, gspread_client)
        if action_do == 'Delete row' and action_status == 'ready_to_process':
            print('>>>>>>>>>>>>>>>>>>>> "Delete row"')
            sheet                   = gspread_client.open_by_url(SPREADSHEET_URL).worksheet(google_selected_details['title'])
            # add domain filter
            print(action_conditions, type(action_conditions))
            action_conditions['domain'] = current_user['domain']

            print(action_conditions)
            # get row index from collection_spreadsheets from action_conditions
            query_result = list(collection_spreadsheets.find(action_conditions))
            # if no row found, return message
            if len(list(query_result)) == 0:
                temp_messages.append("No row found")
            row_indexes = []
            for row in query_result:
                row_indexes.append(row['row_index']) # row 0 is column heading
                print(row['row_index'], row['Projects'])
            total_rows = len(row_indexes)
            # reverse row_indexes to delete from last row
            row_indexes.reverse()
            delete_google_sheet_row(service, google_selected_details['sheetId'], sheet.id, row_indexes)
            try:
                # delete row from google sheet, index start from 1, index 0 is column heading
                temp_messages.append(f"Deleted {total_rows} rows")
            except Exception as e:
                print('>>>>>>>>>>>>>>>>>>>> "Delete {total_rows} rows" failed ', e)
            chat_action_callback(domain, gspread_client)

        if action_do == 'Delete column' and action_status == 'ready_to_process':
            print('>>>>>>>>>>>>>>>>>>>> "Delete column"')
            sheet                   = gspread_client.open_by_url(SPREADSHEET_URL).worksheet(google_selected_details['title'])
            # add domain filter
            print(action_conditions, type(action_conditions))
            action_conditions['domain'] = current_user['domain']
            print(action_conditions)
            temp_messages.append("Skip action...")
            chat_action_callback(domain, gspread_client)

        if action_do == 'Edit cell' and action_status == 'ready_to_process':
            print('>>>>>>>>>>>>>>>>>>>> "Edit cell"')
            # {'do_action': 'Edit cell', 'action_status': 'ready_to_process', 'message': '', 'mongodb_condition_object': {'Projects': 'American Club'}, 'column_values': [], 'replace_query': {'$set': {'Projects': 'Example project'}}, 'row_values': []}
            sheet                   = gspread_client.open_by_url(SPREADSHEET_URL).worksheet(google_selected_details['title'])

            # add domain filter
            print(action_conditions, type(action_conditions))
            action_conditions['domain'] = current_user['domain']

            print(action_conditions)

            try:
                # search for the row data:
                query_result = list(collection_spreadsheets.find(action_conditions))
                row_ids = []
                row_values = []
                # if no row found, return message
                if len(list(query_result)) == 0:
                    temp_messages.append("No row found")
                for row in query_result:
                    print('row index: ', row['row_index'])
                    row_ids.append(row['_id'])
                print(type(action_replace_query), action_replace_query)
                # if action_replace_query is not dict, convert to dict
                if isinstance(action_replace_query, str):
                    action_replace_query = json.loads(action_replace_query)
                print(type(action_replace_query), action_replace_query)
                update_result = collection_spreadsheets.update_many(action_conditions, action_replace_query)
                # get new values
                print('db update_result: ', update_result)
                print(update_result.matched_count, update_result.modified_count)
                # get new values
                query_result = collection_spreadsheets.find({'_id': {'$in': row_ids}})
                for row in query_result:
                    print('>>>>', row) # {'_id': ObjectId('66a327d8e663bce16b57b4a7'), 'ID': 1, 'Projects': 'Example project', 'Need to upgrade': '', 'Set Index , Follow': '', 'Auto Update': 'OFF', 'WP Version': '', 'Password': 'superadmin/lollimedia', 'Login Email': '', 'Site Url': ' https://100.americanclubhk.com', 'Comment': '', 'Polylang': 'FALSE', 'domain': 'domain-1', 'row_index': 1}
                    row.pop('_id')
                    row.pop('domain')
                    row_values.append(row)
                    # get values from row_values (not include key)
                update_response = update_many_row_value(service, google_selected_details['sheetId'], sheet.id, row_values)
                temp_messages.append(f"Found {update_result.matched_count} rows and updated {update_result.modified_count} rows")
                print('update_response: ', update_response)
                
            except Exception as e:
                print('>>>>>>>>>>>>>>>>>>>> "Edit cell" failed ', str(e))
                temp_messages.append("Failed to update cell")
            finally:
                chat_action_callback(domain, gspread_client)


        if action_do == 'Get summary' and action_status == 'ready_to_process':
            print('>>>>>>>>>>>>>>>>>>>> "Get summary"')
            # add domain filter
            action_conditions['domain'] = current_user['domain']
            infomation_result = collection_spreadsheets.count_documents(action_conditions)
            if infomation_result > 1:
                temp_messages.append(f"Found {infomation_result} rows")
            elif infomation_result == 1:
                temp_messages.append(f"Found {infomation_result} row")
            else:
                temp_messages.append("No row found")
        if action_do == 'Get information' and action_status == 'ready_to_process':
            print('>>>>>>>>>>>>>>>>>>>> "Get information"')
            # add domain filter
            action_conditions['domain'] = current_user['domain']
            infomation_result = list(collection_spreadsheets.find(action_conditions))
            # if no row found, return message
            if len(infomation_result) == 0:
                temp_messages.append("No data found")
            for index, info in enumerate(infomation_result):
                print('>>>>>>>>>>>>>>>>>>>> found info: ', info)
                info.pop('_id')
                info.pop('domain')
                info.pop('row_index')
                row_data = ', ' . join([f"{key}: {value}" for key, value in info.items()])
                temp_messages.append('{}. {}'.format(index + 1, row_data))
        if action_do == 'Insert from URL' and action_status == 'ready_to_process':
            print('>>>>>>>>>>>>>>>>>>>> "Insert from URL"')
            print(action_url)
            # get information from URL use gpt-4o
            try:
                heading_columns = ", ".join('"{column}"'.format(column=column) for column in domain.columns)
                completion = create_completion(messages=[
                    # alway return json string
                    {"role": "system", "content": "Your task is to extract specific information from the URL provided and format it as a JSON string. The JSON string should contain the following keys: {columns}".format(columns=heading_columns)},
                    {"role": "user", "content": "URL: {url}".format(url=action_url)},
                ])
                message_content = completion.choices[0].message.content
                # get content from ```json  ```
                if '```json' in message_content:
                    json_data = json.loads(message_content.split('```json')[1].split('```')[0])
                    print('json_data: ', json_data)
                else:
                    json_data = json.loads(completion.choices[0].message.content)
                    print('json_data: ', json_data)
                #  call append_google_sheet_row
                sheet = gspread_client.open_by_url(SPREADSHEET_URL).worksheet(google_selected_details['title'])
                # get value from json_data
                values = [list(json_data.values())]
                sheet.append_rows(values)
                temp_messages.append("Added {total_rows} rows\n\n{row_detail}".format(total_rows=len(values), row_detail=json_data))
                chat_action_callback(domain, gspread_client)
            except Exception as e:
                print('>>>>>>>>>>>>>>>>>>>> "Insert from URL" failed ', e)
                temp_messages.append("Failed to insert information from URL")


    # ===================== END RAG =================================================



    # ===================== End Instructions ========================================
    completion_dict = action_completion.to_dict()

    if temp_messages:
        action_message = action_message + "\n\n" + "\n\n".join(temp_messages)
        # need full json data, will be process in short time
        completion_dict['choices'][0]['message']['content'] = action_message

    # return the JSON string
    return completion_dict
   
def chat_action_callback(domain, gspread_client):
    """
    Chat action callback - re import google sheet data
    """
    try:
        # ===================== pull data ===============================================
        pull_google_response = pull_google_sheets_data(domain.googleSelectedDetails, gspread_client)
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
            except Exception as e:
                print(':::::::::::ERROR - import_google_sheets_data ', str(e))
        else:
            # ===================== pull data error =========================================
            print(':::::::::::ERROR - pull_google_sheets_data ', pull_google_response['message'])
    except Exception as e:
        print(':::::::::::ERROR - pull_google_sheets_data ', str(e))