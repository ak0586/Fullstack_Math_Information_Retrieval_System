
from fastapi import FastAPI
from pydantic import BaseModel
from sklearn import cluster
from MIR_model.search_query import query_search  
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse,FileResponse
from MIR_model.cluster_index import MathClusterIndex
from contextlib import asynccontextmanager
from MIR_model.driver_clustering import clustering_and_indexing
import re
import os
from fastapi.middleware.cors import CORSMiddleware
# from pathlib import Path




class user_query(BaseModel):
    query:str


@asynccontextmanager #To loader index and clustering model on app start
async def lifespan(app: FastAPI):
    global clusterer
    index_storage='math_index_storage'
    if not os.path.exists(index_storage):
        clusterer = clustering_and_indexing()
    else:
        clusterer=MathClusterIndex()
    yield

app = FastAPI(lifespan=lifespan)   

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your web app URL in production
    allow_credentials=True,
    allow_methods=["*"],  # Includes OPTIONS, GET, POST, etc.
    allow_headers=["*"],
)

@app.post('/search')
def query(query_data:user_query):
    global results, results_to_send
    global time
    global clusterer
    if is_plain_text_only(query_data.query):
        raise HTTPException(
            status_code=400,
            detail="Invalid input: not a recognizable LaTeX or plain mathematical expression."
        )
    results,time_taken_in_second = query_search(query_data.query,clusterer)
    results_to_send=[]

    for idx, res in enumerate(results[:20], start=1):  # Top 20 results only
        filepath = res["filepath"]
        filename = os.path.basename(filepath)  # Extracts only the filename.html
        res["filename"] = filename  # Store it in the result dict for later use
        results_to_send.append({"id": str(idx), "filename": filename})

    return JSONResponse(status_code=200,content={"time_taken_in_second":time_taken_in_second,"results":results_to_send})
    

@app.get("/view/{file_id}")
def view_file(file_id: str):
    global results, results_to_send

    # Find filename for given id
    file_entry = next((item for item in results_to_send if item["id"] == file_id), None)
    if not file_entry:
        raise HTTPException(status_code=404, detail="File ID not found.")

    filename = file_entry["filename"]

    # Find full path using filename
    full_entry = next((item for item in results if item.get("filename") == filename), None)
    if not full_entry:
        raise HTTPException(status_code=404, detail="File path not found.")

    filepath = full_entry["filepath"]

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File does not exist on server.")

    return FileResponse(filepath, media_type="text/html")



def is_plain_text_only(text: str) -> bool:
    plain_text_regex=re.compile(r"^[a-zA-Z\s.,'\';!?]+$")
    return bool(plain_text_regex.fullmatch(text.strip()))