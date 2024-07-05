import os
from dotenv import load_dotenv

class Config:
    # Get config from .env file
    load_dotenv()
    SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'you-will-never-guess')
    DATABASE_TYPE = 'mongodb'
    DB_NAME = os.environ.get('DB_NAME', 'sample_mflix')
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://lionelbui:pEciuiTKR28LKOMs@cluster0.hm7buca.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
    MONGO_COLLECTION = os.environ.get('MONGO_COLLECTION', 'sample_mflix')
    MYSQL_USER = os.environ.get('MYSQL_USER')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
    MYSQL_DB = os.environ.get('MYSQL_DB')
    MYSQL_HOST = os.environ.get('MYSQL_HOST')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'text-embedding-3-small')
