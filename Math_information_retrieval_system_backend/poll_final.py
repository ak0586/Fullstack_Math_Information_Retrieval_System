import time
import requests

url = "https://ankit3105-math-retrieval-backend.hf.space/search"
print("Waiting for container startup...")
for i in range(24):  # Poll for up to 2 minutes
    try:
        r = requests.post(url, json={"query": "x^2"}, timeout=5)
        if r.status_code == 200:
            data = r.json()
            sess = data["session_id"]
            v = requests.post("https://ankit3105-math-retrieval-backend.hf.space/search/document", json={"session_id": sess, "file_id": "1"}, timeout=5)
            print(f"Attempt {i+1}: View Status = {v.status_code}")
            if v.status_code == 200:
                print("\nSUCCESS! The /search/document endpoint is fully operational!")
                print(f"HTML Content preview:\n{v.text[:400]}")
                break
        else:
            print(f"Attempt {i+1}: Search Status = {r.status_code}")
    except Exception as e:
        print(f"Attempt {i+1}: Connection issue ({e})")
    time.sleep(5)
