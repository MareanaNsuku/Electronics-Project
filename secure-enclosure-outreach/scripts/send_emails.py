import csv
import os
import smtplib
import yaml
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

CONFIG_PATH = 'config.yaml' if os.path.exists('config.yaml') else 'config.example.yaml'
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

SMTP_SERVER = config['smtp_server']
SMTP_PORT = config['smtp_port']
SMTP_USER = config['smtp_user']
SMTP_PASS = os.environ.get('SMTP_PASS')
FROM_EMAIL = config['from_email']
FROM_NAME = config['from_name']

if not SMTP_PASS:
    raise SystemExit("SMTP_PASS environment variable not set")

with open('templates/email_template.txt', 'r') as f:
    template = f.read()

companies = []
with open('data/companies.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        companies.append(row)

for company in companies:
    if company['status'] != 'pending':
        continue

    subject = "Request for Electronics Warehouse Space – MEA-06434"
    body = template.format(
        company_name=company['company_name'],
        contact_person=company['contact_person'],
        from_name=FROM_NAME,
        from_title=config.get('from_title', ''),
        from_email=FROM_EMAIL,
        from_phone=config.get('from_phone', ''),
        github_repo=config.get('github_repo', ''),
        duration_weeks=config.get('duration_weeks', ''),
        start_date=config.get('start_date', ''),
    )

    msg = MIMEMultipart()
    msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg['To'] = company['email']
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        company['status'] = 'sent'
        company['date_sent'] = datetime.now().strftime('%Y-%m-%d')
        print(f"Sent to {company['email']}")
    except Exception as e:
        print(f"Failed to send to {company['email']}: {e}")
        company['status'] = 'error'

fieldnames = ['company_name', 'contact_person', 'email', 'status', 'date_sent', 'notes']
with open('data/companies.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(companies)
