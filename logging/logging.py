import os
import requests

LOG_API_URL = "http://4.224.186.213/evaluation-service/logs"
ACCESS_TOKEN = os.getenv("AFFORDMED_ACCESS_TOKEN", "")

def log(stack: str, level: str, package: str, message: str):
    """
    stack: 'backend' or 'frontend'
    level: 'debug','info','warn','error','fatal'
    package: one of allowed values (see instructions)
    message: descriptive log message
    """
    if not ACCESS_TOKEN:
        print(f"[LOG FAILED] No token: {stack}/{level}/{package} - {message}")
        return

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "stack": stack,
        "level": level,
        "package": package,
        "message": message
    }
    try:
        requests.post(LOG_API_URL, json=payload, headers=headers, timeout=5)
    except Exception as e:
        print(f"Logging error: {e}")