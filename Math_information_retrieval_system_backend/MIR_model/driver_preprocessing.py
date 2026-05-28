if __name__ == '__main__':
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from MIR_model.preprocessing import preprocess_dataset, MathSymbolBitVector

    symbol_table = MathSymbolBitVector()  # Initialize your symbol table
    folder_path = os.getenv("DATASET_PATH", "E:/ntcir-mathir-12-dataset/NTCIR12_MathIR_WikiCorpus_v2.1.0")
        
    print(f"Starting preprocessing for dataset at: {folder_path}")
    preprocess_dataset(folder_path, symbol_table)
        
    print("Preprocessing completed. Results are stored directly in SQLite and are ready for the clustering phase.")