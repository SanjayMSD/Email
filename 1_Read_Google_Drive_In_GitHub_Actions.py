#%% 1 LIBRARIES AND ENVIORNMENT 

import os
import json
import sys
import traceback
import pandas as pd
from datetime import datetime
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

# --- 1 Local ENVIRONMENT ---
LocalPath = r"D:\SANJAY\7 GitHub Actions"
LocalFile = "filtered_companies.xlsx"

# --- 2 Google Colab ENVIRONMENT ---
ColabPath = "/content/drive/MyDrive/Personal Colab/"
"/content/drive/MyDrive/Personal Colab/filtered_companies.xlsx"
ColabFileID = "1ykHeAaMDchKP8vvolCsct-tKUxdLQwHH"
ColabFile = "filtered_companies.xlsx"

# --- 3 GITHUB ENVIRONMENT ---
GitHubPath = os.getcwd()
GOOGLE_SECRET_ENV = "GOOGLE_CREDENTIALS"


#%% 2 FUNCTIONS

def Github_log(msg: str):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def Github_connect_to_drive():
    """Connect to Google Drive using Service Account credentials."""
    try:
        creds_json = os.getenv(GOOGLE_SECRET_ENV)
        if not creds_json:
            raise ValueError("Missing GOOGLE_CREDENTIALS secret in environment.")
        creds_dict = json.loads(creds_json)
        scopes = ['https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
        gauth = GoogleAuth()
        gauth.credentials = credentials
        drive = GoogleDrive(gauth)
        Github_log("✅ Connected to Google Drive successfully (Service Account Auth).")
        return drive
    except Exception as e:
        Github_log(f"❌ Drive connection failed: {e}")
        traceback.print_exc()
        return None


#%% 3 MAIN FUNCTION

def main():
    # --- Environment Detection ---
    if os.path.exists(LocalPath):
        os.chdir(LocalPath)
        ENVIRONMENT = "LOCAL"
        print("📁 Running Local Environment")
    elif os.path.exists(ColabPath):
        os.chdir(ColabPath)
        ENVIRONMENT = "COLAB"
        print("📁 Running Google Colab Environment")
    else:
        os.chdir(GitHubPath)
        ENVIRONMENT = "GITHUB"
        print("📁 Running GitHub Actions Environment")
        Github_log("🚀 Starting Google Drive connection...")
        drive = Github_connect_to_drive()
        if drive:
            Github_log("✅ Google Drive connection established successfully.")
        else:
            Github_log("❌ Failed to connect to Google Drive.")

    

if __name__ == "__main__":
    main()
