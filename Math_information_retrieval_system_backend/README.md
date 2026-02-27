#﻿# **2️⃣Math_information_retrieval_system Backend**


```markdown
# MIR System - Backend

This is the **backend** of the Mathematical Information Retrieval (MIR) system.  
It handles indexing, clustering, and retrieval of mathematical expressions.

---
## Contributors
# Ankit Kumar - ak0586
# Chirag Sarda - chirag0521
# Rajan Kumar Singh

## Features

- Index and store LaTeX/MathML expressions.  
- Cluster expressions using Bitvector embeddings + MiniBatchKMeans.  
- Support exact and approximate queries.  
- Expose REST APIs for frontend interaction.  
- Store indices and state in memory and file system.

---

## Tech Stack

- **Language**: Python 3.x  
- **Framework**: FastAPI  
- **Clustering**: Autoencoder embeddings + MiniBatchKMeans  
- **Data storage**: Local folders (`clusters/indices`, `state/`)

---

## Setup

1. **Clone the repository** (backend folder):

```bash
git clone https://github.com/yourusername/mir-system.git
cd mir-system/backend
Create a virtual environment:


python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
Install dependencies:

pip install -r requirements.txt

Run FastAPI server:

uvicorn main:app --reload
API available at: http://127.0.0.1:8000


API Endpoints
POST /query → Submit a math query and get results.
GET /view/{session_id}/{file_id}
DELETE /session/{session_id}


Folder Structure

📂 backend
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
┃ ┣ 📜 requirements.txt            # contains all required library and modules to be install
┃ ┗ 📂 math_index_storage          # Stores models & clustering indices
  └── requirements.txt
Contributing
Fork the repo, create a branch, make changes, and submit a pull request.

Ensure API contracts with frontend remain consistent.


