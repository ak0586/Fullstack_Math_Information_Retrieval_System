import requests
import json

url = "https://ankit3105-math-retrieval-backend.hf.space/search"
payload = {"query": "__VIEW__:test-session:1"}
headers = {"Content-Type": "application/json"}

print(f"Sending direct view request to {url}...")
try:
    r = requests.post(url, headers=headers, json=payload, timeout=15)
    print(f"Status: {r.status_code}")
    print("Headers:", dict(r.headers))
    print("Response:", r.text)
except Exception as e:
    print("Error:", e)
