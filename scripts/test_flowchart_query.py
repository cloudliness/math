import sys
import os
import requests
import json

SESSION_URL = "http://localhost:8000/api/v1/chat/session"
CHAT_URL = "http://localhost:8000/api/v1/chat"

# 1. Create a session
res = requests.post(SESSION_URL)
session_id = res.json()["id"]

# 2. Ask for a flowchart
payload = {
    "session_id": session_id,
    "message": "Draw a flowchart explaining the mathematical induction process."
}
print(f"Sending prompt: {payload['message']}")
res = requests.post(CHAT_URL, json=payload)
data = res.json()

print(json.dumps(data, indent=2))
