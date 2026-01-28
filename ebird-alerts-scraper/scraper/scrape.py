#!/usr/bin/env python3
"""
eBird Alert Scraper
Fetches rare bird sightings from eBird alerts and generates HTML/JSON output.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

# Configuration
ALERT_URL = "https://ebird.org/alert/summary?sid=SN35466"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def get_cookies_from_env():
    """Parse cookies from environment variable."""
    cookie_string = os.environ.get("EBIRD_COOKIES", "")
    if not cookie_string:
        print("ERROR: EBIRD_COOKIES environment variable not set")
        sys.exit(1)

    cookies = {}
    for item in cookie_string.split(";"):
        item = item.strip()
        if "=" in item:
            key, value = item.split("=", 1)
            cookies[key.strip()] = value.strip()
    return cookies


def fetch_alerts(cookies):
    """Fetch the eBird alerts page."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    session = requests.Session()
    session.cookies.update(cookies)

    response = session.get(ALERT_URL, headers=headers, timeout=30)

    if response.status_code != 200:
        print(f"ERROR: Failed to fetch alerts. Status code: {response.status_code}")
        if "login" in response.url.lower():
            print("ERROR: Redirected to login page. Cookies may have expired.")
        sys.exit(1)

    return response.text


def parse_alerts(html):
    """Parse the alerts page and extract sighting data."""
    soup = BeautifulSoup(html, "html.parser")
    sightings = []

    # eBird alerts are typically organized in sections by date
    # Look for sighting entries in the page

    # Find all observation rows - eBird uses various structures
    # Try multiple selectors to find sightings

    # Look for the main content area
    content = soup.find("div", {"id": "content"}) or soup.find("main") or soup

    # Find species entries - eBird uses different formats
    # Try to find entries with species names and location data

    # Method 1: Look for observation cards/rows
    obs_rows = content.find_all("div", class_=lambda x: x and ("Observation" in str(x) or "obs" in str(x).lower()))

    # Method 2: Look for list items with species info
    if not obs_rows:
        obs_rows = content.find_all("li", class_=lambda x: x and "species" in str(x).lower())

    # Method 3: Look for table rows
    if not obs_rows:
        obs_rows = content.find_all("tr")

    # Method 4: Look for any links to checklists
    if not obs_rows:
        # Find all links that look like checklist links
        checklist_links = content.find_all("a", href=lambda x: x and "/checklist/" in str(x))
        for link in checklist_links:
            parent = link.find_parent(["div", "li", "tr"])
            if parent and parent not in obs_rows:
                obs_rows.append(parent)

    for row in obs_rows:
        sighting = extract_sighting_data(row)
        if sighting and sighting.get("species"):
            sightings.append(sighting)

    # If we still have no sightings, try a more generic approach
    if not sightings:
        sightings = extract_sightings_generic(soup)

    return sightings


def extract_sighting_data(element):
    """Extract sighting data from an element."""
    sighting = {
        "species": "",
        "location": "",
        "date": "",
        "observer": "",
        "checklist_url": "",
        "count": ""
    }

    # Find species name - usually in a link or strong tag
    species_elem = (
        element.find("a", class_=lambda x: x and "species" in str(x).lower()) or
        element.find("span", class_=lambda x: x and "species" in str(x).lower()) or
        element.find("strong") or
        element.find("b")
    )
    if species_elem:
        sighting["species"] = species_elem.get_text(strip=True)

    # Find location
    location_elem = (
        element.find(class_=lambda x: x and "location" in str(x).lower()) or
        element.find("a", href=lambda x: x and "/hotspot/" in str(x))
    )
    if location_elem:
        sighting["location"] = location_elem.get_text(strip=True)

    # Find date
    date_elem = element.find(class_=lambda x: x and "date" in str(x).lower())
    if date_elem:
        sighting["date"] = date_elem.get_text(strip=True)

    # Find observer
    observer_elem = (
        element.find(class_=lambda x: x and "observer" in str(x).lower()) or
        element.find("a", href=lambda x: x and "/profile/" in str(x))
    )
    if observer_elem:
        sighting["observer"] = observer_elem.get_text(strip=True)

    # Find checklist URL
    checklist_link = element.find("a", href=lambda x: x and "/checklist/" in str(x))
    if checklist_link:
        href = checklist_link.get("href", "")
        if href.startswith("/"):
            href = "https://ebird.org" + href
        sighting["checklist_url"] = href

    return sighting


def extract_sightings_generic(soup):
    """Generic extraction when specific selectors fail."""
    sightings = []

    # Get all text content and try to identify patterns
    # This is a fallback approach

    # Look for any structured data
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            data = json.loads(script.string)
            # Process structured data if available
            if isinstance(data, list):
                for item in data:
                    if "name" in item:
                        sightings.append({
                            "species": item.get("name", ""),
                            "location": item.get("location", {}).get("name", "") if isinstance(item.get("location"), dict) else "",
                            "date": item.get("datePublished", ""),
                            "observer": "",
                            "checklist_url": item.get("url", ""),
                            "count": ""
                        })
        except (json.JSONDecodeError, AttributeError):
            pass

    return sightings


def generate_output(sightings, output_dir):
    """Generate HTML and JSON output files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Prepare data
    data = {
        "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "alert_url": ALERT_URL,
        "sightings": sightings,
        "count": len(sightings)
    }

    # Write JSON
    json_path = output_path / "data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Written: {json_path}")

    # Generate HTML
    template_dir = Path(__file__).parent.parent / "templates"
    if template_dir.exists():
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("index.html")
        html_content = template.render(**data)
    else:
        # Fallback: generate simple HTML if template doesn't exist
        html_content = generate_simple_html(data)

    html_path = output_path / "index.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Written: {html_path}")


def generate_simple_html(data):
    """Generate simple HTML without template."""
    rows = ""
    for s in data["sightings"]:
        checklist = f'<a href="{s["checklist_url"]}" target="_blank">View</a>' if s["checklist_url"] else "-"
        rows += f"""
        <tr>
            <td>{s['species']}</td>
            <td>{s['location']}</td>
            <td>{s['date']}</td>
            <td>{s['observer']}</td>
            <td>{checklist}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>eBird Rare Bird Alerts</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #4a7c59; color: white; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        .updated {{ color: #666; font-size: 0.9em; margin-bottom: 20px; }}
        a {{ color: #4a7c59; }}
    </style>
</head>
<body>
    <h1>Rare Bird Alerts</h1>
    <p class="updated">Last updated: {data['last_updated']} | {data['count']} sightings</p>
    <table>
        <thead>
            <tr>
                <th>Species</th>
                <th>Location</th>
                <th>Date</th>
                <th>Observer</th>
                <th>Checklist</th>
            </tr>
        </thead>
        <tbody>{rows if rows else '<tr><td colspan="5">No sightings found</td></tr>'}
        </tbody>
    </table>
    <p><a href="data.json">Download JSON data</a></p>
</body>
</html>"""


def main():
    print("eBird Alert Scraper")
    print("=" * 40)

    # Get cookies
    print("Loading cookies from environment...")
    cookies = get_cookies_from_env()
    print(f"Loaded {len(cookies)} cookies")

    # Fetch alerts
    print(f"Fetching alerts from {ALERT_URL}...")
    html = fetch_alerts(cookies)
    print(f"Received {len(html)} bytes")

    # Parse alerts
    print("Parsing sightings...")
    sightings = parse_alerts(html)
    print(f"Found {len(sightings)} sightings")

    # Generate output
    output_dir = Path(__file__).parent.parent / "docs"
    print(f"Generating output to {output_dir}...")
    generate_output(sightings, output_dir)

    print("Done!")


if __name__ == "__main__":
    main()
