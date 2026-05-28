import sqlite3
from rapidfuzz import fuzz
from .hamming_mini_batch_kmeans import HammingMiniBatchKMeans
from .database import MIRDatabase
import numpy as np
from typing import List, Dict, Tuple, Optional
import os
from datetime import datetime
from collections import defaultdict
import re

def canonicalize_latex(latex_str: str) -> str:
    """
    Standardize LaTeX formula syntax to improve character-level comparison accuracy.
    """
    if not latex_str:
        return ""
        
    # 1. Remove common math spacing commands
    spacing_commands = [
        r'\\quad', r'\\qquad', r'\\,', r'\\:', r'\\;', r'\\!', r'\\ ', r'\\tilde'
    ]
    for cmd in spacing_commands:
        latex_str = re.sub(cmd, '', latex_str)
        
    # 2. Strip formatting commands but keep their contents
    # e.g., \mathrm{x} -> x, \mathbf{V} -> V, \text{...} -> ...
    formatting_patterns = [
        r'\\mathrm{(.*?)}',
        r'\\mathbf{(.*?)}',
        r'\\mathit{(.*?)}',
        r'\\mathcal{(.*?)}',
        r'\\mathfrak{(.*?)}',
        r'\\mathbb{(.*?)}',
        r'\\text{(.*?)}',
        r'\\cal{(.*?)}',
    ]
    for pattern in formatting_patterns:
        latex_str = re.sub(pattern, r'\1', latex_str)
        
    # Handle brackets-based formatting tags without braces if they exist (e.g. {\cal A})
    latex_str = re.sub(r'{\\cal\s+(.*?)}', r'\1', latex_str)
    latex_str = re.sub(r'{\\bf\s+(.*?)}', r'\1', latex_str)
    
    # Strip standalone commands like \limits, \textstyle, \displaystyle
    standalone_commands = [r'\\limits', r'\\textstyle', r'\\displaystyle', r'\\boldmath']
    for cmd in standalone_commands:
        latex_str = re.sub(cmd, '', latex_str)

    # 3. Standardize scripts by enforcing braces
    # e.g., x^2 -> x^{2}, y_i -> y_{i}
    latex_str = re.sub(r'_([a-zA-Z0-9])(?![{])', r'_{\1}', latex_str)
    latex_str = re.sub(r'\^([a-zA-Z0-9])(?![{])', r'^{\1}', latex_str)
    
    # 4. Remove all whitespace
    latex_str = re.sub(r'\s+', '', latex_str)
    
    return latex_str

def rapidfuzz_similarity(str1, str2):
    c1 = canonicalize_latex(str1)
    c2 = canonicalize_latex(str2)
    if c1 == c2:
        return 1.0
    return fuzz.ratio(c1, c2) / 100.0

class MathClusterIndex:              
    def __init__(self, max_clusters=14, batch_size=1000, 
                 base_dir="math_index_storage"):
        self.n_cluster = max_clusters
        self.batch_size = batch_size
        self.base_dir = os.path.abspath(base_dir)
        
        # Ensure directories exist
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "clusters"), exist_ok=True)
        
        # Initialize SQLite database manager
        self.db = MIRDatabase(os.path.join(self.base_dir, "clusters", "math_index.db"))
        self.cluster_cache = {}  # Cache to store all cluster keys
        
        # Training state tracking
        self.centroids_initialized = False  
        self.training_completed = False  
        
        # Runtime data structures
        self.kmeans = None        
        self.vector_dim = None
        
        # Backward compatibility wrapper for unique bitvectors list
        self.all_bitvectors = {}  
        
        # Load initial state
        self._load_processing_state()
        self.load_all_clusters()  
        
        # Print status for better visibility
        if self.training_completed:
            print(f"MathClusterIndex initialized successfully with {len(self.cluster_cache)} clusters")
            print(f"Model status: {'Trained' if self.training_completed else 'Not trained'}")
        else:
            print("MathClusterIndex initialized. Training needed before searching.")

    def _save_processing_state(self):
        """Save current processing state to SQLite"""
        try:
            self.db.set_metadata('n_clusters', self.n_cluster)
            self.db.set_metadata('batch_size', self.batch_size)
            self.db.set_metadata('vector_dim', self.vector_dim)
            self.db.set_metadata('centroids_initialized', int(self.centroids_initialized))
            self.db.set_metadata('training_completed', int(self.training_completed))
            
            if self.kmeans:
                self.db.set_metadata('kmeans_max_iter', self.kmeans.max_iter)
                self.db.set_metadata('kmeans_random_state', self.kmeans.random_state if self.kmeans.random_state is not None else "")
                self.db.set_metadata('kmeans_verbose', int(self.kmeans.verbose))
                self.db.set_metadata('kmeans_n_iter', self.kmeans.n_iter_)
                if self.kmeans.cluster_centers_ is not None:
                    self.db.set_metadata('kmeans_cluster_centers', self.kmeans.cluster_centers_)
                    
            print(f"Model state saved successfully to SQLite at {datetime.now().isoformat()}")
        except Exception as e:
            print(f"Error saving processing state: {str(e)}")

    def _load_processing_state(self):
        """Load processing state from SQLite"""
        try:
            centroids_init_str = self.db.get_metadata('centroids_initialized')
            if centroids_init_str is not None:
                self.centroids_initialized = bool(int(centroids_init_str))
                self.training_completed = bool(int(self.db.get_metadata('training_completed') or 0))
                vector_dim_str = self.db.get_metadata('vector_dim')
                self.vector_dim = int(vector_dim_str) if vector_dim_str else None
                
                # Reconstruct kmeans
                n_clusters_str = self.db.get_metadata('n_clusters')
                n_clusters = int(n_clusters_str) if n_clusters_str else self.n_cluster
                
                batch_size_str = self.db.get_metadata('batch_size')
                batch_size = int(batch_size_str) if batch_size_str else self.batch_size
                
                max_iter_str = self.db.get_metadata('kmeans_max_iter')
                max_iter = int(max_iter_str) if max_iter_str else 100
                
                random_state_str = self.db.get_metadata('kmeans_random_state')
                random_state = int(random_state_str) if random_state_str else None
                
                verbose_str = self.db.get_metadata('kmeans_verbose')
                verbose = bool(int(verbose_str)) if verbose_str else True
                
                n_iter_str = self.db.get_metadata('kmeans_n_iter')
                n_iter = int(n_iter_str) if n_iter_str else 0
                
                self.kmeans = HammingMiniBatchKMeans(
                    n_clusters=n_clusters,
                    batch_size=batch_size,
                    max_iter=max_iter,
                    random_state=random_state,
                    verbose=verbose
                )
                self.kmeans.n_iter_ = n_iter
                
                cluster_centers = self.db.get_metadata('kmeans_cluster_centers', is_array=True)
                if cluster_centers is not None:
                    self.kmeans.cluster_centers_ = cluster_centers
                
                print("KMeans model loaded successfully from SQLite")
                print(f"Model loaded with {self.kmeans.n_clusters} clusters")
                print(f"Model training status: {'Complete' if self.training_completed else 'Incomplete'}")
                if self.kmeans.cluster_centers_ is not None:
                    print(f"Cluster centers shape: {self.kmeans.cluster_centers_.shape}")
            else:
                print("No saved state found - initializing new models")
        except Exception as e:
            print(f"Error loading processing state: {str(e)}")
            print("Initializing with new models")
            
    def load_preprocessed_data(self):
        """
        Wrapper to get unique bitvectors directly from database.
        """
        print("Using SQLite unified database.")
        bvs = self.db.get_unique_bitvectors()
        self.all_bitvectors = {bv: {} for bv in bvs}
        return self.all_bitvectors
    
    def extract_unique_bitvectors(self, preprocessed_data):
        """
        Extract unique bitvectors from preprocessed data.
        """
        return list(preprocessed_data.keys())
    
    def create_bitvector_batches(self, bitvectors, batch_size=1000):
        """
        Split bitvectors into batches for processing.
        """
        batches = []
        for i in range(0, len(bitvectors), batch_size):
            batch = bitvectors[i:i+batch_size]
            batches.append(batch)
        
        print(f"Created {len(batches)} batches of bitvectors")
        return batches
            
    def bitvector_to_array(self, bitvector: str) -> np.ndarray:
        """Convert a bitvector string to a numpy array"""
        return np.array([int(bit) for bit in bitvector], dtype=np.float32)
    
    def create_feature_matrix_from_bitvectors(self, bitvectors: List[str]) -> np.ndarray:
        """
        Create feature matrix from list of bitvectors
        """
        vectors = []
        for bitvector in bitvectors:
            try:
                vector = self.bitvector_to_array(bitvector)
                vectors.append(vector)
            except Exception as e:
                print(f"Error processing bit vector: {bitvector}: {str(e)}")
        
        if not vectors:
            return np.array([]).reshape(0, 0)
        
        try:
            X = np.vstack(vectors)
            if not self.vector_dim:
                self.vector_dim = X.shape[1]
        except ValueError as e:
            print(f"Error creating feature matrix: {str(e)}")
            return np.array([]).reshape(0, 0)
        
        return X.astype(np.float32)

    def train_on_bitvector_batch(self, bitvectors: List[str], batch_num: int):
        """Process a batch of bitvectors for training"""
        try:
            X = self.create_feature_matrix_from_bitvectors(bitvectors)
            
            if X.size == 0:
                print(f"Skipping empty batch {batch_num}")
                return
            
            # Initialize HammingMiniBatchKMeans only once on first batch
            if not self.centroids_initialized:
                print(f"Initializing centroids with batch {batch_num}")
                self.kmeans = HammingMiniBatchKMeans(
                    n_clusters=self.n_cluster,
                    batch_size=min(70, X.shape[0]),
                    random_state=42
                )
                self.kmeans.fit(X)
                self.centroids_initialized = True
            else:
                print(f"Partial fitting with batch {batch_num}")
                self.kmeans.partial_fit(X)
            
            # Save processing state
            self._save_processing_state()
            print(f"Processed batch {batch_num} with {len(bitvectors)} bitvectors")
        except Exception as e:
            print(f"Error processing batch {batch_num}: {str(e)}")
            raise
    
    def assign_all_bitvectors_to_clusters(self):
        """
        Assign all bitvectors to their final clusters
        and update the database.
        """
        if not self.centroids_initialized:
            print("Cannot assign bitvectors - model not properly fitted")
            return
        
        print("Assigning all bitvectors to final clusters...")
        
        # Retrieve all unique bitvectors from SQLite
        all_bitvectors = self.db.get_unique_bitvectors()
        
        # Process in batches to avoid memory issues
        batch_size = 1000
        num_batches = (len(all_bitvectors) + batch_size - 1) // batch_size
        
        assignments = []
        for batch_idx in range(num_batches):
            start_idx = batch_idx * batch_size
            end_idx = min((batch_idx + 1) * batch_size, len(all_bitvectors))
            batch_bitvectors = all_bitvectors[start_idx:end_idx]
            
            X = self.create_feature_matrix_from_bitvectors(batch_bitvectors)
            labels = self.kmeans.predict(X)
            
            for i, bitvector in enumerate(batch_bitvectors):
                cluster_id = labels[i]
                cluster_key = f"C{cluster_id}"
                assignments.append((cluster_key, bitvector))
            
            print(f"Assigned batch {batch_idx+1}/{num_batches} of bitvectors")
        
        # Update SQLite in-place
        print("Updating database with cluster assignments...")
        self.db.update_cluster_keys(assignments)
        
        self.training_completed = True
        self._save_processing_state()
        
        print("All bitvectors assigned to final clusters in database")
        self.load_all_clusters()
    
    def finish_training(self):
        """
        Mark training as complete, lock centroids, and assign all bitvectors to final clusters
        """
        if self.centroids_initialized:
            self.assign_all_bitvectors_to_clusters()
            print("Training completed, centroids locked")
        else:
            print("Cannot finish training - model not properly initialized")
    
    def load_all_clusters(self):
        """Verify and log SQLite database status"""
        try:
            self.cluster_cache.clear()
            if os.path.exists(self.db.db_path):
                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT cluster_key FROM math_expressions WHERE cluster_key IS NOT NULL")
                clusters = [row[0] for row in cursor.fetchall()]
                conn.close()
                for c in clusters:
                    self.cluster_cache[c] = True 
                print(f"SQLite Database loaded successfully with {len(self.cluster_cache)} clusters")
            else:
                print("SQLite database file not found")
        except Exception as e:
            print(f"Error checking SQLite database: {str(e)}")

    def search(self, query_bitvector: str, query_latex: str = None, k: int = None) -> List[Dict]:
        """
        Search for similar expressions using KMeans prediction with neighbor cluster fallback
        """
        if not self.kmeans:
            print("ERROR: Model not fitted or KMeans model not loaded.")
            print("Please ensure the model has been trained or that a trained model was properly loaded.")
            return []
            
        if not self.training_completed:
            print("Warning: Searching before training is completed may give inconsistent results")
            
        results = []
        try:
            print("--------------Using Binary Minibatch KMeans prediction---------------")
            query_vector = self.bitvector_to_array(query_bitvector).reshape(1, -1)
            predicted_cluster = self.kmeans.predict(query_vector)[0]
            cluster_key = f"C{predicted_cluster}"
            print(f"Searching in predicted cluster: {cluster_key}")
            
            matches = self.db.get_matches(cluster_key, query_bitvector)
            if matches:
                results = self._process_matches(matches, query_bitvector, query_latex, cluster_key)
            else:
                print(f"Bitvector not found in predicted cluster {cluster_key}")
                print("Searching in neighboring clusters...")
                neighbor_results = self._search_neighboring_clusters(query_bitvector, query_latex, predicted_cluster)
                results.extend(neighbor_results)
                
        except Exception as e:
            print(f"Error during search: {str(e)}")
            print("Traceback:", end="")
            import traceback
            traceback.print_exc()
            print("Falling back to full search due to error...")
            return self._full_search(query_bitvector, query_latex)

        final_results = self._deduplicate_and_rank_results(results)
        return final_results if k is None else final_results[:k]

    def _process_matches(self, matches: List[Dict], query_bitvector: str, query_latex: str, cluster_key: str) -> List[Dict]:
        results = []
        for match in matches:
            latex_score = 0.0
            if query_latex and match.get('latex'):
                latex_score = self._prunable_similarity(query_latex, match['latex'])
            
            result = {
                'filepath': match['filepath'],
                'latex': match['latex'],
                'bitvector': query_bitvector,
                'cluster': cluster_key,
                'similarity': latex_score,
                'query_latex': query_latex
            }
            results.append(result)
        return results

    def _prunable_similarity(self, query_latex: str, candidate_latex: str) -> float:
        """
        Optimized LaTeX string similarity with pruning rules to skip slow RapidFuzz on poor matches.
        """
        c_query = canonicalize_latex(query_latex)
        c_candidate = canonicalize_latex(candidate_latex)
        
        if c_query == c_candidate:
            return 1.0
            
        q_len = len(c_query)
        c_len = len(c_candidate)
        if q_len > 0 and (c_len / q_len < 0.4 or c_len / q_len > 2.5):
            return 0.0
            
        return fuzz.ratio(c_query, c_candidate) / 100.0

    def _deduplicate_and_rank_results(self, results: List[Dict]) -> List[Dict]:
        filepath_groups = {}
        for result in results:
            filepath = result['filepath']
            if filepath not in filepath_groups:
                filepath_groups[filepath] = []
            filepath_groups[filepath].append(result)
        
        deduplicated_results = []
        for filepath, group in filepath_groups.items():
            best_result = max(group, key=lambda x: x['similarity'])
            deduplicated_results.append(best_result)
        
        deduplicated_results.sort(key=lambda x: x['similarity'], reverse=True)
        return deduplicated_results

    def _search_neighboring_clusters(self, query_bitvector: str, query_latex: str = None, predicted_cluster: int = 1) -> List[Dict]:
        results = []
        query_vector = self.bitvector_to_array(query_bitvector).reshape(1, -1)
        distances = []
        for i in range(self.kmeans.n_clusters):
            centroid = self.kmeans.cluster_centers_[i].reshape(1, -1)
            distance = np.linalg.norm(query_vector - centroid)
            distances.append((i, distance))
        
        distances.sort(key=lambda x: x[1])
        neighbor_clusters = [d[0] for d in distances[1:min(4, len(distances))]]
        print(f"Checking {len(neighbor_clusters)} neighboring clusters: {neighbor_clusters}")
        
        for neighbor_id in neighbor_clusters:
            neighbor_key = f"C{neighbor_id}"
            matches = self.db.get_matches(neighbor_key, query_bitvector)
            if matches:
                print(f"Found match in neighboring cluster {neighbor_key}")
                cluster_results = self._process_matches(matches, query_bitvector, query_latex, neighbor_key)
                results.extend(cluster_results)
        
        if not results:
            print("No matches found in neighboring clusters, falling back to full search")
            return self._full_search(query_bitvector, query_latex)
        
        return self._deduplicate_and_rank_results(results)

    def _full_search(self, query_bitvector: str, query_latex: str = None) -> List[Dict]:
        print("Warning: Performing global search fallback")
        results = []
        matches = self.db.get_global_matches(query_bitvector)
        for match in matches:
            results.append({
                'filepath': match['filepath'],
                'latex': match['latex'],
                'bitvector': query_bitvector,
                'cluster': match['cluster_key'],
                'similarity': self._prunable_similarity(query_latex, match['latex']) if query_latex else 0.0,
                'query_latex': query_latex
            })
            
        if not results:
            print("No exact matches found globally. Performing soft Hamming distance search...")
            query_vector_arr = self.bitvector_to_array(query_bitvector)
            matching_bitvectors = self.db.get_close_bitvectors(query_vector_arr, threshold=2)
            for bv, cluster_key in matching_bitvectors:
                matches = self.db.get_matches(cluster_key, bv)
                for match in matches:
                    results.append({
                        'filepath': match['filepath'],
                        'latex': match['latex'],
                        'bitvector': bv,
                        'cluster': cluster_key,
                        'similarity': self._prunable_similarity(query_latex, match['latex']) if query_latex else 0.0,
                        'query_latex': query_latex
                    })
                    
        return self._deduplicate_and_rank_results(results)
