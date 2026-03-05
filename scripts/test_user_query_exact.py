import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

# Load env vars from backend
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

from app.core.rag_engine import get_rag_engine

engine = get_rag_engine()
query = "tell me about the growth of functions"
print("Querying:", query)
res = engine.query(query)

print("\n--- RESPONSE ---")
print(res["response"])
print("\n--- SOURCES ---")
for s in res["sources"]:
    print(f"Score: {s.get('score', 0):.4f}")
    print(s["text"])
