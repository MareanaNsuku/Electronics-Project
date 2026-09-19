# Secure Enclosure Outreach

Automated outreach for requesting electronics warehouse/prototyping space for MEA-06434.

## Setup
1. Edit `config.yaml` and `data/companies.csv`.
2. Set `SMTP_PASS` environment variable.
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python scripts/send_emails.py`

## GitHub Actions
Add `SMTP_PASS` as a repository secret. The workflow runs weekly and on manual dispatch.
