import sys
import os
import re

# Add parent directory to path to allow importing packages if executed directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from MIR_model.preprocessing import preprocess_dataset_from_b2, MathSymbolBitVector
from MIR_model.driver_clustering import clustering_and_indexing

def load_b2_credentials():
    credentials = {
        'key_id': os.getenv("B2_KEY_ID"),
        'application_key': os.getenv("B2_APPLICATION_KEY"),
        'endpoint_url': os.getenv("B2_ENDPOINT_URL", "https://s3.eu-central-003.backblazeb2.com"),
        'bucket_name': os.getenv("B2_BUCKET_NAME", "math-ntcir-12-dataset")
    }
    
    # Locate backblaze.txt
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    txt_paths = [
        os.path.join(backend_dir, "backblaze.txt"),
        "backblaze.txt",
        "../backblaze.txt"
    ]
    for path in txt_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    key_id_match = re.search(r"application\s+keyid:\s*(\S+)", content, re.IGNORECASE)
                    app_key_match = re.search(r"Application\s+key:\s*(\S+)", content, re.IGNORECASE)
                    if key_id_match and not credentials['key_id']:
                        credentials['key_id'] = key_id_match.group(1).strip()
                    if app_key_match and not credentials['application_key']:
                        credentials['application_key'] = app_key_match.group(1).strip()
                print(f"Loaded credentials from {path}")
                break
            except Exception as e:
                print(f"Error reading {path}: {e}")
                
    return credentials

if __name__ == '__main__':
    creds = load_b2_credentials()
    
    if not creds['key_id'] or not creds['application_key']:
        print("Error: Could not load Backblaze B2 credentials.")
        print("Please ensure B2_KEY_ID and B2_APPLICATION_KEY are set or backblaze.txt is present.")
        sys.exit(1)
        
    print(f"Starting cloud-native preprocessing from B2 bucket: {creds['bucket_name']}")
    print(f"Endpoint URL: {creds['endpoint_url']}")
    
    symbol_table = MathSymbolBitVector()
    
    # Run preprocessing
    max_files = int(os.getenv("B2_MAX_FILES")) if os.getenv("B2_MAX_FILES") else None
    preprocess_dataset_from_b2(
        bucket_name=creds['bucket_name'],
        symbol_table=symbol_table,
        batch_size=1000,
        output_file="math_index_storage/clusters/math_index.db",
        key_id=creds['key_id'],
        application_key=creds['application_key'],
        endpoint_url=creds['endpoint_url'],
        max_files=max_files
    )
    
    print("\nPreprocessing from B2 complete. Starting clustering and indexing...")
    clustering_and_indexing()
    print("\nCloud-native indexing and clustering completed successfully!")
