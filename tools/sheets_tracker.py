"""
sheets_tracker.py

Creates (or appends to) a Google Sheet called "Job Tracker".
Deduplicates by job URL so re-runs are safe.

Usage:
    uv run tools/sheets_tracker.py --jobs .tmp/jobs_scored.json
    uv run tools/sheets_tracker.py --jobs .tmp/jobs_scored.json --sheet-id 1BxiM...

On first run, opens a browser for Google OAuth. Saves token.json for future runs.

Output:
    Prints the spreadsheet URL.
"""

import argparse
import json
import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

SHEET_NAME = "Job Tracker"
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

HEADERS = [
    "Title", "Company", "Location", "Remote", "Salary Min", "Salary Max",
    "Date Posted", "Score", "Score Reasoning", "URL", "Site",
    "Status", "Applied Date", "Notes", "Scraped At",
]


def get_creds():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def get_or_create_sheet(sheets_svc, drive_svc, sheet_id=None):
    if sheet_id:
        spreadsheet = sheets_svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
        print(f"Using existing sheet: {spreadsheet['spreadsheetUrl']}")
        return sheet_id, spreadsheet["spreadsheetUrl"]

    # Search for existing sheet by name
    result = drive_svc.files().list(
        q=f"name='{SHEET_NAME}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
        fields="files(id, name)",
    ).execute()

    files = result.get("files", [])
    if files:
        sid = files[0]["id"]
        url = f"https://docs.google.com/spreadsheets/d/{sid}"
        print(f"Found existing sheet: {url}")
        return sid, url

    # Create new sheet
    spreadsheet = sheets_svc.spreadsheets().create(body={
        "properties": {"title": SHEET_NAME},
        "sheets": [{"properties": {"title": "Applications"}}],
    }).execute()
    sid = spreadsheet["spreadsheetId"]
    url = spreadsheet["spreadsheetUrl"]
    actual_sheet_id = spreadsheet["sheets"][0]["properties"]["sheetId"]
    print(f"Created new sheet: {url}")

    # Write headers
    sheets_svc.spreadsheets().values().update(
        spreadsheetId=sid,
        range="Applications!A1",
        valueInputOption="RAW",
        body={"values": [HEADERS]},
    ).execute()

    # Freeze header row + bold it
    sheets_svc.spreadsheets().batchUpdate(
        spreadsheetId=sid,
        body={"requests": [
            {"updateSheetProperties": {
                "properties": {"sheetId": actual_sheet_id, "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount",
            }},
            {"repeatCell": {
                "range": {"sheetId": actual_sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                "fields": "userEnteredFormat.textFormat.bold",
            }},
        ]},
    ).execute()

    return sid, url


def get_existing_urls(sheets_svc, sheet_id):
    result = sheets_svc.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range="Applications!J:J",  # URL column
    ).execute()
    rows = result.get("values", [])
    return {row[0] for row in rows if row}


def append_jobs(sheets_svc, sheet_id, jobs, existing_urls):
    new_jobs = [j for j in jobs if j.get("url") not in existing_urls]
    if not new_jobs:
        print("No new jobs to add (all already tracked).")
        return 0

    def clean(v):
        """Convert NaN/None/float to safe string for Sheets API."""
        import math
        if v is None:
            return ""
        if isinstance(v, float) and math.isnan(v):
            return ""
        return str(v) if not isinstance(v, str) else v

    rows = []
    for j in new_jobs:
        rows.append([
            clean(j.get("title")),
            clean(j.get("company")),
            clean(j.get("location")),
            clean(j.get("remote")),
            clean(j.get("salary_min")),
            clean(j.get("salary_max")),
            clean(j.get("date_posted")),
            clean(j.get("score")),
            clean(j.get("score_reasoning")),
            clean(j.get("url")),
            clean(j.get("site")),
            "New",
            "",
            "",
            clean(j.get("scraped_at")),
        ])

    sheets_svc.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range="Applications!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()

    print(f"Added {len(new_jobs)} new jobs ({len(jobs) - len(new_jobs)} duplicates skipped).")
    return len(new_jobs)


def main():
    parser = argparse.ArgumentParser(description="Sync scored jobs to Google Sheets")
    parser.add_argument("--jobs", default=".tmp/jobs_scored.json",
                        help="Path to scored jobs JSON file")
    parser.add_argument("--sheet-id", help="Existing spreadsheet ID (optional)")
    args = parser.parse_args()

    if not os.path.exists(args.jobs):
        print(f"Error: {args.jobs} not found. Run job_scraper.py first.", file=sys.stderr)
        sys.exit(1)

    with open(args.jobs) as f:
        jobs = json.load(f)

    print(f"Loaded {len(jobs)} jobs from {args.jobs}")

    creds = get_creds()
    sheets_svc = build("sheets", "v4", credentials=creds)
    drive_svc = build("drive", "v3", credentials=creds)

    sheet_id, sheet_url = get_or_create_sheet(sheets_svc, drive_svc, args.sheet_id)
    existing_urls = get_existing_urls(sheets_svc, sheet_id)
    added = append_jobs(sheets_svc, sheet_id, jobs, existing_urls)

    print(f"\nSheet URL: {sheet_url}")
    print(f"Sheet ID (save this for future runs): {sheet_id}")

    # Save sheet ID to .tmp for workflow reuse
    os.makedirs(".tmp", exist_ok=True)
    with open(".tmp/sheet_id.txt", "w") as f:
        f.write(sheet_id)


if __name__ == "__main__":
    main()
