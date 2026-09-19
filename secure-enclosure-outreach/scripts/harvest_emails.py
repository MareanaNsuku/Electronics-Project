#!/usr/bin/env python3
"""Scrape emails from company websites."""
import csv, re, time, random, sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
SKIP_EXT = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.pdf', '.zip', '.css', '.js')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
}

def extract_emails(url, timeout=8):
    emails = set()
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if r.status_code != 200:
            return emails
        soup = BeautifulSoup(r.text, 'html.parser')
        text = soup.get_text(" ")
        for e in EMAIL_RE.findall(text):
            emails.add(e.lower())
        # mailto links
        for a in soup.find_all('a', href=True):
            if a['href'].lower().startswith('mailto:'):
                addr = a['href'][7:].split('?')[0].strip().lower()
                if EMAIL_RE.match(addr):
                    emails.add(addr)
        # contact page
        for a in soup.find_all('a', href=True):
            href = a['href'].lower()
            if any(k in href for k in ['contact', 'kontak', 'about', 'info']):
                if href.endswith(SKIP_EXT):
                    continue
                link = urljoin(url, a['href'])
                if urlparse(link).netloc != urlparse(url).netloc:
                    continue
                try:
                    r2 = requests.get(link, headers=HEADERS, timeout=timeout)
                    for e in EMAIL_RE.findall(r2.text):
                        emails.add(e.lower())
                except:
                    pass
                break
    except Exception as e:
        pass
    # filter junk
    return {e for e in emails if not any(x in e for x in ['example.com', 'sentry', 'wixpress', '.png', '.jpg'])}

def main():
    with open('data/master_companies.csv', 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"📧 Harvesting emails from {len(rows)} companies...")
    for i, row in enumerate(rows, 1):
        if row.get('Emails Found'):
            continue
        url = row.get('Website', '').strip()
        if not url or not url.startswith('http'):
            continue
        print(f"[{i}/{len(rows)}] {row['Company Name']}")
        emails = extract_emails(url)
        if emails:
            row['Emails Found'] = ','.join(sorted(emails))
            print(f"   ✅ {len(emails)} emails")
        else:
            print(f"   ⚠️  none found")
        time.sleep(random.uniform(1, 2))
    
    with open('data/master_companies.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Company Name', 'Website', 'Phone', 'Address', 'Emails Found', 'Status'])
        writer.writeheader()
        writer.writerows(rows)
    
    print("✅ Email harvesting complete.")

if __name__ == '__main__':
    main()
