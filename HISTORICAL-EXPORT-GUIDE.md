# Historical Reports Export Guide

## 🎯 What This Does

Exports your **entire trading report history** from multiple sources and formats them as Substack-ready markdown files that you can easily upload.

**Sources:**
- ✅ Gmail (all historical Tic Toc Trading emails)
- ✅ Notion (all past database entries)
- ✅ Local files (future: auto-scan)

**Output:**
Clean, formatted markdown files organized by date and source, ready to copy/paste into Substack.

---

## 🚀 Quick Start

### Step 1: Run the Export

```bash
cd ~/Scripts/savage_flow
python3 export_historical_reports.py
```

This will:
- Connect to Gmail and download all historical emails
- Connect to Notion and export all database entries
- Convert everything to markdown
- Save organized files to `~/Scripts/savage_flow/historical_exports/`

**Time estimate:** 2-5 minutes depending on volume

---

### Step 2: Review Exported Files

```bash
cd ~/Scripts/savage_flow/historical_exports

# Check Gmail exports
ls -lh gmail/

# Check Notion exports
ls -lh notion/
```

You'll see files like:
```
gmail/
  2025-01-15_email_001.md
  2025-01-16_email_002.md
  2025-01-17_email_003.md
  ...

notion/
  notion_entry_001.md
  notion_entry_002.md
  ...
```

---

### Step 3: Upload to Substack

**Manual Upload Process:**

1. **Open Substack** → Go to your publication
2. **Click "New Post"**
3. **Open exported markdown file** in text editor
4. **Copy entire contents**
5. **Paste into Substack editor**
6. **Set publication date** to match original date
7. **Add any images/formatting**
8. **Save as draft or publish**
9. **Repeat** for each file

**Tip:** Start with most recent and work backwards chronologically.

---

## ⚙️ Configuration Options

### Limit Number of Emails

Edit `export_historical_reports.py`:

```python
# Line 91 - Change limit value
gmail_emails = fetch_all_gmail_emails(limit=100)  # Process last 100 emails

# Or remove limit for ALL emails
gmail_emails = fetch_all_gmail_emails(limit=None)  # Get everything
```

### Change Output Directory

```python
# Line 25
OUTPUT_DIR = '/Users/brandondavis/Desktop/SubstackExports'  # New location
```

### Filter by Date Range

Add date filtering (modify the script):

```python
# Only emails from last 6 months
from datetime import timedelta
cutoff_date = datetime.now() - timedelta(days=180)

gmail_emails = [e for e in fetch_all_gmail_emails() if e['date'] > cutoff_date]
```

---

## 📋 File Organization

### Gmail Exports

Format: `YYYY-MM-DD_email_NNN.md`

Example content:
```markdown
# ES Daily Plan - 02/10/26

Subject line from email...

---

Email body content here...

---

**Source:** Tic Toc Trading
**Generated:** 2026-02-11

*Trade the scenario. Respect the levels. Manage the risk.*
```

### Notion Exports

Format: `notion_entry_NNN.md`

Example content:
```markdown
# Day 02/10/26 - ES Analysis

**Date:** 2026-02-10
**ES Level:** 6050
**Market Bias:** Bullish

---

*Exported from Notion Database*

**Generated:** 2026-02-11
```

---

## 🎨 Customizing the Format

### Add Your Branding

Edit the template in `convert_to_substack_markdown()`:

```python
markdown = f"""# ES Daily Plan - {date_str}

{data['subject']}

---

{data['body'][:1000]}

---

**Market Savage Trades**
Follow me: [Twitter](link) | [YouTube](link)

*Trade the scenario. Respect the levels. Manage the risk.*
"""
```

### Include Trading Icons

```python
# Add bias emoji
bias_emoji = '📈' if 'bullish' in data['body'].lower() else '📉'

markdown = f"""# {bias_emoji} ES Daily Plan - {date_str}
...
```

### Add More Data

Include ES levels, targets, scenarios from email parsing:

```python
# You can integrate the extract_trading_data() function
from run_savage_flow import extract_trading_data

trading_data = extract_trading_data(email_data["body"])

markdown = f"""# ES Daily Plan - {date_str}

**Key Zone:** {trading_data['key_zone']}
**Market Bias:** {trading_data['market_bias']}
**ES Level:** {trading_data.get('es_level', 'N/A')}

---

{data['body']}
"""
```

---

## 🤖 Bulk Upload Options

### Option 1: Substack Import API

Substack has a beta import API. Contact them for access:
- Email: support@substack.com
- Subject: "Bulk Import API Access"

Then use their import endpoint to programmatically create posts.

### Option 2: WordPress Export Format

Convert to WordPress XML format, which Substack can import:

```bash
# Install conversion tool
pip install markdown-to-wordpress

# Convert all markdown files
python3 convert_to_wordpress_xml.py
```

Then import via Substack settings → Import.

### Option 3: Manual with Shortcuts

**macOS Automator workflow:**
1. Read markdown file
2. Copy to clipboard
3. Open Substack in browser
4. Paste content
5. Set date from filename
6. Save draft

Can process 1 file every 10-15 seconds.

---

## 📊 Dealing with Large Volumes

### If you have 100+ reports:

**Strategy 1: Prioritize Recent**
- Export last 20-30 most recent
- Upload those first
- Gradually add older content

**Strategy 2: Best-of Collection**
- Review exports, pick highest quality
- Manually enhance before uploading
- Create "best analysis" series

**Strategy 3: Hire VA**
- Export everything
- Hire virtual assistant on Upwork/Fiverr
- Have them copy/paste and format
- Cost: ~$20-50 for 100 posts

---

## 🔧 Advanced: Automated Upload

**Requirements:**
- Substack API access (request from support)
- Or use browser automation (Selenium/Playwright)

**Selenium Example:**
```python
from selenium import webdriver

driver = webdriver.Chrome()
driver.get("https://substack.com/signin")

# Login automation
# Navigate to "New Post"
# Paste content
# Set date
# Publish

# Loop through all markdown files
```

---

## 📁 Directory Structure After Export

```
~/Scripts/savage_flow/
├── historical_exports/
│   ├── gmail/
│   │   ├── 2025-01-15_email_001.md
│   │   ├── 2025-01-16_email_002.md
│   │   └── ... (all email exports)
│   │
│   ├── notion/
│   │   ├── notion_entry_001.md
│   │   ├── notion_entry_002.md
│   │   └── ... (all Notion exports)
│   │
│   └── manifest.json (coming soon - index of all exports)
│
└── export_historical_reports.py
```

---

## ✅ Checklist

- [ ] Run export script
- [ ] Review generated files
- [ ] Pick format strategy (manual/bulk/VA)
- [ ] Test upload with 1-2 files
- [ ] Batch upload remaining files
- [ ] Set correct publication dates
- [ ] Add images/formatting as needed
- [ ] Cross-reference with Notion for accuracy

---

## 🐛 Troubleshooting

**"No emails found"**
- Check `GMAIL_ADDRESS` in .env
- Verify `GMAIL_APP_PASSWORD` is correct
- Check sender filter matches your emails

**"Notion API error"**
- Verify `NOTION_API_KEY` in .env
- Check `NOTION_DATABASE_ID` is correct
- Ensure Notion integration has access

**"Files not created"**
- Check permissions on output directory
- Verify disk space available
- Look for error messages in output

**"Export is too slow"**
- Reduce limit: `limit=50` instead of `limit=None`
- Process in batches
- Run overnight for large volumes

---

## 💡 Pro Tips

1. **Date Preservation:** Use original email dates when uploading to Substack
2. **SEO:** Add relevant keywords to titles/content
3. **Cross-link:** Link new posts to your Notion database
4. **Archive:** Keep exports folder as backup
5. **Automate:** Set up monthly exports to keep archive current

---

**Ready to build your Substack archive!** 🚀

Any questions? Need help customizing the export format?
