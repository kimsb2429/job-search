"""
auto_apply.py

Auto-applies to ClearanceJobs listings that:
  - Are scored >= threshold (default 7)
  - Have apply_method == "email" (native CJ application, no browser needed)
  - Have not already been applied to

Updates Google Sheet Status column to "Applied" for each successful application.

Usage:
    uv run tools/auto_apply.py
    uv run tools/auto_apply.py --threshold 7
    uv run tools/auto_apply.py --jobs .tmp/jobs_scored.json --threshold 6 --dry-run
"""

import argparse
import json
import os
import re
import sys
import time

import requests
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

BASE_URL = "https://api.clearancejobs.com/api/v1"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]
SHEET_NAME = "Job Tracker"
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"


def get_cj_session():
    username = os.getenv("CJ_USERNAME")
    password = os.getenv("CJ_PASSWORD")
    if not username or not password:
        print("Error: CJ_USERNAME and CJ_PASSWORD must be set in .env", file=sys.stderr)
        sys.exit(1)

    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12239.19.0)",
        "X-Requested-With": "XMLHttpRequest",
    })
    resp = session.post(f"{BASE_URL}/auth/login",
                        json={"username": username, "password": password}, timeout=15)
    if resp.status_code != 200:
        print(f"Error: ClearanceJobs login failed ({resp.status_code})", file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    session.headers.update({
        "Authorization": f"Bearer {data['access_token']}",
        "X-CSRF-TOKEN": data["csrf_token"],
    })
    return session


def extract_job_id(url):
    """Extract numeric job ID from ClearanceJobs URL."""
    m = re.search(r"/jobs/(\d+)", url)
    return m.group(1) if m else None


def get_google_creds():
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


def get_sheet_id(sheets_svc, drive_svc):
    # Check cached sheet ID first
    if os.path.exists(".tmp/sheet_id.txt"):
        with open(".tmp/sheet_id.txt") as f:
            return f.read().strip()

    result = drive_svc.files().list(
        q=f"name='{SHEET_NAME}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
        fields="files(id, name)",
    ).execute()
    files = result.get("files", [])
    if not files:
        print("Error: Job Tracker sheet not found. Run sheets_tracker.py first.", file=sys.stderr)
        sys.exit(1)
    return files[0]["id"]


def get_url_to_row(sheets_svc, sheet_id):
    """Return dict of {url: row_number} for all rows in the sheet."""
    result = sheets_svc.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range="Applications!J:J",  # URL column
    ).execute()
    rows = result.get("values", [])
    url_to_row = {}
    for i, row in enumerate(rows):
        if row:
            url_to_row[row[0]] = i + 1  # 1-indexed
    return url_to_row


def update_sheet_status(sheets_svc, sheet_id, row_number, status):
    sheets_svc.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"Applications!L{row_number}",  # Status column
        valueInputOption="RAW",
        body={"values": [[status]]},
    ).execute()


def main():
    parser = argparse.ArgumentParser(description="Auto-apply to ClearanceJobs email-method listings")
    parser.add_argument("--jobs", default=".tmp/jobs_scored.json")
    parser.add_argument("--threshold", type=int, default=7,
                        help="Minimum score to auto-apply (default: 7)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be applied to without actually applying")
    args = parser.parse_args()

    if not os.path.exists(args.jobs):
        print(f"Error: {args.jobs} not found. Run scoring step first.", file=sys.stderr)
        sys.exit(1)

    with open(args.jobs) as f:
        jobs = json.load(f)

    # Filter: ClearanceJobs only, score >= threshold
    candidates = [
        j for j in jobs
        if j.get("site") == "clearancejobs" and (j.get("score") or 0) >= args.threshold
    ]

    if not candidates:
        print(f"No ClearanceJobs jobs with score >= {args.threshold}.")
        return

    print(f"Found {len(candidates)} ClearanceJobs candidates with score >= {args.threshold}")

    cj = get_cj_session()

    # Set up Google Sheets
    g_creds = get_google_creds()
    sheets_svc = build("sheets", "v4", credentials=g_creds)
    drive_svc = build("drive", "v3", credentials=g_creds)
    sheet_id = get_sheet_id(sheets_svc, drive_svc)
    url_to_row = get_url_to_row(sheets_svc, sheet_id)

    applied = []
    skipped_method = []
    skipped_already = []
    errors = []

    for job in candidates:
        url = job.get("url", "")
        job_id = extract_job_id(url)
        title = job.get("title", "?")
        company = job.get("company", "?")
        score = job.get("score", "?")

        if not job_id:
            print(f"  [SKIP] Could not extract job ID from URL: {url}")
            errors.append(job)
            continue

        # Fetch job detail to check apply_method and is_applied
        r = cj.get(f"{BASE_URL}/jobs/{job_id}", timeout=10)
        if r.status_code != 200:
            print(f"  [SKIP] Could not fetch job {job_id}: {r.status_code}")
            errors.append(job)
            continue

        apply_info = r.json().get("apply", {})
        method = apply_info.get("apply_method")
        is_applied = apply_info.get("is_applied", False)

        if is_applied:
            print(f"  [ALREADY APPLIED] [{score}] {title} @ {company}")
            skipped_already.append(job)
            continue

        if method != "email":
            print(f"  [SKIP — {method}] [{score}] {title} @ {company} → add to sheet for manual apply")
            skipped_method.append(job)
            continue

        print(f"  [APPLY] [{score}] {title} @ {company}", end="")
        if args.dry_run:
            print(" (dry run)")
            applied.append(job)
            continue

        put_resp = cj.put(f"{BASE_URL}/jobs/{job_id}/apply", json={}, timeout=10)
        if put_resp.status_code == 200:
            print(" ✓")
            applied.append(job)

            # Update sheet Status column
            row = url_to_row.get(url)
            if row:
                update_sheet_status(sheets_svc, sheet_id, row, "Applied")
            else:
                print(f"    [WARN] Job not found in sheet — status not updated")
        else:
            print(f" FAILED ({put_resp.status_code}: {put_resp.text[:100]})")
            errors.append(job)

        time.sleep(0.5)

    print()
    print(f"--- Summary ---")
    print(f"Applied:          {len(applied)}")
    print(f"Already applied:  {len(skipped_already)}")
    print(f"Skipped (url/ats):{len(skipped_method)} — apply manually via sheet")
    print(f"Errors:           {len(errors)}")

    if skipped_method:
        print()
        print("Manual apply links:")
        for j in skipped_method:
            print(f"  [{j.get('score')}] {j.get('title')} @ {j.get('company')}")
            print(f"    {j.get('url')}")


if __name__ == "__main__":
    main()
