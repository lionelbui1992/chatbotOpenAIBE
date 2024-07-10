from flask import json, jsonify, current_app
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from pymongo import MongoClient, errors
from db import collection_total, collection_attribute, collection_embedded_server, truncate_collection

def get_google_sheets_data(current_user, google_access_token, google_selected_details):
    domain = current_user['domain']

    # truncate data in collection
    truncate_collection(collection_total)
    truncate_collection(collection_attribute)
    truncate_collection(collection_embedded_server)
    
    if not google_access_token or not google_selected_details:
        return jsonify({'message': 'Google access token or selected details not provided'})
    try:
        # Create Google API credentials from the access token
        creds = Credentials(token=google_access_token)

        # Build the Google Sheets API service
        service = build('sheets', 'v4', credentials=creds)

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
                # remove the header row
                rows.pop(0)
                index = 0
                import_heading_attributes(domain, headers)

                for row in rows:
                    index += 1
                    # import_total_data(row, headers, index)
                    import_embedding_data(domain, row, headers, index)
                total_strings = ['total', 'count', 'sum', 'how many']
                for total_string in total_strings:

                    response = current_app.openAIClient.embeddings.create(
                        input = total_string,
                        model="text-embedding-3-small"
                    )
                    
                    search_vector = response.data[0].embedding

                    print('>>>>>>>> Adding Data to MongoDB...', 'total')
                    collection_embedded_server.insert_one(
                        {
                            "title": 'total',
                            'header_column' : headers,
                            "plot": [
                                'total ' + str(len(rows)),

                            ],
                            "plot_embedding": search_vector,
                            "type": "server",
                            "row_index": 0,
                            "column_count": 0,
                            "domain": domain
                        }
                    )


        return jsonify({'message': 'Data retrieved and printed successfully'})
    except Exception as e:
        print(e)
        return jsonify({'message': 'An error occurred while retrieving data'})

def import_heading_attributes(domain, headers):
    try:
        for index, header in enumerate(headers):
            print('Importing heading...', header)
            input_text = header
            column_name = index
            

            response = current_app.openAIClient.embeddings.create(
                input=header,
                model="text-embedding-3-small"
            )

            search_vector = response.data[0].embedding

            collection_attribute.insert_one({
                "title": input_text.trim(),
                "plot_embedding": search_vector,
                "type": "attribute",
                "column_index": column_name,
                "domain": domain
            })

    except Exception as e:
        print(e)


def import_embedding_data(domain, row, headers, index):
    try:
        row_string = ', ' . join(row)
        response = current_app.openAIClient.embeddings.create(
            input=row_string,
            model="text-embedding-3-small"
        )
        
        search_vector = response.data[0].embedding
        print('Importing embedding...', row[1])
        collection_embedded_server.insert_one(
            {
                "title": row[1].trim(),
                'header_column' : headers,
                "plot": row,
                "plot_embedding": search_vector,
                "type": "server",
                "row_index": index,
                "column_count": len(row),
                "domain": domain

            }
        )

    except Exception as e:
        print(e)

def update_google_sheet_data(current_user, values, range_name):
    google_access_token = current_user['settings']['googleAccessToken']
    google_selected_details = current_user['settings']['googleSelectedDetails']

    print('google_access_token', google_access_token)
    print('google_selected_details', google_selected_details)

    if not google_access_token or not google_selected_details:
        return jsonify({'message': 'Google access token or selected details not provided'})
    try:
        # Create Google API credentials from the access token
        credentials = Credentials(token=google_access_token)
        service = build('sheets', 'v4', credentials=credentials)
        for detail in google_selected_details:
            # detail: id, sheetId, sheetName, title
            sheet_id = detail['sheetId']
            result = service.spreadsheets().values().update(
                spreadsheetId=sheet_id, range=range_name,
                valueInputOption='RAW', body={'values': values}).execute()
            print('{0} cells updated.'.format(result.get('updatedCells')))

        return jsonify({'message': 'Data retrieved and printed successfully'})
    except Exception as e:
        print(e)
        return jsonify({'message': 'An error occurred while retrieving data'})
