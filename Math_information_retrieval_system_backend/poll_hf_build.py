import time
import requests

url = "https://ankit3105-math-retrieval-backend.hf.space/search"
print("Polling Hugging Face build status...")
for i in range(18):  # Poll for up to 3 minutes
    try:
        docs = requests.get("https://ankit3105-math-retrieval-backend.hf.space/docs", timeout=5)
        if docs.status_code == 200:
            if "fetch_file_content" in docs.text:
                print("SUCCESS: The new endpoint /fetch_file_content is now live!")
                break
            else:
                print(f"Attempt {i+1}: Old version is still running...")
        else:
            print(f"Attempt {i+1}: Space is rebuilding/restarting (Status: {docs.status_code})...")
    except Exception as e:
        print(f"Attempt {i+1}: Server is down or rebuilding... ({e})")
    time.sleep(10)
