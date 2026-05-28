import os
import sqlite3
from typing import List, Dict, Tuple, Optional
import numpy as np
import ast

class MIRDatabase:
    """Manages SQLite-based storage for preprocessed files, math expressions, and model metadata"""
    def __init__(self, db_path: str):
        self.db_path = os.path.abspath(db_path)
        # Ensure parent directories exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.initialize_database()

    def initialize_database(self):
        """Create tables and indexes if they do not exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Table for tracked processed files
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_files (
                filepath TEXT PRIMARY KEY
            )
        """)
        
        # 2. Table for preprocessed math expressions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS math_expressions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bitvector TEXT NOT NULL,
                latex TEXT NOT NULL,
                filepath TEXT NOT NULL,
                cluster_key TEXT
            )
        """)
        
        # 3. Table for model state/centroids
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_metadata (
                key TEXT PRIMARY KEY,
                value BLOB
            )
        """)
        
        # Build performance indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expr_cluster_bv ON math_expressions(cluster_key, bitvector)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expr_bv ON math_expressions(bitvector)")
        
        conn.commit()
        conn.close()

    def get_connection(self):
        """Return a connection to the SQLite database"""
        return sqlite3.connect(self.db_path)

    # --- File Tracking Operations ---
    
    def mark_file_processed(self, filepath: str):
        """Mark a single file as processed"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO processed_files (filepath) VALUES (?)", (os.path.abspath(filepath),))
        conn.commit()
        conn.close()

    def mark_batch_processed(self, filepaths: List[str]):
        """Mark a list of files as processed in a transaction"""
        if not filepaths:
            return
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.executemany("INSERT OR IGNORE INTO processed_files (filepath) VALUES (?)", 
                           [(os.path.abspath(fp),) for fp in filepaths])
        conn.commit()
        conn.close()

    def is_file_processed(self, filepath: str) -> bool:
        """Check if a file has already been processed"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM processed_files WHERE filepath = ?", (os.path.abspath(filepath),))
        res = cursor.fetchone()
        conn.close()
        return res is not None

    def get_unprocessed_files(self, all_files: List[str]) -> List[str]:
        """Filter list of files to return only the ones not yet processed"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT filepath FROM processed_files")
        processed = {row[0] for row in cursor.fetchall()}
        conn.close()
        return [f for f in all_files if os.path.abspath(f) not in processed]

    # --- Math Expression Operations ---

    def insert_math_expressions(self, batch_data: List[Tuple[str, str, str]]):
        """
        Insert a batch of math expressions: (bitvector, latex, filepath)
        """
        if not batch_data:
            return
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO math_expressions (bitvector, latex, filepath)
            VALUES (?, ?, ?)
        """, batch_data)
        conn.commit()
        conn.close()

    def get_unique_bitvectors(self) -> List[str]:
        """Get all unique bitvectors present in the preprocessed expressions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT bitvector FROM math_expressions")
        bitvectors = [row[0] for row in cursor.fetchall()]
        conn.close()
        return bitvectors

    def update_cluster_keys(self, assignments: List[Tuple[str, str]]):
        """
        Update the cluster_key for math expressions based on bitvectors.
        assignments list of: (cluster_key, bitvector)
        """
        if not assignments:
            return
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.executemany("""
            UPDATE math_expressions 
            SET cluster_key = ? 
            WHERE bitvector = ?
        """, assignments)
        conn.commit()
        conn.close()

    def get_matches(self, cluster_key: str, bitvector: str) -> List[Dict]:
        """Fetch matching expressions within a specific cluster"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT filepath, latex 
            FROM math_expressions 
            WHERE cluster_key = ? AND bitvector = ?
        """, (cluster_key, bitvector))
        rows = cursor.fetchall()
        conn.close()
        return [{'filepath': r[0], 'latex': r[1]} for r in rows]

    def get_global_matches(self, bitvector: str) -> List[Dict]:
        """Fetch all exact matching expressions across all clusters"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT filepath, latex, cluster_key 
            FROM math_expressions 
            WHERE bitvector = ?
        """, (bitvector,))
        rows = cursor.fetchall()
        conn.close()
        return [{'filepath': r[0], 'latex': r[1], 'cluster_key': r[2]} for r in rows]

    def get_close_bitvectors(self, query_vector_arr: np.ndarray, threshold: int = 2) -> List[Tuple[str, str]]:
        """
        Find expressions with similar bitvectors (within Hamming distance threshold)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT bitvector, cluster_key FROM math_expressions WHERE cluster_key IS NOT NULL")
        all_unique = cursor.fetchall()
        conn.close()
        
        matching_bitvectors = []
        for bv, cluster_key in all_unique:
            bv_arr = np.array([int(bit) for bit in bv], dtype=np.uint8)
            if np.sum(query_vector_arr != bv_arr) <= threshold:
                matching_bitvectors.append((bv, cluster_key))
        return matching_bitvectors

    # --- Model Metadata Operations ---

    def set_metadata(self, key: str, value):
        """Set metadata. Converts floats/ints/strings to standard types and serializes NumPy arrays to bytes."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if isinstance(value, np.ndarray):
            # Save raw bytes and dimension/type metadata
            val_bytes = value.tobytes()
            cursor.execute("INSERT OR REPLACE INTO model_metadata (key, value) VALUES (?, ?)", (key, val_bytes))
            cursor.execute("INSERT OR REPLACE INTO model_metadata (key, value) VALUES (?, ?)", (f"{key}_shape", str(value.shape).encode('utf-8')))
            cursor.execute("INSERT OR REPLACE INTO model_metadata (key, value) VALUES (?, ?)", (f"{key}_dtype", str(value.dtype).encode('utf-8')))
        elif isinstance(value, (int, float, str)):
            cursor.execute("INSERT OR REPLACE INTO model_metadata (key, value) VALUES (?, ?)", (key, str(value).encode('utf-8')))
        elif value is None:
            cursor.execute("INSERT OR REPLACE INTO model_metadata (key, value) VALUES (?, NULL)", (key,))
        else:
            raise ValueError(f"Unsupported metadata type for key {key}: {type(value)}")
            
        conn.commit()
        conn.close()

    def get_metadata(self, key: str, is_array: bool = False):
        """Get metadata. Handles numpy array reconstruction if is_array=True."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM model_metadata WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        if not row or row[0] is None:
            conn.close()
            return None
            
        val_bytes = row[0]
        
        if is_array:
            cursor.execute("SELECT value FROM model_metadata WHERE key = ?", (f"{key}_shape",))
            shape_row = cursor.fetchone()
            cursor.execute("SELECT value FROM model_metadata WHERE key = ?", (f"{key}_dtype",))
            dtype_row = cursor.fetchone()
            
            conn.close()
            
            if shape_row and dtype_row and shape_row[0] is not None and dtype_row[0] is not None:
                shape_val = shape_row[0]
                dtype_val = dtype_row[0]
                
                if isinstance(shape_val, bytes):
                    shape_val = shape_val.decode('utf-8')
                if isinstance(dtype_val, bytes):
                    dtype_val = dtype_val.decode('utf-8')
                
                try:
                    if shape_val and dtype_val:
                        # Safely parse shape
                        shape = ast.literal_eval(shape_val)
                        if isinstance(shape, str):
                            shape = ast.literal_eval(shape)
                        
                        # Safely parse dtype
                        dtype = np.dtype(dtype_val)
                        
                        # Ensure shape is a tuple
                        if isinstance(shape, int):
                            shape = (shape,)
                        elif isinstance(shape, list):
                            shape = tuple(shape)
                            
                        return np.frombuffer(val_bytes, dtype=dtype).reshape(shape).copy()
                except Exception as e:
                    print(f"Warning: Failed to reconstruct numpy array for key {key}: {e}")
                    
            # Graceful fallback if shape/dtype is missing or malformed
            return np.frombuffer(val_bytes, dtype=np.uint8)
            
        conn.close()
        if isinstance(val_bytes, bytes):
            return val_bytes.decode('utf-8')
        return val_bytes
