"""
notify.py

Sends a weekly email digest of:
  1. New jobs (Status == "New") — freshly scraped, never surfaced before
  2. Still-open stale jobs (Status == "Pending", scraped > 7 days ago) — re-checked via HTTP

Each job card has:
  - View Job → direct link to the listing
  - ✓ Mark Applied → Apps Script tracking link (marks sheet row as Applied)

After sending:
  - New jobs are marked "Pending" in the sheet
  - Stale jobs confirmed closed are marked "Expired"

Usage:
    uv run tools/notify.py
    uv run tools/notify.py --to kimsb2429@gmail.com
    uv run tools/notify.py --dry-run   # prints digest info, no email sent

Requires:
    - APPS_SCRIPT_URL in .env
    - credentials.json (Google OAuth)
    - token.json with Sheets + Gmail scopes
    - .tmp/sheet_id.txt
"""

import argparse
import base64
import os
import sys
import time
import urllib.parse
from datetime import date, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/gmail.send",
]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
SHEET_TAB = "Applications"
DEFAULT_TO = "kimsb2429@gmail.com"
STALE_DAYS = 6  # Re-check pending jobs older than this


def get_creds():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        if not creds or not creds.valid:
            print("Re-authorizing Google OAuth...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def get_sheet_id():
    if os.path.exists(".tmp/sheet_id.txt"):
        with open(".tmp/sheet_id.txt") as f:
            return f.read().strip()
    print("Error: .tmp/sheet_id.txt not found. Run sheets_tracker.py first.", file=sys.stderr)
    sys.exit(1)


def get_all_rows(sheets_svc, sheet_id):
    """Return (headers, list of (row_number, row_dict)) for all data rows."""
    result = sheets_svc.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"{SHEET_TAB}!A1:O500",
    ).execute()
    rows = result.get("values", [])
    if not rows:
        return [], []
    headers = rows[0]
    data = []
    for i, row in enumerate(rows[1:], start=2):
        padded = row + [""] * (len(headers) - len(row))
        data.append((i, dict(zip(headers, padded))))
    return headers, data


def get_new_jobs(all_rows):
    """Filter rows with Status == 'New'."""
    return [(row, job) for row, job in all_rows if job.get("Status") == "New"]


def get_stale_pending_jobs(all_rows):
    """Return Pending rows where Scraped At is older than STALE_DAYS."""
    cutoff = datetime.now() - timedelta(days=STALE_DAYS)
    stale = []
    for row, job in all_rows:
        if job.get("Status") != "Pending":
            continue
        scraped_at = job.get("Scraped At", "")
        if not scraped_at:
            continue
        try:
            # Handle ISO format: "2026-03-10T14:23:00" or "2026-03-10"
            dt = datetime.fromisoformat(scraped_at[:19])
            if dt <= cutoff:
                stale.append((row, job))
        except (ValueError, TypeError):
            continue
    return stale


def check_job_still_open(url):
    """
    Returns True if job appears open, False if closed/404, None if check inconclusive.
    Uses a simple HTTP GET — best-effort, not perfect for all boards.
    Note: ClearanceJobs requires login so HTTP checks are unreliable; we assume open.
    """
    if not url:
        return None

    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.lower()

    # ClearanceJobs requires auth — HTTP check will just redirect to login, assume open
    if "clearancejobs.com" in domain:
        return None

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)

        if resp.status_code == 404:
            return False

        # Check if redirected far from original domain (job removed → homepage)
        final_domain = urllib.parse.urlparse(resp.url).netloc.lower()
        if domain != final_domain:
            return False

        # Common "job removed" URL patterns
        removed_patterns = ["/search", "job-not-found", "expired", "removed", "not-found", "404"]
        if any(p in resp.url.lower() for p in removed_patterns):
            return False

        return True

    except Exception:
        return None  # Inconclusive — include in email anyway


def mark_pending(sheets_svc, sheet_id, row_numbers):
    data = [{"range": f"{SHEET_TAB}!L{row}", "values": [["Pending"]]} for row in row_numbers]
    sheets_svc.spreadsheets().values().batchUpdate(
        spreadsheetId=sheet_id,
        body={"valueInputOption": "RAW", "data": data},
    ).execute()


def mark_expired(sheets_svc, sheet_id, row_numbers):
    data = [{"range": f"{SHEET_TAB}!L{row}", "values": [["Expired"]]} for row in row_numbers]
    sheets_svc.spreadsheets().values().batchUpdate(
        spreadsheetId=sheet_id,
        body={"valueInputOption": "RAW", "data": data},
    ).execute()


def build_tracking_url(apps_script_url, row, job_url, sheet_id):
    params = urllib.parse.urlencode({"action": "mark_applied", "row": row, "url": job_url, "sheet_id": sheet_id})
    return f"{apps_script_url}?{params}"


def build_mark_all_na_url(apps_script_url, rows, sheet_id):
    params = urllib.parse.urlencode({"action": "mark_all_na", "rows": ",".join(str(r) for r in rows), "sheet_id": sheet_id})
    return f"{apps_script_url}?{params}"


def score_color(score):
    try:
        s = int(score)
    except (ValueError, TypeError):
        return "#555555"
    if s >= 8:
        return "#1a7f37"
    if s == 7:
        return "#0969da"
    return "#6e40c9"


def render_job_card(row, job, apps_script_url, sheet_id):
    score = job.get("Score", "?")
    color = score_color(score)
    job_url = job.get("URL", "")
    tracking_url = build_tracking_url(apps_script_url, row, job_url, sheet_id)

    location = job.get("Location", "")
    location_html = f" &middot; <span style='color:#555;font-size:13px;'>{location}</span>" if location else ""

    salary_min = job.get("Salary Min", "")
    salary_max = job.get("Salary Max", "")
    salary_html = ""
    if salary_min or salary_max:
        salary_html = f"<div style='color:#555;font-size:13px;margin-bottom:6px;'>&#128176; {salary_min or '?'} &ndash; {salary_max or '?'}</div>"

    reasoning = job.get("Score Reasoning", "")

    return f"""
    <div style="border:1px solid #e1e4e8;border-radius:8px;padding:16px;margin-bottom:16px;background:#ffffff;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
        <div style="flex:1;">
          <a href="{job_url}" style="font-size:16px;font-weight:600;color:#0969da;text-decoration:none;">
            {job.get('Title', '?')}
          </a><br>
          <span style="color:#333;font-size:14px;">{job.get('Company', '?')}</span>{location_html}
        </div>
        <span style="background:{color};color:#fff;padding:4px 10px;border-radius:12px;font-size:13px;font-weight:600;white-space:nowrap;flex-shrink:0;">
          {score}/10
        </span>
      </div>
      <div style="margin-top:10px;">
        {salary_html}
        <div style="color:#555;font-size:13px;font-style:italic;">{reasoning}</div>
      </div>
      <div style="margin-top:12px;">
        <a href="{job_url}"
           style="display:inline-block;background:#0969da;color:#ffffff;padding:8px 16px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:500;">
          View Job &rarr;
        </a>
        <a href="{tracking_url}"
           style="display:inline-block;background:#ffffff;color:#1a7f37;border:1px solid #1a7f37;padding:8px 16px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:500;margin-left:8px;">
          &#10003; Mark Applied
        </a>
      </div>
    </div>
    """


def build_email_html(new_jobs, stale_jobs, apps_script_url, sheet_id, sheet_url):
    today = date.today().strftime("%B %d, %Y")
    all_rows = [row for row, _ in new_jobs] + [row for row, _ in stale_jobs]
    mark_all_na_url = build_mark_all_na_url(apps_script_url, all_rows, sheet_id)

    total = len(new_jobs) + len(stale_jobs)

    new_cards = "".join(render_job_card(row, job, apps_script_url, sheet_id) for row, job in new_jobs)
    stale_cards = "".join(render_job_card(row, job, apps_script_url, sheet_id) for row, job in stale_jobs)

    stale_section = ""
    if stale_jobs:
        stale_section = f"""
        <h3 style="color:#555;font-size:14px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin:28px 0 12px;">
          Still Open from Last Week ({len(stale_jobs)})
        </h3>
        {stale_cards}
        """

    new_section = ""
    if new_jobs:
        new_section = f"""
        <h3 style="color:#555;font-size:14px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin:0 0 12px;">
          New This Week ({len(new_jobs)})
        </h3>
        {new_cards}
        """

    return f"""
    <html>
    <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,sans-serif;
                 max-width:640px;margin:0 auto;padding:24px;background:#f6f8fa;color:#24292f;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
        <h2 style="margin:0;color:#24292f;">Job Digest &mdash; {today}</h2>
        <a href="{mark_all_na_url}"
           style="background:#f6f8fa;color:#666;border:1px solid #d0d7de;padding:7px 14px;border-radius:6px;text-decoration:none;font-size:13px;white-space:nowrap;">
          Mark all N/A
        </a>
      </div>
      <p style="color:#555;margin-bottom:20px;">
        {total} job{'s' if total != 1 else ''} to review.
        Click <strong>View Job</strong> to open a listing. Click <strong>&#10003; Mark Applied</strong> after you submit.
        Done with the rest? Click <strong>Mark all N/A</strong> above.
      </p>
      {new_section}
      {stale_section}
      <p style="color:#aaa;font-size:12px;margin-top:24px;border-top:1px solid #e1e4e8;padding-top:16px;">
        <a href="{sheet_url}" style="color:#aaa;">View full sheet</a>
        &nbsp;&middot;&nbsp;
        <a href="{mark_all_na_url}" style="color:#aaa;">Mark all N/A</a>
      </p>
    </body>
    </html>
    """


def send_email(gmail_svc, to, subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["To"] = to
    msg["From"] = "me"
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    gmail_svc.users().messages().send(userId="me", body={"raw": raw}).execute()


def main():
    parser = argparse.ArgumentParser(description="Send weekly job digest email")
    parser.add_argument("--to", default=DEFAULT_TO)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print digest info without sending email or updating sheet")
    args = parser.parse_args()

    apps_script_url = os.getenv("APPS_SCRIPT_URL")
    if not apps_script_url:
        print("Error: APPS_SCRIPT_URL not set in .env.", file=sys.stderr)
        sys.exit(1)

    creds = get_creds()
    sheets_svc = build("sheets", "v4", credentials=creds)
    gmail_svc = build("gmail", "v1", credentials=creds)

    sheet_id = get_sheet_id()
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"

    _, all_rows = get_all_rows(sheets_svc, sheet_id)
    new_jobs = get_new_jobs(all_rows)
    stale_candidates = get_stale_pending_jobs(all_rows)

    # Check stale jobs — filter out confirmed closed ones
    stale_open = []
    expired_rows = []
    if stale_candidates:
        print(f"Checking {len(stale_candidates)} stale pending jobs...")
        for row, job in stale_candidates:
            url = job.get("URL", "")
            still_open = check_job_still_open(url)
            title = f"[{job.get('Score')}] {job.get('Title')} @ {job.get('Company')}"
            if still_open is False:
                print(f"  [EXPIRED] {title}")
                expired_rows.append(row)
            else:
                status = "open" if still_open else "unknown (assuming open)"
                print(f"  [STILL OPEN — {status}] {title}")
                stale_open.append((row, job))
            time.sleep(0.3)  # be polite

    if not new_jobs and not stale_open:
        print("No new or stale-open jobs to notify about. Exiting.")
        if expired_rows and not args.dry_run:
            mark_expired(sheets_svc, sheet_id, expired_rows)
            print(f"Marked {len(expired_rows)} expired jobs in sheet.")
        return

    print(f"New jobs: {len(new_jobs)} | Still open from last week: {len(stale_open)} | Expired: {len(expired_rows)}")

    total = len(new_jobs) + len(stale_open)
    subject = f"Job Digest — {total} job{'s' if total != 1 else ''} ({date.today().strftime('%b %d')})"
    html = build_email_html(new_jobs, stale_open, apps_script_url, sheet_id, sheet_url)

    if args.dry_run:
        print(f"Subject: {subject}")
        print(f"To: {args.to}")
        if new_jobs:
            print("New jobs:")
            for row, job in new_jobs:
                print(f"  Row {row}: [{job.get('Score')}] {job.get('Title')} @ {job.get('Company')}")
        if stale_open:
            print("Still open from last week:")
            for row, job in stale_open:
                print(f"  Row {row}: [{job.get('Score')}] {job.get('Title')} @ {job.get('Company')}")
        if expired_rows:
            print(f"Would mark {len(expired_rows)} rows as Expired.")
        print("(dry run — no email sent, sheet not updated)")
        return

    send_email(gmail_svc, args.to, subject, html)
    print(f"Email sent to {args.to}")

    if new_jobs:
        mark_pending(sheets_svc, sheet_id, [row for row, _ in new_jobs])
        print(f"Marked {len(new_jobs)} new jobs as 'Pending'.")

    if expired_rows:
        mark_expired(sheets_svc, sheet_id, expired_rows)
        print(f"Marked {len(expired_rows)} jobs as 'Expired'.")


if __name__ == "__main__":
    main()
