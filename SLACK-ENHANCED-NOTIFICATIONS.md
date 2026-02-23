# Enhanced Slack Notifications - Setup Guide

## 🎯 What You Get

**Rich, Interactive Notifications:**
```
🚀 Savage Flow Complete - 02/10/26

Subject: ES Daily Plan - Key Zone 6050
Market Bias: 📈 Bullish
Key Zone: 6050-6075
ES Level: 6050

Upside Target: 6100
Downside Target: 6000

━━━━━━━━━━━━━━━━━━━━━

📊 Notion Page: [Open Database Entry] (clickable link)

📝 Files Generated:
• Substack: substack_post.md
• Notion: notion_payload.json

[📊 Open Notion] (button - opens in browser)

✅ Automation complete | Ready for review
```

**Plus: Substack Draft File Upload** (optional)
- Full markdown draft uploaded to Slack
- View/copy/edit directly from your phone
- No need to SSH or access files manually

---

## 📦 Current Setup (Already Working!)

You already have:
✅ Slack webhook notifications
✅ Clickable Notion links
✅ Emoji indicators for market bias (📈📉↔️)
✅ Trading data summary
✅ Action buttons

---

## 🚀 Optional: File Upload Setup

Want the Substack draft uploaded directly to Slack? Follow these steps:

### Step 1: Create Slack Bot

1. **Go to:** https://api.slack.com/apps
2. **Select** your "Savage Flow Bot" app
3. **Click:** "OAuth & Permissions"
4. **Add Bot Token Scopes:**
   - `files:write` - Upload files
   - `chat:write` - Post messages
5. **Click:** "Install to Workspace"
6. **Copy the Bot User OAuth Token** (starts with `xoxb-`)

### Step 2: Get Channel ID

1. **Open Slack**
2. **Right-click** the channel you want files posted to
3. **Click:** "Copy link"
4. **Extract the ID:** From URL like `slack.com/archives/C01234567890`
   - The ID is: `C01234567890`

### Step 3: Add to .env

```bash
# Edit .env file
nano ~/Scripts/savage_flow/.env

# Add these lines:
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_CHANNEL_ID=C01234567890
```

### Step 4: Test It!

```bash
cd ~/Scripts/savage_flow
python3 run_savage_flow.py
```

You should now see the Substack draft uploaded as a file in Slack! 📝

---

## 📱 Mobile Workflow

### When You Get a Notification:

**From Slack Mobile App:**

1. **Tap notification** → Opens Slack
2. **See trading data** at a glance
3. **Tap "Open Notion"** button → View full analysis
4. **Tap uploaded file** → Read full Substack draft
5. **Long-press file** → Share, copy, or download

**From Notion:**
- Tap the Notion link → Opens in Notion mobile app
- Edit database entry directly from phone

**Copy Substack Draft:**
- Tap the uploaded `.md` file in Slack
- Copy text directly
- Paste into Substack mobile editor

---

## 🎨 Notification Features

### Bias Indicators
- 📈 Bullish / Neutral-Bullish
- 📉 Bearish / Neutral-Bearish
- ↔️ Neutral / Range-bound

### Color Coding (Future Enhancement)
- Green for bullish setups
- Red for bearish setups
- Purple for neutral/waiting

### Action Buttons
- **Open Notion** - Direct link to database page
- Future: Add more quick actions

---

## 🔧 For Scaling

When you're ready to scale this as a service:

### Multi-User Support
```python
# Add user-specific channels
USER_CHANNELS = {
    "user1": "C01234567890",
    "user2": "C09876543210"
}

# Send to specific user channel
upload_file_to_slack(
    file_path="draft.md",
    channel_id=USER_CHANNELS[user_id]
)
```

### API Endpoints
- Add REST API for subscribing users
- Webhook system for multiple data sources
- User dashboard for managing preferences

### Advanced Notifications
- Custom notification templates per user
- Timezone-aware scheduling
- Multi-channel posting (Slack, Discord, Telegram)

---

## 💡 Pro Tips

**1. Create Dedicated Channel**
```
#savage-flow-alerts
```
All notifications + files in one place.

**2. Enable Mobile Notifications**
Slack app settings → Notifications → Enable for your channel

**3. Pin Important Drafts**
Long-press message → Pin to channel

**4. Use Slack Search**
Search for: `in:#savage-flow-alerts ES Level`

**5. Set Up Shortcuts**
Slack → Workflows → Create automation from notifications

---

## 📊 Example Notification Flow

```
8:00 AM - Tic Toc Trading email arrives
8:01 AM - Automation runs automatically
8:02 AM - Slack notification appears 📱
         ↓
Tap "Open Notion" → Review analysis
         ↓
Tap uploaded draft → Copy content
         ↓
Open Substack app → Paste & publish
```

**Total time: ~2 minutes from phone!** ⚡

---

## 🐛 Troubleshooting

**File upload not working?**
- Check `SLACK_BOT_TOKEN` starts with `xoxb-`
- Verify bot has `files:write` scope
- Ensure `SLACK_CHANNEL_ID` is correct
- Bot must be invited to the channel

**Notifications not appearing?**
- Check SLACK_WEBHOOK_URL is set
- Verify webhook is for correct workspace
- Look at Flask server logs

**Links not clickable?**
- Make sure Notion URL is valid
- Check Slack app on phone (not just notifications)

---

## 🚀 What's Next?

**Potential Enhancements:**
- [ ] Interactive buttons to approve/edit before posting
- [ ] Thread replies with detailed analysis
- [ ] Chart generation and upload
- [ ] Multi-newsletter aggregation
- [ ] Custom notification templates
- [ ] @mention specific team members
- [ ] Integration with trading platforms

**Ready to scale?** Let me know and we can build out the full platform! 📈

---

**Your automation is now mobile-first!** 🎉
