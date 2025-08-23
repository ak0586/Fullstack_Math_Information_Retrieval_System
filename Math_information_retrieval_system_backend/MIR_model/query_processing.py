import re
from .query_to_bitvector import MathConverter
from .cluster_index import MathClusterIndex
from .preprocessing import analyze_single_mathml,MathSymbolBitVector

def process_query(query: str, converter: MathConverter, clusterer: MathClusterIndex):
    """Process query with exact bitvector matching followed by MathML matching."""
    start_time = time.time()  # Start timing
    
    try:
        # Clean and validate LaTeX query
        if re.search(r"\\[a-zA-Z]+", query):  # LaTeX detection
            mathml = converter.convert_to_mathml(query, input_type='latex')
        else:
            print(f"Processing plain text query: {query}")
            mathml = converter.convert_to_mathml(query, input_type='text')
            
        if isinstance(mathml, str) and not mathml.startswith('Error'):
            # Use the same analysis function as dataset processing
            # print("MathML: ", mathml)
            symbol_table = MathSymbolBitVector()
            bit_vector, _ = analyze_single_mathml(mathml, symbol_table)
            
            if bit_vector:
                print("\nQuery Details:")
                print("Bit-Vector:", bit_vector)
                print("MathML: ", mathml)
                
                # Search with both bitvector and latex
                results = clusterer.search(bit_vector, query)
                
                # Calculate total search time
                search_time = time.time() - start_time
                
                # Return both results and search time
                return results[:20], search_time
            else:
                print("Could not generate bit vector from query")
                return [], time.time() - start_time
        else:
            print(f"MathML conversion failed: {mathml}")
            return [], time.time() - start_time
            
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        print("Debug info - Query:", query)
        return [], time.time() - start_time
    

from pathlib import Path
import os
import webbrowser
import json
import time
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT


def normalize_path(path_str):
    """Normalize path separators to use forward slashes consistently."""
    # Replace all backslashes with forward slashes
    normalized_path = path_str.replace('\\', '/')
    return normalized_path


def safe_path_to_uri(path):
    """Safely convert a path to a URI for hyperlinks."""
    try:
        # Normalize path separators first
        normalized_path = normalize_path(path)
        
        # Convert to absolute path if relative
        abs_path = Path(normalized_path).resolve()
        # Create a valid file URI
        uri = abs_path.as_uri()
        return uri
    except Exception as e:
        print(f"Path conversion error: {str(e)}")
        return f"file:///{normalized_path}"  # Fallback to simple URI format


def open_file_location(file_path):
    """Open the file or its containing folder in the system's file explorer."""
    try:
        path_obj = Path(file_path)
        
        # If it's a directory, open the directory
        if path_obj.is_dir():
            webbrowser.open(safe_path_to_uri(file_path))
            print(f"Opening directory: {file_path}")
            return True
            
        # If it's a file, open the file
        elif path_obj.is_file():
            webbrowser.open(safe_path_to_uri(file_path))
            print(f"Opening file: {file_path}")
            return True
            
        # If the file doesn't exist, try to open its parent directory
        elif path_obj.parent.exists():
            webbrowser.open(safe_path_to_uri(str(path_obj.parent)))
            print(f"File not found. Opening parent directory: {path_obj.parent}")
            return True
            
        else:
            print(f"Neither file nor parent directory exists: {file_path}")
            return False
            
    except Exception as e:
        print(f"Error opening file location: {str(e)}")
        return False


def display_results(results, search_time):
    """Display search results with timing information and clickable file paths."""
    print("\nSearch Performance:")
    print(f"Total search time: {search_time:.4f} seconds")
    print("-" * 80)
    
    if not results:
        print("No results found.")
        return
    
    # Get total number of results
    total_results = len(results)
    
    for index, result in enumerate(results, 1):
        try:
            print()
            print(f"Result #{index} of {total_results}")
            
            # Handle file path - use filepath key, matching second code
            file_path = result['filepath']  # Using 'filepath' instead of 'file_path'
            
            try:
                # Normalize path separators
                file_path = normalize_path(file_path)
                
                # Remove 'file:///' prefix if it exists
                clean_path = file_path.replace('file:///', '')
                path_obj = Path(clean_path)
                
                # Convert to absolute path
                absolute_path = str(path_obj.absolute())
                
                # Normalize the absolute path too
                absolute_path = normalize_path(absolute_path)
                
                # Check if the path exists
                if path_obj.exists():
                    print(f"✓ {absolute_path} [Click to open - type '{index}']")
                else:
                    print(f"✗ {absolute_path} (not found) [Click to open parent - type '{index}']")
                    
            except Exception as path_error:
                print(f"! {file_path} (error: {str(path_error)})")
            
            # Display result details
            print(f"Query latex: {result['query_latex']}")
            print(f"Matched latex: {result['latex']}")
            print(f"Bit Vector: {result['bitvector']}")
            print(f"Cluster: {result['cluster']}")
            
            if 'similarity' in result:
                match_status = "Exact Match" if result['similarity'] == 1.0 else "Partial Match"
                print(f"Similarity Score: {result['similarity']:.4f} ({match_status})")
            
            print("-" * 80)
                
        except Exception as e:
            print(f"Error displaying result: {str(e)}")
            print("-" * 80)
    
    # Add option to open file locations
    # print("\nOptions:")
    # print("- Type the result number to open that file location")
    # print("- Type 'c' to continue")
    
    # while True:
    #     choice = input("Enter your choice: ").strip()
        
    #     if choice.lower() == 'c':
    #         break
            
    #     try:
    #         result_num = int(choice)
    #         if 1 <= result_num <= len(results):
    #             file_path = results[result_num-1]['filepath']
    #             clean_path = file_path.replace('file:///', '')
    #             if open_file_location(clean_path):
    #                 print(f"Opened file location for Result #{result_num}")
    #             else:
    #                 print(f"Could not open file location for Result #{result_num}")
    #         else:
    #             print(f"Invalid result number. Please enter a number between 1 and {len(results)}")
    #     except ValueError:
    #         print("Invalid input. Please enter a valid result number or 'c' to continue")


def save_results_to_pdf(all_results, output_pdf_path):
    """Save all search results to a PDF file with clickable file paths."""
    doc = SimpleDocTemplate(
        output_pdf_path, 
        pagesize=letter,
        leftMargin=15,  # Reduced left margin (default is 72)
        rightMargin=15, # Reduced right margin (default is 72)
        topMargin=36,   # Slightly reduced top margin
        bottomMargin=36 # Slightly reduced bottom margin
    )

    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Create a link style based on the normal style
    link_style = ParagraphStyle(
        'LinkStyle',
        parent=normal_style,
        textColor=colors.blue,
        underline=1
    )
    
    elements = []
    
    # Add title
    elements.append(Paragraph("Math Expression Search Results", title_style))
    elements.append(Spacer(1, 12))
    
    # Summary information
    total_queries = len(all_results)
    successful_queries = sum(1 for query_result in all_results if query_result['results'])
    total_search_time = sum(query_result['search_time'] for query_result in all_results)
    
    elements.append(Paragraph(f"Total Queries Processed: {total_queries}", heading_style))
    elements.append(Paragraph(f"Successful Queries: {successful_queries}", normal_style))
    elements.append(Paragraph(f"Failed Queries: {total_queries - successful_queries}", normal_style))
    elements.append(Paragraph(f"Total Search Time: {total_search_time:.4f} seconds", normal_style))
    elements.append(Spacer(1, 20))
    
    # Detailed results for each query
    for i, query_result in enumerate(all_results, 1):
        query = query_result['query']
        results = query_result['results']
        search_time = query_result['search_time']
        
        elements.append(Paragraph(f"Query #{i}: {query}", heading_style))
        elements.append(Paragraph(f"Search Time: {search_time:.4f} seconds", normal_style))
        elements.append(Spacer(1, 10))
        
        if not results:
            elements.append(Paragraph("No results found.", normal_style))
            elements.append(Spacer(1, 15))
            continue
        
        # Calculate total number of individual results
        total_results = len(results)
        elements.append(Paragraph(f"Found {total_results} matches", normal_style))
        elements.append(Spacer(1, 10))
        
        for current_index, result in enumerate(results, 1):
            try:
                elements.append(Paragraph(f"Result #{current_index} of {total_results}", normal_style))
                
                # Handle file path - use filepath key to match second code
                file_path = result['filepath']
                
                try:
                    # Normalize path separators
                    file_path = normalize_path(file_path)
                    
                    # Remove 'file:///' prefix if it exists
                    clean_path = file_path.replace('file:///', '')
                    path_obj = Path(clean_path)
                    
                    # Create URI for hyperlink
                    try:
                        uri = safe_path_to_uri(clean_path.strip())
                    except:
                        # If converting to URI fails, try with parent directory
                        uri = safe_path_to_uri(str(path_obj.parent)) if path_obj.parent.exists() else None
                    
                    # Check if the path exists
                    if path_obj.exists():
                        # Use ReportLab's built-in hyperlink feature
                        link_text = f'<font color="blue"><u> {file_path} </u></font>'
                        elements.append(Paragraph(link_text, normal_style))
                    else:
                        # Try to link to parent directory
                        if uri:
                            link_text = f'<font color="blue"><u> {file_path} (not found)</u></font>'
                            elements.append(Paragraph(link_text, normal_style))
                        else:
                            elements.append(Paragraph(f" {file_path} (not found)", normal_style))
                        
                except Exception as path_error:
                    elements.append(Paragraph(f"! {file_path} (error: {str(path_error)})", normal_style))
                
                # Create a table for result details
                data = [
                    ["Query LaTeX", result['query_latex']],
                    ["Matched LaTeX", result['latex']],
                    ["Bit Vector", result['bitvector']],
                    ["Cluster", result['cluster']]
                ]
                
                if 'similarity' in result:
                    match_status = "Exact Match" if result['similarity'] == 1.0 else "Partial Match"
                    data.append(["Similarity Score", f"{result['similarity']:.4f} ({match_status})"])
                
                table = Table(data, colWidths=[120, 350])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                elements.append(table)
                elements.append(Spacer(1, 15))
                    
            except Exception as e:
                elements.append(Paragraph(f"Error displaying result: {str(e)}", normal_style))
                elements.append(Spacer(1, 15))
                continue
        
        # Add a separator between queries
        elements.append(Paragraph("-" * 80, normal_style))
        elements.append(Spacer(1, 20))
    
    # Build the PDF
    doc.build(elements)
    print(f"PDF saved to: {output_pdf_path}")
    
    # Open the PDF after creation
    try:
        webbrowser.open(output_pdf_path)
        print(f"PDF opened: {output_pdf_path}")
    except Exception as e:
        print(f"Could not automatically open the PDF: {str(e)}")


def process_json_queries(json_path, clusterer, output_pdf_path):
    """Process multiple queries from a JSON file and save results to PDF."""
    converter = MathConverter()
    all_results = []
    
    try:
        # Load queries from JSON file
        with open(json_path, 'r') as file:
            queries_data = json.load(file)
        
        # Handle different JSON formats - either a list of strings or an object with a queries property
        if isinstance(queries_data, list):
            queries = queries_data
        elif isinstance(queries_data, dict) and 'queries' in queries_data:
            queries = queries_data['queries']
        else:
            raise ValueError("Invalid JSON format. Expected either a list of queries or an object with 'queries' property")
        
        # Make sure we have valid queries
        if not queries or not isinstance(queries, list):
            raise ValueError("No queries found in the JSON file or invalid format")
        
        print(f"Found {len(queries)} queries in {json_path}")
        
        # Process each query
        start_total_time = time.time()
        for i, query in enumerate(queries, 1):
            print(f"Processing query {i}/{len(queries)}: {query}")
            results, search_time = process_query(query, converter, clusterer)
            all_results.append({
                'query': query,
                'results': results,
                'search_time': search_time
            })
        total_time = time.time() - start_total_time
        
        # Save results to PDF
        save_results_to_pdf(all_results, output_pdf_path)
        
        # Print summary report
        print("\nQuery Processing Summary:")
        print(f"Total queries processed: {len(queries)}")
        print(f"Successful queries: {sum(1 for r in all_results if r['results'])}")
        print(f"Failed queries: {sum(1 for r in all_results if not r['results'])}")
        print(f"Total processing time: {total_time:.4f} seconds")
        
    except Exception as e:
        print(f"Error processing queries: {str(e)}")




# # Initialize the clusterer
# # Changed from MathClusterIndex to BitvectorClusterIndex to match the second code
checkpoint_dir = "math_index_storage"

clusterer = MathClusterIndex(
    max_clusters=14,
    batch_size=1000,
    base_dir=checkpoint_dir
)

# # Start interactive search
# # if __name__ == "__main__":
# interactive_search(clusterer)
