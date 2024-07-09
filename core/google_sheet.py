from flask import json, jsonify, current_app
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from pymongo import MongoClient, errors
from db import collection_total, collection_attribute, collection_embedded_server

def get_google_sheets_data(google_access_token, google_selected_details):
    try:
        # Create Google API credentials from the access token
        creds = Credentials(token=google_access_token)

        # Build the Google Sheets API service
        service = build('sheets', 'v4', credentials=creds)

        # truncate data in collection
        truncate_collection(collection_total)
        truncate_collection(collection_attribute)
        truncate_collection(collection_embedded_server)

        results = {}

        for detail in google_selected_details:
            sheet_id = detail['sheetId']
            sheet_name = detail['title']

            # Read the first 100 rows from the sheet
            range_name = f'{sheet_name}!A1:AE999'
            result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_name).execute()
            rows = result.get('values', [])

            if not rows:
                print('No data found.')
            else:
                headers = rows[0]
                import_heading_attributes(rows[0])
                # return
                index = 0
                for row in rows:
                    index += 1
                    import_embedding_data(row, headers, index)
                response = current_app.openAIClient.embeddings.create(
                    input='total',
                    model="text-embedding-3-small"
                )
                    
                search_vector = response.data[0].embedding
                print('Adding Data to MongoDB...', 'total')
                collection_total.insert_one({
                    "title": "total",
                    "plot_embedding": search_vector,
                    "total": index,
                    "domain": 'domain_1'
                })

        return jsonify({'message': 'Data retrieved and printed successfully'})
    except Exception as e:
        print(e)
        return jsonify({'message': 'An error occurred while retrieving data'})

def truncate_collection(collection):
    try:
        collection.delete_many({})
    except errors.OperationFailure as e:
        print(e)

def import_heading_attributes(row):
    try:
        for i in range(len(row)):
            print('Adding Data to MongoDB...', row[i])
            input_text = row[i]
            # get column letter from google sheet
            column_name = i


            response = current_app.openAIClient.embeddings.create(
                input=input_text,
                model="text-embedding-3-small"
            )
        
            search_vector = response.data[0].embedding

            collection_attribute.insert_one(
                {
                    "title": input_text,
                    "plot_embedding": search_vector,
                    "type": "attribute",
                    "column_index": column_name
                }
            )

    except Exception as e:
        print(e)

def import_embedding_data(row, headers, index):
    try:
        response = current_app.openAIClient.embeddings.create(
            input=row[1],
            model="text-embedding-3-small"
        )
        
        search_vector = response.data[0].embedding
        print('Adding Data to MongoDB...', row[0])
        collection_embedded_server.insert_one(
            {
                "title": row[0],
                'header_column' : headers,
                "plot": row,
                "plot_embedding": search_vector,
                "type": "server",
                "domain": 'domain_1',
                "row_index": index,
                "column_count": len(row)

            }
        )

    except Exception as e:
        print(e)
