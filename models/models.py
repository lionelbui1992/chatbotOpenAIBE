import time
from bson import ObjectId
from flask_jwt_extended import get_jwt_identity
from db import collection_users

def get_models():
    models ={
        "status": "success",
        "message": "Models retrieved",
        "object": "list",
        "data": [
            {
            "id": "gpt-4o-mini",
            "object": "model",
            "created": time.time(),
            "owned_by": "system"
            }
        ]
    }
    return models
