# Clustering phase
import os
import pickle
import tempfile
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
from datetime import datetime


class ProcessingState:
    """Manages the storage and retrieval of processing state"""
    def __init__(self, state_dir: str):
        self.state_file = os.path.join(state_dir, "processing_state.pkl")
        os.makedirs(state_dir, exist_ok=True)

    def save_state(self, state: Dict):
        """Save processing state to disk"""
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='wb', dir=os.path.dirname(self.state_file), delete=False) as temp_file:
                pickle.dump(state, temp_file, protocol=pickle.HIGHEST_PROTOCOL)
                temp_file.flush()
                os.fsync(temp_file.fileno())
                
            if os.path.exists(self.state_file):
                os.remove(self.state_file)
            os.rename(temp_file.name, self.state_file)
                
        except Exception as e:
            print(f"Error saving state: {str(e)}")
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
            raise

    def load_state(self) -> Optional[Dict]:
        """Load processing state from disk"""
        if not os.path.exists(self.state_file):
            return None
            
        try:
            with open(self.state_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Error loading state: {str(e)}")
            return None

class ClusterStorage:
    """Handles storage and retrieval of cluster indices using pickle with lazy loading"""
    def __init__(self, base_dir: str = "cluster_storage"):
        self.base_dir = base_dir
        self.indices_dir = os.path.join(base_dir, "indices")
        self.initialize_storage()
        self._active_clusters: Dict[str, Dict] = {}  # Cache for actively used clusters
        self._modified_clusters: Set[str] = set()    # Track which clusters need saving

    def initialize_storage(self):
        """Create necessary directories if they don't exist"""
        os.makedirs(self.indices_dir, exist_ok=True)

    def get_cluster_file_path(self, cluster_key: str) -> str:
        """Generate file path for a cluster index"""
        return os.path.join(self.indices_dir, f"cluster_{cluster_key}.pkl")

    def get_cluster_index(self, cluster_key: str) -> Optional[Dict]:
        """Get cluster data, loading from disk if necessary"""
        if cluster_key not in self._active_clusters:
            data = self._load_cluster_from_disk(cluster_key)
            if data is not None:
                self._active_clusters[cluster_key] = data
        return self._active_clusters.get(cluster_key)

    def update_cluster(self, cluster_key: str, new_data: Dict[str, list]):
        """Update cluster data and mark for saving"""
        current_data = self.get_cluster_index(cluster_key) or {}
        
        # Merge new data with existing data
        for bitvector, entries in new_data.items():
            if bitvector not in current_data:
                current_data[bitvector] = []
            current_data[bitvector].extend(entries)
        
        self._active_clusters[cluster_key] = current_data
        self._modified_clusters.add(cluster_key)

    def save_modified_clusters(self):
        """Save only the clusters that have been modified"""
        for cluster_key in self._modified_clusters:
            if cluster_key in self._active_clusters:
                self._save_cluster_to_disk(cluster_key, self._active_clusters[cluster_key])
        self._modified_clusters.clear()

    def _load_cluster_from_disk(self, cluster_key: str) -> Optional[Dict]:
        """Load a single cluster's index from disk"""
        file_path = self.get_cluster_file_path(cluster_key)
        try:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                    if not file_content:
                        return None
                    return pickle.loads(file_content)
        except Exception as e:
            print(f"Error loading cluster {cluster_key}: {str(e)}")
            # Handle corrupted file
            self._handle_corrupted_file(file_path, cluster_key)
        return None
    

    # def _save_cluster_to_disk(self, cluster_key: str, index_data: Dict):
    #     """Save a single cluster's index to disk using atomic writing"""
    #     file_path = self.get_cluster_file_path(cluster_key)
    #     temp_dir = os.path.dirname(file_path)
    #     temp_file = None
        
    #     try:
    #         with tempfile.NamedTemporaryFile(mode='wb', dir=temp_dir, delete=False) as temp_file:
    #             pickle.dump(index_data, temp_file, protocol=pickle.HIGHEST_PROTOCOL)
    #             temp_file.flush()
    #             os.fsync(temp_file.fileno())
                
    #         if os.path.exists(file_path):
    #             os.remove(file_path)
    #         os.rename(temp_file.name, file_path)
                
    #     except Exception as e:
    #         print(f"Error saving cluster {cluster_key}: {str(e)}")
    #         if temp_file and os.path.exists(temp_file.name):
    #             try:
    #                 os.unlink(temp_file.name)
    #             except:
    #                 pass
    #         raise
            
    def _save_cluster_to_disk(self, cluster_key: str, index_data: Dict):
        """Save a single cluster's index to disk using atomic writing"""
        file_path = self.get_cluster_file_path(cluster_key)
        temp_dir = os.path.dirname(file_path)

        # Create temporary file in the same directory
        fd, temp_path = tempfile.mkstemp(dir=temp_dir, suffix='.tmp')
        try:
            # Write data to temporary file
            with os.fdopen(fd, 'wb') as tmp_file:
                pickle.dump(index_data, tmp_file, protocol=pickle.HIGHEST_PROTOCOL)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
            # fd is now closed after the with block

            # On Windows, we need to handle the rename differently
            if os.name == 'nt':  # Windows
                # On Windows, rename won't overwrite existing files
                if os.path.exists(file_path):
                    # Create a backup name for atomic replacement
                    backup_path = file_path + '.bak'
                    try:
                        # Remove any existing backup
                        if os.path.exists(backup_path):
                            os.remove(backup_path)
                        # Move current file to backup
                        os.rename(file_path, backup_path)
                        # Move temp file to target location
                        os.rename(temp_path, file_path)
                        # Remove backup file
                        os.remove(backup_path)
                    except Exception as e:
                        # If anything goes wrong, try to restore from backup
                        if os.path.exists(backup_path) and not os.path.exists(file_path):
                            try:
                                os.rename(backup_path, file_path)
                            except:
                                pass
                        raise e
                else:
                    # No existing file, simple rename
                    os.rename(temp_path, file_path)
            else:
                # Unix-like systems: rename can atomically replace
                os.rename(temp_path, file_path)

        except Exception as e:
            print(f"Error saving cluster {cluster_key}: {str(e)}")
            # Clean up temporary file if it still exists
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
            raise


    def clear_cache(self):
        """Clear the in-memory cache of clusters"""
        self.save_modified_clusters()  # Save any pending changes
        self._active_clusters.clear()

