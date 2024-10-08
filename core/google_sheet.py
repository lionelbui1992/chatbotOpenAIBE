# -*- coding: utf-8 -*-

import json
import threading
import traceback
from flask import jsonify

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import gspread

from core.openai import create_embedding

from db import collection_attribute
from db import collection_embedded_server
from db import collection_spreadsheets
from db import collection_cell_words
from db import truncate_collection

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
            print('No data found')
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
    except Exception:
        print(':::::::::::ERROR - get_google_sheets_data:::::::::::::', traceback.format_exc())
        return jsonify({'message': 'An error occurred while retrieving data: {error_message}'.format(error_message=traceback.format_exc())})


def pull_google_sheets_data(google_selected_details: dict, gspread_client: gspread.Client) -> dict:
    """
    Pull data from Google Sheets and store in MongoDB
    """

    try:
        # open Google Sheet use URL or ID
        SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/{sheet_id}'.format(sheet_id=google_selected_details['sheetId'])
        sheet = gspread_client.open_by_url(SPREADSHEET_URL).worksheet(google_selected_details['title'])

        # get the headers from Google Sheet
        headers = sheet.row_values(1)
        # clearn spacing from headers
        headers = [header.strip() for header in headers]
        # update the headers in Google Sheet
        sheet.update('A1', [headers])

        shet_data = sheet.get_all_records()
        # stripe the data containing empty spaces
        for row in shet_data:
            for key, value in row.items():
                if isinstance(value, str):
                    row[key] = value.strip()
        return {
            'status': 'success',
            'data': shet_data
        }
    except Exception:
        print(':::::::::::ERROR - pull_google_sheets_data:::::::::::::', traceback.format_exc())
        return {
            'status': 'error',
            'message': 'An error occurred while retrieving data: {error_message}'.format(error_message=traceback.format_exc())
        }


def import_google_sheets_data(_domain, rows: list) -> dict:
    # ===================== Print log ===============================================
    if not rows:
        print('No data found')
        return {
            'status': 'error',
            'message': 'No data found'
        }
    # ===================== End Print log ===========================================


    # ===================== Import to MongoDB =======================================
    # modify the data before importing to MongoDB
    # add domain, row_index to each row
    for index, row in enumerate(rows):
        row['domain'] = _domain.name
        row['row_index'] = index + 1
    # import all rows to mongodb
    print(_domain.name, ' - Importing data to MongoDB... ', len(rows), ' rows')
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


def append_google_sheet_row(google_selected_details: dict, gspread_client: gspread.Client, new_item) -> dict:
    SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/{sheet_id}'.format(sheet_id=google_selected_details['sheetId'])
    sheet = gspread_client.open_by_url(SPREADSHEET_URL).worksheet(google_selected_details['title'])

    append_response = sheet.append_row(list(new_item.values()))
    print('Append response:', append_response)
    return append_response


def append_google_sheet_column(google_selected_details: dict, gspread_client: gspread.Client, column_name: str) -> dict:
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


def import_rows(rows):
    domain = None
    if len(rows) > 0:
        domain = rows[0].get('domain')
        truncate_collection(collection_cell_words, domain)
    threads = []
    for row in rows:
        try:
            thread = threading.Thread(target=process_row, args=(row,))
            threads.append(thread)
            thread.start()
        except Exception:
            print(traceback.format_exc())
            return False
    for thread in threads:
        thread.join()


def process_row(row):
    # print('ROW:ROW:ROW:ROW:', row)
    row_index = row.get('row_index')
    domain = row.get('domain')
    insert_data = list()

    # remove _id if exists
    row.pop('_id', None)
    row.pop('domain', None)
    row.pop('row_index', None)
    
    for column_title, cell_value in row.items():
        if isinstance(cell_value, int) or isinstance(cell_value, float):
            cell_value = str(cell_value)
        insert_data.append({
            'domain': domain,
            'row_index': row_index,
            'column_title': column_title,
            'text': cell_value,
            # 'word': cell_value,
            # 'vector': words_to_vectors(cell_value).tolist()
        })

    if len(insert_data) > 0:
        collection_cell_words.insert_many(insert_data)


def get_cell_info(domain: str, input_text: str) -> list:
    """Search cell information from MongoDB"""

    return list(collection_cell_words.aggregate([
        {
            "$search": {
                "index": "default",
                "text": {
                    "query": input_text,
                    "path": ["text"],
                    "fuzzy": {
                        "maxEdits": 2,
                        "prefixLength": 0,
                        "maxExpansions": 50
                    }
                }
            },
        },
        {
            '$match': {
                'domain': domain
            }
        },
        {
            '$project': {
                '_id': 0,
                'row_index': 1,
                'column_title': 1,
                'text': 1,
                'word': 1,
                'score': {
                    '$meta': 'searchScore'
                }
            }
        },
        {
            '$match': {
                'score': { '$gt': 0.7 }
            }
        },
        {
            '$limit': 10
        },
    ]))


def get_best_match(domain: str, input_text: str, limit=3) -> dict | None:
    """Get the best match from the cell words"""

    result = get_cell_info(domain, input_text)
    if len(result) < 1:
        return None
    # get list of column_title, if row_index is the same get the highest score
    best_match = dict()
    for item in result:
        if item['column_title'] in best_match:
            if item['score'] > best_match[item['column_title']]['score']:
                best_match[item['column_title']] = item
        else:
            best_match[item['column_title']] = item
    # sort by score
    best_match = sorted(best_match.values(), key=lambda x: x['score'], reverse=True)
    return best_match[:limit] if len(best_match) > 0 else None
