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
LocalPath = r"D:\SANJAY\7 GitHub Actions"  # 🔹 Replace with your local path
LocalFile = "filtered_companies.xlsx"

# --- 2 Google Colab ENVIRONMENT ---
ColabPath = "/content/drive/MyDrive/Personal Colab/"  # 🔹 Replace with your Colab path
ColabFileID = "1ykHeAaMDchKP8vvolCsct-tKUxdLQwHH"  # Replace with actual Google Drive file ID

# --- 3 GITHUB ENVIRONMENT ---
GitHubPath = os.getcwd()  # 🔹 Default repo path for GitHub Actions
GOOGLE_SECRET_ENV = "GOOGLE_CREDENTIALS"

UPDATED_FILE = "filtered_companies.xlsx"

# --- Environment Detection ---
if os.path.exists(LocalPath):
    os.chdir(LocalPath)
    ENVIRONMENT = "LOCAL"
    LastKeyFile = "Last_Keys.txt"
    print("📁 Running Local Environment")
elif os.path.exists(ColabPath):
    os.chdir(ColabPath)
    ENVIRONMENT = "COLAB"
    LastKeyFile = "Last_Keys"
    print("📁 Running Google Colab Environment")
else:
    os.chdir(GitHubPath)
    ENVIRONMENT = "GITHUB"
    LastKeyFile = "Last_Keys"
    print("📁 Running GitHub Actions Environment")

# =====================================================
# --- LOGGING ---
def Github_log(msg: str):
    """Timestamped logger for consistent output."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

# =====================================================
def Github_connect_to_drive():
    try:
        creds_json = os.getenv("GOOGLE_CREDENTIALS")
        if not creds_json:
            raise ValueError("Missing GOOGLE_CREDENTIALS secret in environment.")
        
        creds_dict = json.loads(creds_json)
        scopes = ['https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
        
        gauth = GoogleAuth()
        gauth.credentials = credentials
        drive = GoogleDrive(gauth)
        
        print("✅ Connected to Google Drive successfully (Service Account Auth).")
        return drive
    except Exception as e:
        print(f"❌ Drive connection failed: {e}")
        raise

# =====================================================
def Github_download_file_from_drive(file_id: str, local_name: str):
    """Download a Google Drive file by ID first; fallback to file name if ID fails."""
    try:
        drive = Github_connect_to_drive()
        Github_log(f"📥 Attempting to download file by ID: {file_id}")

        try:
            # Try by File ID
            file_obj = drive.CreateFile({'id': file_id})
            file_obj.GetContentFile(local_name)
            Github_log(f"✅ File downloaded by ID as '{local_name}'")
            return True
        except Exception as e_id:
            Github_log(f"⚠️ Failed to download by ID: {e_id}")
            Github_log(f"📥 Attempting to download file by name: '{local_name}'")

            # Fallback: search by file name
            file_list = drive.ListFile({'q': f"title='{local_name}' and trashed=false"}).GetList()
            if not file_list:
                Github_log(f"❌ No file found with name '{local_name}'")
                return False

            # Download the first match
            file_obj = file_list[0]
            file_obj.GetContentFile(local_name)
            Github_log(f"✅ File downloaded by name as '{local_name}'")
            return True

    except Exception as e:
        Github_log(f"❌ Failed to download file: {e}")
        traceback.print_exc()
        return False

# =====================================================
def Github_process_file(local_name: str, updated_name: str):
    """Example processing step."""
    try:
        Github_log(f"🔍 Reading '{local_name}'...")
        df = pd.read_excel(local_name)
        df["Processed_At"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df.to_excel(updated_name, index=False)
        Github_log(f"✅ Processed and saved as '{updated_name}'")
        return True
    except FileNotFoundError:
        Github_log(f"❌ File not found: {local_name}")
        traceback.print_exc()
        return False
    except Exception as e:
        Github_log(f"❌ Error processing file: {e}")
        traceback.print_exc()
        return False

# =====================================================
def Github_upload_file_to_drive(local_name: str, folder_id: str = None):
    """Upload processed file back to Drive."""
    try:
        drive = Github_connect_to_drive()
        metadata = {'title': os.path.basename(local_name)}
        if folder_id:
            metadata['parents'] = [{'id': folder_id}]
        upload = drive.CreateFile(metadata)
        upload.SetContentFile(local_name)
        upload.Upload()
        Github_log(f"📤 Uploaded '{local_name}' to Google Drive successfully.")
        return True
    except Exception as e:
        Github_log(f"❌ Upload failed: {e}")
        traceback.print_exc()
        return False

# =====================================================
def main():
    if ENVIRONMENT in ("LOCAL", "COLAB"):
        print("DO THIS")
    else:
        try:
            Github_log(f"🚀 Starting script in {ENVIRONMENT} environment...")

            # ✅ Download with fallback
            if not Github_download_file_from_drive(ColabFileID, LocalFile):
                Github_log("❌ Stopping: File download failed.")
                sys.exit(1)

            # ✅ Process file
            if not Github_process_file(LocalFile, UPDATED_FILE):
                Github_log("⚠️ Processing failed. Skipping upload.")
                sys.exit(1)

            # ✅ Upload processed file
            if not Github_upload_file_to_drive(UPDATED_FILE):
                Github_log("⚠️ Upload failed, but script completed gracefully.")
            else:
                Github_log("🎉 All steps completed successfully.")

        except Exception as e:
            Github_log(f"💥 Fatal error in main: {e}")
            traceback.print_exc()
            sys.exit(1)

# =====================================================
if __name__ == "__main__":
    main()
