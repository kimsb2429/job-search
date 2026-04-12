"""
clearancejobs_scraper.py

Scrapes ClearanceJobs.com via their internal API using session auth.
Requires CJ_LARAVEL_TOKEN and CJ_CSRF_TOKEN in .env (grab from browser DevTools).

Usage:
    uv run tools/clearancejobs_scraper.py
    uv run tools/clearancejobs_scraper.py --hours 168 --results 25

Output:
    Appends to .tmp/jobs_raw.json (same format as job_scraper.py)

Refreshing credentials:
    If you get 401/403 errors, grab fresh cookies from browser DevTools and
    update CJ_LARAVEL_TOKEN and CJ_CSRF_TOKEN in .env
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

SEARCH_TERMS = [
    "data engineer",
    "data migration engineer",
    "data platform engineer",
    "ETL engineer",
    "data architect",
    "AWS data engineer",
    "PostgreSQL engineer",
    "Redshift engineer",
    "AI automation engineer",
    "AI workflow engineer",
    "AI operations engineer",
    "AI integration engineer",
    "LLM engineer",
    "AI engineer",
]

BASE_URL = "https://api.clearancejobs.com/api/v1"


def get_session():
    """Login with username/password to get a fresh session. No manual cookie needed."""
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
                        json={"username": username, "password": password},
                        timeout=15)
    if resp.status_code != 200:
        print(f"Error: ClearanceJobs login failed ({resp.status_code}): {resp.text[:200]}", file=sys.stderr)
        sys.exit(1)

    csrf = resp.json().get("csrf_token")
    if not csrf:
        print("Error: No csrf_token in login response", file=sys.stderr)
        sys.exit(1)

    session.headers.update({"X-CSRF-TOKEN": csrf})
    print("  [ClearanceJobs] Logged in successfully.")
    return session


def is_acceptable_location(locations, is_telecommute):
    """Return True if job is remote, NYC, or European location."""
    if is_telecommute:
        return True
    for loc in (locations or []):
        loc_str = (loc.get("location") or "").lower()
        if any(k in loc_str for k in ["new york", ", ny", "nyc", "manhattan", "brooklyn"]):
            return True
        if any(k in loc_str for k in ["london", "berlin", "amsterdam", "paris", "dublin",
                                       "barcelona", "madrid", "lisbon", "zurich"]):
            return True
    return False


def scrape(search_terms=None, hours_old=168, results_per_term=25):
    search_terms = search_terms or SEARCH_TERMS
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_old)
    session = get_session()

    all_jobs = []
    seen_urls = set()

    for term in search_terms:
        print(f"  [ClearanceJobs] Scraping '{term}'...")
        page = 1
        term_count = 0
        hit_cutoff = False

        while term_count < results_per_term and not hit_cutoff:
            body = {
                "keywords": term,
                "telecommute": True,
                "page": page,
            }

            try:
                resp = session.post(f"{BASE_URL}/jobs/search", json=body, timeout=15)
                if resp.status_code in (401, 403):
                    print("  [ClearanceJobs] Auth expired — update CJ_LARAVEL_TOKEN and CJ_CSRF_TOKEN in .env", file=sys.stderr)
                    return all_jobs
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"  [ClearanceJobs] Warning: failed page {page} for '{term}': {e}", file=sys.stderr)
                break

            jobs = data.get("data", [])
            if not jobs:
                break

            for job in jobs:
                updated = job.get("updated_at", "")
                if updated:
                    try:
                        job_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                        if job_dt < cutoff:
                            hit_cutoff = True
                            break
                    except ValueError:
                        pass

                url = job.get("job_url", "")
                if not url or url in seen_urls:
                    continue

                locations = job.get("locations") or []
                is_telecommute = True  # we're searching with telecommute=True
                if not is_acceptable_location(locations, is_telecommute):
                    continue

                seen_urls.add(url)
                loc_str = ", ".join(
                    loc.get("location", "") for loc in locations if loc.get("location")
                ) or "Remote"

                all_jobs.append({
                    "title": job.get("job_name", ""),
                    "company": job.get("company_name", ""),
                    "location": loc_str,
                    "remote": str(is_telecommute),
                    "salary_min": "",
                    "salary_max": "",
                    "salary_interval": "",
                    "date_posted": (updated or "")[:10],
                    "description": job.get("preview_text", "")[:3000],
                    "url": url,
                    "site": "clearancejobs",
                    "clearance_required": job.get("clearance", ""),
                    "search_term": term,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                })
                term_count += 1

            pagination = data.get("meta", {}).get("pagination", {})
            if not pagination.get("next_page"):
                break
            page += 1
            time.sleep(1)

    all_jobs.sort(key=lambda x: x.get("date_posted", ""), reverse=True)
    print(f"  [ClearanceJobs] Total unique jobs: {len(all_jobs)}")
    return all_jobs


def main():
    parser = argparse.ArgumentParser(description="Scrape ClearanceJobs.com")
    parser.add_argument("--hours", type=int, default=168)
    parser.add_argument("--results", type=int, default=25)
    parser.add_argument("--output", default=".tmp/jobs_raw.json")
    args = parser.parse_args()

    os.makedirs(".tmp", exist_ok=True)

    existing = []
    if os.path.exists(args.output):
        with open(args.output) as f:
            existing = json.load(f)

    existing_urls = {j.get("url") for j in existing}

    print(f"Scraping ClearanceJobs, last {args.hours}h...")
    new_jobs = scrape(hours_old=args.hours, results_per_term=args.results)
    new_jobs = [j for j in new_jobs if j.get("url") not in existing_urls]

    all_jobs = existing + new_jobs
    all_jobs.sort(key=lambda x: x.get("date_posted", ""), reverse=True)

    with open(args.output, "w") as f:
        json.dump(all_jobs, f, indent=2)

    print(f"Added {len(new_jobs)} new ClearanceJobs jobs. Total in {args.output}: {len(all_jobs)}")


if __name__ == "__main__":
    main()
