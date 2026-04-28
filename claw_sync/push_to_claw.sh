#!/bin/bash
# Push the ClearanceJobs scraper output to the Claw VPS.
# Reads config from claw_sync/.env

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: $ENV_FILE not found. Copy .env.example to .env and fill in." >&2
    exit 1
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

CJ_OUTPUT="${CJ_OUTPUT:-/tmp/cj_jobs.json}"

if [ ! -f "$CJ_OUTPUT" ]; then
    echo "ERROR: $CJ_OUTPUT does not exist. Run the scraper first." >&2
    exit 1
fi

count=$(python3 -c "import json,sys; print(len(json.load(open('$CJ_OUTPUT'))))" 2>/dev/null || echo "?")

echo "Pushing $CJ_OUTPUT ($count jobs) to $CLAW_VPS_USER@$CLAW_VPS_HOST:$CLAW_INBOX/jobs_raw.json"
scp -o BatchMode=yes "$CJ_OUTPUT" "$CLAW_VPS_USER@$CLAW_VPS_HOST:$CLAW_INBOX/jobs_raw.json"

echo "Pushed $count jobs to claw."
