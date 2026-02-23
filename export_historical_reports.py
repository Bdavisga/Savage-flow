#!/usr/bin/env python3
"""
Export Historical Reports for Substack
Consolidates past reports from Notion, Gmail, and local files
Formats them as Substack-ready markdown files
"""

import os
import json
import imaplib
import email
from email.header import decode_header
from datetime import datetime
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

# Configuration
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
GMAIL_SENDER_FILTER = os.environ.get("GMAIL_SENDER_FILTER", "tictoctrading@substack.com")
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

OUTPUT_DIR = '/Users/brandondavis/Scripts/savage_flow/historical_exports'


def fetch_all_gmail_emails(limit=None):
    """Fetch ALL historical emails from Tic Toc Trading"""

    if not GMAIL_APP_PASSWORD:
        print("❌ GMAIL_APP_PASSWORD not set")
        return []

    print(f"📧 Connecting to Gmail to fetch historical emails...")

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD.replace(" ", ""))
        mail.select("inbox")

        # Search for ALL emails from sender
        search_criteria = f'(FROM "{GMAIL_SENDER_FILTER}")'
        status, messages = mail.search(None, search_criteria)

        if status != "OK" or not messages[0]:
            print("❌ No emails found")
            mail.logout()
            return []

        email_ids = messages[0].split()
        total = len(email_ids)

        if limit:
            email_ids = email_ids[-limit:]  # Get most recent N emails

        print(f"✅ Found {total} total emails, processing {len(email_ids)}...")

        emails = []

        for i, email_id in enumerate(email_ids, 1):
            try:
                status, msg_data = mail.fetch(email_id, "(RFC822)")

                if status != "OK":
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Get subject
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8")

                # Get date
                date_tuple = email.utils.parsedate_tz(msg["Date"])
                if date_tuple:
                    email_date = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                else:
                    email_date = datetime.now()

                # Get body (simplified for batch processing)
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = payload.decode('utf-8', errors='ignore')
                                break
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode('utf-8', errors='ignore')

                emails.append({
                    "subject": subject,
                    "date": email_date,
                    "body": body
                })

                if i % 10 == 0:
                    print(f"  Processed {i}/{len(email_ids)} emails...")

            except Exception as e:
                print(f"⚠️  Error processing email {i}: {e}")
                continue

        mail.logout()
        print(f"✅ Successfully fetched {len(emails)} emails")
        return emails

    except Exception as e:
        print(f"❌ Error fetching emails: {e}")
        return []


def fetch_all_notion_entries():
    """Fetch ALL entries from Notion database"""

    if not NOTION_API_KEY or not NOTION_DATABASE_ID:
        print("⚠️  Notion credentials not set - skipping Notion export")
        return []

    print(f"📊 Fetching all Notion database entries...")

    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    all_entries = []
    has_more = True
    start_cursor = None

    try:
        while has_more:
            payload = {}
            if start_cursor:
                payload["start_cursor"] = start_cursor

            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')

            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))

                all_entries.extend(result.get('results', []))
                has_more = result.get('has_more', False)
                start_cursor = result.get('next_cursor')

                print(f"  Fetched {len(all_entries)} entries so far...")

        print(f"✅ Successfully fetched {len(all_entries)} Notion entries")
        return all_entries

    except Exception as e:
        print(f"❌ Error fetching Notion entries: {e}")
        return []


def convert_to_substack_markdown(data, source="email"):
    """Convert email or Notion entry to Substack-ready markdown"""

    if source == "email":
        date_str = data['date'].strftime("%m/%d/%y")

        # Simple template format
        markdown = f"""# ES Daily Plan - {date_str}

{data['subject']}

---

{data['body'][:1000]}

---

**Source:** Tic Toc Trading
**Generated:** {datetime.now().strftime("%Y-%m-%d")}

*Trade the scenario. Respect the levels. Manage the risk.*
"""

    elif source == "notion":
        # Extract properties from Notion entry
        props = data.get('properties', {})

        title = ""
        if 'Name' in props and props['Name'].get('title'):
            title = props['Name']['title'][0]['text']['content']

        date_str = "N/A"
        if 'Week Of' in props and props['Week Of'].get('date'):
            date_str = props['Week Of']['date']['start']

        es_level = props.get('ES Level', {}).get('number', 'N/A')
        market_bias = props.get('Market Bias', {}).get('select', {}).get('name', 'Neutral')

        markdown = f"""# {title}

**Date:** {date_str}
**ES Level:** {es_level}
**Market Bias:** {market_bias}

---

*Exported from Notion Database*

**Generated:** {datetime.now().strftime("%Y-%m-%d")}
"""

    return markdown


def main():
    """Main export workflow"""

    print("=" * 60)
    print("📦 HISTORICAL REPORTS EXPORT FOR SUBSTACK")
    print("=" * 60)
    print()

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print()

    # Export from Gmail
    print("1️⃣  GMAIL EXPORT")
    print("-" * 60)
    gmail_emails = fetch_all_gmail_emails(limit=100)  # Adjust limit as needed

    print()
    print(f"📝 Converting {len(gmail_emails)} emails to markdown...")

    for i, email_data in enumerate(gmail_emails, 1):
        try:
            markdown = convert_to_substack_markdown(email_data, source="email")

            # Create filename with date
            date_str = email_data['date'].strftime("%Y-%m-%d")
            filename = f"{date_str}_email_{i:03d}.md"
            filepath = os.path.join(OUTPUT_DIR, 'gmail', filename)

            os.makedirs(os.path.join(OUTPUT_DIR, 'gmail'), exist_ok=True)

            with open(filepath, 'w') as f:
                f.write(markdown)

            if i % 10 == 0:
                print(f"  Converted {i}/{len(gmail_emails)} emails...")

        except Exception as e:
            print(f"⚠️  Error converting email {i}: {e}")
            continue

    print(f"✅ Saved {len(gmail_emails)} email reports to {OUTPUT_DIR}/gmail/")
    print()

    # Export from Notion
    print("2️⃣  NOTION EXPORT")
    print("-" * 60)
    notion_entries = fetch_all_notion_entries()

    print()
    print(f"📝 Converting {len(notion_entries)} Notion entries to markdown...")

    for i, entry in enumerate(notion_entries, 1):
        try:
            markdown = convert_to_substack_markdown(entry, source="notion")

            # Get date from entry or use index
            filename = f"notion_entry_{i:03d}.md"
            filepath = os.path.join(OUTPUT_DIR, 'notion', filename)

            os.makedirs(os.path.join(OUTPUT_DIR, 'notion'), exist_ok=True)

            with open(filepath, 'w') as f:
                f.write(markdown)

            if i % 10 == 0:
                print(f"  Converted {i}/{len(notion_entries)} entries...")

        except Exception as e:
            print(f"⚠️  Error converting entry {i}: {e}")
            continue

    print(f"✅ Saved {len(notion_entries)} Notion reports to {OUTPUT_DIR}/notion/")
    print()

    # Summary
    print("=" * 60)
    print("✅ EXPORT COMPLETE!")
    print("=" * 60)
    print()
    print(f"📊 Total exports:")
    print(f"  • Gmail: {len(gmail_emails)} reports")
    print(f"  • Notion: {len(notion_entries)} reports")
    print(f"  • Total: {len(gmail_emails) + len(notion_entries)} reports")
    print()
    print(f"📁 Location: {OUTPUT_DIR}")
    print()
    print("📌 Next steps:")
    print("1. Review the exported markdown files")
    print("2. Copy/paste each into Substack as new posts")
    print("3. Set correct publication dates")
    print("4. Add any custom formatting or images")
    print()


if __name__ == "__main__":
    main()
