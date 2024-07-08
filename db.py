from pymongo import MongoClient
import os
from dotenv import load_dotenv
 
load_dotenv()
 
DATABASE_TYPE = os.getenv('DATABASE_TYPE')
DB_NAME = os.getenv('DB_NAME')
MONGO_URI = os.getenv('MONGO_URI')
MONGO_COLLECTION = os.getenv('MONGO_COLLECTION')
 
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[MONGO_COLLECTION]
collection_users = db['users']
collection_action = db['embedded_actions']
collection_attribute = db['embedded_attributes']
collection_total = db['embedded_total']