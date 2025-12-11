"""
Simple script to test the backend /chat endpoint locally.

Usage:
  # activate your venv, then run:
  python scripts/test_chat_api.py

Override API base with API_BASE env var if needed.
"""
import os
import json
import requests

API_BASE = os.getenv("API_BASE", "http://localhost:8000")


def test_chat(question: str = "What were the key decisions?", top_k: int = 3):
    url = API_BASE.rstrip("/") + "/chat"
    payload = {
        "messages": [
            {"role": "user", "content": question}
        ],
        "top_k": top_k
    }
    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        print(f"Status: {resp.status_code}")
        try:
            print(json.dumps(resp.json(), indent=2))
        except Exception:
            print(resp.text)
    except Exception as e:
        print("Error connecting to API:", str(e))


if __name__ == "__main__":
    print("Testing chat API at", API_BASE)
    test_chat()
