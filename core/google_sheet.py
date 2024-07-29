import json
from flask import jsonify
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import gspread

from numpy import number
from core.openai import create_embedding
from db import collection_attribute, collection_embedded_server, collection_domain, collection_spreadsheets, truncate_collection

MESSAGE_CONSTANT = {
    'google_access_token_or_selected_details_not_provided': 'Google access token or selected details not provided',
    'no_data_found': 'No data found.',
    'data_retrieved_and_printed_successfully': 'Data retrieved and printed successfully',
}

def get_credentials(google_access_token: str) -> Credentials:
    return Credentials(token=google_access_token)

def get_service(credentials: Credentials) -> build:
    return build('sheets', 'v4', credentials=credentials)

def get_gspread_client(creds: Credentials) -> gspread.Client:
    return gspread.authorize(creds)

def get_google_sheets_data(current_user, google_access_token, google_selected_details):
    _domain = current_user['domain']

    # truncate data in collection
    truncate_collection(collection_attribute, _domain)
    truncate_collection(collection_embedded_server, _domain)
    
    if not google_access_token or not google_selected_details:
        return jsonify({'message': MESSAGE_CONSTANT['google_access_token_or_selected_details_not_provided']})
    try:
        # Create Google API credentials from the access token
        creds = Credentials(token=google_access_token)

        # Build the Google Sheets API service
        service = build('sheets', 'v4', credentials=creds)

        # for detail in google_selected_details:
        sheet_id = google_selected_details['sheetId']
        sheet_name = google_selected_details['title']

        # Read the first 100 rows from the sheet
        range_name = f'{sheet_name}!A1:AE999'
        result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_name).execute()
        rows = result.get('values', [])

        if not rows:
            print(MESSAGE_CONSTANT['no_data_found'])
        else:
            headers = rows[0]
            # remove the header row
            rows.pop(0)
            index = 0
            import_heading_attributes(_domain, headers)

            for row in rows:
                index += 1
                # import_total_data(row, headers, index)
                import_embedding_data(_domain, row, headers, index)
            total_strings = ['total', 'count', 'sum', 'how many']
            for total_string in total_strings:

                response = create_embedding(input_string = total_string)
                
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
                        "domain": _domain
                    }
                )


        return jsonify({'message': MESSAGE_CONSTANT['data_retrieved_and_printed_successfully']})
    except Exception as e:
        print(':::::::::::ERROR - get_google_sheets_data:::::::::::::', e)
        error_message = str(e)
        return jsonify({'message': 'An error occurred while retrieving data: {error_message}'})

def pull_google_sheets_data(google_selected_details: dict, gspread_client: gspread.Client) -> dict:
    """
    Pull data from Google Sheets and store in MongoDB
    """

    sheet_id = google_selected_details['sheetId']

    try:
        # open Google Sheet use URL or ID
        SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/{sheet_id}'.format(sheet_id=google_selected_details['sheetId'])
        sheet = gspread_client.open_by_url(SPREADSHEET_URL).worksheet(google_selected_details['title'])

        # get all data from Google Sheet
        return {
            'status': 'success',
            'data': sheet.get_all_records()
        }
    except Exception as e:
        print(':::::::::::ERROR - pull_google_sheets_data:::::::::::::', e)
        error_message = str(e)
        return {
            'status': 'error',
            'message': 'An error occurred while retrieving data: {error_message}'
        }


def import_google_sheets_data(_domain, rows: list) -> dict:
    # ===================== Print log ===============================================
    if not rows:
        print(MESSAGE_CONSTANT['no_data_found'])
        return {
            'status': 'error',
            'message': MESSAGE_CONSTANT['no_data_found']
        }
    # ===================== End Print log ===========================================


    # ===================== Import to MongoDB =======================================
    # modify the data before importing to MongoDB
    # add domain, row_index to each row
    for index, row in enumerate(rows):
        row['domain'] = _domain.name
        row['row_index'] = index + 1
    # import all rows to mongodb
    print('Importing data to MongoDB... ', len(rows), ' rows')
    return collection_spreadsheets.insert_many(rows)


def import_heading_attributes(_domain, headers):
    try:
        for index, header in enumerate(headers):
            print('<<<<<<<<< Importing heading...', header)
            input_text = header
            column_name = index
            

            response = create_embedding(header)

            search_vector = response.data[0].embedding

            collection_attribute.insert_one({
                "title": input_text.strip(),
                "plot_embedding": search_vector,
                "type": "attribute",
                "column_index": column_name,
                "domain": _domain
            })

    except Exception as e:
        print(':::::::::::ERROR - import_heading_attributes:::::::::::::', e)

def import_embedding_data(_domain, row, headers, index):
    try:
        row_string = ', ' . join(row)
        response = create_embedding(row_string)
        
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
            "domain": _domain
        }
        for i in range(len(row)):
            insert_data[headers[i]] = row[i]
        collection_embedded_server.insert_one(insert_data)

    except Exception as e:
        print(':::::::::::ERROR - import_embedding_data:::::::::::::', e)

def update_google_sheet_data(current_user, values: str, column_index: number, row_index: number):

    print(values)

    domain_data = collection_domain.find_one({"domain": current_user['domain']})

    google_access_token = current_user['settings']['googleAccessToken']
    google_selected_details = []
    if domain_data:
        google_selected_details = domain_data['googleSelectedDetails']

    if not google_access_token or not google_selected_details:
        return jsonify({'message': MESSAGE_CONSTANT['google_access_token_or_selected_details_not_provided']})
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
                print(MESSAGE_CONSTANT['no_data_found'])
            else:
                # update the value of the cell
                old_value = rows[row_index][column_index]
                print(old_value)
                rows[row_index][column_index] = values
                result = service.spreadsheets().values().update(
                    spreadsheetId=sheet_id, range=range_name,
                    valueInputOption='RAW', body={'values': rows}).execute()
                print(f'Value updated from {old_value} to {values}.')
        

        return jsonify({'message': MESSAGE_CONSTANT['data_retrieved_and_printed_successfully']})
    except Exception as e:
        print(':::::::::::ERROR - update_google_sheet_data:::::::::::::', e)
        return jsonify({'message': 'An error occurred while retrieving data'})

def append_google_sheet_row(google_selected_details: dict, gspread_client: gspread.Client, new_item) -> dict:
    sheet_id = google_selected_details['sheetId']
    SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/{sheet_id}'.format(sheet_id=google_selected_details['sheetId'])
    sheet = gspread_client.open_by_url(SPREADSHEET_URL).worksheet(google_selected_details['title'])

    append_response = sheet.append_row(list(new_item.values()))
    print('Append response:', append_response)
    return append_response

def append_google_sheet_column(google_selected_details: dict, gspread_client: gspread.Client, column_name: str) -> dict:
    sheet_id = google_selected_details['sheetId']
    SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/{sheet_id}'.format(sheet_id=google_selected_details['sheetId'])
    sheet = gspread_client.open_by_url(SPREADSHEET_URL).worksheet(google_selected_details['title'])

    # append new column to the last column of first row
    last_column = len(sheet.row_values(1))
    return sheet.update_cell(1, last_column + 1, column_name)


def delete_google_sheet_row(service, spreadsheet_id: str, sheet_id: str, row_indexes: list) -> dict:
    """Delete a row from Google Sheet"""

    # build the batch update request
    requests = []
    for row_index in row_indexes:
        requests.append({
            "deleteDimension": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "ROWS",
                    "startIndex": row_index,
                    "endIndex": row_index + 1
                }
            }
        })
    # execute the batch update request
    body = {
        "requests": requests
    }
    # Execute the batchUpdate request
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()

    # Print the response
    print(json.dumps(response, indent=4))
    return response

def update_many_row_value(service, spreadsheet_id: str, sheet_id: str, row_values: list) -> dict:
    """Update a cell value in Google Sheet"""

    # build the batch update request
    requests = []
    for row in row_values:
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print(row)
        row_index = row['row_index']
        # remove row_index from row
        row.pop('row_index')
        values = []
        for key, value in row.items():
            if isinstance(value, int):
                values.append({"userEnteredValue": {"numberValue": value}})
            elif isinstance(value, bool):
                values.append({"userEnteredValue": {"boolValue": value}})
            else:
                values.append({"userEnteredValue": {"stringValue": value}})
        requests.append({
            "updateCells": {
                "rows": [
                    {
                        "values": values
                    }
                ],
                "fields": "userEnteredValue",
                "start": {
                    "sheetId": sheet_id,
                    "rowIndex": row_index,
                    "columnIndex": 0
                }
            }
        })
    # execute the batch update request
    body = {
        "requests": requests
    }
    print(body)
    # Execute the batchUpdate request
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()

    # Print the response
    print(json.dumps(response, indent=4))
    return response