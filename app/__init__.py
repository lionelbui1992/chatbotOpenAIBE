import os  # Import the os module

from flask import Flask
from app.routes import chat, settings, admin, models
from app.db import init_db
from app.openai import init_openai
from app.config import Config
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, resources={r"*": {"origins": "*", "methods": "*", "allow_headers": "*", "expose_headers": "*"}})

    init_db(app)  # Initialize the database
    init_openai(app)  # Initialize OpenAI

    app.register_blueprint(chat.bp)
    app.register_blueprint(settings.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(models.bp)

    return app
