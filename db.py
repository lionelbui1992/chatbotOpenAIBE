from pymongo import MongoClient
import os
from dotenv import load_dotenv
 
load_dotenv()
 
DATABASE_TYPE = os.getenv('DATABASE_TYPE')
DB_NAME = os.getenv('DB_NAME')
MONGO_URI = os.getenv('MONGO_URI')
 
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection_users = db['users']
collection_action = db['embedded_actions']
collection_attribute = db['embedded_attributes']
collection_total = db['embedded_total']
collection_embedded_server = db['embedded_server']

def truncate_collection(collection, domain: str):
    try:
        collection.delete_many({'domain': domain})
    except errors.OperationFailure as e:
        print(e)
