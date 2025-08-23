##############################################################
# hamming minibatch clustering and indexing with searching.ipynb
# ready to run on server

############################

import os
import re
import pickle
import numpy as np
import time
import math
import tempfile
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple,Any
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import latex2mathml.converter
import html
from collections import defaultdict
import shutil

class MathSymbolBitVector:
    def __init__(self):
         self.categories = {
            'Numerals': r'[0123456789𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳⓪①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹᠐᠑᠒᠓᠔᠕᠖᠗᠘᠙০১২৩৪৫৬৭৮৯०१२३४५६७८९𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫]',
            'Latin/Greek': r'[ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ𝒜ℬℰℱ𝒢ℋℐℒ𝒥𝒦ℳ𝒩𝒪𝒫𝒬ℛ𝒯𝒰𝒱𝒲𝒳𝒴𝒵ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩαβγδεζηθικλμνξοπρστυφχψωϵϑϰϕϖϱϜϝϞϟϠϡ𝜀𝜃𝜅𝜑𝜋𝜌σ𝜎𝜏𝜔]',
            'Arithmetic': r'[÷×*−∕±+=!√∛∜\-\|]',
            'Calculus': r'[∫∂Δ∇∬∭⨌∮∯∰∱⨑∲∳]|log|lim|ln',
            'Brackets': r'[\(\)\[\]\{\}\⟨⟩⦅⦆⟦⟧⟮⟯⟪⟫⟬⟭〈〉⌈⌉⌊⌋]', 
            'Equivalence': r'[≠≅≉∼≢≣≦≧≨≩≪≫≬≭≮≯≰≱≲≳≴≵≶≷≸≹≁≂≃≄≆≇≉≊≋≌]',
            'Logic': r'[∀∁∃∄∅¬˜∧∨⊻⊼⊽∩∪∈∉∊∋∌∍∖⊂⊃⊄⊅⊆⊇⊈⊉⊊⊋⋄⊌⊍⊎⋐⋑⋒⋓⋀⋁⋂⋃⋎⋏⨁⊕⊖⊗⊘⋲⋳⋴⋵⋶⋷⋸⋹⋺⋻⋼⋽⋾⋿]',
            'Statistics': r'[χ][^A-Za-z]|∑(?![A-Za-z])|∏(?![A-Za-z])|∐(?![A-Za-z])',
            'Letters': r'[∞]|(?<![A-Za-z])[ℵ℘ℑℜℝℂℕℙℚℤ](?![A-Za-z])',
            'Measurement': r'[°₹‰$]',
            'Geometric': r'[∟∠∡∢∣∤∥∦⊾⊿⊥⟂⊢⊣⊤]',
            'Arrows': r'[¯→←↑↓↔↕⇌⇄⇆⇇⇉⇊⇒⇔⇑⇓⟶⟵⟷⟸⟹⟺↞↠↢↣↦↤↼⇀⇁↽⇋⇍⇏⇖⇗⇘⇙⇜⇝⇪]',
            'Superscript': r'[⁰¹²³⁴⁵⁶⁷⁸⁹ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᵛʷˣʸᶻᴬᴮᶜᴰᴱᶠᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾᴿˢᵀᵁⱽᵂˣʸᶻ^]',
            'Subscript': r'[_₀₁₂₃₄₅₆₇₈₉ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ]',
            'Fraction': r'[/½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞⅟]',
            'Trigonometry': r'sin|cos|tan|cosec|sec|cot|arcsin|arccos|arctan|sinh|cosh|tanh',
            'Matrix':  r'matrix|det|determinant',
            'Misc': r'[,⋅∓·∔∗∘∙∝∶∷∸∹∺∻∼∽∾∿≀≍≎≏≐≑≒≓≔≕≖≗≘≙≚≛≜≝≞≟≺≻≼≽≾≿⊀⊁□⊏⊐⊑⊒⊓⊔⊙⊚⊛⊜⊝⊞⊟⊠⊪⊦⊧⊨⊩⊪⊫⊬⊭⊮⊯⊰⊱⊲⊳⊴⊵⊶⊷⊸⊹⊺⋅⋆⋇⋈⋉⋊⋋⋌⋍⋎⋏⋐⋑⋒⋓⋔⋕⋖⋗⋘⋙⋚⋛⋜⋝⋞⋟⋠⋡⋢⋣⋤⋥⋦⋧⋨⋩⋪⋫⋬⋭⋮⋯…⋰⋱∴∵∎ƒ′″‴]'
        }   


    def validate_bit_vector(self, bit_vector: str) -> bool:
        """Validate that a bit vector has the correct length and format."""
        if not bit_vector:
            return False
        if len(bit_vector) != len(self.categories):
            return False
        if not all(bit in '01' for bit in bit_vector):
            return False
        return True

    def generate_bit_vector(self, expression: str, has_mfrac: bool = False, has_msubsup: bool = False, 
                          has_msup: bool = False, has_msub: bool = False,has_mtable:bool=False,has_mover:bool=False,has_munder:bool=False,has_munderover:bool=False,has_msqrt:bool=False,has_mroot:bool=False,has_mfenced:bool=False ) -> str:

        # Initialize bit vector
        bits = [0] * len(self.categories)
        
        # Clean expression
        cleaned_expression = ' '.join(expression.split())
        
        # Check each category
        for i, (category, pattern) in enumerate(self.categories.items()):
            # Handle structural elements from MathML
            if category == 'Superscript' and (has_msubsup or has_msup or has_munderover or has_mover):
                bits[i] = 1
            elif category == 'Subscript' and (has_msubsup or has_msub or has_munderover or has_munder):
                bits[i] = 1
            elif category == 'Fraction' and has_mfrac:
                bits[i] = 1
            elif category == 'Matrix' and has_mtable:
                bits[i] = 1
            elif category == 'Brackets' and has_mfenced:
                bits[i] = 1
            elif category == 'Arithmatic' and (has_msqrt or has_mroot):
                bits[i] = 1
            elif category == 'Logic' and (re.search(pattern, cleaned_expression, re.UNICODE | re.IGNORECASE) or 
                    '⨁' in cleaned_expression):
                bits[i] = 1
            # Check for pattern matches in the expression
            elif re.search(pattern, cleaned_expression, re.UNICODE | re.IGNORECASE):
                bits[i] = 1
        
        # Convert to binary string
        bit_vector = ''.join(str(bit) for bit in bits)
        
        # Validate before returning
        return bit_vector if self.validate_bit_vector(bit_vector) else ''


def get_mathml_content(math_tag) -> str:
    """
    Extract pure content from MathML, ignoring annotation elements.
    
    Args:
        math_tag: BeautifulSoup tag containing MathML content
        
    Returns:
        str: Pure MathML content without annotations
    """
    # Remove all annotation elements first
    for annotation in math_tag.find_all(['annotation', 'annotation-xml']):
        annotation.decompose()
    

    # Extract text content from remaining elements
    content = []
    for element in math_tag.find_all(True):  # True finds all elements
        if element.name not in ['math', 'semantics']:  # Skip container elements
            if element.string and element.string.strip():
                content.append(element.string.strip())
    
    return ' '.join(content)

def check_mathml_structures(math_tag) -> Tuple[bool, bool, bool,bool, bool, bool, bool, bool,bool,bool,bool] :
    """
    Check for specific MathML structural elements.
    
    Returns:
        Tuple containing:
        - has_mfrac (bool)
        - has_msubsup (bool)
        - has_msup (bool)
        - has_msub (bool)
        - has_mtable (bool)
        - has_mover (bool)
        - has_msqrt (bool)

    """
    has_mfrac = bool(math_tag.find('mfrac'))
    has_msubsup = bool(math_tag.find('msubsup'))
    has_msup = bool(math_tag.find('msup'))
    has_msub = bool(math_tag.find('msub'))
    has_mtable = bool(math_tag.find('mtable'))
    has_mover = bool(math_tag.find('mover'))
    has_munder = bool(math_tag.find('munder'))
    has_munderover = bool(math_tag.find('munderover'))
    has_msqrt = bool(math_tag.find('msqrt'))
    has_mroot = bool(math_tag.find('mroot'))
    has_mfenced = bool(math_tag.find('mfenced'))
    
    
    
    return has_mfrac, has_msubsup, has_msup, has_msub, has_mtable, has_mover,has_munder,has_munderover, has_msqrt,has_mroot,has_mfenced


def analyze_single_mathml(mathml_string: str, symbol_table: MathSymbolBitVector) -> Tuple[str, str]:
    """
    Analyze a MathML string and return its bit vector and LaTeX representation.
    Only uses MathML content for bit vector generation.
    
    Args:
        mathml_string: The MathML string to analyze
        symbol_table: Instance of MathSymbolBitVector
        
    Returns:
        Tuple[str, str]: (bit_vector, latex)
    """
    try:
        soup = BeautifulSoup(mathml_string, 'lxml-xml')
        math_tag = soup.find('math')
        
        if math_tag:
            # Get pure MathML content without annotations
            expression = get_mathml_content(math_tag)
            latex = extract_latex_from_mathml(mathml_string)
            
            # Check for MathML structural elements
            structures = check_mathml_structures(math_tag)
            has_mfrac, has_msubsup, has_msup, has_msub, has_mtable, has_mover,has_munder,has_munderover, has_msqrt,has_mroot,has_mfenced= structures
           
            if expression:
                bit_vector = symbol_table.generate_bit_vector(
                    expression,
                    has_mfrac=has_mfrac,
                    has_msubsup=has_msubsup,
                    has_msup=has_msup,
                    has_msub=has_msub,
                    has_mtable=has_mtable,
                    has_mover=has_mover,
                    has_munder=has_munder,
                    has_munderover=has_munderover,
                    has_msqrt=has_msqrt,
                    has_mroot=has_mroot,
                    has_mfenced=has_mfenced,
                )
                
                if bit_vector:
                    return bit_vector, latex
        
        return '', ''
        
    except Exception as e:
        print(f"Error in analyze_single_mathml: {str(e)}")
        return '', ''

def extract_latex_from_mathml(mathml: str) -> str:
    """Extract LaTeX from MathML with robust annotation handling."""
    try:
        soup = BeautifulSoup(mathml, 'lxml-xml')
        
        # Try different annotation types in order of preference
        annotations = [
            {'encoding': 'application/x-tex'},
            {'encoding': 'text/x-tex'},
            {'encoding': 'TeX'},
            {'encoding': 'text/tex'},
            {}  # Try any annotation as last resort
        ]
        
        for annotation_attrs in annotations:
            annotation = soup.find('annotation', annotation_attrs)
            if annotation and annotation.string:
                latex = annotation.string.strip()
                if latex:
                    return latex
        
        # If no annotation found, try to get content from semantics tag
        semantics = soup.find('semantics')
        if semantics:
            content = ' '.join(semantics.stripped_strings)
            if content:
                return content
                
        # Last resort: get all text content from math tag
        math_tag = soup.find('math')
        if math_tag:
            return ' '.join(math_tag.stripped_strings)
            
        return ""
    except Exception as e:
        print(f"Error in LaTeX extraction: {str(e)}")
        return ""


class FileProcessingTracker:
    def __init__(self, base_dir: str = "processing_tracker"):
        self.base_dir = base_dir
        self.processed_files_path = os.path.join(base_dir, "processed_files.pkl")
        self.initialize_tracker()

    def initialize_tracker(self):
        """Create necessary directory and files if they don't exist"""
        os.makedirs(self.base_dir, exist_ok=True)
        if not os.path.exists(self.processed_files_path):
            self.save_processed_files(set())

    def load_processed_files(self) -> set:
        """Load the set of previously processed files"""
        try:
            if os.path.exists(self.processed_files_path):
                with open(self.processed_files_path, 'rb') as f:
                    return pickle.load(f)
            return set()
        except Exception as e:
            print(f"Error loading processed files list: {str(e)}")
            return set()

    def save_processed_files(self, processed_files: set):
        """Save the set of processed files using absolute paths"""
        try:
            # Convert all paths to absolute paths before saving
            absolute_paths = {os.path.abspath(path) for path in processed_files}
            with open(self.processed_files_path, 'wb') as f:
                pickle.dump(absolute_paths, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            print(f"Error saving processed files list: {str(e)}")

    def mark_file_processed(self, file_path: str):
        """Mark a single file as processed using absolute path"""
        processed_files = self.load_processed_files()
        processed_files.add(os.path.abspath(file_path))
        self.save_processed_files(processed_files)

    def mark_batch_processed(self, file_paths: list):
        """Mark a batch of files as processed using absolute paths"""
        processed_files = self.load_processed_files()
        processed_files.update(os.path.abspath(path) for path in file_paths)
        self.save_processed_files(processed_files)

    def is_file_processed(self, file_path: str) -> bool:
        """Check if a file has been processed using absolute path"""
        return os.path.abspath(file_path) in self.load_processed_files()

    def get_unprocessed_files(self, all_files: list) -> list:
        """Get list of files that haven't been processed yet using absolute paths"""
        processed_files = self.load_processed_files()
        return [f for f in all_files if os.path.abspath(f) not in processed_files]

    # def clear_tracking_data(self):
    #     """Clear all tracking data"""
    #     if os.path.exists(self.processed_files_path):
    #         os.remove(self.processed_files_path)
    #     self.initialize_tracker()


class ProcessingStats:
    def __init__(self):
        self.start_time = time.time()
        self.last_update = self.start_time
        self.total_files = 0
        self.processed_files = 0
        # self.indexed_files = 0
        self.current_batch = 0
        self.paused = False
        self.pause_start_time = None
        self.total_pause_time = 0
        
    def update_progress(self, files_processed: int, batch_num: int):
        current_time = time.time()
        self.processed_files += files_processed
        self.current_batch = batch_num
        
        # Calculate processing speed and estimated time remaining
        elapsed_time = current_time - self.start_time - self.total_pause_time
        files_per_second = self.processed_files / elapsed_time if elapsed_time > 0 else 0
        
        # Only update every 2 seconds to avoid console spam
        if current_time - self.last_update >= 2:
            self.print_progress(files_per_second)
            self.last_update = current_time
    
    def print_progress(self, files_per_second: float):
        status = "PAUSED" if self.paused else "RUNNING"
        print(f"\n{'='*50}")
        print(f"Progress Report at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {status}")
        print(f"{'='*50}")
        print(f"Current Batch: {self.current_batch}")
        print(f"Files Processed: {self.processed_files}")
        # print(f"Files Indexed: {self.indexed_files}")
        print(f"Processing Speed: {files_per_second:.2f} files/second")
        effective_time = time.time() - self.start_time - self.total_pause_time
        print(f"Effective Processing Time: {effective_time:.2f} seconds")
        if self.total_pause_time > 0:
            print(f"Total Pause Time: {self.total_pause_time:.2f} seconds")
        print(f"{'='*50}\n")

    def pause(self):
        if not self.paused:
            self.paused = True
            self.pause_start_time = time.time()
            print("\nProcessing PAUSED - Press Ctrl+C again to resume")
            
    def resume(self):
        if self.paused:
            self.paused = False
            pause_duration = time.time() - self.pause_start_time
            self.total_pause_time += pause_duration
            print(f"\nProcessing RESUMED after {pause_duration:.2f} seconds")
            self.pause_start_time = None


import traceback
def save_preprocessed_data(preprocessed_output, output_file="preprocessed_data.pkl"):
    """Save the preprocessed data to a file"""
    import pickle
    import os
    
    try:
        # Create a temporary file first to avoid corrupting the main file
        temp_file = f"{output_file}.temp"
        with open(temp_file, 'wb') as f:
            pickle.dump(preprocessed_output, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        # If the temporary file was created successfully, replace the main file
        if os.path.exists(temp_file):
            if os.path.exists(output_file):
                os.replace(temp_file, output_file)
            else:
                os.rename(temp_file, output_file)
                
        print(f"Preprocessed data saved to {output_file}")
        return True
    except Exception as e:
        print(f"Error saving preprocessed data: {str(e)}")
        return False


def load_preprocessed_data(input_file="preprocessed_data.pkl"):
    """Load the preprocessed data from a file"""
    import pickle
    try:
        with open(input_file, 'rb') as f:
            data = pickle.load(f)
        print(f"Preprocessed data loaded from {input_file}")
        return data
    except Exception as e:
        print(f"Error loading preprocessed data: {str(e)}")
        return {}




def process_html_file(file_path: str, symbol_table) -> Dict[str, List[Dict[str, str]]]:
    """Process a single HTML file to extract MathML expressions"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_doc = f.read()
    except FileNotFoundError:
        print(f"Input file '{file_path}' not found.")
        return {}

    soup = BeautifulSoup(html_doc, 'lxml')
    mathml_expressions = soup.find_all('math')

    math_list = []
    for mathml in mathml_expressions:
        bit_vector, latex = analyze_single_mathml(str(mathml), symbol_table)
        if bit_vector and latex:
            math_list.append({'bit_vector': bit_vector, 'latex': latex})

    return {file_path: math_list}


def preprocess_dataset(folder_path: str, symbol_table, batch_size=1000, tracker_base_dir="processing_tracker", 
                 save_frequency=20, output_file="preprocessed_data.pkl"):
    """
    Preprocesses the entire dataset and organizes results by bitvector and latex.
    Automatically saves data every 'save_frequency' batches and on interruption.
    
    Returns:
    preprocessed_output = {
        bitvector1: {
            latex1: [directory1, directory2, ...],
            latex2: [directory1, directory2, ...],
            ...
        },
        bitvector2: {
            ...
        },
        ...
    }
    """
    # Initialize structures
    preprocessed_output = defaultdict(lambda: defaultdict(list))
    stats = ProcessingStats()
    file_tracker = FileProcessingTracker(base_dir=tracker_base_dir)
    
    # Load previously saved data if exists
    if os.path.exists(output_file):
        try:
            with open(output_file, 'rb') as f:
                saved_data = pickle.load(f)
                # Convert regular dict to defaultdict of defaultdicts
                for bit_vector, latex_dict in saved_data.items():
                    for latex, paths in latex_dict.items():
                        preprocessed_output[bit_vector][latex].extend(paths)
                print(f"Loaded existing preprocessed data from {output_file}")
        except Exception as e:
            print(f"Error loading previous preprocessed data: {str(e)}")
            # Create a backup of the potentially corrupted file
            if os.path.exists(output_file):
                backup_file = f"{output_file}.bak.{int(time.time())}"
                try:
                    shutil.copy2(output_file, backup_file)
                    print(f"Created backup of possibly corrupted data file: {backup_file}")
                except Exception as be:
                    print(f"Failed to create backup: {str(be)}")
    
    # Control variables
    last_interrupt_time = 0
    QUIT_THRESHOLD = 2
    should_quit = False
    
    # Get list of all HTML files
    try:
        all_files = []
        for root, _, files in os.walk(folder_path):
            all_files.extend([
                os.path.join(root, f) 
                for f in files 
                if f.endswith('.html')
            ])
    except Exception as e:
        print(f"Error scanning folder {folder_path}: {str(e)}")
        return preprocessed_output
    
    if not all_files:
        print(f"No HTML files found in {folder_path}")
        return preprocessed_output
    
    # Get only unprocessed files
    files_to_process = file_tracker.get_unprocessed_files(all_files)
    stats.total_files = len(all_files)
    
    if not files_to_process:
        print("All files have already been processed.")
        # Always save the data before returning, even if no new files were processed
        save_preprocessed_data(dict(preprocessed_output), output_file)
        return preprocessed_output
    
    print(f"Found {len(files_to_process)} unprocessed files out of {len(all_files)} total files")
    print("Press Ctrl+C once to pause/resume processing")
    print("Press Ctrl+C twice within 2 seconds to quit")
    
    def save_current_state(force_save=False):
        """Helper function to save the current state of preprocessed data"""
        try:
            print(f"\nSaving preprocessed data to {output_file}...")
            # Create a temporary file first to avoid corrupting the main file
            temp_file = f"{output_file}.temp"
            with open(temp_file, 'wb') as f:
                pickle.dump(dict(preprocessed_output), f, protocol=pickle.HIGHEST_PROTOCOL)
            
            # If the temporary file was created successfully, replace the main file
            if os.path.exists(temp_file):
                if os.path.exists(output_file):
                    os.replace(temp_file, output_file)
                else:
                    os.rename(temp_file, output_file)
                    
            print(f"Data saved successfully at batch {stats.current_batch}")
            return True
        except Exception as e:
            print(f"Error saving preprocessed data: {str(e)}")
            return False
    
    def signal_handler(signum, frame):
        nonlocal last_interrupt_time, should_quit
        current_time = time.time()
        
        if current_time - last_interrupt_time < QUIT_THRESHOLD:
            print("\nDouble Ctrl+C detected. Quitting program...")
            should_quit = True
            # Force save current state before quitting
            save_current_state(force_save=True)
            if stats.paused:
                stats.resume()
        else:
            if stats.paused:
                stats.resume()
            else:
                stats.pause()
                # Save current state when paused
                save_current_state(force_save=True)
        
        last_interrupt_time = current_time
    
    import signal
    signal.signal(signal.SIGINT, signal_handler)
    
    # Process files in batches
    try:
        batch_files = []
        batch_count = 0
        batch_results = []
        
        for file_idx, file_path in enumerate(files_to_process):
            if should_quit:
                print("Processing terminated by user")
                # Make sure to save data even if quitting early
                save_current_state(force_save=True)
                break
                
            while stats.paused and not should_quit:
                time.sleep(1)
                continue
                
            try:
                result = process_html_file(file_path, symbol_table)
                
                if result:
                    batch_results.append(result)
                    batch_files.append(file_path)
                    
                    # Process batch if it reaches the batch size
                    if len(batch_files) >= batch_size:
                        batch_count += 1
                        print(f"\nProcessing batch {batch_count}...")
                        
                        # Organize results by bitvector and latex
                        for file_result in batch_results:
                            for file_path, math_expressions in file_result.items():
                                for expr in math_expressions:
                                    bit_vector = expr['bit_vector']
                                    latex = expr['latex']
                                    # Update the overall output
                                    preprocessed_output[bit_vector][latex].append(file_path)
                        
                        # Mark batch as processed
                        file_tracker.mark_batch_processed(batch_files)
                        
                        stats.update_progress(
                            files_processed=len(batch_files),
                            batch_num=batch_count
                        )
                        
                        # Check if we should save based on batch frequency
                        if batch_count % save_frequency == 0:
                            save_current_state()
                        
                        # Reset batch
                        batch_files = []
                        batch_results = []
                        
            except Exception as e:
                print(f"Error processing file {file_path}: {str(e)}")
                traceback.print_exc()
                continue
            
            # Save periodically based on file count too (as a backup mechanism)
            # This ensures we save even if batch_size is very large
            if (file_idx + 1) % (batch_size * save_frequency) == 0 and batch_count % save_frequency != 0:
                save_current_state()
        
        # Process remaining files if any exist (even if quitting)
        if batch_files:
            batch_count += 1
            print(f"\nProcessing final batch {batch_count}...")
            
            # Organize results for the final batch
            for file_result in batch_results:
                for file_path, math_expressions in file_result.items():
                    for expr in math_expressions:
                        bit_vector = expr['bit_vector']
                        latex = expr['latex']
                        # Update the overall output
                        preprocessed_output[bit_vector][latex].append(file_path)
            
            # Mark remaining batch as processed
            file_tracker.mark_batch_processed(batch_files)
            
            stats.update_progress(
                files_processed=len(batch_files),
                batch_num=batch_count
            )
            
            # Always save at the end if we've processed additional files
            save_current_state(force_save=True)
    
    except Exception as e:
        print(f"Unexpected error in main processing loop: {str(e)}")
        traceback.print_exc()
        # Try to save what we have
        save_current_state(force_save=True)
    
    finally:
        signal.signal(signal.SIGINT, signal.default_int_handler)
        
        # Always save in the finally block, regardless of should_quit status
        save_current_state(force_save=True)
        
        if should_quit:
            print("\nFinal status before quitting:")
            files_per_second = stats.processed_files / (time.time() - stats.start_time - stats.total_pause_time) if (time.time() - stats.start_time - stats.total_pause_time) > 0 else 0
            stats.print_progress(files_per_second)
    
    print(f"Preprocessing completed. Processed {stats.processed_files} files.")
    
    # Use the external save function to ensure the data is saved before returning
    save_preprocessed_data(dict(preprocessed_output), output_file)
    
    return dict(preprocessed_output)  # Convert defaultdict to regular dict


