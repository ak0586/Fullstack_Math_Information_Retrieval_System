# ![model_banner.png](A_2D_digital_graphic_design_banner_for_a_"model_banner.png)

# Math Information Retrieval System

This repository contains **both** the Flutter frontend and the FastAPI backend for a **Clustering-Based Mathematical Information Retrieval (MathIR)** system.

It supports **LaTeX/MathML search**, **cross-platform rendering**, and **fast retrieval** of mathematical documents.

---

## 📌 Features

### Frontend (Flutter)

* 🔍 Search LaTeX or math expressions
* 📄 Render HTML with MathML on Android and Web
* 💡 WebView for Android, iframe + MathJax for Web
* ⏱ Show response time and result count
* ✅ Clean UI with animation, loading indicators, and error handling

### Backend (FastAPI)

* ⚡ Cluster-based approximate nearest neighbor (ANN) search
* 🔢 MiniBatchKMeans with Hamming distance for binary bit-vectors
* 📂 Preprocessing of HTML to extract MathML & LaTeX
* 🚀 Scalable and optimized for large datasets

---

## 📁 Directory Structure

<pre lang="md">
📦 math-ir-system
┣ 📂 frontend
┃ ┣ 📜 main.dart                  # Main search UI and routing logic
┃ ┣ 📜 mobile_html_viewer.dart    # WebView-based HTML renderer for Android
┃ ┣ 📜 web_html_viewer.dart       # iframe-based HTML renderer for Web
┃ ┗ 📜 pubspec.yaml               # Flutter dependencies
┃
┣ 📂 backend
┃ ┣ 📂 MIR_model
┃ ┃ ┣ 📜 cluster_index.py          # Handles cluster index loading and searching
┃ ┃ ┣ 📜 clustering_phase.py       # Performs clustering on bit-vector data
┃ ┃ ┣ 📜 driver_clustering.py      # Triggers clustering and index creation
┃ ┃ ┣ 📜 driver_preprocessing.py   # Preprocesses HTML documents
┃ ┃ ┣ 📜 hamming_mini_batch_kmeans.py  # MiniBatchKMeans adapted for Hamming distance
┃ ┃ ┣ 📜 preprocessing.py          # Extracts MathML & LaTeX, generates bit-vectors
┃ ┃ ┣ 📜 query_processing.py       # Identifies query type and processes
┃ ┃ ┣ 📜 query_to_bitvector.py     # Converts LaTeX → MathML → bit-vector
┃ ┃ ┣ 📜 search_query.py           # Main search execution logic
┃ ┣ 📜 main.py                     # FastAPI entry point
┃ ┗ 📂 math_index_storage          # Stores models & clustering indices
┃
┗ 📜 README.md

</pre>

---

## 🚀 How It Works

### **Clustering & Indexing**

1. Extract MathML/LaTeX from HTML documents.
2. Convert to binary bit-vector representation.
3. Apply MiniBatchKMeans clustering with Hamming distance.
4. Store cluster indices for fast lookup.

### **Searching**

1. User submits query (`LaTeX` or plain text).
2. Query is processed into a bit-vector.
3. Nearest clusters are found.
4. Retrieve and rank top results.

---

## 🛠 Setup

### **Frontend**

```bash
cd frontend
flutter run -d chrome   # For Web
dart pub get            # Install dependencies
flutter run -d emulator-5554  # For Android
```

### **Backend**

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Runs at **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 📡 API Endpoints

### **POST** `/search`

```json
{
  "query": "\\frac{a}{b} + c^2"
}
```

Response:

```json
{
  "time_taken_in_second": 0.25,
  "results": [
    { "id": "1", "filename": "doc1.html" },
    { "id": "2", "filename": "doc2.html" }
  ]
}
```

### **GET** `/view/{file_id}`

Returns HTML content with MathML.

---

## 📜 License & Usage

**Author:** Ankit Kumar
**Email:** [ankit.kumar@aus.ac.in](mailto:ankit.kumar@aus.ac.in)

This repository is for **demonstration purposes only**.

You **may**:

* ✅ View the code
* ✅ Access the demo

You **may not**:

* ❌ Copy, clone, or reuse the code
* ❌ Modify or distribute any part of this project

Violations will be prosecuted under copyright law.

---

🎯 **Designed for cross-platform simplicity and full MathML compatibility.**
