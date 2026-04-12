# Job Search

Automated job discovery, scoring, and application pipeline for remote data engineering roles. Personal use only — not a business.

## Architecture

Skills (`.claude/skills/`) define pipelines. Tools (`tools/`) handle execution — Python scripts for scraping, scoring, syncing, and applying.

## File Structure

```
tools/              # Python scripts (scraper, scorer, auto-apply, notifier)
.tmp/               # Intermediate files (jobs_raw.json, jobs_scored.json). Disposable.
.env                # API keys, CJ credentials
credentials.json    # Google OAuth (gitignored)
token.json          # Auto-generated OAuth token (gitignored)
```

## Key Conventions

- Deliverables go to cloud services (Google Sheets), not local files
- `.tmp/` is fully disposable — all intermediate data can be regenerated

## Before Expanding Auto-Apply

Before adding any new auto-apply channel, research whether a legitimate API exists:
- Check if the job board has a public candidate-facing apply API (rare)
- Check GitHub for open-source solutions and their approach
- Document findings and present before building

**Known apply channels (as of March 2026):**
- ClearanceJobs `email`-method: API-based (implemented in `tools/auto_apply.py`)
- LinkedIn / Indeed / ZipRecruiter: No public apply API — browser automation only (fragile, ToS risk)
- Greenhouse ATS: Has API but requires per-company private key (not practical for bulk)
