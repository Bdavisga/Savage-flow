#!/usr/bin/env python3
"""
Savage Flow Automation Runner
Complete workflow: Gmail -> Notion -> Substack
"""

import imaplib
import email
from email.header import decode_header
import json
import re
import os
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from html.parser import HTMLParser
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

# Configuration - All sensitive values loaded from .env file
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
GMAIL_SENDER_FILTER = os.environ.get("GMAIL_SENDER_FILTER", "tictoctrading@substack.com")
GMAIL_SENDER_FILTERS = [
    os.environ.get("GMAIL_SENDER_FILTER_1", "tictoctrading@substack.com"),
    os.environ.get("GMAIL_SENDER_FILTER_2", "adamset@substack.com"),
]
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

OUTPUT_DIR = '/Users/brandondavis/Scripts/savage_flow'
STYLE_RUBRIC_FILE = os.path.join(OUTPUT_DIR, 'style_rubric.md')


def _email_id_file(sender: str) -> str:
    """Return the per-sender last-email-id file path"""
    safe = re.sub(r'[^a-zA-Z0-9]', '_', sender)
    return os.path.join(OUTPUT_DIR, f'.last_email_id_{safe}')


def get_last_processed_email_id(sender: str):
    """Get the ID of the last processed email for a given sender"""
    try:
        with open(_email_id_file(sender), 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def save_last_processed_email_id(email_id, sender: str):
    """Save the ID of the last processed email for a given sender"""
    with open(_email_id_file(sender), 'w') as f:
        f.write(str(email_id))


class HTMLTextExtractor(HTMLParser):
    """Extract text from HTML content"""
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ['script', 'style']:
            self.skip = True

    def handle_endtag(self, tag):
        if tag in ['script', 'style']:
            self.skip = False
        if tag in ['p', 'br', 'div', 'h1', 'h2', 'h3', 'li']:
            self.text.append('\n')

    def handle_data(self, data):
        if not self.skip:
            self.text.append(data)

    def get_text(self):
        return ''.join(self.text)


def html_to_text(html_content):
    """Convert HTML to plain text"""
    parser = HTMLTextExtractor()
    parser.feed(html_content)
    text = parser.get_text()
    # Clean up whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()


def fetch_latest_email(sender: str = None):
    """Fetch the latest email from a given sender via Gmail IMAP"""

    sender = sender or GMAIL_SENDER_FILTER

    if not GMAIL_APP_PASSWORD:
        print("❌ GMAIL_APP_PASSWORD not set")
        return None

    print(f"  📧 Checking {sender}...")

    try:
        # Connect to Gmail IMAP
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD.replace(" ", ""))
        mail.select("inbox")

        search_criteria = f'(FROM "{sender}")'
        status, messages = mail.search(None, search_criteria)

        if status != "OK" or not messages[0]:
            print(f"  ❌ No emails found from {sender}")
            mail.logout()
            return None

        # Get the latest email
        email_ids = messages[0].split()
        latest_id = email_ids[-1]

        # Check if we've already processed this email
        last_processed = get_last_processed_email_id(sender)
        if last_processed == latest_id.decode():
            print(f"  ℹ️  No new emails from {sender}")
            mail.logout()
            return None

        status, msg_data = mail.fetch(latest_id, "(RFC822)")

        if status != "OK":
            print(f"  ❌ Failed to fetch email from {sender}")
            mail.logout()
            return None

        # Parse the email
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Get subject
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8")

        # Get body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode('utf-8', errors='ignore')
                        break
                elif content_type == "text/html" and not body:
                    payload = part.get_payload(decode=True)
                    if payload:
                        html_body = payload.decode('utf-8', errors='ignore')
                        body = html_to_text(html_body)
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                if msg.get_content_type() == "text/html":
                    body = html_to_text(payload.decode('utf-8', errors='ignore'))
                else:
                    body = payload.decode('utf-8', errors='ignore')

        mail.logout()

        print(f"  ✅ Found NEW email: {subject}")

        # Save this email ID as processed
        save_last_processed_email_id(latest_id.decode(), sender)

        return {
            "subject": subject,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "body": body
        }

    except imaplib.IMAP4.error as e:
        print(f"❌ IMAP Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error fetching email: {e}")
        return None


def clean_email_body(body: str) -> str:
    """Strip Substack boilerplate and source branding from email body"""
    lines = body.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Skip Substack view-on-web links
        if re.match(r'^View this post on the web at\s+https?://\S+', stripped, re.IGNORECASE):
            continue
        # Skip bare Substack URLs
        if re.match(r'^https?://\S*substack\.com\S*$', stripped, re.IGNORECASE):
            continue
        # Skip source branding lines
        if re.match(r'^(tic\s*toc|tictoc)\s*trading', stripped, re.IGNORECASE):
            continue
        if re.match(r'^(adam\s*set|set\s*from\s*setstack|setstack)', stripped, re.IGNORECASE):
            continue
        # Remove inline substack URLs embedded within other text
        line = re.sub(r'https?://\S*substack\.com\S*', '', line)
        cleaned.append(line)
    # Collapse excess blank lines
    text = '\n'.join(cleaned)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_trading_data(email_body: str) -> dict:
    """Extract key trading levels and scenarios from email"""

    # Default structure
    data = {
        "es_level": None,
        "spx_level": None,
        "key_zone": "",
        "support_levels": [],
        "resistance_levels": [],
        "downside_target": None,
        "upside_target": None,
        "scenarios": [],
        "market_bias": "Neutral",
        "key_observations": [],
        "macro_theme": ""
    }

    # Extract numbers that look like ES levels (4 digits starting with 6 or 7)
    level_pattern = r'\b([67]\d{3})\b'
    levels = [int(x) for x in re.findall(level_pattern, email_body)]

    if levels:
        levels = sorted(set(levels))
        # Assume middle levels are key, highest is resistance, lowest is support
        if len(levels) >= 2:
            data["support_levels"] = levels[:len(levels)//2 + 1]
            data["resistance_levels"] = levels[len(levels)//2:]
            data["downside_target"] = min(levels)
            data["upside_target"] = max(levels)
            data["es_level"] = levels[len(levels)//2]
            data["spx_level"] = data["es_level"] - 60  # Approximate SPX from ES
            data["key_zone"] = f"{levels[len(levels)//2]}-{levels[len(levels)//2 + 1] if len(levels) > len(levels)//2 + 1 else levels[-1]}"

    # Extract scenarios
    scenario_pattern = r'Scenario \d+[:\s]+(.+?)(?=Scenario \d+|~|$)'
    scenarios = re.findall(scenario_pattern, email_body, re.DOTALL | re.IGNORECASE)
    data["scenarios"] = [s.strip()[:200] for s in scenarios]

    # Determine bias from keywords
    body_lower = email_body.lower()
    bullish_words = ['bullish', 'higher', 'rally', 'upside', 'support held', 'continuation']
    bearish_words = ['bearish', 'lower', 'selloff', 'sell off', 'downside', 'breakdown']

    bullish_count = sum(1 for w in bullish_words if w in body_lower)
    bearish_count = sum(1 for w in bearish_words if w in body_lower)

    if bullish_count > bearish_count + 1:
        data["market_bias"] = "Bullish"
    elif bearish_count > bullish_count + 1:
        data["market_bias"] = "Bearish"
    elif bullish_count > bearish_count:
        data["market_bias"] = "Neutral-Bullish"
    elif bearish_count > bullish_count:
        data["market_bias"] = "Neutral-Bearish"
    else:
        data["market_bias"] = "Neutral"

    # Extract key observations (sentences with important keywords)
    sentences = re.split(r'[.!?\n]', email_body)
    important_keywords = ['must', 'need', 'key', 'important', 'critical', 'watch', 'hold', 'break', 'invalidat']
    for sentence in sentences:
        if any(kw in sentence.lower() for kw in important_keywords):
            clean = sentence.strip()
            if 20 < len(clean) < 150:
                data["key_observations"].append(clean)
    data["key_observations"] = data["key_observations"][:5]

    # Try to extract a theme from the subject or first paragraph
    first_para = email_body.split('\n\n')[0] if '\n\n' in email_body else email_body[:200]
    data["macro_theme"] = first_para[:100].strip()

    return data


def merge_trading_data(data_list: list) -> dict:
    """Merge trading data from multiple sources into a unified dataset"""

    if len(data_list) == 1:
        return data_list[0]

    # Collect all levels across sources, deduplicate within 5-point proximity
    all_levels_raw = []
    for d in data_list:
        all_levels_raw.extend(d.get("support_levels", []))
        all_levels_raw.extend(d.get("resistance_levels", []))
    all_levels_raw = sorted(set(all_levels_raw))

    # Deduplicate nearby levels (within 5 points, keep average)
    deduped = []
    for level in all_levels_raw:
        if deduped and abs(level - deduped[-1]) <= 5:
            deduped[-1] = round((deduped[-1] + level) / 2)
        else:
            deduped.append(level)

    # Split into support/resistance at midpoint
    if len(deduped) >= 2:
        mid = len(deduped) // 2
        support_levels = deduped[:mid + 1]
        resistance_levels = deduped[mid:]
    else:
        support_levels = deduped
        resistance_levels = deduped

    # Widest range for targets
    all_downside = [d["downside_target"] for d in data_list if d.get("downside_target")]
    all_upside = [d["upside_target"] for d in data_list if d.get("upside_target")]
    downside_target = min(all_downside) if all_downside else None
    upside_target = max(all_upside) if all_upside else None

    # ES level: average of all sources
    es_levels = [d["es_level"] for d in data_list if d.get("es_level")]
    es_level = round(sum(es_levels) / len(es_levels)) if es_levels else None

    # Key zone from merged levels
    if len(deduped) > 1:
        mid = len(deduped) // 2
        key_zone = f"{deduped[mid]}-{deduped[mid + 1] if mid + 1 < len(deduped) else deduped[-1]}"
    else:
        key_zone = str(deduped[0]) if deduped else ""

    # Bias: count across all sources combined
    bias_map = {"Bullish": 2, "Neutral-Bullish": 1, "Neutral": 0,
                "Neutral-Bearish": -1, "Bearish": -2}
    bias_scores = [bias_map.get(d.get("market_bias", "Neutral"), 0) for d in data_list]
    avg_bias = sum(bias_scores) / len(bias_scores)
    if avg_bias > 1:
        market_bias = "Bullish"
    elif avg_bias > 0.25:
        market_bias = "Neutral-Bullish"
    elif avg_bias < -1:
        market_bias = "Bearish"
    elif avg_bias < -0.25:
        market_bias = "Neutral-Bearish"
    else:
        market_bias = "Neutral"

    # Concatenate scenarios from all sources (cap at 6)
    scenarios = []
    for d in data_list:
        scenarios.extend(d.get("scenarios", []))
    scenarios = scenarios[:6]

    # Merge observations, deduplicate, cap at 6
    observations = []
    seen = set()
    for d in data_list:
        for obs in d.get("key_observations", []):
            lower = obs.lower().strip()
            if lower not in seen:
                seen.add(lower)
                observations.append(obs)
    observations = observations[:6]

    # Combine macro themes
    themes = [d.get("macro_theme", "") for d in data_list if d.get("macro_theme")]
    macro_theme = " | ".join(themes)[:150]

    return {
        "es_level": es_level,
        "spx_level": (es_level - 60) if es_level else None,
        "key_zone": key_zone,
        "support_levels": support_levels,
        "resistance_levels": resistance_levels,
        "downside_target": downside_target,
        "upside_target": upside_target,
        "scenarios": scenarios,
        "market_bias": market_bias,
        "key_observations": observations,
        "macro_theme": macro_theme,
    }


def create_notion_payload(email_data: dict, trading_data: dict) -> dict:
    """Create Notion page payload"""

    date_str = datetime.now().strftime("%m/%d/%y")

    return {
        "Name": f"Savage Flow Methodology - {date_str}",
        "Status": "Active",
        "Outcome": "In Progress",
        "ES Level": trading_data.get("es_level") or 0,
        "SPX Level": trading_data.get("spx_level") or 0,
        "Key Pivot": trading_data["resistance_levels"][0] if trading_data["resistance_levels"] else 0,
        "Market Bias": trading_data["market_bias"],
        "Key Zone": trading_data["key_zone"],
        "Downside Target": trading_data.get("downside_target") or 0,
        "Upside Target": trading_data.get("upside_target") or 0,
        "Primary Setup": "Waiting",
        "date:Week Of:start": email_data["date"],
        "date:Week Of:is_datetime": 0
    }


def push_to_notion(trading_data: dict, email_data: dict) -> dict:
    """Push entry to Notion database via API"""

    if not NOTION_API_KEY:
        print("⚠️  NOTION_API_KEY not set - skipping Notion push")
        return None

    date_str = datetime.now().strftime("%m/%d/%y")

    hvn_text = f"{trading_data['key_zone']} (key zone)"
    if trading_data['support_levels']:
        hvn_text += f", {trading_data['support_levels'][0]} (support)"

    # Build the Notion API payload
    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Name": {
                "title": [{"text": {"content": f"Savage Flow Methodology - {date_str}"}}]
            },
            "Status": {
                "select": {"name": "Active"}
            },
            "Outcome": {
                "select": {"name": "In Progress"}
            },
            "ES Level": {
                "number": trading_data.get("es_level") or 0
            },
            "SPX Level": {
                "number": trading_data.get("spx_level") or 0
            },
            "Key Pivot": {
                "number": trading_data["resistance_levels"][0] if trading_data["resistance_levels"] else 0
            },
            "Market Bias": {
                "select": {"name": trading_data["market_bias"]}
            },
            "HVN Levels": {
                "rich_text": [{"text": {"content": hvn_text}}]
            },
            "Bearish Target": {
                "number": trading_data.get("downside_target") or 0
            },
            "Bullish Target": {
                "number": trading_data.get("upside_target") or 0
            },
            "Edge Case High": {
                "number": trading_data.get("upside_target") or 0
            },
            "Edge Case Low": {
                "number": trading_data.get("downside_target") or 0
            },
            "Primary Setup": {
                "select": {"name": "Waiting"}
            },
            "Week Of": {
                "date": {"start": email_data["date"]}
            }
        }
    }

    # Make the API request
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"❌ Notion API Error: {e.code} - {error_body}")
        return None
    except Exception as e:
        print(f"❌ Error pushing to Notion: {e}")
        return None


def upload_file_to_slack(file_path: str, title: str = None) -> bool:
    """Upload a file to Slack (requires SLACK_BOT_TOKEN)"""
    slack_token = os.environ.get("SLACK_BOT_TOKEN")
    slack_channel = os.environ.get("SLACK_CHANNEL_ID")

    if not slack_token or not slack_channel:
        print("ℹ️  SLACK_BOT_TOKEN or SLACK_CHANNEL_ID not set - skipping file upload")
        return False

    try:
        with open(file_path, 'rb') as f:
            data = f.read()

        # Create multipart form data
        boundary = '----WebKitFormBoundary' + ''.join([str(i) for i in range(16)])
        body = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="channels"\r\n\r\n{slack_channel}\r\n'
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="title"\r\n\r\n{title or "Substack Draft"}\r\n'
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(file_path)}"\r\n'
            f'Content-Type: text/markdown\r\n\r\n'
        ).encode('utf-8') + data + f'\r\n--{boundary}--\r\n'.encode('utf-8')

        req = urllib.request.Request(
            'https://slack.com/api/files.upload',
            data=body,
            headers={
                'Authorization': f'Bearer {slack_token}',
                'Content-Type': f'multipart/form-data; boundary={boundary}'
            }
        )

        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get('ok'):
                print("✅ File uploaded to Slack!")
                return True
            else:
                print(f"⚠️  File upload failed: {result.get('error')}")
                return False

    except Exception as e:
        print(f"❌ Error uploading file to Slack: {e}")
        return False


def send_slack_notification(email_data: dict, trading_data: dict, notion_url: str = None, substack_preview: str = None, substack_file: str = None) -> bool:
    """Send completion notification to Slack with key details"""

    if not SLACK_WEBHOOK_URL:
        print("ℹ️  SLACK_WEBHOOK_URL not set - skipping Slack notification")
        return False

    date_str = datetime.now().strftime("%m/%d/%y")

    # Determine bias emoji
    bias = trading_data.get('market_bias', 'Neutral')
    if 'Bullish' in bias:
        bias_emoji = '📈'
    elif 'Bearish' in bias:
        bias_emoji = '📉'
    else:
        bias_emoji = '↔️'

    # Build the notification message
    message_blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Savage Flow Methodology - {date_str}",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Market Bias:*\n{bias_emoji} {trading_data.get('market_bias', 'N/A')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*ES Level:*\n{trading_data.get('es_level', 'N/A')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Key Zone:*\n{trading_data.get('key_zone', 'N/A')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Scenarios:*\n{len(trading_data.get('scenarios', []))} setups"
                }
            ]
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Upside Target:*\n{trading_data.get('upside_target', 'N/A')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Downside Target:*\n{trading_data.get('downside_target', 'N/A')}"
                }
            ]
        },
        {"type": "divider"}
    ]

    # Add links section
    links = []
    if notion_url:
        links.append(f"📊 <{notion_url}|Notion Database Entry>")
    if substack_file:
        links.append(f"📝 Substack Draft: `{substack_file}`")
    if links:
        message_blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n".join(links)
            }
        })

    # Add action buttons
    buttons = []
    if notion_url:
        buttons.append({
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "📊 Open Notion",
                "emoji": True
            },
            "url": notion_url,
            "style": "primary"
        })
    if buttons:
        message_blocks.append({
            "type": "actions",
            "elements": buttons
        })

    # Add preview snippet
    if substack_preview:
        preview_text = substack_preview[:200] + "..." if len(substack_preview) > 200 else substack_preview
        message_blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"```{preview_text}```"
            }
        })

    message_blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "Savage Flow Methodology | Ready for review and publishing"
            }
        ]
    })

    payload = {
        "blocks": message_blocks
    }

    # Send to Slack
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            SLACK_WEBHOOK_URL,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("✅ Slack notification sent!")
                return True
            else:
                print(f"⚠️  Slack notification failed: {response.status}")
                return False

    except Exception as e:
        print(f"❌ Error sending Slack notification: {e}")
        return False


def _generate_substack_post_template(email_data: dict, trading_data: dict) -> str:
    """Fallback: Generate Substack post using simple template (no LLM)"""

    date_str = datetime.now().strftime("%m/%d/%y")

    # Build levels table
    levels_rows = ""
    all_levels = sorted(set(trading_data["support_levels"] + trading_data["resistance_levels"]), reverse=True)
    for level in all_levels:
        if level == trading_data.get("upside_target"):
            levels_rows += f"| **{level}** | Upside Target |\n"
        elif level in trading_data["resistance_levels"]:
            levels_rows += f"| **{level}** | Resistance |\n"
        elif level in trading_data["support_levels"]:
            levels_rows += f"| **{level}** | Support |\n"
        if level == trading_data.get("downside_target"):
            levels_rows += f"| **{level}** | Downside Target |\n"

    # Build scenarios section
    scenarios_text = ""
    for i, scenario in enumerate(trading_data["scenarios"], 1):
        scenarios_text += f"### Scenario {i}\n\n{scenario}\n\n"

    # Build observations
    observations = "\n".join(f"- {obs}" for obs in trading_data["key_observations"])

    post = f"""# Savage Flow Methodology - {date_str}

**{trading_data['macro_theme'][:100]}**

---

## Market Context

{email_data['body'][:500]}...

---

## KEY LEVELS

| Level | Type |
|-------|------|
{levels_rows.strip()}

---

## SCENARIO ANALYSIS

{scenarios_text if scenarios_text else "See email for detailed scenarios."}

---

## CRITICAL OBSERVATIONS

{observations if observations else "- Monitor key levels for confirmation"}

---

**Key Resistance:** {trading_data['resistance_levels'][0] if trading_data['resistance_levels'] else 'TBD'}
**Key Support:** {trading_data['support_levels'][0] if trading_data['support_levels'] else 'TBD'}
**Bias:** {trading_data['market_bias']}
**Upside:** {trading_data.get('upside_target') or 'TBD'} | **Downside:** {trading_data.get('downside_target') or 'TBD'}

*Trade the scenario. Respect the levels. Manage the risk.*

---

### Risk Disclaimer

This newsletter is educational content only. Not financial advice. Trading involves substantial risk.

"""

    return post


def _load_style_rubric() -> str:
    """Load the style rubric from the external markdown file"""
    try:
        with open(STYLE_RUBRIC_FILE, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"⚠️  Style rubric not found at {STYLE_RUBRIC_FILE}")
        return ""


def generate_substack_post(email_data: dict, trading_data: dict) -> tuple[str, bool]:
    """Generate Substack-ready markdown post.

    Attempts LLM-powered generation via Claude API. Falls back to
    template-based generation if API key is missing or the call fails.

    Returns:
        tuple of (post_content, used_ai) where used_ai indicates
        whether the AI-powered path was used.
    """

    # Check if we can use the AI path
    if not ANTHROPIC_API_KEY:
        print("  ℹ️  No ANTHROPIC_API_KEY set — using template fallback")
        return _generate_substack_post_template(email_data, trading_data), False

    if not HAS_ANTHROPIC:
        print("  ℹ️  anthropic package not installed — using template fallback")
        return _generate_substack_post_template(email_data, trading_data), False

    # Load style rubric
    style_rubric = _load_style_rubric()
    if not style_rubric:
        print("  ⚠️  No style rubric found — using template fallback")
        return _generate_substack_post_template(email_data, trading_data), False

    # Build the user prompt with all source material
    date_str = datetime.now().strftime("%m/%d/%y")
    trading_data_str = json.dumps(trading_data, indent=2, default=str)

    user_prompt = f"""Generate a complete Substack post for today ({date_str}) using the source material below.
This post is for the "Savage Flow Methodology" newsletter by The Market Savage.

## Source Analysis (combined from multiple analysts)
{email_data['body']}

## Merged Trading Data
```json
{trading_data_str}
```

## Instructions
- Follow the style rubric exactly for structure, voice, and formatting.
- Use ALL the data provided — levels, scenarios, bias, observations.
- This is a Savage Flow Methodology post — write as The Market Savage voice.
- Do NOT reference or attribute any specific source analysts or newsletters.
- The post should be ready to copy-paste into Substack's editor.
- End with a brief one-line risk disclaimer.
- Output ONLY the final markdown post, no preamble or commentary."""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            system=f"You are The Market Savage, author of the Savage Flow Methodology newsletter. You are a professional futures trader who synthesizes analysis from multiple sources into one authoritative, branded voice. Never reference or attribute source analysts. Follow this style rubric:\n\n{style_rubric}",
            messages=[
                {"role": "user", "content": user_prompt}
            ],
        )
        post = message.content[0].text
        return post, True

    except Exception as e:
        print(f"  ⚠️  Claude API error: {e}")
        print("  ℹ️  Falling back to template generation")
        return _generate_substack_post_template(email_data, trading_data), False


def main():
    """Main automation workflow"""

    print("=" * 60)
    print("SAVAGE FLOW METHODOLOGY")
    print("=" * 60)
    print()

    # Step 1: Fetch latest emails from all sources
    print("Step 1: Fetching latest emails...")
    email_results = []
    for sender in GMAIL_SENDER_FILTERS:
        result = fetch_latest_email(sender=sender)
        if result:
            result["body"] = clean_email_body(result["body"])
            email_results.append(result)

    if not email_results:
        print("No new emails from any source. Exiting.")
        return None, None

    print(f"  Received {len(email_results)} source(s)")
    print()

    # Step 2: Extract trading data from each source, then merge
    print("Step 2: Extracting and merging trading data...")
    trading_data_list = []
    for edata in email_results:
        td = extract_trading_data(edata["body"])
        trading_data_list.append(td)

    trading_data = merge_trading_data(trading_data_list)
    print(f"  Key Zone: {trading_data['key_zone']}")
    print(f"  {len(trading_data['scenarios'])} scenarios")
    print(f"  Market Bias: {trading_data['market_bias']}")
    print()

    # Build combined email_data for downstream consumers
    combined_body = "\n\n---\n\n".join(e["body"] for e in email_results)
    email_data = {
        "subject": "Savage Flow Methodology",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "body": combined_body,
    }

    # Step 3: Create Notion payload
    print("Step 3: Creating Notion database entry...")
    notion_payload = create_notion_payload(email_data, trading_data)
    print(f"  Notion page: {notion_payload['Name']}")
    print()

    # Step 4: Push to Notion
    print("Step 4: Pushing to Notion...")
    notion_result = push_to_notion(trading_data, email_data)
    if notion_result:
        page_url = notion_result.get("url", "")
        print(f"  Created Notion page: {page_url}")
    else:
        print("  Notion push skipped or failed")
    print()

    # Step 5: Generate Substack post (AI-powered)
    print("Step 5: Generating Substack post...")
    substack_post, used_ai = generate_substack_post(email_data, trading_data)
    method = "AI (Claude)" if used_ai else "template fallback"
    print(f"  Generated {len(substack_post)} character post via {method}")
    print()

    # Step 6: Save outputs
    print("Step 6: Saving outputs...")

    date_suffix = datetime.now().strftime("%m-%d-%y")

    with open(f'{OUTPUT_DIR}/notion_payload.json', 'w') as f:
        json.dump(notion_payload, f, indent=2)
    print("  Saved: notion_payload.json")

    with open(f'{OUTPUT_DIR}/substack_post.md', 'w') as f:
        f.write(substack_post)
    print("  Saved: substack_post.md")

    with open(f'{OUTPUT_DIR}/substack_post_{date_suffix}.md', 'w') as f:
        f.write(substack_post)
    print(f"  Saved: substack_post_{date_suffix}.md")
    print()

    # Step 7: Send Slack notification
    print("Step 7: Sending Slack notification...")
    notion_url = notion_result.get("url") if notion_result else None
    substack_file = f'substack_post_{date_suffix}.md'
    send_slack_notification(
        email_data=email_data,
        trading_data=trading_data,
        notion_url=notion_url,
        substack_preview=substack_post[:200],
        substack_file=substack_file
    )

    # Upload Substack draft to Slack
    upload_file_to_slack(
        file_path=f'{OUTPUT_DIR}/substack_post.md',
        title=f"Savage Flow Methodology - {date_suffix}"
    )
    print()

    print("=" * 60)
    print("COMPLETE - Savage Flow Methodology")
    print("=" * 60)
    print()
    print("Next Steps:")
    print("1. Review substack_post.md")
    print("2. Copy to Substack editor and publish")
    print()

    return notion_payload, substack_post


if __name__ == "__main__":
    notion_data, substack_content = main()
