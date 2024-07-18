from flask import json, jsonify, current_app
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from numpy import number
from pymongo import MongoClient, errors
from db import collection_attribute, collection_embedded_server, truncate_collection

def get_google_sheets_data(current_user, google_access_token, google_selected_details):
    domain = current_user['domain']

    # truncate data in collection
    truncate_collection(collection_attribute, domain)
    truncate_collection(collection_embedded_server, domain)
    
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

                    # print('>>>>>>>> Adding Data to MongoDB...', 'total')
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
        print(':::::::::::ERROR - get_google_sheets_data:::::::::::::', e)
        return jsonify({'message': 'An error occurred while retrieving data: ' + str(e)})

def import_heading_attributes(domain, headers):
    # skip this attributes key
    # exclude_attributes = [
    #     'ID',
    #     'STT',
    #     'So thu tu',
    #     'Số thứ tự',
    #     'no',
    #     'no.',
    #     '#',
    # ]
    try:
        for index, header in enumerate(headers):
            # if header in exclude_attributes:
            #     print('<<<<<<<<< Skipping heading...', header)
            #     continue
            print('<<<<<<<<< Importing heading...', header)
            input_text = header
            column_name = index
            

            response = current_app.openAIClient.embeddings.create(
                input=header,
                model="text-embedding-3-small"
            )

            search_vector = response.data[0].embedding

            collection_attribute.insert_one({
                "title": input_text.strip(),
                "plot_embedding": search_vector,
                "type": "attribute",
                "column_index": column_name,
                "domain": domain
            })

    except Exception as e:
        print(':::::::::::ERROR - import_heading_attributes:::::::::::::', e)


def import_embedding_data(domain, row, headers, index):
    try:
        row_string = ', ' . join(row)
        response = current_app.openAIClient.embeddings.create(
            input=row_string,
            model="text-embedding-3-small"
        )
        
        search_vector = response.data[0].embedding
        print('Importing embedding...', row[1])
        insert_data = {
            "title": row[1].strip(),
            'header_column' : headers,
            "plot": row,
            "plot_embedding": search_vector,
            "type": "server",
            "row_index": index,
            "column_count": len(row),
            "domain": domain
        }
        for i in range(len(row)):
            insert_data[headers[i]] = row[i]
        collection_embedded_server.insert_one(insert_data)

    except Exception as e:
        print(':::::::::::ERROR - import_embedding_data:::::::::::::', e)

def update_google_sheet_data(current_user, values: str, column_index: number, row_index: number):

    print(values)
    google_access_token = current_user['settings']['googleAccessToken']
    google_selected_details = current_user['settings']['googleSelectedDetails']

    if not google_access_token or not google_selected_details:
        return jsonify({'message': 'Google access token or selected details not provided'})
    try:
        # Create Google API credentials from the access token
        credentials = Credentials(token=google_access_token)
        service = build('sheets', 'v4', credentials=credentials)
        for detail in google_selected_details:
            sheet_id = detail['sheetId']
            sheet_name = detail['title']
            range_name = f'{sheet_name}!A1:AE999'
            result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_name).execute()
            rows = result.get('values', [])
            if not rows:
                print('No data found.')
            else:
                # update the value of the cell
                old_value = rows[row_index][column_index]
                print(old_value)
                rows[row_index][column_index] = values
                result = service.spreadsheets().values().update(
                    spreadsheetId=sheet_id, range=range_name,
                    valueInputOption='RAW', body={'values': rows}).execute()
                print(f'Value updated from {old_value} to {values}.')
        

        return jsonify({'message': 'Data retrieved and printed successfully'})
    except Exception as e:
        print(':::::::::::ERROR - update_google_sheet_data:::::::::::::', e)
        return jsonify({'message': 'An error occurred while retrieving data'})

def append_google_sheet_row(current_user, new_item):
    # new_item :{
    #     "ID": "87",
    #     "Projects": "Teenskey",
    #     "Need to upgrade": "",
    #     "Set Index , Follow": "",
    #     "Auto Update": "OFF",
    #     "WP Version": "6.0.1",
    #     "Password": "lollimedia",
    #     "Login Email": "cyrus@lolli.com.hk",
    #     "Site Url": "https://teenskey.org/",
    #     "Comment": "for teenskey.org/cmsadmin, pw is Teenskey123#@!",
    #     "Polylang": "TRUE"
    # }
    google_access_token = current_user['settings']['googleAccessToken']
    google_selected_details = current_user['settings']['googleSelectedDetails']

    if not google_access_token or not google_selected_details:
        return jsonify({'message': 'Google access token or selected details not provided'})
    try:
        # Create Google API credentials from the access token
        credentials = Credentials(token=google_access_token)
        service = build('sheets', 'v4', credentials=credentials)
        for detail in google_selected_details:
            sheet_id = detail['sheetId']
            sheet_name = detail['title']
            range_name = f'{sheet_name}!A1:AE999'
            result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_name).execute()
            rows = result.get('values', [])
            if not rows:
                print('No data found.')
            else:
                # append new_item to the last row
                rows.append(list(new_item.values()))
                result = service.spreadsheets().values().update(
                    spreadsheetId=sheet_id, range=range_name,
                    valueInputOption='RAW', body={'values': rows}).execute()
                print('{0} cells updated.'.format(result.get('updatedCells')))


        return jsonify({'message': 'Data retrieved and printed successfully'})
    except Exception as e:
        print(':::::::::::ERROR - append_google_sheet_row:::::::::::::', e)
        return jsonify({'message': 'An error occurred while retrieving data'})

def append_google_sheet_column(current_user, column_name):
    google_access_token = current_user['settings']['googleAccessToken']
    google_selected_details = current_user['settings']['googleSelectedDetails']

    if not google_access_token or not google_selected_details:
        return jsonify({'message': 'Google access token or selected details not provided'})
    try:
        # Create Google API credentials from the access token
        credentials = Credentials(token=google_access_token)
        service = build('sheets', 'v4', credentials=credentials)
        for detail in google_selected_details:
            sheet_id = detail['sheetId']
            sheet_name = detail['title']
            range_name = f'{sheet_name}!A1:AE999'
            result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_name).execute()
            rows = result.get('values', [])
            if not rows:
                print('No data found.')
            else:
                # append new column to the last column
                rows[0].append(column_name)
                # for row in rows:
                #     row.append('')
                result = service.spreadsheets().values().update(
                    spreadsheetId=sheet_id, range=range_name,
                    valueInputOption='RAW', body={'values': rows}).execute()
                print('{0} cells updated.'.format(result.get('updatedCells')))

        return jsonify({'message': 'Data retrieved and printed successfully'})
    except Exception as e:
        print(':::::::::::ERROR - append_google_sheet_column:::::::::::::', e)
        return jsonify({'message': 'An error occurred while retrieving data'})