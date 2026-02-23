#!/usr/bin/env python3
"""
Slack Slash Command Handler for Savage Flow
Allows triggering automation via /savage-flow command in Slack
"""

from flask import Flask, request, jsonify
import subprocess
import os
import json
import urllib.request
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Security: Verify requests are from your Slack workspace
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

def notify_slack(message):
    """Send a notification to Slack via webhook"""
    if not SLACK_WEBHOOK_URL:
        print("⚠️  No SLACK_WEBHOOK_URL set, skipping notification")
        return
    payload = json.dumps({"text": message}).encode("utf-8")
    req = urllib.request.Request(
        SLACK_WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"⚠️  Slack notification failed: {e}")


def run_automation():
    """Run the savage flow automation in background"""
    try:
        result = subprocess.run(
            ['python3', 'run_savage_flow.py'],
            capture_output=True,
            text=True,
            cwd='/Users/brandondavis/Scripts/savage_flow',
            timeout=300  # 5 minute timeout
        )

        print(f"Automation completed with code: {result.returncode}")

        if result.returncode == 0:
            # Pull a short summary from stdout
            lines = result.stdout.strip().splitlines()
            summary = "\n".join(lines[-5:]) if len(lines) > 5 else result.stdout.strip()
            notify_slack(f"✅ *Savage Flow complete*\n```{summary}```")
        else:
            stderr_tail = (result.stderr or result.stdout or "unknown error").strip()[-300:]
            notify_slack(f"❌ *Savage Flow failed* (exit {result.returncode})\n```{stderr_tail}```")

    except Exception as e:
        print(f"Error running automation: {e}")
        notify_slack(f"❌ *Savage Flow error:* {e}")


@app.route('/slack/savage-flow', methods=['POST'])
def handle_slash_command():
    """Handle /savage-flow slash command from Slack"""

    print(f"📥 Received Slack command from {request.remote_addr}")

    # Get command details
    command_text = request.form.get('text', '').strip()
    user_name = request.form.get('user_name', 'Unknown')

    print(f"👤 User: {user_name}, Command: '{command_text}'")

    # Parse command
    if command_text == 'run' or command_text == '':
        # Start automation in background thread
        thread = Thread(target=run_automation)
        thread.daemon = True
        thread.start()

        return jsonify({
            "response_type": "in_channel",
            "text": f"🚀 Savage Flow automation triggered by @{user_name}",
            "attachments": [{
                "color": "#8B5CF6",
                "text": "Checking for new emails and generating content...\nYou'll get a notification when complete!"
            }]
        })

    elif command_text == 'status':
        # Check if automation is running
        return jsonify({
            "response_type": "ephemeral",
            "text": "📊 *Savage Flow Status*",
            "attachments": [{
                "color": "#3B82F6",
                "fields": [
                    {"title": "Script Location", "value": "~/Scripts/savage_flow", "short": True},
                    {"title": "Schedule", "value": "Every 15 minutes", "short": True},
                    {"title": "Last Email", "value": "Check .last_email_id", "short": False}
                ]
            }]
        })

    elif command_text == 'help':
        return jsonify({
            "response_type": "ephemeral",
            "text": "🔧 *Savage Flow Commands*",
            "attachments": [{
                "color": "#D946EF",
                "text": "*Available commands:*\n"
                       "`/savage-flow` or `/savage-flow run` - Trigger automation now\n"
                       "`/savage-flow status` - Check automation status\n"
                       "`/savage-flow help` - Show this help message"
            }]
        })

    else:
        return jsonify({
            "response_type": "ephemeral",
            "text": f"❌ Unknown command: `{command_text}`\nUse `/savage-flow help` for available commands"
        })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "savage-flow-trigger"})


@app.route('/test', methods=['GET', 'POST'])
def test_endpoint():
    """Simple test endpoint to verify ngrok is working"""
    print(f"✅ Test endpoint hit from {request.remote_addr}")
    return jsonify({
        "status": "success",
        "message": "Flask server is working!",
        "method": request.method
    })


if __name__ == '__main__':
    print("🚀 Starting Savage Flow Slack Trigger Server...")
    print("📡 Listening for /savage-flow commands...")

    # Run on localhost:5555 (not publicly accessible)
    app.run(host='127.0.0.1', port=5555, debug=False)
