'''
from preprocessing import preprocess_dataset, save_preprocessed_data, MathSymbolBitVector
# Driver code of preprocessing

symbol_table = MathSymbolBitVector()  # Initialize your symbol table
folder_path = "E:/ntcir_mathir/DATASET/NTCIR_2014_dataset_HTML5_1"
    
 # Preprocess dataset
preprocessed_output = preprocess_dataset(folder_path, symbol_table)
    
    # Save preprocessed data
save_preprocessed_data(preprocessed_output)
    
print("Preprocessing completed. Results are saved and ready for clustering phase.")
print("Example structure of preprocessed data:")
print("preprocessed_output = {")
print("    bitvector1: {")
print("        latex1: [directory1, directory2, ...],")
print("        latex2: [directory1, directory2, ...],")
print("    },")
print("    bitvector2: { ... },")
print("}")
'''