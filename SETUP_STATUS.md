# Savage Flow Automation - Setup Status

**Last Updated:** 2026-02-10

## ✅ COMPLETED

### Server Deployment (192.168.0.10)
- [x] All automation running on Ubuntu server (`marketsavage@192.168.0.10`)
- [x] Python venv at `/home/marketsavage/savage_flow/venv/`
- [x] Credentials in `/home/marketsavage/savage_flow/.env` (python-dotenv)
- [x] systemd user services with auto-restart and linger enabled
- [x] ngrok tunnel for Slack slash command integration
- [x] Slack `/savage-flow` command in `#savage-flow` channel

### Systemd Services
- [x] `savage-flow.timer` — runs automation every 15 minutes
- [x] `savage-flow-trigger.service` — Flask server (port 5555) for Slack slash commands
- [x] `savage-flow-ngrok.service` — ngrok tunnel to expose trigger server

### Integrations
- [x] Gmail IMAP — pulls emails from `tictoctrading@substack.com`
- [x] Notion — pushes content to database
- [x] Anthropic Claude — generates Substack posts
- [x] Slack — `/savage-flow run`, `/savage-flow status`, `/savage-flow help`

### Credential Migration
- [x] All credentials in `.env` — no hardcoded secrets in scripts
- [x] `.env` contains: Gmail, Notion, Anthropic, Slack webhook

---

## ❌ ABANDONED

### n8n / Docker Migration
- Attempted n8n in Docker on same server
- **Blocked:** HTTPS/localhost issue
- Replaced by direct Python + systemd setup

### Local Mac Setup
- Originally ran via launchd on Mac
- Migrated to server to reduce Mac resource usage
- All LaunchAgent plists removed

---

## 🔑 CREDENTIALS & CONFIG

All credentials live in `/home/marketsavage/savage_flow/.env` on the server.
Local copy at `~/Scripts/savage_flow/.env` on Mac (for reference/development).

### Gmail
- Address: `mr.brandon.davis@gmail.com`
- Sender Filter: `tictoctrading@substack.com`

### Notion
- Database ID: `5bf4c5b08cb848708ea74bf7aa528580`

### Slack
- Channel: `#savage-flow`
- ngrok URL: `https://unconsecutive-unstern-lane.ngrok-free.dev`

---

## 📁 KEY FILES

### Server (`marketsavage@192.168.0.10`)
| File | Purpose |
|------|---------|
| `~/savage_flow/run_savage_flow.py` | Main automation script |
| `~/savage_flow/slack_trigger.py` | Slack slash command handler |
| `~/savage_flow/.env` | All credentials |
| `~/savage_flow/venv/` | Python virtual environment |
| `~/savage_flow/savage_flow.log` | Automation log |
| `~/savage_flow/slack_trigger.log` | Trigger server log |
| `~/.config/systemd/user/savage-flow.*` | systemd service/timer files |

### Mac (reference only)
| File | Purpose |
|------|---------|
| `~/Scripts/savage_flow/run_savage_flow.py` | Local copy of script |
| `~/Scripts/savage_flow/.env` | Local copy of credentials |
| `~/Scripts/savage_flow/run_daily.sh` | Old cron entry point (unused) |

---

## 🔧 SERVER MANAGEMENT

```bash
# SSH to server
ssh marketsavage@192.168.0.10

# Check service status
systemctl --user status savage-flow.timer savage-flow-trigger savage-flow-ngrok

# View logs
tail -f ~/savage_flow/savage_flow.log
tail -f ~/savage_flow/slack_trigger.log

# Restart services
systemctl --user restart savage-flow-trigger
systemctl --user restart savage-flow-ngrok
```
