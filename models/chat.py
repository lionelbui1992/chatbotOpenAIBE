from bson import ObjectId
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from core.domain import DomainObject
from core.google_sheet import append_google_sheet_column, append_google_sheet_row, get_gspread_client, update_google_sheet_data
from core.input_actions import get_analysis_input_action
from core.openai import create_completion, create_embedding
from db import collection_embedded_server, collection_action, collection_attribute, collection_users

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
        temp_messages = []
        action_do               = action_info.get('do_action', 'None') # 'Add row', Add column, Delete row, Delete column, Edit cell, Get summary, Get information, None
        action_status           = action_info.get('action_status', 'None') # 'ready_to_process', 'missing_data', 'None'
        action_message          = action_info.get('message', '')
        action_conditions       = action_info.get('conditions', [])
        action_column_selector  = action_info.get('column_selector', [])
        action_value_to_replace = action_info.get('value_to_replace', '')
        action_row_values       = action_info.get('row_values', [])


        # "Add row", "Add column", "Delete row", "Delete column", "Edit cell" or "None", "Get summary", "Get information"
        if action_do == 'Add row' and action_status == 'ready_to_process':
            #  call append_google_sheet_row
            google_access_token     = current_user['settings']['googleAccessToken']
            google_selected_details = domain.googleSelectedDetails
            gspread_client          = get_gspread_client(google_access_token)
            print(action_row_values)
            for index, new_item in enumerate(action_row_values):
                new_item_string = ', '.join([f"{key}: {value}" for key, value in new_item.items()])

                print('>>>>>>>>>>>>>>>>>>>> "Add row" new_item: ', new_item_string)
                try:
                    add_row_response = append_google_sheet_row(google_selected_details, gspread_client, new_item)
                    temp_messages.append(f"{index + 1}. {new_item_string} -> Added.")
                except Exception as e:
                    temp_messages.append(f"{index + 1}. {new_item_string} -> Failed.")
                    print('>>>>>>>>>>>>>>>>>>>> "Add row" failed ', e)
        if action_do == 'Add column':
            print('>>>>>>>>>>>>>>>>>>>> "Add column"')
        if action_do == 'Delete row':
            print('>>>>>>>>>>>>>>>>>>>> "Delete row"')
        if action_do == 'Delete column':
            print('>>>>>>>>>>>>>>>>>>>> "Delete column"')
        if action_do == 'Edit cell':
            print('>>>>>>>>>>>>>>>>>>>> "Edit cell"')
        if action_do == 'Get summary':
            print('>>>>>>>>>>>>>>>>>>>> "Get summary"')
        if action_do == 'Get information':
            print('>>>>>>>>>>>>>>>>>>>> "Get information"')
    # ===================== END RAG =================================================



    # ===================== End Instructions ========================================
    completion_dict = action_completion.to_dict()

    if temp_messages:
        action_message = action_message + "\n" + "\n".join(temp_messages)
        # need full json data, will be process in short time
        completion_dict['choices'][0]['message']['content'] = action_message

    # return the JSON string
    return completion_dict
    messages = []
    # message only get latest item from input_messages

    if not input_messages:
        return jsonify({"error": "No messages provided"})
    
    # get latest message content text
    latest_message = input_messages[-1].get('content', "")
    input_text = latest_message[0].get('text', "")

    # handle action
    print('==================== HANDLE ACTIONS')
    action_info =[]
    target_action = ""
    column_index = ""
    print('>>>>>>>>>>>>>>>>>>>> analysis text for action')
    try:
        target_action = "has_action"
        action_info = get_analysis_input_action(input_text=input_text, domain=current_user['domain'])
        # Convert action_info string to dictionary
        print('action_info: ', action_info)
        action_info_dict = json.loads(action_info)

        # Get the action, title, old_value, and new_value from the dictionary
        action = action_info_dict.get('action', 'None')
        column_title = action_info_dict.get('column_title', 'None')

        if action != 'None':
            # update google sheet data
            old_value = action_info_dict.get('old_value', '')
            new_value = action_info_dict.get('new_value', '')
            new_items = action_info_dict.get('values', [])
            column_index = -1
            row_index = -1
            if column_title != 'None':
                # get column_index from collection_attribute
                search_attribute = embedding_search_attribute(column_title, current_user['domain'])
                # print('search_attribute: ', search_attribute)
                for message in search_attribute:
                    print('>>>>> found column: ', message.get('column_index', 0))
                    column_index = message.get('column_index', -1)
                    # if message['score'] > 0.8:
                    #     column_index = message['column_index']
                    #     column_name = chr(65 + column_index)
            if action == 'Add row':
                # update google sheet data
                print('>>>>>>>>>>>>>>>>>>>> "Add row"')
                # get latest row_index
                if new_items != []:
                    temp_message = ''
                    # new_items is an array of items to be added
                    for index, new_item in enumerate(new_items):
                        print('>>>>>>>>>>>>>>>>>>>> "Add row" new_item: ', new_item, type(new_item))
                        new_item_string = ', '.join([f"{key}: {value}" for key, value in new_item.items()])

                        print('>>>>>>>>>>>>>>>>>>>> "Add row" new_item: ', new_item_string)
                        # new_item will be {'ID': '14', 'Projects': 'Citic', 'Need to upgrade': '', 'Set Index , Follow': '', 'Auto Update': 'OFF', 'WP Version': '', 'Password': 'Citicpacific123#@!', 'Login Email': 'cyrus@lolli.com.hk', 'Site Url': 'https://www.citicpacific.com/en/', 'Comment': '', 'Polylang': 'TRUE'}, {}, {'ID': '30', 'Projects': 'GIBF', 'Need to upgrade': '', 'Set Index , Follow': '', 'Auto Update': '', 'WP Version': '', 'Password': '5PYSO9tONhpfztggNyry(%uM', 'Login Email': 'cyrus@lolli.com.hk', 'Site Url': 'https://gibf-bio.com', 'Comment': 'There is a pending change of your email to cyrus@lolli.com.hk', 'Polylang': 'FALSE'}
                        add_row_response = append_google_sheet_row(current_user, new_item)
                        if add_row_response.status == 'success':
                            temp_message += f"{index + 1}. {new_item_string} -> Added\n"
                        else:
                            temp_message += f"{index + 1}. {new_item_string} -> Failed\n"
                    messages.append({"role": "system", "content": f"Added new row: {temp_message}"})
                else:
                    messages.append({"role": "system", "content": "No new row have been added"})
            elif action == 'Add column':
                # update google sheet data
                print('>>>>>>>>>>>>>>>>>>>> "Add column"')
                try:
                    add_column_response = append_google_sheet_column(current_user, column_title)
                    if add_column_response.status == 'success':
                        messages.append({"role": "system", "content": f"Added new column: {column_title}"})
                        print('>>>>>>>>>>>>>>>>>>>> "Add column" success')
                    else:
                        messages.append({"role": "system", "content": "Sorry, I can't add the new column, please try again! {add_column_response.message}"})
                        print('>>>>>>>>>>>>>>>>>>>> "Add column" failed')
                except Exception as e:
                    print('>>>>>>>>>>>>>>>>>>>> "Add column" failed ', e)
                    messages.append({"role": "system", "content": "Sorry, I can't add the new column, please try again! {e}"})
            else:
                print('>>>>>>>>>>>>>>>>>>>> "Modify"')
                # search for the row_index
                sheet_result = collection_embedded_server.find({
                    'domain': current_user['domain'],
                    'plot': {'$elemMatch': {'$eq': old_value}}
                })
                if sheet_result:
                    for message in sheet_result:
                        row_index = message['row_index']
                        print('>>>>>>>>>>>>>>>>>>>> found row: ', row_index)
                if row_index != -1 and column_index != -1:
                    update_google_sheet_data(current_user, new_value, column_index, row_index + 1)
                    messages.append({"role": "system", "content": f"Information has been updated: {old_value} -> {new_value} at row {row_index + 1}, column {column_index}"})
                else:
                    messages.append({"role": "system", "content": "No information has been updated"})

        else:
            print('==================== NO ACTION')
            target_action = "no_action"

        print('>>>>>>>>>>>>>>>>>>>> end analysis text for action')
        # update_data_to_db(_id, full_plot)
    except Exception as e:
        print('==================== ERROR HANDLE ACTIONS')
        print(e)
        messages.append({"role": "system", "content": "Sorry, I can't update the information, please try again!"})
    print('==================== END HANDLE ACTIONS')
    # end handle action
    # print("target_action: ", target_action)
    completion = []
    print('>>>>>>>>>>>> show_messages', messages)
    if target_action == "has_action":
        completion = create_completion(messages)

    try:
        print('>>>>>>>>>>>> search server embedding')
        # get the embedding
        search_vector = embedding_function(input_text)
        # run pipeline
        aggregate_result    = embedding_search_info(search_vector, current_user['domain'], 5)
        print("aggregate_result: ", aggregate_result)
        header_column       = ""
        score               = 0
        full_plot           = ""
        target_score       = 0 # target score to show message

        for message in aggregate_result:
            # title = message['title']
            score = message['score']
            print("message: ", message['title'])
            print("score: ", score)

            target_score = 1
            index = 0
            for value in message['plot']:
                if value == "":
                    value = ""
                # check if value is not string, convert to string
                if not isinstance(value, str):
                    value = str(value)
                
                if index < len(message['header_column']):
                    print(index)
                    print(len(message['header_column']))
                    header_column = message['header_column'][index] # index
                else:
                    header_column = ""

                full_plot = full_plot + header_column + ":" + value + ", "
                index += 1

            messages.append({"role": "assistant", "content": full_plot })
               
    except Exception as e:
        messages.append({"role": "system", "content": e.message})
        print(e)

    messages.append({"role": "user", "content":input_text})
    
    if(target_score == 0):
        completion = create_completion(messages)
    else:
        messages.append({"role": "user", "content":"WITH ABOVE INFORMATIONS ONLY"})
        completion = create_completion(messages)

    completion_dict = completion.to_dict()

    for choice in completion_dict['choices']:
        choice['delta'] = choice['message']

    # return the JSON string
    return completion_dict
    
   