---
name: job-application
description: Discover remote data engineering jobs on Indeed/Glassdoor/ZipRecruiter/ClearanceJobs, score against profile, sync to Google Sheet, auto-apply where possible, and send email digest for manual applications.
user-invocable: true
---

# Workflow: Job Application Pipeline

## Objective
Discover remote data engineering / data migration / AI automation / AI workflow jobs on Indeed, score them against Jae's profile, and sync new listings to a Google Sheet for manual review and application.

## Candidate Profile
- **Name:** Jae Kim — Data Architect / Data Engineer
- **Location:** New York, NY (seeking remote)
- **Security Clearance:** Active Secret clearance (eligible for cleared and non-cleared roles)
- **Core Stack:** PostgreSQL, PL/SQL, Python, AWS (Glue, DMS, Redshift, Lambda), Java/Spring, Jenkins, Terraform
- **Strengths:** Legacy-to-cloud data migration, microservices/strangler pattern, REST API security, stakeholder leadership, event-driven pipelines
- **Background:** Princeton BA Chemistry, WashU MFA/PhD (Digital Humanities), 10+ years in data engineering
- **Target roles:** Data Engineer, Data Migration Engineer, AI Automation Engineer, AI Workflow Engineer, AI Engineer, Data Architect
- **Open to:** Full-time, part-time, fractional, and contract roles
- **Salary:** Open
- **Location filter:** Remote only

## Inputs Required
- `credentials.json` in project root (Google OAuth — one-time setup)
- `token.json` auto-generated on first run

## Steps

### Step 1 — Scrape job boards

**Indeed + Glassdoor + ZipRecruiter** (via JobSpy):
```bash
uv run tools/job_scraper.py --hours 168 --results 25
```

**ClearanceJobs** (appends to same file):
```bash
uv run tools/clearancejobs_scraper.py --hours 168 --results 25
```

Output: `.tmp/jobs_raw.json`

**ClearanceJobs auth:** Uses `CJ_USERNAME` and `CJ_PASSWORD` from `.env`. Logs in fresh every run — no manual cookie management needed.

**Notes:**
- Default search terms: AI engineer roles prioritized first ("AI engineer remote", "AI automation engineer remote", "applied AI engineer remote", "generative AI engineer remote", "LLM engineer remote", "agentic AI engineer remote", ...), then data engineering. See `DEFAULT_SEARCH_TERMS` in `job_scraper.py` for the full list.
- Add/remove terms by editing `DEFAULT_SEARCH_TERMS` in `job_scraper.py`
- `--hours 72` = jobs posted in the last 3 days. Use `--hours 168` for a full week.
- Indeed has no rate limiting currently. No proxy needed for normal use.

### Step 2 — Score jobs (agent step — done by Claude)
Read `.tmp/jobs_raw.json` and for each job, score against Jae's actual resume.

**Jae's verified skills (use these for matching — not keywords, actual experience):**
- **Cloud/infra:** AWS (Glue, DMS, Redshift, Workflows, Lambda, State Machine, Textract), Terraform, Jenkins
- **Data:** PostgreSQL, PL/SQL, SQL Server, data migration, legacy-to-cloud, data sync, event-driven pipelines, AWS Glue ETL
- **Languages:** Python, Java/Spring, PL/SQL, Excel VBA
- **Architecture:** Microservices, strangler pattern, REST API design + security testing
- **Testing/tooling:** TestNG, Allure, Insomnia
- **Domain:** Federal/government (VA), healthcare-adjacent, financial data (Valkyrie Trading)
- **Soft:** Stakeholder leadership, cross-functional solutioning, scope/requirements definition
- **Clearance:** Active Secret clearance

**Score 1–10:**
- **9–10:** Direct match — remote DE/migration/data architect role, 3+ tools explicitly on resume, senior/lead level
- **7–8:** Strong match — right role type, 2+ tools explicitly on resume, seniority fits
- **5–6:** Right role type but only 1 resume tool match, OR adjacent role (platform eng, data architect) with 2+ matches
- **3–4:** Weak match — right domain but wrong role, or no resume tool overlap
- **1–2:** Wrong role type, wrong location, or irrelevant domain

**Critical rule: only count tools/skills explicitly listed on the resume. Do not give credit for "adjacent" or "transferable" skills. If Kafka, dbt, Spark, Snowflake, or any other tool isn't on the resume, it does not count as a match — even if it's conceptually similar to something that is.**

**Auto-disqualify (score 1) if any:**
- On-site outside NYC and outside Europe — non-starter
- NYC on-site or hybrid: acceptable, no scoring penalty
- Europe (London, Berlin, Amsterdam, etc.): acceptable, no scoring penalty
- Sales, support, management-only, or recruiter roles
- Principal or Lead-level titles (too senior)
- Duplicate posting (same job, different city)
- Posted > 30 days ago

**Score reasoning:** 1–2 sentences citing specific resume skills that match (or don't).

Output: `.tmp/jobs_scored.json` — same structure as `jobs_raw.json` with two added fields:
```json
{
  "score": 8,
  "score_reasoning": "Strong stack match (PostgreSQL, Python, AWS). Senior DE role at a federal contractor — Secret clearance is an asset here."
}
```

Filter out jobs with score < 5 before writing to scored file.

### Step 3 — Sync to Google Sheet
```bash
uv run tools/sheets_tracker.py --jobs .tmp/jobs_scored.json
```

On first run: browser opens for Google OAuth. Approve it.
Sheet ID is saved to `.tmp/sheet_id.txt` for future deduplication.

Output: URL to "Job Tracker" Google Sheet printed to console.

### Step 4 — Auto-apply (ClearanceJobs email-method only)
```bash
uv run tools/auto_apply.py --threshold 7
```

**What it does:**
- Filters ClearanceJobs jobs with score >= threshold (default 7)
- For each candidate: fetches job detail to check `apply_method`
- Applies only to `email`-method jobs (native CJ application using your on-file profile — no browser needed)
- Skips `url`/`ats`-method jobs and prints their links for manual apply
- Updates Google Sheet Status column to "Applied" for each successful application

**Apply methods on ClearanceJobs:**
- `email` (~35%): Fully automated. Single API call, uses your on-file profile/resume.
- `url` (~50%): External company site. Apply manually.
- `ats` (~15%): External ATS (Greenhouse, Lever, Workday). Apply manually.

**Dry run (preview without applying):**
```bash
uv run tools/auto_apply.py --threshold 7 --dry-run
```

### Step 5 — Send email digest (manual apply jobs)
```bash
uv run tools/notify.py
```

**What it does:**
- Reads all rows with Status == "New" from the Google Sheet
- Sends an HTML email to kimsb2429@gmail.com with each job as a card (title, company, score, reasoning, Apply button)
- Each **Apply →** button is a tracking link: clicking it marks the row as "Applied" in the sheet, then redirects to the job listing
- After sending, marks all notified rows as "Pending" so they don't repeat in future digests

**Status flow:**
- `New` → just scraped, not yet notified
- `Pending` → in digest, awaiting your manual apply
- `Applied` → done (set by clicking Apply → in email, or by auto_apply.py for CJ email-method jobs)

**One-time setup (Google Apps Script redirect handler):**
1. Open the Job Tracker Google Sheet → Extensions → Apps Script
2. Paste contents of `tools/apps_script_tracker.js` → Save
3. Deploy → New deployment → Type: Web app → Execute as: Me → Who has access: Anyone → Deploy → Authorize
4. Copy the Web app URL → add to `.env`:
   ```
   APPS_SCRIPT_URL=https://script.google.com/macros/s/.../exec
   ```
5. Delete `token.json` (re-auth needed to add Gmail scope) → run `uv run tools/notify.py` → authorize in browser

**Dry run (preview without sending):**
```bash
uv run tools/notify.py --dry-run
```

## Outputs
- **Google Sheet "Job Tracker"** with columns:
  - Title | Company | Location | Remote | Salary Min | Salary Max | Date Posted
  - Score | Score Reasoning | URL | Site
  - Status (default: "New") | Applied Date | Notes | Scraped At

## Running the Full Pipeline
Ask Claude:
> "Run the job application pipeline"

Claude will execute Steps 1–5 in order and return the sheet URL, a summary of auto-applied jobs, and confirm the digest email was sent.

## Iterating on Search
To refine what gets surfaced, adjust:
- **Search terms:** Edit `DEFAULT_SEARCH_TERMS` in `job_scraper.py`
- **Score threshold:** Currently filters < 5. Change in Step 2.
- **Scoring criteria:** Edit the scoring rubric in Step 2 above
- **Time window:** Change `--hours` flag (72 = 3 days, 168 = 1 week)

## Edge Cases
- **Rate limiting (429):** Indeed rarely rate-limits, but if it happens, wait 10 min and retry. Add `--results 15` to reduce load.
- **OAuth expired:** Delete `token.json` and re-run to re-authorize.
- **Duplicate jobs:** `sheets_tracker.py` deduplicates by URL — safe to re-run anytime.
- **Empty results:** Try wider `--hours` window or add more `--site` options.

## Future Phases
- [ ] Add LinkedIn scraping (`--site linkedin`)
- [ ] Add cover letter generation per job (triggered on specific job URL)
- [ ] Add resume bullet tailoring per job description
- [ ] Add email monitoring for responses (Gmail API)
