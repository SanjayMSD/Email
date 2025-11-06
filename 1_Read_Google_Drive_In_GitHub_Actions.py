# import os
# import pandas as pd


# repo_path = os.getcwd()
# print("Current Repo Path:", repo_path)


# file_name = "Dataset_M10_D20.xlsx"
# file_path = os.path.join(repo_path, file_name)


# if os.path.exists(file_path):
#     print(f"✅ File found: {file_path}")
#     df = pd.read_excel(file_path)
#     print(df.head())
# else:
#     print(f"❌ File not found: {file_path}")

import os
import re
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ---------------- CONFIG ----------------
common_company_emails = [
    "info@", "contact@", "hello@", "support@", "help@", "sales@", "business@", "partnerships@",
    "media@", "press@", "hr@", "careers@", "jobs@", "admin@", "office@", "feedback@", "marketing@",
    "billing@", "accounts@", "ceo@"
]

repo_path = os.getcwd()
file_name = "Dataset_M10_D20.xlsx"
file_path = os.path.join(repo_path, file_name)
emails_file = os.path.join(repo_path, "Website_Emails.xlsx")
not_accessible_file = os.path.join(repo_path, "Not_Accessible_Websites.xlsx")

# --- Time limit: 5 hours 50 minutes ---
start_time = time.time()
MAX_RUNTIME = 0 * 60 * 60 + 30 * 60# 5 * 60 * 60 + 50 * 60  # 5h 50m = 21000 seconds

# ------------- Helper Functions -------------

def time_exceeded():
    return (time.time() - start_time) >= MAX_RUNTIME

def save_excel(df, path):
    """Safely save Excel"""
    try:
        df.to_excel(path, index=False)
    except Exception as e:
        print(f"⚠️ Error saving {path}: {e}")

def get_emails_from_html(html):
    """Extract all emails from HTML text"""
    return list(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html)))

def get_emails_from_url(url):
    """Scrape one URL for email addresses"""
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            return []
        return get_emails_from_html(response.text)
    except Exception:
        return []

def get_sub_links(base_url):
    """Fetch limited subpages from same domain"""
    try:
        response = requests.get(base_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        base_domain = base_url.split("//")[1].split("/")[0]
        links = set()
        for tag in soup.find_all("a", href=True):
            link = urljoin(base_url, tag['href'])
            if base_domain in link:
                links.add(link)
        return list(links)[:10]  # limit to 10 pages max
    except Exception:
        return []

# ------------- Main Logic -------------

if not os.path.exists(file_path):
    raise FileNotFoundError(f"❌ File not found: {file_path}")

print(f"✅ File found: {file_path}")
df = pd.read_excel(file_path)

# Ensure 'accessible' column exists
if "accessible" not in df.columns:
    df["accessible"] = ""

# Load or create result files
if os.path.exists(emails_file):
    website_emails = pd.read_excel(emails_file)
else:
    website_emails = pd.DataFrame(columns=["Website", "Emails"])

if os.path.exists(not_accessible_file):
    not_accessible = pd.read_excel(not_accessible_file)
else:
    not_accessible = pd.DataFrame(columns=["Website", "Accessible"])

# Process only websites with blank accessible field
pending_websites = df[df["accessible"].isna() | (df["accessible"] == "")]
print(f"🔍 Total pending websites: {len(pending_websites)}")

try:
    for idx, row in pending_websites.iterrows():
        if time_exceeded():
            print("\n⏰ Max runtime reached. Stopping safely.")
            break

        website = str(row["Website"]).strip()
        if not website:
            continue

        if not website.startswith("http"):
            website = "https://" + website

        print(f"\n🌐 Checking: {website}")

        accessible_flag = "NO"  # default
        filtered_emails = []

        try:
            response = requests.get(website, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code == 200:
                # Collect emails from main + subpages
                all_links = [website] + get_sub_links(website)
                all_emails = set()

                for link in all_links:
                    all_emails.update(get_emails_from_url(link))

                # Filter by common company usernames
                filtered_emails = [
                    e for e in all_emails if any(e.lower().startswith(prefix) for prefix in common_company_emails)
                ]

                # Decision: only mark accessible if emails found
                if filtered_emails:
                    accessible_flag = "YES"
                    print(f"✅ Accessible & Emails found: {len(filtered_emails)}")
                else:
                    print("⚠️ Accessible but 0 valid emails → treated as Not Accessible")
            else:
                print(f"❌ Website returned status code {response.status_code}")

        except Exception as e:
            print(f"⚠️ Error accessing {website}: {e}")

        # --- Update status in main file ---
        df.loc[idx, "accessible"] = accessible_flag

        if accessible_flag == "YES":
            website_emails.loc[len(website_emails)] = [website, ", ".join(filtered_emails)]
            save_excel(website_emails, emails_file)
        else:
            not_accessible.loc[len(not_accessible)] = [website, "NO"]
            save_excel(not_accessible, not_accessible_file)

        # Save main file progress after every website
        save_excel(df, file_path)

except KeyboardInterrupt:
    print("\n🛑 Keyboard interrupt detected. Saving all progress before exit...")

finally:
    # Final save for all data before exit
    save_excel(df, file_path)
    save_excel(website_emails, emails_file)
    save_excel(not_accessible, not_accessible_file)
    print("\n💾 All progress saved successfully. Exiting safely.")

print("\n🏁 Task completed.")
print(f"✅ Website emails saved in: {emails_file}")
print(f"❌ Not accessible list saved in: {not_accessible_file}")
