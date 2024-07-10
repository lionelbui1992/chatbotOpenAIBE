from bson import ObjectId
from flask import jsonify, current_app
from flask_jwt_extended import get_jwt_identity
from db import collection, collection_action, collection_attribute, collection_users
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
        {"role": "system", "content": "Please analyze the attributes to update from the string below, without name or subject. Separate the attributes with a comma and separate attribute label and attribute value with a 2 dots mark."},
        {"role": "user", "content": input_text}
    ]
    completion = current_app.openAIClient.chat.completions.create(
    model="gpt-3.5-turbo",
    messages= var_messages
    )
    return completion.choices[0].message.content.split(',')

def update_data_to_db(_id, plot):
    collection.update_one(
        {"_id": _id},
        {"$set": {"plot": plot}}

    )
    return collection.find_one({"_id": _id})

def add_data_to_db(title, plot, embedding):
    collection.insert_one(
        {
            "title": title,
            "plot": plot,
            "plot_embedding": embedding,
            "type": "server",
            "row_index": 0,
            "column_count": len(plot)
        }
    )
    return collection.find_one({"title": title})

def embedding_search_attribute(searchVector, domain):
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
        'type': 1, 
        'column_index': 1,
        'score': {
            '$meta': 'vectorSearchScore'
        }
        }
    }]
    info_funtion = collection_attribute.aggregate(pipeline)
    
    return info_funtion
def embedding_search_total(searchVector, domain):
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
            'score': -1  # Sort by score in descending order
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
    action = 0;
    for message in action_funtion:
        action = message['score']

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


    # get the embedding
    search_vector = embedding_function(input_text)
    # end get the embedding
    # handle search info
    has_attribute = False
    _id = ""
    full_plot = []
    search_info = embedding_search_info(search_vector, domain, 1)
    if search_info:
       has_attribute = True
       for message in search_info:
            _id = message['_id']
            row_index = message['row_index']
            full_plot = message['plot']
    # handle total  
    total_row = 0
    search_total = embedding_search_total( embedding_function('total'), domain)
    if search_total:
        for message in search_total:
            total_row = message['total']
            print(message)

    # handle action
    action_score_status = False
    for textabc in input_text.split(" "):
        search_vector_abc = embedding_function(textabc)
        action_score = embedding_search_action(search_vector_abc)
        #print("action_score: ", action_score)
        if  action_score > 0.7:
            action_score_status = True
            break
    

    action_embedding_arr =[]
    target_action = ""
    rage = ""
    column_index = ""
    column_name = ""

    if action_score_status:
        
        try:
            target_action = "has_action"
            action_embedding_arr = analysis_text(input_text)
            for embedding in action_embedding_arr:
                full_plot.append(embedding)
                label = embedding.split(":")[0]
                value = embedding.split(":")[1]
                search_attribute = embedding_search_attribute(embedding_function(label), domain)
                for message in search_attribute:
                    if message['score'] > 0.8:
                        column_index = message['column_index']
                        column_name = chr(65 + column_index)

                print("label: ", label)
                print("value: ", value)
                print("column_index: ", column_index)
                print("column_name: ", column_name)

                if has_attribute:
                    if column_name:
                        rage = "Sheet1!"+column_name + str(row_index)
                        print("rage 1: ", rage)
                        update_google_sheet([[value]],rage)
                    else: 

                        rage = "Sheet1!M" + str(row_index)
                        print("rage 2: ", rage)
                        update_google_sheet([[value]],rage)
                else:
                    if column_name:
                        rage = "Sheet1!"+column_name + str(total_row)
                        print("rage 3: ", rage)
                        update_google_sheet([[value]],rage)
                    else:
                        rage = "Sheet1!M" + str(total_row)
                        print("rage 4: ", rage)
                        update_google_sheet([[value]],rage)
                messages.append({"role": "system", "content": "The infomations have been updated vào vị trí "+ rage})
            update_data_to_db(_id, full_plot)
        except Exception as e:
            messages.append({"role": "system", "content": "Sorry, I can't update the information, please try again!"})

    # end handle action
    print("target_action: ", target_action)
    completion = []
    if target_action == "has_action":
        completion = show_message(messages)

    
    try:
        # run pipeline
        aggregate_result    = embedding_search_info(search_vector, domain, 10)
        print("aggregate_result: ", aggregate_result)
        header_column       = ""
        score               = 0
        full_plot           = ""
        target_score       = 0 # target score to show message

        # prompt for message in aggregate_result, should be manage by tags
       # messages.append({"role": "system", "content": "Hey OAS Asisstant! please display the best info bellow:" })
        messages.append({"role": "system", "content": "Hey OAS Asisstant! Write nature langage for bellow text:" })
        messages.append({"role": "user", "content":input_text})
        
        # messages.append({"role": "user", "content": "Total is "+ str(total_row) + " Developers"})
        #print(messages)
        for message in aggregate_result:
            # title = message['title']
            score = message['score']

            print(score)
           
            #if(score > 0.7):
            #print("score: ", score)
            print("message: ", message['title'])

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
               
    except Exception as e:
        #messages.append({"role": "assistant", "content": "Sorry, I can't get the information, please try again!"})
        messages.append({"role": "system", "content": e.message})
        print(e)
    if(target_score == 0):
        messages= [
            {"role": "system", "content": "Hey OAS Asisstant! Write nature langage for bellow text:" },
            {"role": "user", "content": input_text },
        ]
        completion = show_message(messages)
    else:
        completion = show_message(messages)

    #print("messages: ", messages)
    completion_dict = completion.to_dict()

    # Serialize the dictionary to a JSON string
    # chat_completion_json = json.dumps(completion_dict, indent=2)
    # clone choices message to choices delta: choices[]['delta'] = choices[]['message']

    for choice in completion_dict['choices']:
        choice['delta'] = choice['message']

    # return the JSON string
    return completion_dict
    
   