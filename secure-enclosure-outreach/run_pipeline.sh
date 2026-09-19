#!/bin/bash
cd "$(dirname "$0")"

# Sync CSV from remote so we never double-contact
if git rev-parse --git-dir >/dev/null 2>&1; then
    git pull --rebase --autostash origin main >/dev/null 2>&1 || true
fi

source venv/bin/activate 2>/dev/null || true

python scripts/maps_scraper.py
python scripts/harvest_emails.py
python scripts/send_emails.py

# Push updated CSV back
if git rev-parse --git-dir >/dev/null 2>&1; then
    git add data/master_companies.csv
    if ! git diff --cached --quiet; then
        git -c user.email="bot@local" -c user.name="Outreach Bot" \
            commit -m "Update outreach CSV [skip ci]"
        git push origin main >/dev/null 2>&1 || true
    fi
fi
