import json
from flask import current_app, jsonify

def create_embedding(input_string:str):
    """
    Create completions from a list of messages <br />
    input_string: input string to create embeddings <br />
    document from OpenAI: https://platform.openai.com/docs/guides/embeddings
    """
    try:
        embeddings = current_app.openAIClient.embeddings.create(
            input=input_string,
            model=current_app.config['EMBEDDING_MODEL']
        )
        print('::::::::::::::::::::::::::::::::::::::::::::::')
        print('Create embedding: ', input_string, ', ', embeddings.usage.total_tokens, ' tokens')
        print('::::::::::::::::::::::::::::::::::::::::::::::')
        return embeddings
    except Exception as e:
        return str(e)

def create_completion(messages: list):
    """
    Create completions from a list of messages <br />
    messages: list of messages <br />
    document from OpenAI: https://platform.openai.com/docs/guides/completions
    """
    completions = current_app.openAIClient.chat.completions.create(
        model = current_app.config['OPENAI_MODEL'],
        messages = messages,
        max_tokens = 1500,
    )
    print('::::::::::::::::::::::::::::::::::::::::::::::')
    print('Create completetions: ', completions.usage.total_tokens, ' tokens, ', messages)
    print('::::::::::::::::::::::::::::::::::::::::::::::')
    return completions
        