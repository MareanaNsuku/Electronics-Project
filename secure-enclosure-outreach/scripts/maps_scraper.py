#!/usr/bin/env python3
"""Google Maps scraper using DOM extraction (stable across JSON changes)."""
import sys, time, urllib.parse, os, re, csv, random
from playwright.sync_api import sync_playwright
import yaml

def load_config():
    path = 'config.yaml' if os.path.exists('config.yaml') else 'config.example.yaml'
    with open(path) as f:
        return yaml.safe_load(f)

def extract_place_urls(page, max_urls=12):
    """Collect unique /maps/place/ URLs from the current search page."""
    try:
        page.wait_for_selector('a[href*="/maps/place/"]', timeout=8000)
    except:
        return []
    links = page.eval_on_selector_all(
        'a[href*="/maps/place/"]',
        'els => els.map(e => e.href)'
    )
    seen, out = set(), []
    for l in links:
        base = l.split('?')[0]
        if base in seen:
            continue
        # ignore review/photo pages
        if '/reviews' in l or '/photos' in l:
            continue
        seen.add(base)
        out.append(l)
        if len(out) >= max_urls:
            break
    return out

def extract_place_details(page, url):
    """Visit a single place page and pull name / website / phone / address."""
    d = {"name": "", "website": "", "phone": "", "address": ""}
    try:
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(800)
    except Exception as e:
        return d
    # Name
    try:
        d["name"] = page.locator('h1').first.inner_text(timeout=1200).strip()
    except:
        pass
    # Website (multiple selector fallbacks)
    for sel in [
        'a[data-item-id="authority"]',
        'a[aria-label^="Website:"]',
        'a[data-tooltip="Open website"]',
    ]:
        try:
            href = page.locator(sel).first.get_attribute('href', timeout=800)
            if href:
                d["website"] = href
                break
        except:
            continue
    # Phone
    for sel in [
        'button[data-item-id^="phone:tel:"]',
        'button[aria-label^="Phone:"]',
    ]:
        try:
            aria = page.locator(sel).first.get_attribute('aria-label', timeout=800)
            if aria:
                d["phone"] = re.sub(r'^Phone:\s*', '', aria).strip()
                break
        except:
            continue
    # Address
    for sel in [
        'button[data-item-id="address"]',
        'button[aria-label^="Address:"]',
    ]:
        try:
            aria = page.locator(sel).first.get_attribute('aria-label', timeout=800)
            if aria:
                d["address"] = re.sub(r'^Address:\s*', '', aria).strip()
                break
        except:
            continue
    return d

def main():
    cfg = load_config()
    queries = cfg.get('queries', [])
    cities = cfg.get('cities', [])

    all_places = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="en-ZA",
            viewport={"width": 1280, "height": 900},
        )
        search_page = ctx.new_page()
        detail_page = ctx.new_page()

        total = len(queries) * len(cities)
        i = 0
        for query in queries:
            for city in cities:
                i += 1
                full_query = f"{query} {city} South Africa"
                print(f"[{i}/{total}] 🔍 {full_query}")
                url = f"https://www.google.com/maps/search/{urllib.parse.quote(full_query)}"
                try:
                    search_page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    search_page.wait_for_timeout(4000)
                    place_urls = extract_place_urls(search_page, max_urls=6)
                    print(f"        → {len(place_urls)} place URLs")
                    for pu in place_urls:
                        d = extract_place_details(detail_page, pu)
                        if d["name"]:
                            all_places.append(d)
                            print(f"           • {d['name']}  {d['website']}")
                        time.sleep(random.uniform(0.5, 1.0))
                except Exception as e:
                    print(f"        ❌ {e}")
                time.sleep(random.uniform(1, 2))
        browser.close()

    # Deduplicate by name (fallback by website)
    seen, unique = set(), []
    for r in all_places:
        key = (r["name"].lower().strip(), r["website"].lower().strip())
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)

    os.makedirs('data', exist_ok=True)
    with open('data/master_companies.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['Company Name', 'Website', 'Phone', 'Address', 'Emails Found', 'Status'])
        for r in unique:
            w.writerow([r['name'], r['website'], r['phone'], r['address'], '', ''])

    print(f"\n✅ Saved {len(unique)} unique companies to data/master_companies.csv")

if __name__ == '__main__':
    main()
