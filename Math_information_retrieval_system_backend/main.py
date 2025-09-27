#MIR backend API can handle multiple users concurrently.

from fastapi import FastAPI
from pydantic import BaseModel
from MIR_model.search_query import query_search  
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, FileResponse
from MIR_model.cluster_index import MathClusterIndex
from contextlib import asynccontextmanager
from MIR_model.driver_clustering import clustering_and_indexing
import re
import os
import uuid
import asyncio
from typing import Dict
from fastapi.middleware.cors import CORSMiddleware
import logging


# ----------------- Logging -----------------
logger = logging.getLogger("uvicorn.error")

# ----------------- Models -----------------
class user_query(BaseModel):
    query: str

class SearchSession:
    """Class to store search session data for each user"""
    def __init__(self):
        self.results = []
        self.results_to_send = []
        self.time_taken = 0
        self.timestamp = asyncio.get_event_loop().time()

# Global storage for user sessions
user_sessions: Dict[str, SearchSession] = {}
SESSION_TIMEOUT = 3600  # 1 hour timeout for sessions

def cleanup_expired_sessions():
    """Remove expired sessions to prevent memory leaks"""
    current_time = asyncio.get_event_loop().time()
    expired_sessions = [
        session_id for session_id, session in user_sessions.items()
        if current_time - session.timestamp > SESSION_TIMEOUT
    ]
    for session_id in expired_sessions:
        logger.info(f"Cleaning up expired session {session_id}")
        del user_sessions[session_id]

async def session_cleanup_task():
    """Background task to periodically cleanup expired sessions"""
    while True:
        cleanup_expired_sessions()
        await asyncio.sleep(600)  # every 10 minutes


def is_index_storage_valid(index_storage_path: str) -> bool:
    """
    Check if the index storage is valid and contains necessary data
    """
    if not os.path.exists(index_storage_path):
        logger.info("Index storage directory does not exist")
        return False
    
    # Check for required subdirectories
    required_dirs = ['clusters', 'state','clusters/indices']
    for dir_name in required_dirs:
        dir_path = os.path.join(index_storage_path, dir_name)
        if not os.path.exists(dir_path):
            logger.info(f"Missing required directory: {dir_path}")
            return False
        
        # Method 1: Using os.listdir() - checks if directory has any files/folders
        try:
            if not os.listdir(dir_path):
                logger.info(f"Required directory is empty: {dir_path}")
                return False
        except PermissionError:
            logger.error(f"Permission denied accessing directory: {dir_path}")
            return False
        except OSError as e:
            logger.error(f"Error accessing directory {dir_path}: {e}")
            return False
    return True

@asynccontextmanager
async def lifespan(app: FastAPI):
    # print("🔥 Lifespan hook is running")

    global clusterer
    
    index_storage = 'math_index_storage'
    
    # Check if index storage is valid and complete
    if not is_index_storage_valid(index_storage):
        logger.info("Index storage is invalid, missing, or incomplete. Creating new clustering index...")
        clusterer = clustering_and_indexing()
    else:
        logger.info("Loading existing clustering index...")
        try:
            clusterer = MathClusterIndex()
            # Optionally, you can add a validation step here to ensure the loaded index works
            # If loading fails, fall back to recreating the index
        except Exception as e:
            logger.error(f"Failed to load existing index: {e}")
            logger.info("Falling back to creating new clustering index...")
            clusterer = clustering_and_indexing()
    
    # Start background cleanup task
    asyncio.create_task(session_cleanup_task())
    yield
    print("👋 Lifespan hook shutting down")
    
app = FastAPI(lifespan=lifespan)   

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your web app URL in production
    allow_credentials=True,
    allow_methods=["*"],  # Includes OPTIONS, GET, POST, etc.
    allow_headers=["*"],
)

@app.post('/search')
async def query(query_data: user_query):
    # global clusterer
    
    # Clean up expired sessions periodically
    cleanup_expired_sessions()
    
    if is_plain_text_only(query_data.query):
        raise HTTPException(
            status_code=400,
            detail="Invalid input: not a recognizable LaTeX or plain mathematical expression."
        )
    
    # Generate unique session ID for this search
    session_id = str(uuid.uuid4())
    
    # Create new session
    session = SearchSession()
    
    # Perform search
    session.results, session.time_taken = query_search(query_data.query, clusterer)
    
    # Process results for response
    for idx, res in enumerate(session.results[:20], start=1):  # Top 20 results only
        filepath = res["filepath"]
        filename = os.path.basename(filepath)  # Extracts only the filename.html
        res["filename"] = filename  # Store it in the result dict for later use
        session.results_to_send.append({"id": str(idx), "filename": filename})
    
    # Store session
    user_sessions[session_id] = session
    
    return JSONResponse(
        status_code=200,
        content={
            "session_id": session_id,
            "time_taken_in_second": session.time_taken,
            "results": session.results_to_send
        }
    )

@app.get("/view/{session_id}/{file_id}")
async def view_file(session_id: str, file_id: str):
    # Check if session exists
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    
    session = user_sessions[session_id]
    
    # Find filename for given id
    file_entry = next((item for item in session.results_to_send if item["id"] == file_id), None)
    if not file_entry:
        raise HTTPException(status_code=404, detail="File ID not found.")

    filename = file_entry["filename"]

    # Find full path using filename
    full_entry = next((item for item in session.results if item.get("filename") == filename), None)
    if not full_entry:
        raise HTTPException(status_code=404, detail="File path not found.")

    filepath = full_entry["filepath"]

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File does not exist on server.")

    return FileResponse(filepath, media_type="text/html")

@app.delete("/session/{session_id}")
async def cleanup_session(session_id: str):
    """Optional endpoint to manually cleanup a session"""
    if session_id in user_sessions:
        del user_sessions[session_id]
        return JSONResponse(status_code=200, content={"message": "Session cleaned up successfully"})
    else:
        raise HTTPException(status_code=404, detail="Session not found.")

def is_plain_text_only(text: str) -> bool:
    plain_text_regex = re.compile(r"^[a-zA-Z\s.,'\';!?]+$")
    return bool(plain_text_regex.fullmatch(text.strip()))