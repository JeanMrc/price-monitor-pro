import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds  = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
client = gspread.authorize(creds)

import os
from dotenv import load_dotenv
load_dotenv()

sheet = client.open_by_key(os.getenv("GOOGLE_SHEET_ID"))
ws    = sheet.sheet1
ws.update(range_name="A1", values=[["Price Monitor Pro"]])
ws.update(range_name="B1", values=[["Connected!"]])

print("Google Sheets connected successfully!")