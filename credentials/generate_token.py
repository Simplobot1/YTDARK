import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'google_credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'youtube_token.json')

flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
creds = flow.run_local_server(port=0)

with open(TOKEN_FILE, 'w') as f:
    f.write(creds.to_json())

print(f'Token salvo em: {TOKEN_FILE}')
