#MIR backend API can handle multiple users concurrently.

from fastapi import FastAPI
from pydantic import BaseModel
from MIR_model.search_query import query_search  
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse, HTMLResponse
from MIR_model.cluster_index import MathClusterIndex
from contextlib import asynccontextmanager
from MIR_model.driver_clustering import clustering_and_indexing
import re
import os
import uuid
import asyncio
import time
import boto3
from typing import Dict, Optional
from fastapi.middleware.cors import CORSMiddleware
import logging


# ----------------- Logging -----------------
logger = logging.getLogger("uvicorn.error")

# ----------------- Models -----------------
class user_query(BaseModel):
    query: str

class FileViewRequest(BaseModel):
    session_id: str
    file_id: str

class SearchSession:
    """Class to store search session data for each user"""
    def __init__(self):
        self.results = []
        self.results_to_send = []
        self.time_taken = 0
        self.timestamp = time.time()

# Global storage for user sessions
user_sessions: Dict[str, SearchSession] = {}
SESSION_TIMEOUT = 3600  # 1 hour timeout for sessions

def cleanup_expired_sessions():
    """Remove expired sessions to prevent memory leaks"""
    current_time = time.time()
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
    Check if the index database exists and has completed training.
    """
    db_path = os.path.join(index_storage_path, 'clusters', 'math_index.db')
    if not os.path.exists(db_path):
        logger.info(f"Index database does not exist at {db_path}")
        return False
    
    try:
        # Check if database is valid and training is completed
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS model_metadata (key TEXT PRIMARY KEY, value BLOB)")
        cursor.execute("SELECT value FROM model_metadata WHERE key = 'training_completed'")
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0] is not None:
            training_completed = int(row[0].decode('utf-8'))
            if training_completed == 1:
                logger.info("Index storage is valid and training is completed.")
                return True
        logger.info("Index storage is invalid or training is not completed.")
        return False
    except Exception as e:
        logger.error(f"Error validating index storage: {e}")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # print("🔥 Lifespan hook is running")

    global clusterer
    
    index_storage = os.getenv("INDEX_STORAGE_PATH", "math_index_storage")
    
    # Check if index storage is valid and completed
    if not is_index_storage_valid(index_storage):
        logger.info("Index storage is invalid, missing, or incomplete. Creating new clustering index...")
        clusterer = clustering_and_indexing()
    else:
        logger.info("Loading existing clustering index...")
        try:
            clusterer = MathClusterIndex(base_dir=index_storage)
            # Optionally, you can add a validation step here to ensure the loaded index works
            # If loading fails, fall back to recreating the index
        except Exception as e:
            logger.error(f"Failed to load existing index: {e}")
            logger.info("Falling back to creating new clustering index...")
            clusterer = clustering_and_indexing()
    
    # Start background cleanup tasks
    asyncio.create_task(session_cleanup_task())
    yield
    print("Lifespan hook shutting down")
    
app = FastAPI(lifespan=lifespan)   

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your web app URL in production
    allow_credentials=True,
    allow_methods=["*"],  # Includes OPTIONS, GET, POST, etc.
    allow_headers=["*"],
)

def get_b2_client_and_bucket():
    key_id = os.getenv("B2_KEY_ID")
    application_key = os.getenv("B2_APPLICATION_KEY")
    endpoint_url = os.getenv("B2_ENDPOINT_URL", "https://s3.eu-central-003.backblazeb2.com")
    bucket_name = os.getenv("B2_BUCKET_NAME", "math-ntcir-12-dataset")
    
    # Fallback to backblaze.txt
    if not key_id or not application_key:
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        txt_path = os.path.join(backend_dir, "backblaze.txt")
        if os.path.exists(txt_path):
            try:
                with open(txt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    key_id_match = re.search(r"application\s+keyid:\s*(\S+)", content, re.IGNORECASE)
                    app_key_match = re.search(r"Application\s+key:\s*(\S+)", content, re.IGNORECASE)
                    if key_id_match:
                        key_id = key_id_match.group(1).strip()
                    if app_key_match:
                        application_key = app_key_match.group(1).strip()
            except Exception as e:
                logger.error(f"Error parsing backblaze.txt: {e}")
                
    if not key_id or not application_key:
        return None, None
        
    try:
        s3_client = boto3.client(
            service_name='s3',
            endpoint_url=endpoint_url,
            aws_access_key_id=key_id,
            aws_secret_access_key=application_key
        )
        return s3_client, bucket_name
    except Exception as e:
        logger.error(f"Failed to create B2 client: {e}")
        return None, None

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
    
    # Perform search asynchronously in a worker thread to prevent blocking the event loop
    session.results, session.time_taken = await asyncio.to_thread(query_search, query_data.query, clusterer)
    
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

@app.post("/search/document")
async def view_file(request_data: FileViewRequest):
    session_id = request_data.session_id
    file_id = request_data.file_id
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

    db_filepath = full_entry["filepath"]
    
    # Normalize Windows backslashes to forward slashes
    normalized_path = db_filepath.replace('\\', '/')
    
    # Resolve relative path (supports direct B2 keys in database and legacy absolute paths)
    if 'MathTagArticles/' in normalized_path:
        relative_path = "MathTagArticles/" + normalized_path.split('MathTagArticles/')[1]
    elif 'TextArticles/' in normalized_path:
        relative_path = "TextArticles/" + normalized_path.split('TextArticles/')[1]
    elif 'Dataset/' in normalized_path:
        relative_path = normalized_path.split('Dataset/')[1]
    elif 'NTCIR-12_MathIR_Wikipedia_Corpus/' in normalized_path:
        relative_path = "NTCIR-12_MathIR_Wikipedia_Corpus/" + normalized_path.split('NTCIR-12_MathIR_Wikipedia_Corpus/')[1]
    elif 'NTCIR12_MathIR_WikiCorpus_v2.1.0/' in normalized_path:
        relative_path = normalized_path.split('NTCIR12_MathIR_WikiCorpus_v2.1.0/')[1]
    elif 'ntcir-mathir-12-dataset/' in normalized_path:
        relative_path = normalized_path.split('ntcir-mathir-12-dataset/')[1]
    else:
        relative_path = normalized_path
        
    static_url = os.getenv("STATIC_DATASET_URL")
    if static_url:
        # TextArticles is flat on B2 bucket, strip subfolders if legacy path is used
        if 'TextArticles/' in relative_path:
            relative_path = f"TextArticles/{os.path.basename(relative_path)}"
        target_url = f"{static_url.rstrip('/')}/{relative_path}"
        return RedirectResponse(url=target_url)
        
    # Resolve relative path against the container's configured dataset path
    dataset_root = os.getenv("DATASET_PATH", "Dataset")
    filepath = os.path.normpath(os.path.join(dataset_root, relative_path))
    
    # Try local file first (if running locally or volume is mounted)
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="text/html")
        
    # Fallback: Private streaming from Backblaze B2 (safe for Private buckets!)
    s3_client, bucket_name = get_b2_client_and_bucket()
    if s3_client and bucket_name:
        try:
            # B2 bucket structure for TextArticles is flat
            b2_key = relative_path
            if 'TextArticles/' in b2_key:
                b2_key = f"TextArticles/{os.path.basename(b2_key)}"
                
            logger.info(f"Fetching {b2_key} privately from B2...")
            response = s3_client.get_object(Bucket=bucket_name, Key=b2_key)
            html_content = response['Body'].read().decode('utf-8')
            return HTMLResponse(content=html_content)
        except Exception as e:
            logger.error(f"Error fetching {relative_path} from B2: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch file from cloud storage.")
            
    # Neither local nor B2 is available
    raise HTTPException(status_code=404, detail="File does not exist on server or B2 cloud storage.")

    if not os.path.exists(filepath):
        logger.error(f"File not found on server at resolved path: {filepath}")
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

class B2IndexRequest(BaseModel):
    key_id: Optional[str] = None
    application_key: Optional[str] = None
    endpoint_url: Optional[str] = None
    bucket_name: Optional[str] = None
    batch_size: Optional[int] = 1000
    max_files: Optional[int] = None

@app.post("/index/b2")
async def trigger_b2_indexing(request: B2IndexRequest):
    """
    Trigger Backblaze B2 dataset indexing and K-Means training.
    This runs asynchronously in the background.
    """
    from MIR_model.preprocessing import preprocess_dataset_from_b2, MathSymbolBitVector
    from MIR_model.driver_clustering import clustering_and_indexing
    
    # Resolve credentials
    key_id = request.key_id or os.getenv("B2_KEY_ID")
    application_key = request.application_key or os.getenv("B2_APPLICATION_KEY")
    endpoint_url = request.endpoint_url or os.getenv("B2_ENDPOINT_URL", "https://s3.eu-central-003.backblazeb2.com")
    bucket_name = request.bucket_name or os.getenv("B2_BUCKET_NAME", "math-ntcir-12-dataset")
    
    # Try parsing backblaze.txt if not fully specified
    if not key_id or not application_key:
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        txt_path = os.path.join(backend_dir, "backblaze.txt")
        if os.path.exists(txt_path):
            try:
                with open(txt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    key_id_match = re.search(r"application\s+keyid:\s*(\S+)", content, re.IGNORECASE)
                    app_key_match = re.search(r"Application\s+key:\s*(\S+)", content, re.IGNORECASE)
                    if key_id_match and not key_id:
                        key_id = key_id_match.group(1).strip()
                    if app_key_match and not application_key:
                        application_key = app_key_match.group(1).strip()
            except Exception as e:
                logger.error(f"Error parsing backblaze.txt: {e}")
                
    if not key_id or not application_key:
        raise HTTPException(
            status_code=400,
            detail="B2 Key ID and Application Key are required (either in request, environment, or backblaze.txt)."
        )
        
    def run_indexing_and_training():
        global clusterer
        try:
            logger.info(f"Background thread: Starting Cloud-Native Indexing from B2 bucket: {bucket_name}")
            symbol_table = MathSymbolBitVector()
            
            # Step 1: Preprocess dataset from B2 into SQLite
            preprocess_dataset_from_b2(
                bucket_name=bucket_name,
                symbol_table=symbol_table,
                batch_size=request.batch_size,
                output_file="math_index_storage/clusters/math_index.db",
                key_id=key_id,
                application_key=application_key,
                endpoint_url=endpoint_url,
                max_files=request.max_files
            )
            
            logger.info("Background thread: Preprocessing from B2 complete. Starting clustering and indexing...")
            # Step 2: Run KMeans clustering
            clusterer = clustering_and_indexing()
            logger.info("Background thread: Cloud-native indexing and clustering completed successfully!")
        except Exception as e:
            logger.error(f"Error during background B2 indexing: {e}")
            
    # Run tasks in background thread using asyncio
    asyncio.create_task(asyncio.to_thread(run_indexing_and_training))
    
    return JSONResponse(
        status_code=202,
        content={"message": "Backblaze B2 indexing and K-Means training started in the background."}
    )

def is_plain_text_only(text: str) -> bool:
    plain_text_regex = re.compile(r"^[a-zA-Z\s.,'\';!?]+$")
    return bool(plain_text_regex.fullmatch(text.strip()))