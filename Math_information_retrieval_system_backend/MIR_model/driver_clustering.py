import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from MIR_model.cluster_index import MathClusterIndex

def clustering_and_indexing():
    # Clustering driver module
    index_storage = os.getenv("INDEX_STORAGE_PATH", "./math_index_storage")
    os.makedirs(index_storage, exist_ok=True)
    # Initialize the cluster index
    index = MathClusterIndex(max_clusters=14, base_dir=index_storage)
    
    # Load unique bitvectors from the SQLite database
    preprocessed_data = index.load_preprocessed_data()
    unique_bitvectors = index.extract_unique_bitvectors(preprocessed_data)
    print(f"Extracted {len(unique_bitvectors)} unique bitvectors for clustering")
    
    # Create batches of bitvectors
    bitvector_batches = index.create_bitvector_batches(unique_bitvectors, batch_size=1000)
    # Train on each batch
    for i, batch in enumerate(bitvector_batches):
        print(f"Training on batch {i+1}/{len(bitvector_batches)}")
        index.train_on_bitvector_batch(batch, i+1)

    # Finish training - this will assign all bitvectors to final clusters in SQLite
    print("Training complete, assigning all bitvectors to clusters in database...")
    index.finish_training()
    return index

if __name__ == '__main__':
    clustering_and_indexing()