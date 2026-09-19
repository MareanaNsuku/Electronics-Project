#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || true
python scripts/maps_scraper.py
python scripts/harvest_emails.py
python scripts/send_emails.py
