import os
import pandas as pd

# 🧭 Get current working directory (repo root in GitHub Actions)
repo_path = os.getcwd()
print("Current Repo Path:", repo_path)

# 📁 Build full file path
file_name = "filtered_companies.xlsx"
file_path = os.path.join(repo_path, file_name)

# ✅ Check if file exists
if os.path.exists(file_path):
    print(f"✅ File found: {file_path}")
    df = pd.read_excel(file_path)
    print(df.head())
else:
    print(f"❌ File not found: {file_path}")
