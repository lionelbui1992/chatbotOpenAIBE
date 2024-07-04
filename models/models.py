import time

def get_models(request):
    models ={
        "object": "list",
        "data": [
            {
            "id": "gpt-4o",
            "object": "model",
            "created": time.time(),
            "owned_by": "system"
            }
        ]
    }

    return models