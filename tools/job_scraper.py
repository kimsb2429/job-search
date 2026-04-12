"""
job_scraper.py

Scrapes Indeed (and optionally other boards) for jobs matching Jae's criteria.
Uses JobSpy library — no API key required.

Usage:
    uv run tools/job_scraper.py
    uv run tools/job_scraper.py --site indeed linkedin --hours 48

Output:
    .tmp/jobs_raw.json  — list of job dicts, newest first
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

from jobspy import scrape_jobs


DEFAULT_SEARCH_TERMS = [
    "data engineer remote",
    "data migration engineer remote",
    "data platform engineer remote",
    "ETL engineer remote",
    "data pipeline engineer remote",
    "data architect remote",
    "Snowflake data engineer",
    "Databricks data engineer",
    "AWS Glue data engineer",
    "Redshift data engineer",
    "PostgreSQL data engineer",
    "AI automation engineer remote",
    "AI workflow engineer remote",
    "AI operations engineer remote",
    "AI integration engineer remote",
    "automation engineer AI remote",
    "LLM engineer remote",
    "AI engineer remote",
    "fractional data engineer",
    "fractional AI engineer",
    "part time data engineer remote",
    "contract AI engineer remote",
]

DEFAULT_SITES = ["indeed", "glassdoor", "zip_recruiter"]

DEFAULT_HOURS_OLD = 168  # only jobs posted in the last N hours

# Post-scrape filter: drop any job where is_remote is explicitly False
REMOTE_ONLY = True


def scrape(search_terms=None, sites=None, hours_old=None, results_per_term=25):
    search_terms = search_terms or DEFAULT_SEARCH_TERMS
    sites = sites or DEFAULT_SITES
    hours_old = hours_old or DEFAULT_HOURS_OLD

    all_jobs = []
    seen_urls = set()

    for term in search_terms:
        print(f"  Scraping '{term}' on {sites}...")
        try:
            df = scrape_jobs(
                site_name=sites,
                search_term=term,
                location="United States",
                results_wanted=results_per_term,
                hours_old=hours_old,
                is_remote=True,
                country_indeed="USA",
            )

            for _, row in df.iterrows():
                url = row.get("job_url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                job = {
                    "title": row.get("title", ""),
                    "company": row.get("company", ""),
                    "location": row.get("location", ""),
                    "remote": str(row.get("is_remote", "")),
                    "salary_min": str(row.get("min_amount", "")),
                    "salary_max": str(row.get("max_amount", "")),
                    "salary_interval": str(row.get("interval", "")),
                    "date_posted": str(row.get("date_posted", "")),
                    "description": (row.get("description", "") or "")[:3000],
                    "url": url,
                    "site": row.get("site", ""),
                    "search_term": term,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                }
                # Filter: keep remote, NYC, or Europe — drop all other on-site US
                if REMOTE_ONLY and str(row.get("is_remote", "")).lower() == "false":
                    loc = str(row.get("location", "")).lower()
                    nyc = any(k in loc for k in ["new york", ", ny", "nyc", "manhattan", "brooklyn", "queens"])
                    europe = any(k in loc for k in ["london", "berlin", "amsterdam", "paris", "dublin", "barcelona", "madrid", "lisbon", "zurich", "remote, eu"])
                    if not nyc and not europe:
                        continue

                all_jobs.append(job)

        except Exception as e:
            print(f"  Warning: failed scraping '{term}': {e}", file=sys.stderr)

        time.sleep(2)  # avoid rate limiting on Glassdoor/ZipRecruiter

    # Sort newest first
    all_jobs.sort(key=lambda x: x.get("date_posted", ""), reverse=True)
    print(f"  Total unique jobs found: {len(all_jobs)}")
    return all_jobs


def main():
    parser = argparse.ArgumentParser(description="Scrape job listings")
    parser.add_argument("--site", nargs="+", default=DEFAULT_SITES,
                        choices=["indeed", "linkedin", "glassdoor", "zip_recruiter"],
                        help="Job boards to scrape")
    parser.add_argument("--hours", type=int, default=DEFAULT_HOURS_OLD,
                        help="Only include jobs posted within this many hours")
    parser.add_argument("--results", type=int, default=25,
                        help="Results per search term per site")
    args = parser.parse_args()

    os.makedirs(".tmp", exist_ok=True)
    output_path = ".tmp/jobs_raw.json"

    print(f"Scraping {args.site}, last {args.hours}h...")
    jobs = scrape(sites=args.site, hours_old=args.hours, results_per_term=args.results)

    with open(output_path, "w") as f:
        json.dump(jobs, f, indent=2)

    print(f"Saved {len(jobs)} jobs to {output_path}")


if __name__ == "__main__":
    main()
