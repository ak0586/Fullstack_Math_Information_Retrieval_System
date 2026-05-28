import requests
import json

base_url = "https://ankit3105-math-retrieval-backend.hf.space"
headers = {"Content-Type": "application/json"}

# Step 1: Perform search
search_payload = {"query": "x^2"}
print(f"1. Performing search on {base_url}/search...")
try:
    search_res = requests.post(f"{base_url}/search", headers=headers, json=search_payload, timeout=15)
    print(f"Search Status: {search_res.status_code}")
    if search_res.status_code != 200:
        print("Search failed:", search_res.text)
        exit(1)
        
    search_data = search_res.json()
    session_id = search_data["session_id"]
    results = search_data["results"]
    print(f"Session ID: {session_id}")
    print(f"Total results: {len(results)}")
    
    if not results:
        print("No results returned!")
        exit(1)
        
    # Get first result
    first_res = results[0]
    file_id = first_res["id"]
    filename = first_res["filename"]
    print(f"First result: ID={file_id}, Filename={filename}")
    
    # Step 2: Query /view endpoint
    view_url = f"{base_url}/fetch_file_content/{session_id}/{file_id}"
    print(f"\n2. Fetching file view from {view_url}...")
    view_res = requests.get(view_url, timeout=15)
    print(f"View Status: {view_res.status_code}")
    print("View Headers:", dict(view_res.headers))
    if view_res.status_code == 200:
        print("File loaded successfully!")
        print(f"HTML Content preview (first 500 chars):\n{view_res.text[:500]}")
    else:
        print("Error response text:")
        print(view_res.text)
        
except Exception as e:
    print(f"Test failed with error: {e}")
