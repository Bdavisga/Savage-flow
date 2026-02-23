# Savage Flow Automation - Setup Guide

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd ~/Scripts/savage_flow
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
# Copy the example file
cp .env.example .env

# Edit .env and fill in your actual credentials
nano .env  # or use your preferred editor
```

### 3. Required Credentials

You need to obtain and add the following to your `.env` file:

#### Gmail App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and your device
3. Copy the generated password
4. Add to `.env`: `GMAIL_APP_PASSWORD=your-password-here`

#### Notion API Key
1. Go to https://www.notion.so/my-integrations
2. Create a new integration or use existing
3. Copy the "Internal Integration Token"
4. Add to `.env`: `NOTION_API_KEY=your-key-here`

#### Notion Database ID
1. Open your Notion database
2. Copy the ID from the URL: `https://notion.so/workspace/DATABASE_ID?v=...`
3. Add to `.env`: `NOTION_DATABASE_ID=your-database-id`

#### Anthropic API Key
1. Go to https://console.anthropic.com/settings/keys
2. Create a new API key
3. Copy the key (starts with `sk-ant-`)
4. Add to `.env`: `ANTHROPIC_API_KEY=your-key-here`

### 4. Run the Automation
```bash
python run_savage_flow.py
```

---

## 📋 What the Script Does

1. **Fetches Email** - Gets latest email from Tic Toc Trading via Gmail IMAP
2. **Extracts Data** - Parses trading levels, scenarios, and market bias
3. **Creates Notion Entry** - Adds structured data to your Notion database
4. **Generates Substack Post** - Creates AI-powered or template-based newsletter
5. **Saves Outputs** - Exports JSON payload and markdown post

---

## 🔒 Security Notes

- Never commit `.env` file to git (already in `.gitignore`)
- Keep your API keys secure and rotate them periodically
- Use `.env.example` as reference, not `.env`

---

## 🐛 Troubleshooting

### "No module named 'dotenv'"
```bash
pip install python-dotenv
```

### "GMAIL_APP_PASSWORD not set"
Make sure `.env` file exists and contains your Gmail app password.

### "Notion API Error: 401"
Your Notion API key may be invalid or expired. Regenerate it.

### "anthropic package not installed"
```bash
pip install anthropic
```

---

## 📁 Project Structure

```
savage_flow/
├── run_savage_flow.py      # Main automation script
├── .env                     # Your credentials (DO NOT COMMIT)
├── .env.example             # Template for credentials
├── .gitignore              # Git ignore rules
├── requirements.txt         # Python dependencies
├── SETUP.md                # This file
├── style_rubric.md         # Writing style guide (for AI generation)
├── notion_payload.json     # Latest Notion data (output)
├── substack_post.md        # Latest post (output)
└── .last_email_id          # Tracks processed emails
```

---

## 🎯 Automation Workflow

```
Gmail (IMAP)
    ↓
Extract Trading Data
    ↓
    ├─→ Notion Database (via API)
    └─→ Substack Post (via Claude AI)
         ↓
    Save Outputs (JSON + Markdown)
```

---

## 📅 Scheduling (Optional)

### Using cron (macOS/Linux):
```bash
# Edit crontab
crontab -e

# Run every day at 7 AM
0 7 * * * cd ~/Scripts/savage_flow && /usr/bin/python3 run_savage_flow.py >> ~/Scripts/savage_flow/logs/cron.log 2>&1
```

### Using launchd (macOS):
Create `~/Library/LaunchAgents/com.savageflow.automation.plist`

---

**Questions?** Check the cleanup summary or review the code comments.
