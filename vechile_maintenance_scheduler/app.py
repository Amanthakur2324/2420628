import os
import sys
import time
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging.logger import log

app = Flask(__name__)
CORS(app)

ACCESS_TOKEN = os.getenv("AFFORDMED_ACCESS_TOKEN")
if not ACCESS_TOKEN:
    log("backend", "fatal", "config", "Missing AFFORDMED_ACCESS_TOKEN")
    sys.exit(1)

DEPOT_API = "http://4.224.186.213/evaluation-service/depots"
VEHICLE_API = "http://4.224.186.213/evaluation-service/vehicles"

def api_get(url):
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        log("backend", "error", "service", f"API call failed: {url} - {str(e)}")
        raise

def knapsack(tasks, budget):
    durations = [t["Duration"] for t in tasks]
    impacts = [t["Impact"] for t in tasks]
    n = len(tasks)
    dp = [[0]*(budget+1) for _ in range(n+1)]
    for i in range(1, n+1):
        for cap in range(budget+1):
            if durations[i-1] <= cap:
                dp[i][cap] = max(dp[i-1][cap], dp[i-1][cap - durations[i-1]] + impacts[i-1])
            else:
                dp[i][cap] = dp[i-1][cap]
    cap = budget
    selected = []
    for i in range(n, 0, -1):
        if dp[i][cap] != dp[i-1][cap]:
            selected.append(tasks[i-1])
            cap -= durations[i-1]
    return dp[n][budget], selected

def fetch_tasks():
    log("backend", "info", "service", "Fetching tasks")
    data = api_get(VEHICLE_API)
    if isinstance(data, dict) and "vehicles" in data:
        tasks = data["vehicles"]
    else:
        tasks = data if isinstance(data, list) else []
    if not tasks:
        log("backend", "warn", "service", "No tasks from API, using sample data")
        tasks = [
            {"Duration":6,"Impact":6},{"Duration":6,"Impact":1},{"Duration":1,"Impact":5},
            {"Duration":6,"Impact":9},{"Duration":2,"Impact":5},{"Duration":5,"Impact":7},
            {"Duration":1,"Impact":1},{"Duration":8,"Impact":7},{"Duration":6,"Impact":2},
            {"Duration":1,"Impact":3},{"Duration":5,"Impact":5},{"Duration":7,"Impact":3},
            {"Duration":6,"Impact":3},{"Duration":5,"Impact":1},{"Duration":5,"Impact":9},
            {"Duration":6,"Impact":10},{"Duration":2,"Impact":9},{"Duration":2,"Impact":3},
            {"Duration":2,"Impact":5},{"Duration":3,"Impact":10},{"Duration":8,"Impact":8},
            {"Duration":8,"Impact":5},{"Duration":7,"Impact":10},{"Duration":7,"Impact":1},
            {"Duration":1,"Impact":8},{"Duration":5,"Impact":8},{"Duration":8,"Impact":8},
            {"Duration":7,"Impact":8}
        ]
    return tasks

def fetch_depots():
    log("backend", "info", "service", "Fetching depots")
    data = api_get(DEPOT_API)
    return data.get("depots", [])

@app.route('/solve', methods=['POST'])
def solve():
    data = request.json
    if not data:
        return jsonify({"error": "missing body"}), 400
    if "budget" in data:
        budget = data["budget"]
    elif "depotId" in data:
        depots = fetch_depots()
        depot = next((d for d in depots if d.get("ID") == data["depotId"]), None)
        if not depot:
            return jsonify({"error": "depot not found"}), 404
        budget = depot.get("MechanicHours")
    else:
        return jsonify({"error": "provide 'budget' or 'depotId'"}), 400
    
    tasks = fetch_tasks()
    if not tasks:
        return jsonify({"error": "no tasks"}), 500
    
    start = time.time()
    max_impact, selected = knapsack(tasks, budget)
    elapsed_ms = (time.time() - start) * 1000
    total_duration = sum(t["Duration"] for t in selected)
    
    log("backend", "info", "controller", f"Budget={budget}, impact={max_impact}, duration={total_duration}, time={elapsed_ms:.2f}ms")
    return jsonify({
        "budget": budget,
        "max_impact": max_impact,
        "total_duration": total_duration,
        "selected_count": len(selected),
        "execution_time_ms": round(elapsed_ms, 2)
    })

@app.route('/depots', methods=['GET'])
def list_depots():
    return jsonify({"depots": fetch_depots()})

if __name__ == "__main__":
    log("backend", "info", "config", "Starting Vehicle Scheduler API on port 5000")
    app.run(host="0.0.0.0", port=5000)