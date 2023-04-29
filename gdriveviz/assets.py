import pandas as pd
#google related imports

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload

from dagster import asset
from github import Github
import pandas as pd
from datetime import timedelta
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import pickle
import jupytext
from github import InputFileContent
import os
import os.path

@asset
def drive_api(context):
    SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
    ]

    # we have to add google spreadsheets in the scope because we will be accessing data in the future from google spreadsheets api
    # dont forget to enable google spreadsheet api as well
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        '''look, not creds means no token.json found, therefore, creds could not be created up there
        another assumption was that maybe we created creds, but maybe token.json was not valid, so our
        cred also turned out to be not valid which is same as saying not creds.valid'''
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token: # 
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            ) 
            creds = flow.run_local_server(port=0)   
        ''' If creds are not empty and are expired with a 
            refresh token, refresh the creds '''
    # if credsnot found or not valid. at this point create a token.json file any way
        with open('token.json', 'w') as token:
            token.write(creds.to_json()) 
    #now it will write down all the permissions you gave using your browser ^^^

    try:
        service = build("drive", "v3", credentials=creds) 
        #query = f"'{folder_id}' in parents" --this is not relevant here
        response = service.files().list(q="mimeType='application/vnd.google-apps.spreadsheet'", fields = "files(id,name,mimeType,createdTime,modifiedTime)", orderBy= "modifiedTime desc", spaces='drive').execute()
                                                                                                #spaces define where I want to search, in this case, I want to search whole of my drive
                                                                                                #https://www.notion.so/coding-in-python-for-google-api-3f338c2a0cc248ff9829f6ec3e8673b9?pvs=4#66c4563cfa9244e9a76dcec9f0e376f8
    except HttpError as e:
        print("Error: " + str(e))

    # print(response['files'])
    google_sheet_id = response['files'][0]['id']
    #print(google_sheet_id)


    try:
        # call in the google sheet api
        service = build('sheets', 'v4', credentials=creds)
        
        # get spreadsheet metadata, as in, titles of worksheets of the spreadsheets
        sheet_metadata = service.spreadsheets().get(spreadsheetId=google_sheet_id).execute()
        sheets = sheet_metadata.get('sheets', '') #sheets explicitly refers to sheets/worksheets/tabs

        range_id = sheets[0]['properties']['title'] # gets the title/name of the tab/sheet/worksheet in the spreadsheets
        
        #print(sheets[0]['properties']['title'])
        #print("printing your dataframe here")

    
        result = service.spreadsheets().values().get(
            spreadsheetId=google_sheet_id, range=range_id).execute() #range_id is name of sheets/tabs
        rows = result.get('values', [])
        #print(rows[0:2])
        
        df=pd.DataFrame(rows, columns=rows[0])

    except HttpError as e:
        print("Error: " + str(e))
    
    return df


@asset
def github_notebook(drive_api):
    markdown = f"""
## drive_api data

```python
import pickle
datas = pickle.loads({pickle.dumps(drive_api)!r})
```

## print all the data
```python
print(datas)
```
    """
    nb = jupytext.reads(markdown, "md")
    ExecutePreprocessor().preprocess(nb)
    return nbformat.writes(nb)

@asset(required_resource_keys={"github_api"})
def put_to_gist(context, github_notebook):
    gist=(
        context.resources.github_api # getting the variable github_api from resources of the __init__.py file
        .get_user()
        .create_gist(
        public=False,
        files={
        "google_sheets_sheet.ipynb":InputFileContent(github_notebook)
        }
        )
    )
    context.log.info(f"Notebook created at {gist.html_url}")
    return gist.html_url