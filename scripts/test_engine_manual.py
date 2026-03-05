import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
from app.core.rag_engine import get_rag_engine

print("Initializing engine...")
engine = get_rag_engine()
query_text = "tell me about the growth of functions"
print("\n--- Querying ---")
res = engine.query(query_text)
print("\n--- Final Result ---")
print(res)
