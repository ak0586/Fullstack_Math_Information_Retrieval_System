# Customized minibatch kmeans for bitvector with serial minibatches

import numpy as np
from scipy.stats import mode
from tqdm import tqdm

class HammingMiniBatchKMeans:
    def __init__(self, n_clusters=14, batch_size=1000, max_iter=100, random_state=None, verbose=True):
        self.n_clusters = n_clusters
        self.batch_size = batch_size
        self.max_iter = max_iter
        self.random_state = random_state
        self.verbose = verbose
        self.cluster_centers_ = None
        self.labels_ = None
        self.total_similarity_ = None
        self.n_iter_ = 0

    def _hamming_distance(self, X, centroids):
        """
        Calculate inverse Hamming distance between samples in X and centroids.
        
        Hamming distance = proportion of bits that differ
        Inverse Hamming distance = 1 - Hamming distance = proportion of bits that match
        
        Returns negative similarity (to be minimized in K-means)
        """
        n_features = X.shape[1]
        
        # Calculate Hamming distances (proportion of differing bits)
        hamming_distances = np.array([[np.sum(x != c) / n_features for c in centroids] for x in X])
        
        # Convert to inverse Hamming distance (similarity)
        # inverse_hamming = 1 - hamming_distances
        
        # Return similarity (to be maximized)
        return hamming_distances

    def _compute_binary_centroid(self, vectors):
        """
        Compute binary centroid by majority voting on each bit position.
        """
        if len(vectors) == 0:
            return None
        # Compute sum of 1s per bit position
        ones_count = np.sum(vectors, axis=0)
        # Majority voting: 1 if 1s are at least half, else 0
        return (ones_count >= (len(vectors) / 2)).astype(np.uint8)

    def _update_centroids(self, X, labels):
        """
        Update centroids based on assigned samples.
        """
        for k in range(self.n_clusters):
            cluster_points = X[labels == k]
            if len(cluster_points) > 0:
                self.cluster_centers_[k] = self._compute_binary_centroid(cluster_points)
        return self.cluster_centers_

    def partial_fit(self, X):
        # print("Partial FIt Called!")
        """
        Update the model with a single batch of samples.
        """
        X = np.asarray(X, dtype=np.uint8)
        
        # Initialize centroids if not already initialized
        if self.cluster_centers_ is None:
            n_samples = X.shape[0]
            if n_samples < self.n_clusters:
                raise ValueError(f"The number of samples ({n_samples}) is less than the number of clusters ({self.n_clusters})")
            
            self.fit(X)
            
            # Initialize labels array if needed
            if self.labels_ is None or len(self.labels_) != n_samples:
                self.labels_ = np.zeros(n_samples, dtype=np.int32)
            
            return self
        
        # Compute distances and assign samples to closest centroid
        distances = self._hamming_distance(X, self.cluster_centers_)
        labels = np.argmax(distances, axis=1)  # Use argmax since we want maximum similarity
        
        # Update centroids based on this batch
        self._update_centroids(X, labels)
        
        return self

    def fit(self, X):
        """
        Train the model using serial mini-batches, updating centroids after each batch.
        """
        X = np.asarray(X, dtype=np.uint8)
        n_samples, n_features = X.shape
        
        if self.random_state is not None:
            np.random.seed(self.random_state)
        
        # Initialize centroids by sampling from X
        indices = np.random.choice(n_samples, self.n_clusters, replace=False)
        self.cluster_centers_ = X[indices].copy()
        self.labels_ = np.zeros(n_samples, dtype=np.int32)
        
        # Calculate number of batches
        n_batches = int(np.ceil(n_samples / self.batch_size))
        
        # Run iterations
        for iteration in tqdm(range(self.max_iter), disable=not self.verbose, desc="Training KMeans"):
            # Process data in serial mini-batches
            for batch_idx in range(n_batches):
                # Get the current batch (serially)
                start_idx = batch_idx * self.batch_size
                end_idx = min((batch_idx + 1) * self.batch_size, n_samples)
                batch_X = X[start_idx:end_idx]
                
                self.partial_fit(batch_X)
                
                
            
            self.n_iter_ += 1
        
        # Calculate final inertia (negative sum of inverse Hamming distances)
        distances = self._hamming_distance(X, self.cluster_centers_)
        self.labels_=np.argmin(distances,axis=1)
        self.total_similarity_ = np.sum(np.max(distances, axis=1))
        # self.print_centroids()
        
        return self

    def predict(self, X):
        """
        Predict the closest cluster for each sample in X.
        """
        X = np.asarray(X, dtype=np.uint8)
        distances = self._hamming_distance(X, self.cluster_centers_)
        return np.argmin(distances, axis=1)  # Use argmax since we want maximum similarity
    
    # def print_centroids(self):
    #     """
    #     Print the cluster centroids.
    #     """
    #     if self.cluster_centers_ is not None:
    #         print("Cluster Centers:")
    #         for i, center in enumerate(self.cluster_centers_):
    #             print(f"Cluster {i}: {center}")
    #     else:
    #         print("Centroids not yet initialized.")
# print_centroids
