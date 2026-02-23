#!/bin/bash
# Savage Flow Daily Automation Runner
# Runs the automation with required environment variables
# Checks for new emails and only processes if new content found

# Change to project dir so load_dotenv() finds .env
cd /Users/brandondavis/Scripts/savage_flow

# Files
LOG_FILE="/Users/brandondavis/Scripts/savage_flow/savage_flow.log"
LAST_EMAIL_FILE="/Users/brandondavis/Scripts/savage_flow/.last_email_id"

echo "----------------------------------------" >> "$LOG_FILE"
echo "$(date): Checking for new emails..." >> "$LOG_FILE"

/usr/bin/python3 /Users/brandondavis/Scripts/savage_flow/run_savage_flow.py >> "$LOG_FILE" 2>&1

echo "$(date): Check complete" >> "$LOG_FILE"
