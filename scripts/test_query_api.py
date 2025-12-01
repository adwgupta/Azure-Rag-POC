"""
Simple script to test the backend /query endpoint locally.

Usage:
  # activate your venv, then run:
  python scripts/test_query_api.py

This will POST a sample question to http://localhost:8000/query (or override with API_BASE env var)
and print the response JSON.
"""
import os
import json
import requests

API_BASE = os.getenv('API_BASE', 'http://localhost:8000')

def test_query(question='What were the key decisions?', top_k=3):
    url = API_BASE.rstrip('/') + '/query'
    payload = {"question": question, "top_k": top_k}
    headers = {'Content-Type': 'application/json'}
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        print(f'Status: {resp.status_code}')
        try:
            print(json.dumps(resp.json(), indent=2))
        except Exception:
            print(resp.text)
    except Exception as e:
        print('Error connecting to API:', str(e))

if __name__ == '__main__':
    print('Testing API at', API_BASE)
    test_query()
