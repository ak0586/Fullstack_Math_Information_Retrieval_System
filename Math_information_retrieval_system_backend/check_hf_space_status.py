import requests
import json

url = "https://huggingface.co/api/spaces/ankit3105/math-retrieval-backend"
print(f"Fetching space status from {url}...")
try:
    response = requests.get(url, timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        safe_data = {
            "sha": data.get("sha"),
            "runtime_stage": data.get("runtime", {}).get("stage"),
            "siblings": [s.get("rpath") for s in data.get("siblings", [])]
        }
        print(json.dumps(safe_data, indent=2).encode("ascii", errors="backslashreplace").decode("ascii"))
    else:
        print(response.text)
except Exception as e:
    print(f"Failed to fetch status: {e}")
