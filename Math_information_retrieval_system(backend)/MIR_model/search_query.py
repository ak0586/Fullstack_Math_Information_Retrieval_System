
from .query_to_bitvector import MathConverter
from .query_processing import process_query
from .cluster_index import MathClusterIndex

def query_search(query:str,clusterer:MathClusterIndex):
    """Main interactive function with options for JSON file processing."""
    print("\nMath Expression Search System")
    print("Enter LaTeX/Text expression") 
    
    converter = MathConverter()
    # clusterer = MathClusterIndex()
    results, search_time = process_query(query, converter, clusterer)
        # Use updated display_results for single query
    if results:
        # display_results(results, search_time)
        return results, search_time
    
    
# results=query_search(r'[{\cal A}(I_{1}),{\cal A}(I_{2})]=0')

