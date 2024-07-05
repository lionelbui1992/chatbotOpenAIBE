from google.oauth2 import service_account
from googleapiclient.discovery import build



def user_google_connect(request):
    try:
        # db.create_collection("embedded_server")
    
        # collection = db["embedded_server"]
        
        # print("Connected to MongoDB")
    
        # collection.delete_many({})
        # print("TRUNCATED")
    
        # Define the scope
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    
        # Path to your service account key file
        SERVICE_ACCOUNT_FILE = 'service_account.json'
    
        # Authenticate using the service account file
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    
        # Create a service object
        service = build('sheets', 'v4', credentials=credentials)
    
        # The ID and range of the spreadsheet
        SAMPLE_SPREADSHEET_ID = '13OKFuHbP5DwThDDlgiUcsR3D4cc3e8l-3-yn-3bG1_4'
        SAMPLE_RANGE_NAME = 'Sheet1!A1:AE999'
    
        # Call the Sheets API
        sheet = service.spreadsheets()
    
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=SAMPLE_RANGE_NAME).execute()
        values = result.get('values', [])
    
        if not values:
            print('No data found.')
        else:
            print('Data:')
            index = 0
            input_text = ""
            for row in values:
                index += 1
                for i in range(len(row)):
                    input_text = input_text + row[i] + "\n"

                    print(input_text)
    
                # response = clientAI.embeddings.create(
                #     input=input_text,
                #     model="text-embedding-3-small"
                # )
                
                # searchVector = response.data[0].embedding
    
                # collection.insert_one(
                #     {
                #         "title": row[1],
                #         'header_column' : values[0],
                #         "plot": row,
                #         "plot_embedding": searchVector,
                #         "type": "server",
                #         "row_index": index,
                #         "column_count": len(row)
    
    
                #     }
                # )
    except Exception as e:
        print(e)
        return {"status": "error", "message": "An error occurred"}
    return {"status": "success", "message": "Data successfully imported"}
