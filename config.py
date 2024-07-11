import os
from dotenv import load_dotenv

class Config:
    # Get config from .env file
    load_dotenv()
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'you-will-never-guess')
    DATABASE_TYPE = 'mongodb'
    DB_NAME = os.environ.get('DB_NAME', 'sample_mflix')
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://lionelbui:pEciuiTKR28LKOMs@cluster0.hm7buca.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
    MYSQL_USER = os.environ.get('MYSQL_USER')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
    MYSQL_DB = os.environ.get('MYSQL_DB')
    MYSQL_HOST = os.environ.get('MYSQL_HOST')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'text-embedding-3-small')
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI')
    GOOGLE_AUTHORIZATION_URL = os.environ.get('GOOGLE_AUTHORIZATION_URL')
    GOOGLE_TOKEN_URL = os.environ.get('GOOGLE_TOKEN_URL')
