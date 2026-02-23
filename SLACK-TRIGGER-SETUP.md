# Slack Slash Command Setup for Savage Flow

Trigger your automation from Slack with `/savage-flow run` 🚀

## 🎯 What You'll Get

Type in any Slack channel:
- `/savage-flow` or `/savage-flow run` → Triggers automation immediately
- `/savage-flow status` → Shows automation status
- `/savage-flow help` → Lists available commands

---

## 📋 Setup Steps

### Step 1: Install Flask
```bash
cd ~/Scripts/savage_flow
pip install flask
```

### Step 2: Create Slack App & Slash Command

1. **Go to:** https://api.slack.com/apps
2. **Click:** "Create New App" → "From scratch"
3. **Name:** "Savage Flow Bot"
4. **Workspace:** Select your workspace
5. **Click:** "Slash Commands" in sidebar
6. **Create New Command:**
   - **Command:** `/savage-flow`
   - **Request URL:** `https://YOUR-NGROK-URL/slack/savage-flow` (we'll get this in Step 3)
   - **Short Description:** "Trigger Market Savage trading automation"
   - **Usage Hint:** `[run|status|help]`
   - **Save**

### Step 3: Expose Local Server to Internet (Using ngrok)

**Option A: Using ngrok (Recommended)**

1. **Install ngrok:**
   ```bash
   brew install ngrok
   ```

2. **Sign up:** https://dashboard.ngrok.com/signup (free)

3. **Get your auth token:** https://dashboard.ngrok.com/get-started/your-authtoken

4. **Configure ngrok:**
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

5. **Start ngrok tunnel:**
   ```bash
   ngrok http 5555
   ```

6. **Copy the HTTPS URL** (looks like `https://abc123.ngrok-free.app`)

7. **Update Slack slash command** with this URL + `/slack/savage-flow`:
   ```
   https://abc123.ngrok-free.app/slack/savage-flow
   ```

**Option B: Using Cloudflare Tunnel (Alternative)**
```bash
# Install cloudflared
brew install cloudflare/cloudflare/cloudflared

# Run tunnel
cloudflared tunnel --url http://localhost:5555
```

### Step 4: Install Slack App to Workspace

1. Go back to your Slack app settings
2. Click **"Install to Workspace"**
3. **Authorize** the app

### Step 5: Start the Trigger Server

**Terminal 1 (ngrok):**
```bash
ngrok http 5555
```

**Terminal 2 (Flask server):**
```bash
cd ~/Scripts/savage_flow
python3 slack_trigger.py
```

You should see:
```
🚀 Starting Savage Flow Slack Trigger Server...
📡 Listening for /savage-flow commands...
```

### Step 6: Test It!

Go to any Slack channel and type:
```
/savage-flow run
```

You should see:
```
🚀 Savage Flow automation triggered by @yourname
Checking for new emails and generating content...
You'll get a notification when complete!
```

---

## 🤖 Auto-Start on Mac Boot (Optional)

### Make it run automatically using launchd:

1. **Create plist file:**
   ```bash
   nano ~/Library/LaunchAgents/com.savageflow.slacktrigger.plist
   ```

2. **Paste this:**
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.savageflow.slacktrigger</string>

       <key>ProgramArguments</key>
       <array>
           <string>/usr/bin/python3</string>
           <string>/Users/brandondavis/Scripts/savage_flow/slack_trigger.py</string>
       </array>

       <key>WorkingDirectory</key>
       <string>/Users/brandondavis/Scripts/savage_flow</string>

       <key>RunAtLoad</key>
       <true/>

       <key>KeepAlive</key>
       <true/>

       <key>StandardOutPath</key>
       <string>/Users/brandondavis/Scripts/savage_flow/slack_trigger.log</string>

       <key>StandardErrorPath</key>
       <string>/Users/brandondavis/Scripts/savage_flow/slack_trigger_error.log</string>
   </dict>
   </plist>
   ```

3. **Load the service:**
   ```bash
   launchctl load ~/Library/LaunchAgents/com.savageflow.slacktrigger.plist
   ```

4. **Start ngrok on boot too** (create another plist for ngrok if needed)

---

## 🔒 Security Notes

- The Flask server runs on `localhost:5555` (not publicly accessible)
- ngrok creates a secure HTTPS tunnel
- Only your Slack workspace can trigger commands
- Add `SLACK_SIGNING_SECRET` to `.env` for verification (optional but recommended)

---

## 🐛 Troubleshooting

**"Command not recognized" in Slack**
- Make sure you installed the app to workspace
- Check the slash command URL is correct (includes /slack/savage-flow)

**"Connection refused"**
- Make sure Flask server is running: `python3 slack_trigger.py`
- Make sure ngrok is running: `ngrok http 5555`

**"Automation doesn't run"**
- Check server logs: `tail -f ~/Scripts/savage_flow/slack_trigger.log`
- Make sure main automation works: `python3 run_savage_flow.py`

---

## 📱 Mobile Usage

Once set up, you can trigger from:
- ✅ Slack mobile app
- ✅ Slack desktop app
- ✅ Slack web browser

Just type `/savage-flow` in any channel! 🎉

---

## 💡 Pro Tips

1. **Keep ngrok running:** Use tmux or screen to keep the tunnel alive
   ```bash
   tmux new -s ngrok
   ngrok http 5555
   # Press Ctrl+B then D to detach
   ```

2. **Monitor logs:**
   ```bash
   tail -f ~/Scripts/savage_flow/slack_trigger.log
   ```

3. **Create a dedicated #savage-flow channel** for notifications

---

Need help? The server is simple Flask + threading. Easy to customize! 🚀
