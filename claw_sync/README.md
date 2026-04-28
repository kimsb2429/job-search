# claw_sync — push ClearanceJobs results to the Claw VPS

Self-contained pipeline that runs the existing `tools/clearancejobs_scraper.py` and ships the output to the Claw discovery agent on the VPS.

This is needed because the VPS IP is blocked from `clearancejobs.com` at the network level — the scraper has to run from a residential IP (your laptop).

## Setup

1. **Configure** — copy and fill in:
   ```bash
   cp claw_sync/.env.example claw_sync/.env
   ```
   Set `CLAW_VPS_HOST`, `CLAW_VPS_USER`, and `CLAW_INBOX` (the destination path on the VPS).

2. **SSH key** — make sure your laptop can SSH into the VPS without a password prompt:
   ```bash
   ssh -o BatchMode=yes "$CLAW_VPS_USER@$CLAW_VPS_HOST" exit
   ```
   If that prompts for a password, run `ssh-copy-id` first.

3. **Test once manually:**
   ```bash
   ./claw_sync/run_and_push.sh
   ```
   You should see CJ scrape progress, then a "Pushed N jobs to claw" line.

4. **Schedule** — add to crontab (see `crontab.example`):
   ```bash
   crontab -e
   ```
   Recommended: 8:30am daily, just before the VPS daily discovery job at 9am ET.

## What gets pushed

The script:

1. Runs `uv run tools/clearancejobs_scraper.py --hours 24 --results 25 --output /tmp/cj_jobs.json`
2. `scp`'s `/tmp/cj_jobs.json` to `$CLAW_VPS_USER@$CLAW_VPS_HOST:$CLAW_INBOX/jobs_raw.json`
3. Logs to `claw_sync/logs/push.log`

Same JSON format the existing scraper produces — the VPS-side discovery agent reads it as one of its sources.

## Files

- `run_and_push.sh` — wrapper: runs scraper, pushes result
- `push_to_claw.sh` — push only (use if you have your own scraper output)
- `.env.example` — config template
- `crontab.example` — cron schedule snippet
