from flask import json, jsonify, current_app
from db import collection
from db import collection_action
from google.oauth2 import service_account
from googleapiclient.discovery import build

def update_google_sheet(values, rage):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    SERVICE_ACCOUNT_FILE = 'service_account.json'
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials)
    SAMPLE_SPREADSHEET_ID = '13OKFuHbP5DwThDDlgiUcsR3D4cc3e8l-3-yn-3bG1_4'
    SAMPLE_RANGE_NAME = rage
    sheet = service.spreadsheets()
    body = {
        'values': values
    }
    result = sheet.values().update(
        spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME,
        valueInputOption='RAW', body=body).execute()

def analysis_text(input_text):
    var_messages=[
        {"role": "system", "content": "Please analyze the attributes to update from the string below, without name or subject. Separate the attributes with a comma."},
        {"role": "user", "content": input_text}
    ]
    completion = current_app.openAIClient.chat.completions.create(
    model="gpt-3.5-turbo",
    messages= var_messages
    )
    return completion.choices[0].message.content.split(',')

def update_data_to_db(_id, plot,embedding):
    collection.update_one(
        {"_id": _id},
        {"$set": {"plot": plot, "plot_embedding": embedding}}

    )
    return collection.find_one({"_id": _id})


def embedding_search_info(searchVector,limit=100):
    pipeline = [
    {
        '$vectorSearch': {
        'index': 'vector_index', 
        'path': 'plot_embedding', 
        'queryVector': searchVector, 
        'numCandidates': 150, 
        'limit': limit
        }
    }, {
        '$project': {
        '_id': 1, 
        'plot': 1, 
        'title': 1, 
        'header_column': 1,
        'row_index': 1,
        'column_count': 1,
        'score': {
            '$meta': 'vectorSearchScore'
        }
        }
    }]
    info_funtion = collection.aggregate(pipeline)
    
    return info_funtion

def embedding_search_action(searchVector):
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
    action = ""
    for message in action_funtion:
        action = message['title']

    return action

def embedding_function(input_text):
    response = current_app.openAIClient.embeddings.create(
        input=input_text,
        model=current_app.config['EMBEDDING_MODEL']
    )
    search_vector = response.data[0].embedding
    return search_vector

def show_message(messages):
    completion = current_app.openAIClient.chat.completions.create(
        model=current_app.config['OPENAI_MODEL'],
        messages= messages
    )
    return completion

def get_chat_completions(request):
   
    data = request.get_json()
    messages = data.get('messages', [])
    if not messages:
        return jsonify({"error": "No messages provided"})
    
    # get latest message content text
    latest_message = messages[-1].get('content', "")
    input_text = latest_message[0].get('text', "")

    # get the embedding
    search_vector = embedding_function(input_text)
    # end get the embedding

    # handle action
    action = embedding_search_action(search_vector)
    action_embedding_arr =[]
    action_input_text = ""
    target_action = ""
    row_index = 0
    column_count = 0
    rage = ""

    if action == "update":
        target_action = "update"
        results = embedding_search_info(search_vector,1)
        for result in results:
            _id = result['_id']
            action_embedding_arr = result['plot']
            row_index = result['row_index'] - 1
            column_count = result['column_count']
        rage = 'Sheet1!'+ chr(65 + column_count) + str(row_index)
        attributes = analysis_text(input_text)
        for attribute in attributes:
            action_embedding_arr.append(attribute)
    
        for embedding in action_embedding_arr:
            action_input_text = action_input_text + embedding + "\n"

        update_google_sheet([attributes], rage)
        update_data_to_db(_id, action_embedding_arr, embedding_function(action_input_text))

    
    # end handle action
    completion = []
    if target_action == "update":
        messages.append({"role": "system", "content": "The attributes have been updated."})
        completion = show_message(messages)

    else:
        # run pipeline
        aggregate_result    = embedding_search_info(search_vector,100)
        header_column       = ""
        score               = 0
        full_plot           = ""
        target_score       = 0 # target score to show message

        # prompt for message in aggregate_result, should be manage by tags
        messages.append({"role": "system", "content": "Hey OAS Asisstant! show me the information bellow:"})
        messages.append({"role": "system", "content":input_text})
        for message in aggregate_result:
            # title = message['title']
            score = message['score']
            print("score: ", score)
            if(score > 0.8):
                target_score = 1
                index = 0
                for value in message['plot']:
                    if value == "":
                        value = "N/A"
                    # check if value is not string, convert to string
                    if not isinstance(value, str):
                        value = str(value)

                    if 'index' in message['header_column']:
                        header_column = message['header_column'][index]
                        # debug header_column value
                    else:
                        header_column = "N/A"
                    # header_column = message['header_column'][1] # index
                    full_plot = full_plot + header_column + ":" + value + ", "
                    index += 1

                messages.append({"role": "user", "content": full_plot })

        #print("target_score: ", target_score)
        #print("full_plot: ", full_plot)
        # clientAi create completions
        if(target_score == 0):
            messages= [
                {"role": "system", "content": "Hey OAS Asisstant! Write nature langage for bellow text:" },
                {"role": "system", "content": input_text },
            ]
            completion = show_message(messages)
        else:
            completion = show_message(messages)

        # end clientAi create completions
    try:
        completion_dict = completion.to_dict()

        # Serialize the dictionary to a JSON string
        # chat_completion_json = json.dumps(completion_dict, indent=2)
        # clone choices message to choices delta: choices[]['delta'] = choices[]['message']

        for choice in completion_dict['choices']:
            choice['delta'] = choice['message']

        # return the JSON string
        return completion_dict
    except Exception as e:
        return jsonify({"error": str(e)})
