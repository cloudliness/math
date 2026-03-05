import requests
import json
import time
import sys

def test_chat_api():
    url = "http://127.0.0.0:8000/api/v1/chat"
    # Actually uvicorn defaults to 127.0.0.1 or 0.0.0.0
    url = "http://127.0.0.1:8000/api/v1/chat"
    
    payload = {
        "message": "What is a proposition?"
    }
    headers = {
        "Content-Type": "application/json"
    }

    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        
        if response.status_code == 200:
            print("\n✅ API Request Successful!")
            data = response.json()
            print("-" * 40)
            print("RESPONSE TEXT:")
            print(data.get("response"))
            print("-" * 40)
            print(f"SOURCES ({len(data.get('sources', []))}):")
            for idx, source in enumerate(data.get("sources", [])):
                print(f"[{idx+1}] Score: {source.get('score'):.4f}")
                print(f"Preview: {source.get('text')[:100]}...\n")
        else:
            print(f"\n❌ API Request Failed with status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"\n❌ Connection or request error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Wait a few seconds to let the server start if run consecutively
    time.sleep(3)
    test_chat_api()
