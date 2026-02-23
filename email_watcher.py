#!/usr/bin/env python3
"""
Savage Flow — IMAP IDLE Email Watcher

Connects to Gmail and listens in real-time using IMAP IDLE.
Fires run_savage_flow.py the moment a new email arrives from
a configured sender. Reconnects automatically on any failure.
"""

import imaplib
import os
import subprocess
import time
import logging
import socket
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Config
GMAIL_ADDRESS     = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
GMAIL_SENDER_FILTERS = [
    os.environ.get("GMAIL_SENDER_FILTER_1", "tictoctrading@substack.com"),
    os.environ.get("GMAIL_SENDER_FILTER_2", "adamset@substack.com"),
]
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT  = os.path.join(SCRIPT_DIR, "run_savage_flow.py")
LOG_FILE     = os.path.join(SCRIPT_DIR, "watcher.log")

# IDLE timeout — Gmail drops idle connections after ~29 min, renew at 25
IDLE_TIMEOUT_SEC = 25 * 60
RECONNECT_DELAY  = 30  # seconds between reconnect attempts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WATCHER] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


def sender_matches(from_header: str) -> bool:
    """Return True if the From header matches any configured sender."""
    from_lower = from_header.lower()
    return any(f.lower() in from_lower for f in GMAIL_SENDER_FILTERS)


def trigger_automation():
    """Run the main savage flow script as a subprocess."""
    log.info("Triggering run_savage_flow.py ...")
    try:
        result = subprocess.run(
            ["python3", MAIN_SCRIPT],
            cwd=SCRIPT_DIR,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            log.info("Automation completed successfully.")
        else:
            log.error(f"Automation failed (exit {result.returncode}):\n{result.stderr[-500:]}")
    except subprocess.TimeoutExpired:
        log.error("Automation timed out after 5 minutes.")
    except Exception as e:
        log.error(f"Error triggering automation: {e}")


def check_unseen_from_senders(imap) -> bool:
    """
    Search for UNSEEN emails from any configured sender.
    Returns True if at least one matching unseen email is found.
    """
    for sender in GMAIL_SENDER_FILTERS:
        typ, data = imap.search(None, f'(UNSEEN FROM "{sender}")')
        if typ == "OK" and data[0].strip():
            log.info(f"New email detected from {sender}")
            return True
    return False


def idle_loop():
    """Main IDLE loop — connect, wait, trigger, repeat."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        log.error("GMAIL_ADDRESS or GMAIL_APP_PASSWORD not set. Exiting.")
        return

    while True:
        try:
            log.info(f"Connecting to Gmail as {GMAIL_ADDRESS} ...")
            imap = imaplib.IMAP4_SSL("imap.gmail.com")
            imap.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            imap.select("INBOX")
            log.info("Connected. Entering IDLE watch loop.")

            while True:
                # Send IDLE command
                tag = imap._new_tag().decode()
                imap.send(f"{tag} IDLE\r\n".encode())

                # Wait for "+ idling" continuation
                response = imap.readline()
                if b"idling" not in response.lower() and b"+" not in response:
                    log.warning(f"Unexpected IDLE response: {response}")

                idle_start = time.time()
                triggered = False

                # Listen for server push — set socket timeout to check periodically
                imap.socket().settimeout(60)

                while True:
                    elapsed = time.time() - idle_start

                    # Renew IDLE before Gmail drops it
                    if elapsed >= IDLE_TIMEOUT_SEC:
                        log.info("Renewing IDLE connection...")
                        break

                    try:
                        line = imap.readline()
                    except socket.timeout:
                        continue
                    except Exception as e:
                        log.warning(f"Socket read error: {e}")
                        raise

                    if not line:
                        log.warning("Empty response — server may have dropped connection.")
                        raise imaplib.IMAP4.abort("Empty response")

                    log.debug(f"IDLE push: {line.strip()}")

                    # EXISTS means new mail landed
                    if b"EXISTS" in line:
                        log.info("EXISTS notification received — checking senders...")
                        triggered = True
                        break

                # Exit IDLE mode
                imap.send(b"DONE\r\n")
                # Drain the tagged OK response
                try:
                    imap.socket().settimeout(10)
                    imap.readline()
                except Exception:
                    pass

                if triggered:
                    if check_unseen_from_senders(imap):
                        trigger_automation()
                    else:
                        log.info("New mail not from a tracked sender — skipping.")

        except (imaplib.IMAP4.error, imaplib.IMAP4.abort, OSError, socket.error) as e:
            log.warning(f"Connection error: {e}. Reconnecting in {RECONNECT_DELAY}s...")
            time.sleep(RECONNECT_DELAY)
        except Exception as e:
            log.error(f"Unexpected error: {e}. Reconnecting in {RECONNECT_DELAY}s...")
            time.sleep(RECONNECT_DELAY)
        finally:
            try:
                imap.logout()
            except Exception:
                pass


if __name__ == "__main__":
    log.info("=== Savage Flow Email Watcher started ===")
    idle_loop()
