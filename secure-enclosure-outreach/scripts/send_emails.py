#!/usr/bin/env python3
"""Send warehouse-space request emails."""
import csv, os, smtplib, yaml
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

CONFIG_PATH = os.environ.get('CONFIG_FILE') or ('config.yaml' if os.path.exists('config.yaml') else 'config.example.yaml')
if not os.path.exists(CONFIG_PATH):
    CONFIG_PATH = 'config.yaml' if os.path.exists('config.yaml') else 'config.example.yaml'
with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)

SMTP_PASS = os.environ.get('SMTP_PASS')
if not SMTP_PASS:
    raise SystemExit("❌ SMTP_PASS environment variable not set")

with open('data/email_template.txt') as f:
    template = f.read()

with open('data/master_companies.csv', 'r') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

sent_count = 0
for row in rows:
    status = (row.get('Status') or '').strip().lower()
    if status == 'sent':
        continue
    if status.startswith('error'):
        continue
    emails_raw = row.get('Emails Found', '').strip()
    if not emails_raw:
        continue
    emails = [e.strip() for e in emails_raw.split(',') if '@' in e]
    if not emails:
        continue
    to_email = emails[0]

    body = template.format(
        contact_person=row.get('Company Name', 'there'),
        from_name=config['from_name'],
        from_title=config.get('from_title', ''),
        from_email=config['from_email'],
        from_phone=config.get('from_phone', ''),
        github_repo=config.get('github_repo', ''),
        linkedin_url=config.get('linkedin_url', ''),
        duration_weeks=config.get('duration_weeks', ''),
        start_date=config.get('start_date', ''),
    )

    msg = MIMEMultipart()
    msg['From'] = f"{config['from_name']} <{config['from_email']}>"
    msg['To'] = to_email
    msg['Subject'] = "Request for Electronics Warehouse/Prototyping Space – MEA-06434"
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as s:
            s.starttls()
            s.login(config['smtp_user'], SMTP_PASS)
            s.send_message(msg)
        row['Status'] = 'sent'
        sent_count += 1
        print(f"✅ Sent to {to_email}")
    except Exception as e:
        row['Status'] = f'error: {e}'
        print(f"❌ Failed {to_email}: {e}")

with open('data/master_companies.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['Company Name', 'Website', 'Phone', 'Address', 'Emails Found', 'Status'])
    writer.writeheader()
    writer.writerows(rows)

print(f"\n🎉 Sent {sent_count} new emails.")
