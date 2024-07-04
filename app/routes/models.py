from flask import Blueprint, jsonify, request
import time
from flask_cors import CORS, cross_origin

from app.routes import _build_cors_preflight_response, _corsify_actual_response

# Create a blueprint for the v1/models API
bp = Blueprint('models', __name__, url_prefix='/api/v1/models')

CORS(bp, resources={r"*": {"origins": "*", "methods": "*", "allow_headers": "*", "expose_headers": "*", "supports_credentials": "true"}})

# Define a route for getting all models
@bp.route('/', methods=['GET', 'OPTIONS'])
# @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def get_all_models():
    if request.method == "OPTIONS": # CORS preflight
        return _build_cors_preflight_response()
    
    models = [
        {
            "id": "main-domain",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "openai-internal"
        },
    ]
    return _corsify_actual_response(jsonify(models))
