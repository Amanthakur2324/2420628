import os
import sys
import requests
import math
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging.logger import log

ACCESS_TOKEN = os.getenv("AFFORDMED_ACCESS_TOKEN")
if not ACCESS_TOKEN:
    log("backend", "fatal", "config", "Missing access token")
    sys.exit(1)

NOTIF_API = "http://4.224.186.213/evaluation-service/notifications"
WEIGHTS = {"Placement": 3, "Result": 2, "Event": 1}

def fetch_notifications():
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    try:
        resp = requests.get(NOTIF_API, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json().get("notifications", [])
    except Exception as e:
        log("backend", "error", "service", f"Fetch failed: {e}")
        return []

def score(notif):
    w = WEIGHTS.get(notif.get("Type"), 1)
    ts_str = notif.get("Timestamp")
    if not ts_str:
        return w * 0.5
    try:
        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        days = (datetime.now(timezone.utc) - ts).total_seconds() / 86400.0
        recency = math.exp(-days / 7.0)
        return w * recency
    except:
        return w * 0.5

def top_n(n=10):
    notifs = fetch_notifications()
    if not notifs:
        log("backend", "warn", "service", "No notifications")
        return []
    scored = [(score(n), n) for n in notifs]
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [n for _, n in scored[:n]]
    log("backend", "info", "service", f"Returning top {len(top)} priority notifications")
    return top

if __name__ == "__main__":
    log("backend", "info", "controller", "Calculating priority inbox")
    top10 = top_n(10)
    print("\n===== TOP 10 PRIORITY NOTIFICATIONS =====")
    for i, n in enumerate(top10, 1):
        print(f"{i}. [{n['Type']:8}] {n['Message']:30} @ {n['Timestamp']}")