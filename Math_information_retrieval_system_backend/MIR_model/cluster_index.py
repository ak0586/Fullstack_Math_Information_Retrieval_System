
import pickle
from .clustering_phase import ProcessingState,ClusterStorage
from rapidfuzz import fuzz
from .hamming_mini_batch_kmeans import HammingMiniBatchKMeans
import numpy as np
from typing import List,Dict
import os
from datetime import datetime
from collections import defaultdict
# Processed batch 1 with 1000 bitvectors
def rapidfuzz_similarity(str1, str2):
    if str1==str2:
        return 1.0
    """Calculate similarity between two LaTeX strings"""
    return fuzz.ratio(str1, str2) / 100.0
# Cluster Centers:
# Model status
# print_centroids
class MathClusterIndex:              
    def __init__(self, max_clusters=14, batch_size=1000, 
                 base_dir="math_index_storage"):
        self.n_cluster = max_clusters
        self.batch_size = batch_size
        self.base_dir = os.path.abspath(base_dir)
        # Initialize storage components
        self.cluster_storage = ClusterStorage(os.path.join(base_dir, "clusters"))
        self.state_manager = ProcessingState(os.path.join(base_dir, "state"))
        
        self.cluster_cache = {}  # Cache to store all clusters
        
        # Training state tracking
        self.centroids_initialized = False  # Track if centroids have been initialized
        self.training_completed = False  # Track if all training is complete
        
        # Runtime data structures
        self.kmeans = None        # self.is_fitted = False
        self.vector_dim = None
        
        # Store all bitvectors and their metadata
        self.all_bitvectors = {}  # {bitvector: {latex: [directories]}}
        
        # Ensure directories exist
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "clusters"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "state"), exist_ok=True)
        
        # Load initial state
        self._load_processing_state()
        self.load_all_clusters()  # Load clusters after state is loaded
        
        # Print status for better visibility
        if self.training_completed:
            print(f"MathClusterIndex initialized successfully with {len(self.cluster_cache)} clusters")
            print(f"Model status: {'Trained' if self.training_completed else 'Not trained'}")
        else:
            print("MathClusterIndex initialized. Training needed before searching.")

    def _save_processing_state(self):
        """Save current processing state"""
        try:
            state = {
                'kmeans_state': pickle.dumps(self.kmeans) if self.kmeans else None,
                # 'scaler_state': pickle.dumps(self.scaler) if self.is_fitted else None,
                # 'is_fitted': self.is_fitted,
                'vector_dim': self.vector_dim,
                'centroids_initialized': self.centroids_initialized,
                'training_completed': self.training_completed,
                'timestamp': datetime.now().isoformat()
            }
            self.state_manager.save_state(state)
            print(f"Model state saved successfully at {datetime.now().isoformat()}")
        except Exception as e:
            print(f"Error saving processing state: {str(e)}")

    def _load_processing_state(self):
        """Load processing state"""
        try:
            state = self.state_manager.load_state()
            if state:
                if state.get('kmeans_state'):
                    self.kmeans = pickle.loads(state['kmeans_state'])
                    print("KMeans model loaded successfully")
                
                # self.is_fitted = state.get('is_fitted', False)
                self.vector_dim = state.get('vector_dim')
                self.centroids_initialized = state.get('centroids_initialized', False)
                self.training_completed = state.get('training_completed', False)
                
                # Print loaded state information
                if  self.kmeans:
                    print(f"Model loaded with {self.kmeans.n_clusters} clusters")
                    print(f"Model training status: {'Complete' if self.training_completed else 'Incomplete'}")
                    if hasattr(self.kmeans, 'cluster_centers_'):
                        print(f"Cluster centers shape: {self.kmeans.cluster_centers_.shape}")
                else:
                    print("No trained model found in saved state")
                    
            else:
                print("No saved state found - initializing new models")
        except Exception as e:
            print(f"Error loading processing state: {str(e)}")
            print("Initializing with new models")
            
    def load_preprocessed_data(self, data_path='preprocessed_data.pkl'):
        """
        Load preprocessed data in the format:
        {
            bitvector1: {
                latex1: [directory1, directory2, ...],
                latex2: [directory1, directory2, ...],
            },
            bitvector2: { ... },
        }
        """
        try:
            with open(data_path, 'rb') as f:
                preprocessed_data = pickle.load(f)
            
            print(f"Loaded preprocessed data with {len(preprocessed_data)} bitvectors")
            
            # Store the complete data in memory
            self.all_bitvectors = preprocessed_data
            
            return preprocessed_data
        except Exception as e:
            print(f"Error loading preprocessed data: {str(e)}")
            return {}
    
    def extract_unique_bitvectors(self, preprocessed_data):
        """
        Extract unique bitvectors from preprocessed data
        Returns a list of unique bitvectors
        """
        return list(preprocessed_data.keys())
    
    def create_bitvector_batches(self, bitvectors, batch_size=1000):
        """
        Split bitvectors into batches for processing
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
        Returns matrix X
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
            
                
            # Initialize SerialMiniBatchKMeans only once on first batch
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
                # Otherwise just partial_fit
                print(f"Partial fitting with batch {batch_num}")
                self.kmeans.partial_fit(X)
            
            # Save processing state
            self._save_processing_state()
            
            print(f"Processed batch {batch_num} with {len(bitvectors)} bitvectors")
            # self.kmeans.print_centroids()
        except Exception as e:
            print(f"Error processing batch {batch_num}: {str(e)}")
            raise
    
    def assign_all_bitvectors_to_clusters(self):
        """
        Assign all bitvectors to their final clusters
        and organize the data for storage
        """
        if not self.centroids_initialized:
            print("Cannot assign bitvectors - model not properly fitted")
            return
        
        print("Assigning all bitvectors to final clusters...")
        
        # Get all unique bitvectors
        all_bitvectors = list(self.all_bitvectors.keys())
        
        # Process in batches to avoid memory issues
        batch_size = 1000
        num_batches = (len(all_bitvectors) + batch_size - 1) // batch_size
        
        # Create cluster data structure
        cluster_data = defaultdict(lambda: defaultdict(list))
        
        for batch_idx in range(num_batches):
            start_idx = batch_idx * batch_size
            end_idx = min((batch_idx + 1) * batch_size, len(all_bitvectors))
            batch_bitvectors = all_bitvectors[start_idx:end_idx]
            
            # Convert bitvectors to feature matrix
            X = self.create_feature_matrix_from_bitvectors(batch_bitvectors)
              
            
            # Predict clusters
            labels = self.kmeans.predict(X)
            
            # Assign bitvectors to clusters
            for i, bitvector in enumerate(batch_bitvectors):
                cluster_id = labels[i]
                cluster_key = f"C{cluster_id}"
                
                # Get all LaTeX expressions and directories for this bitvector
                for latex, directories in self.all_bitvectors[bitvector].items():
                    for directory in directories:
                        metadata_entry = {
                            'filepath': directory,
                            'latex': latex,
                            'vector_id': i
                        }
                        cluster_data[cluster_key][bitvector].append(metadata_entry)
            
            print(f"Processed batch {batch_idx+1}/{num_batches} of bitvectors")
        
        # Update the cluster storage with the final assignments
        for cluster_key, data in cluster_data.items():
            self.cluster_storage.update_cluster(cluster_key, data)
        
        # Save the modified clusters
        self.cluster_storage.save_modified_clusters()
        
        # Mark training as complete
        self.training_completed = True
        self._save_processing_state()
        
        print("All bitvectors assigned to final clusters")
        
        # Reload clusters to ensure we have the latest data
        self.load_all_clusters()
    
    def finish_training(self):
        """
        Mark training as complete, lock centroids, and assign all bitvectors to final clusters
        """
        if  self.centroids_initialized:
            self.assign_all_bitvectors_to_clusters()
            print("Training completed, centroids locked")
        else:
            print("Cannot finish training - model not properly initialized")
    
    def load_all_clusters(self):
        """Pre-load all cluster data into memory during initialization"""
        try:
            # Clear current cache
            self.cluster_cache.clear()
            
            # Get all cluster files
            if os.path.exists(self.cluster_storage.indices_dir):
                cluster_files = [f for f in os.listdir(self.cluster_storage.indices_dir) 
                               if f.startswith("cluster_") and f.endswith(".pkl")]
                
                # Load each cluster into memory
                for cluster_file in cluster_files:
                    cluster_key = cluster_file[8:-4]  # Remove "cluster_" prefix and ".pkl" suffix
                    cluster_data = self.cluster_storage.get_cluster_index(cluster_key)
                    if cluster_data is not None:
                        self.cluster_cache[cluster_key] = cluster_data
                
                print(f"Successfully loaded {len(self.cluster_cache)} clusters into memory")
                
                # Optional: Print memory usage statistics
                # import sys
                # memory_usage = sys.getsizeof(self.cluster_cache) / (1024 * 1024)  # Convert to MB
                # print(f"Approximate memory usage: {memory_usage:.2f} MB")
            else:
                print(f"Cluster directory not found: {self.cluster_storage.indices_dir}")
                
        except Exception as e:
            print(f"Error loading clusters into memory: {str(e)}")
            raise
                
    def search(self, query_bitvector: str, query_latex: str = None, k: int = None) -> List[Dict]:
        """
        Search for similar expressions using KMeans prediction with neighbor cluster fallback
        
        Args:
            query_bitvector: Bitvector string to search for
            query_latex: Optional LaTeX string for similarity refinement
            k: Optional number of results to return
            
        Returns:
            List of matching results sorted by similarity
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
            
            # Convert bitvector to feature vector and predict cluster
            query_vector = self.bitvector_to_array(query_bitvector).reshape(1, -1)
            
            
            
            # Predict the cluster
            predicted_cluster = self.kmeans.predict(query_vector)[0]
            cluster_key = f"C{predicted_cluster}"
            print(f"Searching in predicted cluster: {cluster_key}")
            
            # Search in the predicted cluster from cache
            if cluster_key in self.cluster_cache:
                # Check if exact bitvector exists in predicted cluster
                if query_bitvector in self.cluster_cache[cluster_key]:
                    matches = self.cluster_cache[cluster_key][query_bitvector]
                    for match in matches:
                        latex_score = 0.0
                        if query_latex and match.get('latex'):
                            latex_score = rapidfuzz_similarity(query_latex, match['latex'])
                        
                        result = {
                            'filepath': match['filepath'],
                            'latex': match['latex'],
                            'bitvector': query_bitvector,
                            'cluster': cluster_key,
                            'similarity': latex_score,
                            'query_latex': query_latex
                        }
                        results.append(result)
                else:
                    print(f"Bitvector not found in predicted cluster {cluster_key}")
                    # Search in neighboring clusters instead of full search
                    print("Searching in neighboring clusters...")
                    neighbor_results = self._search_neighboring_clusters(query_bitvector, query_latex, predicted_cluster)
                    results.extend(neighbor_results)
            else:
                print(f"Predicted cluster {cluster_key} not found in cache")
                print("Falling back to full search...")
                return self._search_neighboring_clusters(query_bitvector, query_latex, predicted_cluster)
                
        except Exception as e:
            print(f"Error during search: {str(e)}")
            print("Traceback:", end="")
            import traceback
            traceback.print_exc()
            # Fallback to full search on error
            print("Falling back to full search due to error...")
            return self._search_neighboring_clusters(query_bitvector, query_latex, predicted_cluster)

        # Sort results by similarity score
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results if k is None else results[:k]

    def _search_neighboring_clusters(self, query_bitvector: str, query_latex: str = None, predicted_cluster: int=1) -> List[Dict]:
        """
        Search for the bitvector in neighboring clusters
        
        Args:
            query_bitvector: Bitvector string to search for
            query_latex: Optional LaTeX string for similarity refinement
            predicted_cluster: The original predicted cluster ID
            
        Returns:
            List of matching results from neighboring clusters
        """
        results = []
        
        # Calculate distances from query vector to all cluster centroids
        query_vector = self.bitvector_to_array(query_bitvector).reshape(1, -1)
      
        
        # Calculate distances to all centroids
        distances = []
        for i in range(self.kmeans.n_clusters):
            centroid = self.kmeans.cluster_centers_[i].reshape(1, -1)
            distance = np.linalg.norm(query_vector - centroid)
            distances.append((i, distance))
        
        # Sort clusters by distance (closest first)
        distances.sort(key=lambda x: x[1])
        
        # Skip the first one as it's the original predicted cluster
        # Take the next 3 closest clusters (or fewer if there aren't 3)
        neighbor_clusters = [d[0] for d in distances[1:min(4, len(distances))]]
        
        print(f"Checking {len(neighbor_clusters)} neighboring clusters: {neighbor_clusters}")
        
        # Search in each neighboring cluster
        for neighbor_id in neighbor_clusters:
            neighbor_key = f"C{neighbor_id}"
            
            if neighbor_key in self.cluster_cache and query_bitvector in self.cluster_cache[neighbor_key]:
                print(f"Found match in neighboring cluster {neighbor_key}")
                matches = self.cluster_cache[neighbor_key][query_bitvector]
                
                for match in matches:
                    latex_score = 0.0
                    if query_latex and match.get('latex'):
                        latex_score = rapidfuzz_similarity(query_latex, match['latex'])
                    
                    result = {
                        'filepath': match['filepath'],
                        'latex': match['latex'],
                        'bitvector': query_bitvector,
                        'cluster': neighbor_key,
                        'similarity': latex_score,
                        'query_latex': query_latex
                    }
                    results.append(result)
        
        if not results:
            print("No matches found in neighboring clusters, falling back to full search")
            return self._full_search(query_bitvector, query_latex)
            
        return results


