import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
from app.core.rag_engine import get_rag_engine

print("Initializing engine...")
engine = get_rag_engine()
query_text = "Draw a flowchart explaining mathematical induction."
print(f"\n--- Querying: {query_text} ---")
res = engine.query(query_text)

print("\n--- FINAL PARSED RESULT ---")
print("Response Expl: ", res["response"][:100], "...")
print("Flow Data Keys:", list(res.get("flow_data", {}).keys()) if res.get("flow_data") else None)

if res.get("flow_data"):
    print("SUCCESS: JSON extracted successfully!")
else:
    print("FAILED: flow_data is null")
