import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "pipeline_history.json"

def load_incidents():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_incident(deployment_id):
    for incident in load_incidents():
        if str(incident["deployment_id"]) == str(deployment_id):
            return incident
    return None

