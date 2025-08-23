# '''
import os
from .cluster_index import MathClusterIndex

def clustering_and_indexing():
    # CLustering driver module
    os.makedirs("math_index_storage", exist_ok=True)
    # print_centroids
    # Initialize the cluster index
    index = MathClusterIndex(max_clusters=14, base_dir="./math_index_storage")
    
    # Load preprocessed data
    preprocessed_data=index.load_preprocessed_data("MIR_Model/preprocessed_data.pkl")
    unique_bitvectors = index.extract_unique_bitvectors(preprocessed_data)
    print(f"Extracted {len(unique_bitvectors)} unique bitvectors for clustering")
    
    # Create batches of bitvectors
    bitvector_batches = index.create_bitvector_batches(unique_bitvectors, batch_size=1000)
    # Train on each batch
    for i, batch in enumerate(bitvector_batches):
        print(f"Training on batch {i+1}/{len(bitvector_batches)}")
        index.train_on_bitvector_batch(batch, i+1)



   
    # Finish training - this will assign all bitvectors to final clusters
    print("Training complete, assigning all bitvectors to clusters...")
    index.finish_training()
    return index
# clustering_and_indexing()
    # Verify that bitvectors have been assigned to clusters
    # print(f"Bitvectors assigned to clusters: {len(index.bitvector_to_cluster)}")
    # '''