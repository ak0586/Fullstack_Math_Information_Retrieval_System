# 📚 Math Information Retrieval System

[![Flutter](https://img.shields.io/badge/Flutter-02569B?logo=flutter&logoColor=white)](https://flutter.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/License-Proprietary-red)](#-license)

A **cross-platform Math Search Engine** with a **Flutter frontend** and **FastAPI backend**.  
It enables users to search mathematical expressions (LaTeX or MathML), retrieve relevant documents, and view them seamlessly on **Android APK** and **Web browsers**.

---

## ✨ Features

### Frontend (Flutter)
- 🔍 Search using LaTeX or plain math expressions  
- 📄 Render HTML with **MathML** correctly on both Android and Web  
- 💡 **WebView** for Android, **iframe + MathJax** for Web  
- ⏱ Display response time and result count  
- ✅ Clean UI with animations, loading indicators, and error handling  

### Backend (FastAPI)
- ⚡ Bit-vector encoding for math expressions  
- 📊 MiniBatchKMeans clustering with Hamming distance  
- 🚀 High-speed approximate nearest neighbor (ANN) search  
- 📦 Persistent index storage for instant startup  

---

## 🚀 How It Works

### 1️⃣ Clustering & Indexing (Backend)
1. Extract MathML/LaTeX from documents.  
2. Convert to **binary bit-vectors**.  
3. Apply **MiniBatchKMeans** (Hamming distance) to cluster expressions.  
4. Save cluster indices to disk (`math_index_storage`).

### 2️⃣ Searching
1. User submits query via `/search` API.  
2. Query is classified (LaTeX or plain math).  
3. Converted to bit-vector → matched to nearest cluster(s).  
4. Return top results from pre-built indices.  

---

## 📁 Project Structure

### Frontend
📦frontend
┣ 📜main.dart # Search UI & routing
┣ 📜mobile_html_viewer.dart # WebView for Android
┗ 📜web_html_viewer.dart # iframe renderer for Web

shell
Copy
Edit

### Backend
📦backend
┣ 📂MIR_model
┃ ┣ 📜cluster_index.py # Loads & searches cluster index
┃ ┣ 📜clustering_phase.py # Performs clustering
┃ ┣ 📜driver_clustering.py # Runs clustering & index creation
┃ ┣ 📜driver_preprocessing.py # Preprocess HTML → bitvectors + metadata
┃ ┣ 📜hamming_mini_batch_kmeans.py # MiniBatchKMeans for binary data
┃ ┣ 📜preprocessing.py # Extract MathML/LaTeX → bitvectors
┃ ┣ 📜query_processing.py # Detect & convert query type
┃ ┣ 📜query_to_bitvector.py # LaTeX → MathML → bitvector
┃ ┗ 📜search_query.py # Executes search
┣ 📜main.py # FastAPI entry point
┗ 📁math_index_storage # Stores models & indices

yaml
Copy
Edit

---

## ⚙️ API Endpoints

### `POST /search`
Search for math expressions.

**Request:**
```json
{
  "query": "\\frac{a}{b} + c^2"
}
Response:

json
Copy
Edit
{
  "time_taken_in_second": 0.25,
  "results": [
    { "id": "1", "filename": "doc1.html" },
    { "id": "2", "filename": "doc2.html" }
  ]
}
GET /view/{file_id}
Retrieve HTML content of a result.

Example:
/view/1 → returns doc1.html

Error:
404 if file not found.

🛠 Setup Instructions
Prerequisites
Flutter SDK

Python 3.8+

Backend running at http://127.0.0.1:8000

Frontend (Flutter)
Run on Web
bash
Copy
Edit
flutter run -d chrome
Run on Android Emulator
bash
Copy
Edit
flutter run -d emulator-5554
The app automatically switches between Web and Mobile renderers.

Backend (FastAPI)
Install dependencies
bash
Copy
Edit
pip install -r requirements.txt
Start server
bash
Copy
Edit
uvicorn main:app --reload
Server: http://127.0.0.1:8000
Docs: http://127.0.0.1:8000/docs

🔐 CORS Middleware
Allows any frontend to connect:

python
Copy
Edit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
In production, replace "*" with your domain.
```
🧪 Development Notes
HTML returned from backend must contain MathML.

MathJax v3 ensures cross-platform MathML rendering.

Large index files (>50MB) are excluded from GitHub (.gitignore).

📬 Contact
Author: Ankit Kumar
Email: ankit.kumar@aus.ac.in

🚫 License
This repository is for demonstration only.
Copyright © 2025 Ankit Kumar. All rights reserved.

You may:

✅ View the code and demo.

You may not:

❌ Copy, clone, or reuse the code.

❌ Modify or distribute any part.

Violations may lead to legal action.

yaml
Copy
Edit
