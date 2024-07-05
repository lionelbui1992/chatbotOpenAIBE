from flask import json, jsonify, current_app
from db import collection


def get_chat_completions(request):
    # request format:
    # {
    #     messages: 
    #     [{role: "system", content: [{type: "text", text: "You are a helpful assistant."}]},…]
    #     model: "gpt-4o"
    #     stream: true
    # }
    data = request.get_json()
    messages = data.get('messages', [])
    if not messages:
        return jsonify({"error": "No messages provided"})
    # get latest message content text
    latest_message = messages[-1].get('content', "")
    input_text = latest_message[0].get('text', "")

    # get the embedding
    embedding_response = current_app.openAIClient.embeddings.create(
        input=input_text,
        model=current_app.config['EMBEDDING_MODEL']
    )
    search_vector = embedding_response.data[0].embedding
    # end get the embedding

    # create prompting message
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
                '_id': 0, 
                'plot': 1, 
                'title': 1, 
                'header_column': 1,
                'row_index': 1,
                'column_count': 1,
                'score': {
                    '$meta': 'vectorSearchScore'
                }
            }
        }
    ]

    # run pipeline
    aggregate_result    = collection.aggregate(pipeline)

    full_plot           = ""
    header_column       = ""
    score               = 0
    # prompt for message in aggregate_result, should be manage by tags
    messages.append({"role": "system", "content": "show me the information bellow with table format, pick one of the server bellow:"})
    for message in aggregate_result:
        # title = message['title']
        score = message['score']
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

    # messages.append({"role": "user", "content": input_text})
    # end create prompting message

    # clientAi create completions
    if(score < 0.55):
        completion = current_app.openAIClient.chat.completions.create(
            model=current_app.config['OPENAI_MODEL'],
            messages= [
                {"role": "system", "content": "Write Some thing for bellow text:" },
                {"role": "system", "content": input_text },
            ]
        )
    else:
        completion = current_app.openAIClient.chat.completions.create(
            model=current_app.config['OPENAI_MODEL'],
            messages= messages
        )
    # end clientAi create completions

    completion_dict = completion.to_dict()

    # Serialize the dictionary to a JSON string
    # chat_completion_json = json.dumps(completion_dict, indent=2)
    # clone choices message to choices delta: choices[]['delta'] = choices[]['message']
    for choice in completion_dict['choices']:
        choice['delta'] = choice['message']

    


    return completion_dict
