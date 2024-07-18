from bson import ObjectId
from flask import jsonify, current_app
from flask_jwt_extended import get_jwt_identity
from core.google_sheet import append_google_sheet_column, append_google_sheet_row, update_google_sheet_data
from core.input_actions import get_analysis_input_action
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

def embedding_search_total(searchVector, domain):
    """
    Search for total in the database based on the given searchVector and domain.
    """
    pipeline = [
    {
        '$vectorSearch': {
        'index': 'vector_index', 
        'path': 'plot_embedding', 
        'queryVector': searchVector, 
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

def embedding_search_info(searchVector, domain, limit=100):
    """
    Search for information in the database based on the given searchVector, domain, and limit.
    """
    pipeline = [{
        '$vectorSearch': {
            'index': 'vector_index', 
            'path': 'plot_embedding', 
            'queryVector': searchVector, 
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

def embedding_search_action(searchVector):
    """
    Search for action in the database based on the given searchVector.
    """
    pipeline = [
    {
        '$vectorSearch': {
        'index': 'vector_index', 
        'path': 'plot_embedding', 
        'queryVector': searchVector, 
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
    response = current_app.openAIClient.embeddings.create(
        input=input_text,
        model=current_app.config['EMBEDDING_MODEL']
    )
    return response.data[0].embedding

def show_message(messages):
    """
    Show the message based on the given messages.
    """
    completion = current_app.openAIClient.chat.completions.create(
        model=current_app.config['OPENAI_MODEL'],
        messages= messages
    )
    #print("total tockens", completion.choices[0].message.total_tokens)
    return completion

def get_chat_completions(request):
    """
    Get the chat completions based on the given request.
    """
    print('>>>>>>>>>>>> verify user')
    current_user_id = get_jwt_identity()
    current_user = collection_users.find_one({"_id": ObjectId(current_user_id)})

    if not current_user:
        return {"error": "Invalid user ID or token"}
    
    domain = current_user['domain']


    data = request.get_json()
    input_messages = data.get('messages', [])
    messages = []
    # message only get latest item from input_messages
    # messages.append(input_messages[-1].copy())

    # print("messages: ", messages)
    if not input_messages:
        return jsonify({"error": "No messages provided"})
    
    # get latest message content text
    latest_message = input_messages[-1].get('content', "")
    input_text = latest_message[0].get('text', "")
    #print("messages: ", input_text)

    # print('>>>>>>>>>>>> get input data: ', input_text)

    print('>>>>>>>>>>>> search server embedding')
    # get the embedding
    search_vector = embedding_function(input_text)
    # end get the embedding
    # handle search info
    # has_attribute = False
    _id = ""
    full_plot = []
    search_info = embedding_search_info(search_vector, domain, 1)
    if search_info:
    #    has_attribute = True
       for message in search_info:
            _id = message['_id']
            row_index = message['row_index']
            full_plot = message['plot']
            # print('==================== search info', message)
    # handle total

    print('>>>>>>>>>>>> search vector for "total" in collection_action: ')

    # total_row = 0
    search_total = embedding_search_total( embedding_function('total'), domain)
    if search_total:
        for message in search_total:
            total_row = message['total']
            print('>>>>>>>>>>>> setup total_row value: ', message)

    # handle action
    print('==================== HANDLE ACTIONS')
    # print('>>>>>>>>>>>>>>>>>>>> search vector for "action" in collection_action: ')
    # action_score_status = False
    for input_single_word in input_text.split(" "):
        search_vector_i_s_w = embedding_function(input_single_word)
        action_score = embedding_search_action(search_vector_i_s_w)
        # print("action_score: ", action_score, "search text: ", input_single_word)
        # if  action_score > 0.7:
        #     # action_score_status = True
        #     break
    # print('>>>>>>>>>>>>>>>>>>>> end search vector for "action" in collection_action: ')
    

    action_info =[]
    target_action = ""
    # rage = ""
    column_index = ""
    # column_name = ""

    print('>>>>>>>>>>>>>>>>>>>> analysis text for action')
    try:
        target_action = "has_action"
        action_info = get_analysis_input_action(input_text, domain)

        # Convert action_info string to dictionary
        action_info_dict = json.loads(action_info)

        # Get the action, title, old_value, and new_value from the dictionary
        action = action_info_dict.get('action', 'None')
        column_title = action_info_dict.get('column_title', 'None')

        if action != 'None':
            # update google sheet data
            old_value = action_info_dict.get('old_value', '')
            new_value = action_info_dict.get('new_value', '')
            new_items = action_info_dict.get('new_items', [])
            column_index = -1
            row_index = -1
            if column_title != 'None':
                # get column_index from collection_attribute
                search_attribute = embedding_search_attribute(column_title, domain)
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
                    for new_item in new_items:
                        # new_item will be {'ID': '14', 'Projects': 'Citic', 'Need to upgrade': '', 'Set Index , Follow': '', 'Auto Update': 'OFF', 'WP Version': '', 'Password': 'Citicpacific123#@!', 'Login Email': 'cyrus@lolli.com.hk', 'Site Url': 'https://www.citicpacific.com/en/', 'Comment': '', 'Polylang': 'TRUE'}, {}, {'ID': '30', 'Projects': 'GIBF', 'Need to upgrade': '', 'Set Index , Follow': '', 'Auto Update': '', 'WP Version': '', 'Password': '5PYSO9tONhpfztggNyry(%uM', 'Login Email': 'cyrus@lolli.com.hk', 'Site Url': 'https://gibf-bio.com', 'Comment': 'There is a pending change of your email to cyrus@lolli.com.hk', 'Polylang': 'FALSE'}
                        print(append_google_sheet_row(current_user, new_item))
                        messages.append({"role": "system", "content": f"New row have been added: {new_item}"})
                else:
                    messages.append({"role": "system", "content": "No new row have been added"})
            elif action == 'Add column':
                # update google sheet data
                print('>>>>>>>>>>>>>>>>>>>> "Add column"')
                append_google_sheet_column(current_user, column_title)
                messages.append({"role": "system", "content": f"Added new column: {column_title}"})
            else:
                print('>>>>>>>>>>>>>>>>>>>> "Modify"')
                # search for the row_index
                sheet_result = collection_embedded_server.find({
                    'domain': domain,
                    'plot': {'$elemMatch': {'$eq': old_value}}
                })
                if sheet_result:
                    for message in sheet_result:
                        row_index = message['row_index']
                        print('>>>>>>>>>>>>>>>>>>>> found row: ', row_index)
                if row_index != -1 and column_index != -1:
                    # rage = "Sheet1!"+chr(65 + column_index) + str(row_index)
                    # print("rage 1: ", rage)
                    update_google_sheet_data(current_user, new_value, column_index, row_index + 1)
                    messages.append({"role": "system", "content": f"Information has been updated: {old_value} -> {new_value} at row {row_index + 1}, column {column_index}"})
                else:
                    messages.append({"role": "system", "content": "No information has been updated"})

        else:
            print('==================== NO ACTION')
            target_action = "no_action"

        print('>>>>>>>>>>>>>>>>>>>> end analysis text for action')
        # for embedding in action_info:
        #     full_plot.append(embedding)
        #     label = embedding.split(":")[0]
        #     value = embedding.split(":")[1]
        #     search_attribute = embedding_search_attribute(embedding_function(label), domain)
        #     for message in search_attribute:
        #         if message['score'] > 0.8:
        #             column_index = message['column_index']
        #             column_name = chr(65 + column_index)

        #     print("label: ", label)
        #     print("value: ", value)
        #     print("column_index: ", column_index)
        #     print("column_name: ", column_name)

        #     if has_attribute:
        #         if column_name:
        #             rage = "Sheet1!"+column_name + str(row_index)
        #             print("rage 1: ", rage)
        #             update_google_sheet_data(current_user, [[value]] ,rage)
        #         else: 

        #             rage = "Sheet1!M" + str(row_index)
        #             print("rage 2: ", rage)
        #             update_google_sheet_data(current_user, [[value]] ,rage)
        #     else:
        #         if column_name:
        #             rage = "Sheet1!"+column_name + str(total_row)
        #             print("rage 3: ", rage)
        #             update_google_sheet_data(current_user, [[value]] ,rage)
        #         else:
        #             rage = "Sheet1!M" + str(total_row)
        #             print("rage 4: ", rage)
        #             update_google_sheet_data(current_user, [[value]] ,rage)
        #             update_google_sheet_data(current_user, [[value]] ,rage)
        #     messages.append({"role": "system", "content": "The infomations have been updated vào vị trí "+ rage})
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
        completion = show_message(messages)

    
    try:
        # run pipeline
        aggregate_result    = embedding_search_info(search_vector, domain, 5)
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
        completion = show_message(messages)
    else:
        messages.append({"role": "user", "content":"WITH ABOVE INFORMATIONS ONLY"})
        completion = show_message(messages)
        

    #print("messages: ", messages)

    # for m in messages:
    #     print(m)
    #     print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    completion_dict = completion.to_dict()

    # Serialize the dictionary to a JSON string
    # chat_completion_json = json.dumps(completion_dict, indent=2)
    # clone choices message to choices delta: choices[]['delta'] = choices[]['message']

    for choice in completion_dict['choices']:
        choice['delta'] = choice['message']

    # return the JSON string
    return completion_dict
    
   