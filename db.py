from pymongo import MongoClient
import os
from dotenv import load_dotenv
 
load_dotenv()
 
DATABASE_TYPE = os.getenv('DATABASE_TYPE')
DB_NAME = os.getenv('DB_NAME')
MONGO_URI = os.getenv('MONGO_URI')
 
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection_users = db['users'] # _id, email, password, domain, name, role, token, settings: {userTheme, theme, model, googleAccessToken, googleSelectedDetails, tags}
collection_action = db['embedded_actions']
collection_attribute = db['embedded_attributes']
collection_total = db['embedded_total']
collection_embedded_server = db['embedded_server']
collection_domain = db['domain'] # _id, name, label, instructions, googleSelectedDetails: {id, title, sheetName, sheetId}
collection_spreadsheets = db['spreadsheets'] # _id, filename, sheet_name, domain_id, columns: [{column_name}], rows: [{column_name: value}]
collection_cell_words = db['cell_words'] # _id, domain, row_index, column_title, text, words: [{word, vector}]


def truncate_collection(collection, domain: str):
    try:
        collection.delete_many({'domain': domain})
    except Exception as e:
        print('Error truncating collection: ', e)
        return False
