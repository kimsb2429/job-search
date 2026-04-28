#!/bin/bash
# Run the ClearanceJobs scraper, then push the output to the Claw VPS.
# Designed for daily cron use.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"
LOG_DIR="$SCRIPT_DIR/logs"

mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/push.log"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: $ENV_FILE not found. Copy .env.example to .env and fill in." >&2
    exit 1
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

CJ_OUTPUT="${CJ_OUTPUT:-/tmp/cj_jobs.json}"

{
    echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
    echo "Repo root: $REPO_ROOT"

    cd "$REPO_ROOT"
    echo "Running ClearanceJobs scraper..."
    uv run tools/clearancejobs_scraper.py --hours 24 --results 25 --output "$CJ_OUTPUT"

    echo "Pushing to claw..."
    "$SCRIPT_DIR/push_to_claw.sh"

    echo "Done."
} >> "$LOG_FILE" 2>&1

# Surface errors to terminal too
if [ $? -ne 0 ]; then
    echo "ERROR — see $LOG_FILE" >&2
    tail -20 "$LOG_FILE" >&2
    exit 1
fi

echo "OK. Log: $LOG_FILE"
