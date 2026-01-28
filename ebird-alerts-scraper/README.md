# eBird Alerts Auto-Scraper

Automatically scrapes rare bird sightings from your eBird alert subscription and publishes them to GitHub Pages.

## Features

- Daily automatic updates via GitHub Actions
- Clean, responsive HTML display with sortable columns
- JSON data export for programmatic access
- Mobile-friendly design

## Setup Instructions

### 1. Create a GitHub Repository

1. Create a new repository on GitHub
2. Clone it locally and copy these files into it
3. Push the initial commit

### 2. Get Your eBird Session Cookies

Since eBird alerts require authentication, you need to provide your session cookies:

1. **Log into eBird** in your web browser
2. **Open Developer Tools** (F12 or right-click → Inspect)
3. **Go to the Network tab**
4. **Visit your alert page**: https://ebird.org/alert/summary?sid=SN35466
5. **Find any request** in the Network tab and click on it
6. **Copy the Cookie header** value from the Request Headers section
   - It will look something like: `_ga=GA1.2....; EBIRD_SESSIONID=abc123; ...`

### 3. Add Cookie as GitHub Secret

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `EBIRD_COOKIES`
5. Value: Paste the cookie string you copied
6. Click **Add secret**

### 4. Enable GitHub Pages

1. Go to **Settings** → **Pages**
2. Under "Source", select **Deploy from a branch**
3. Select `main` branch and `/docs` folder
4. Click **Save**

### 5. Run the Workflow

1. Go to **Actions** tab
2. Select "Scrape eBird Alerts" workflow
3. Click **Run workflow** to test it manually

After a few minutes, your GitHub Pages site will be live at:
`https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/`

## Local Development

To run the scraper locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Set your cookies as an environment variable
export EBIRD_COOKIES="your_cookie_string_here"

# Run the scraper
python scraper/scrape.py
```

The output will be generated in the `docs/` folder.

## Customization

### Change the Alert URL

Edit `scraper/scrape.py` and update the `ALERT_URL` constant with your specific alert URL.

### Change Update Frequency

Edit `.github/workflows/scrape.yml` and modify the cron schedule:
- `0 6 * * *` = Daily at 6 AM UTC
- `0 */6 * * *` = Every 6 hours
- `0 6,18 * * *` = Twice daily at 6 AM and 6 PM UTC

### Customize the HTML Template

Edit `templates/index.html` to change the styling or layout.

## Troubleshooting

### "Redirected to login page" Error

Your session cookies have expired. Get new cookies by:
1. Log into eBird again in your browser
2. Copy the new Cookie header
3. Update the `EBIRD_COOKIES` secret in GitHub

### No Sightings Found

The scraper may need adjustment for the specific page structure. Check:
- That you're logged in when copying cookies
- That the alert URL is correct
- The raw HTML in the workflow logs for debugging

## Files

| File | Description |
|------|-------------|
| `scraper/scrape.py` | Main scraper script |
| `templates/index.html` | Jinja2 HTML template |
| `.github/workflows/scrape.yml` | GitHub Actions workflow |
| `docs/index.html` | Generated HTML page |
| `docs/data.json` | Generated JSON data |

## License

MIT License - Feel free to modify and use as you wish.
