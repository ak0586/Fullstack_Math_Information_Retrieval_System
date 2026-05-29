import os
import re
import time
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple, Any
from .database import MIRDatabase

def map_to_b2_key(filepath: str) -> str:
    """Normalize local filepaths or B2 keys into clean, platform-independent B2 keys."""
    norm_path = filepath.replace('\\', '/')
    filename = norm_path.split('/')[-1]
    if 'TextArticles' in norm_path:
        return f"TextArticles/{filename}"
    elif 'MathTagArticles' in norm_path:
        parts = norm_path.split('MathTagArticles/')
        if len(parts) > 1:
            return "MathTagArticles/" + parts[1]
    return norm_path

class MathSymbolBitVector:
    def __init__(self):
         self.categories = {
            'Numerals': r'[0123456789𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳⓪①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶٧٨٩᠐᠑᠒᠓᠔᠕᠖᠗᠘᠙০১২৩৪৫৬৭৮৯०१२३४५६७८९𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫]',
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
            'Arrows': r'[¯→←↑↓↔↕⇌⇄⇆⇇⇉⇊⇒⇔⇑⇓⟶⟵⟷⟸⟹⟺↞↠↢↣↦↤↼⇀⇁↽⇋⇋⇍⇏⇖⇗⇘⇙⇜⇝⇪]',
            'Superscript': r'[⁰¹²³⁴⁵⁶⁷⁸⁹ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᵛʷˣʸᶻᴬᴮᶜᴰᴱᶠᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾ𝑅ˢᵀᵁⱽᵂˣʸᶻ^]',
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
            elif re.search(pattern, cleaned_expression, re.UNICODE | re.IGNORECASE):
                bits[i] = 1
        
        bit_vector = ''.join(str(bit) for bit in bits)
        return bit_vector if self.validate_bit_vector(bit_vector) else ''


def get_mathml_content(math_tag) -> str:
    """Extract pure content from MathML, ignoring annotation elements."""
    for annotation in math_tag.find_all(['annotation', 'annotation-xml']):
        annotation.decompose()
    content = []
    for element in math_tag.find_all(True):
        if element.name not in ['math', 'semantics']:
            if element.string and element.string.strip():
                content.append(element.string.strip())
    return ' '.join(content)

def check_mathml_structures(math_tag) -> Tuple[bool, bool, bool,bool, bool, bool, bool, bool,bool,bool,bool] :
    """Check for specific MathML structural elements."""
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
    Optimized to parse the MathML XML exactly once.
    """
    try:
        soup = BeautifulSoup(mathml_string, 'lxml-xml')
        math_tag = soup.find('math')
        
        if math_tag:
            # 1. Extract LaTeX using the existing parsed soup
            latex = ""
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
                        break
            
            if not latex:
                semantics = soup.find('semantics')
                if semantics:
                    latex = ' '.join(semantics.stripped_strings)
            
            if not latex:
                latex = ' '.join(math_tag.stripped_strings)

            # 2. Get pure MathML content without annotations
            for annotation in math_tag.find_all(['annotation', 'annotation-xml']):
                annotation.decompose()
                
            content = []
            for element in math_tag.find_all(True):
                if element.name not in ['math', 'semantics']:
                    if element.string and element.string.strip():
                        content.append(element.string.strip())
            expression = ' '.join(content)
            
            # Check structures
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


def analyze_single_mathml_tag(math_tag, symbol_table: MathSymbolBitVector) -> Tuple[str, str]:
    """
    Analyze a parsed MathML BeautifulSoup Tag object and return its bit vector and LaTeX representation.
    Avoids re-parsing the MathML element, yielding substantial performance gains.
    """
    try:
        if math_tag:
            # 1. Extract LaTeX
            latex = ""
            annotations = [
                {'encoding': 'application/x-tex'},
                {'encoding': 'text/x-tex'},
                {'encoding': 'TeX'},
                {'encoding': 'text/tex'},
                {}  # Try any annotation as last resort
            ]
            
            for annotation_attrs in annotations:
                annotation = math_tag.find('annotation', annotation_attrs)
                if annotation and annotation.string:
                    latex = annotation.string.strip()
                    if latex:
                        break
            
            if not latex:
                semantics = math_tag.find('semantics')
                if semantics:
                    latex = ' '.join(semantics.stripped_strings)
            
            if not latex:
                latex = ' '.join(math_tag.stripped_strings)

            # 2. Get pure MathML content without annotations
            for annotation in math_tag.find_all(['annotation', 'annotation-xml']):
                annotation.decompose()
                
            content = []
            for element in math_tag.find_all(True):
                if element.name not in ['math', 'semantics']:
                    if element.string and element.string.strip():
                        content.append(element.string.strip())
            expression = ' '.join(content)
            
            # Check structures
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
        print(f"Error in analyze_single_mathml_tag: {str(e)}")
        return '', ''


class FileProcessingTracker:
    def __init__(self, db: MIRDatabase):
        self.db = db

    def load_processed_files(self) -> set:
        return self.db.get_unprocessed_files([]) # Dummy call or query

    def mark_file_processed(self, file_path: str):
        self.db.mark_file_processed(file_path)

    def mark_batch_processed(self, file_paths: list):
        self.db.mark_batch_processed(file_paths)

    def is_file_processed(self, file_path: str) -> bool:
        return self.db.is_file_processed(file_path)

    def get_unprocessed_files(self, all_files: list) -> list:
        # Load processed B2 keys from the database
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT filepath FROM processed_files")
        processed = {row[0] for row in cursor.fetchall()}
        conn.close()
        
        # Filter all_files by mapping their local path to B2 keys
        unprocessed = []
        for f in all_files:
            b2_key = map_to_b2_key(f)
            if b2_key not in processed:
                unprocessed.append(f)
        return unprocessed


class ProcessingStats:
    def __init__(self):
        self.start_time = time.time()
        self.last_update = self.start_time
        self.total_files = 0
        self.processed_files = 0
        self.current_batch = 0
        self.paused = False
        self.pause_start_time = None
        self.total_pause_time = 0
        
    def update_progress(self, files_processed: int, batch_num: int):
        current_time = time.time()
        self.processed_files += files_processed
        self.current_batch = batch_num
        
        elapsed_time = current_time - self.start_time - self.total_pause_time
        files_per_second = self.processed_files / elapsed_time if elapsed_time > 0 else 0
        
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



def process_html_file_worker(args) -> Optional[Tuple[str, List[Dict[str, str]]]]:
    """Worker function to process a single HTML file in a process pool."""
    file_path, categories = args
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_doc = f.read()
    except Exception:
        return None

    # Fast regex filter
    if '<math' not in html_doc:
        return None

    soup = BeautifulSoup(html_doc, 'lxml')
    mathml_expressions = soup.find_all('math')
    if not mathml_expressions:
        return None

    symbol_table = MathSymbolBitVector()
    symbol_table.categories = categories

    math_list = []
    for mathml in mathml_expressions:
        bit_vector, latex = analyze_single_mathml_tag(mathml, symbol_table)
        if bit_vector and latex:
            math_list.append({'bit_vector': bit_vector, 'latex': latex})

    if not math_list:
        return None

    return (file_path, math_list)


def process_html_file(file_path: str, symbol_table) -> Dict[str, List[Dict[str, str]]]:
    """Process a single HTML file (compatibility)"""
    res = process_html_file_worker((file_path, symbol_table.categories))
    if res:
        return {res[0]: res[1]}
    return {}


def preprocess_dataset(folder_path: str, symbol_table, batch_size=1000, tracker_base_dir="math_index_storage", 
                 save_frequency=20, output_file="math_index_storage/clusters/math_index.db"):
    """
    Preprocesses the entire dataset, writing results directly to the SQLite database.
    Replaces pickle files completely.
    """
    # Ensure database folder exists
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    db = MIRDatabase(output_file)
    
    stats = ProcessingStats()
    file_tracker = FileProcessingTracker(db)
    
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
        return {}
    
    if not all_files:
        print(f"No HTML files found in {folder_path}")
        return {}
    
    # Get only unprocessed files
    files_to_process = file_tracker.get_unprocessed_files(all_files)
    stats.total_files = len(all_files)
    
    if not files_to_process:
        print("All files have already been processed.")
        return {}
    
    print(f"Found {len(files_to_process)} unprocessed files out of {len(all_files)} total files")
    print("Press Ctrl+C once to pause/resume processing")
    print("Press Ctrl+C twice within 2 seconds to quit")
    
    def signal_handler(signum, frame):
        nonlocal last_interrupt_time, should_quit
        current_time = time.time()
        
        if current_time - last_interrupt_time < QUIT_THRESHOLD:
            print("\nDouble Ctrl+C detected. Quitting program...")
            should_quit = True
            if stats.paused:
                stats.resume()
        else:
            if stats.paused:
                stats.resume()
            else:
                stats.pause()
        
        last_interrupt_time = current_time
    
    import signal
    signal.signal(signal.SIGINT, signal_handler)
    
    # Process files in parallel batches
    try:
        from concurrent.futures import ProcessPoolExecutor
        import multiprocessing
        
        num_workers = multiprocessing.cpu_count()
        categories = symbol_table.categories
        worker_args = [(f, categories) for f in files_to_process]
        
        print(f"Starting parallel preprocessing with {num_workers} workers...")
        
        batch_files = []
        batch_count = 0
        
        chunk_size = batch_size
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            for i in range(0, len(worker_args), chunk_size):
                if should_quit:
                    break
                    
                while stats.paused and not should_quit:
                    time.sleep(1)
                    continue
                    
                chunk = worker_args[i:i+chunk_size]
                chunk_files = [args[0] for args in chunk]
                
                # Execute chunk in parallel
                futures_results = list(executor.map(process_html_file_worker, chunk, chunksize=50))
                
                # Process results of the chunk
                batch_expressions = []
                for res in futures_results:
                    if res:
                        file_path, math_list = res
                        b2_key_path = map_to_b2_key(file_path)
                        for expr in math_list:
                            batch_expressions.append((expr['bit_vector'], expr['latex'], b2_key_path))
                
                # Insert directly to SQLite in a batch
                db.insert_math_expressions(batch_expressions)
                
                batch_count += 1
                print(f"\nCompleted parallel batch {batch_count}...")
                
                # Mark chunk files as processed
                mapped_chunk_files = [map_to_b2_key(fp) for fp in chunk_files]
                file_tracker.mark_batch_processed(mapped_chunk_files)
                
                stats.update_progress(
                    files_processed=len(chunk_files),
                    batch_num=batch_count
                )
                
    except Exception as e:
        print(f"Unexpected error in main processing loop: {str(e)}")
        traceback.print_exc()
    
    finally:
        signal.signal(signal.SIGINT, signal.default_int_handler)
        
        if should_quit:
            print("\nFinal status before quitting:")
            files_per_second = stats.processed_files / (time.time() - stats.start_time - stats.total_pause_time) if (time.time() - stats.start_time - stats.total_pause_time) > 0 else 0
            stats.print_progress(files_per_second)
            
    print(f"Preprocessing completed. Processed {stats.processed_files} files.")
    return {}


def process_b2_html_worker(args):
    """
    Worker function to fetch and process a single HTML file from B2.
    """
    key, bucket_name, categories, b2_config = args
    try:
        import boto3
        # Create a thread-safe S3 client for this worker
        s3_client = boto3.client(
            service_name='s3',
            endpoint_url=b2_config['endpoint_url'],
            aws_access_key_id=b2_config['key_id'],
            aws_secret_access_key=b2_config['application_key']
        )
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        html_doc = response['Body'].read().decode('utf-8')
    except Exception as e:
        print(f"Error downloading {key} from B2: {e}")
        return None

    # Fast regex filter
    if '<math' not in html_doc:
        return None

    try:
        soup = BeautifulSoup(html_doc, 'lxml')
        mathml_expressions = soup.find_all('math')
        if not mathml_expressions:
            return None

        symbol_table = MathSymbolBitVector()
        symbol_table.categories = categories

        math_list = []
        for mathml in mathml_expressions:
            bit_vector, latex = analyze_single_mathml(str(mathml), symbol_table)
            if bit_vector and latex:
                math_list.append({'bit_vector': bit_vector, 'latex': latex})

        if not math_list:
            return None

        return (key, math_list)
    except Exception as e:
        print(f"Error parsing HTML {key}: {e}")
        return None


def preprocess_dataset_from_b2(bucket_name: str, symbol_table, batch_size=1000, 
                               output_file="math_index_storage/clusters/math_index.db",
                               key_id=None, application_key=None, endpoint_url=None,
                               max_files: Optional[int] = None):
    """
    Indexes files directly from a Backblaze B2 bucket, streaming the content in parallel,
    and writing directly to SQLite.
    """
    import boto3
    from concurrent.futures import ThreadPoolExecutor
    
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    db = MIRDatabase(output_file)
    file_tracker = FileProcessingTracker(db)
    
    b2_config = {
        'key_id': key_id or os.getenv("B2_KEY_ID", "003844e190e34440000000001"),
        'application_key': application_key or os.getenv("B2_APPLICATION_KEY", "K003fxzRvi25Fxd3sroe9uC0EC6QNlI"),
        'endpoint_url': endpoint_url or os.getenv("B2_ENDPOINT_URL", "https://s3.eu-central-003.backblazeb2.com")
    }
    
    print(f"Connecting to Backblaze B2 bucket '{bucket_name}'...")
    try:
        s3_client = boto3.client(
            service_name='s3',
            endpoint_url=b2_config['endpoint_url'],
            aws_access_key_id=b2_config['key_id'],
            aws_secret_access_key=b2_config['application_key']
        )
    except Exception as e:
        print(f"Failed to create S3 client: {e}")
        return {}
 
    print("Listing files in B2 bucket (this may take a few minutes for large buckets)...")
    
    # Load processed files once to check fast in-memory
    processed_set = set()
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT filepath FROM processed_files")
        processed_set = {row[0] for row in cursor.fetchall()}
        conn.close()
    except Exception as e:
        print(f"Error loading processed files list: {e}")

    all_keys = []
    keys_to_process = []
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        should_break = False
        for page in paginator.paginate(Bucket=bucket_name):
            if should_break:
                break
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    if key.endswith('.html') and not (
                        '._' in key or '.DS_Store' in key or key.startswith('.')
                    ):
                        all_keys.append(key)
                        if os.path.abspath(key) not in processed_set:
                            keys_to_process.append(key)
                            if max_files is not None and len(keys_to_process) >= max_files:
                                should_break = True
                                break
    except Exception as e:
        print(f"Error listing bucket objects: {e}")
        return {}
        
    if not all_keys:
        print("No valid HTML files found in the B2 bucket.")
        return {}
 
    print(f"Found {len(all_keys)} valid HTML files in B2 bucket (listed so far).")
    
    stats = ProcessingStats()
    stats.total_files = len(all_keys)
    stats.processed_files = len(all_keys) - len(keys_to_process)
    
    if not keys_to_process:
        print("All files in B2 bucket have already been processed.")
        return {}
 
    print(f"Found {len(keys_to_process)} unprocessed files to index.")
    
    num_threads = min(32, os.cpu_count() * 4)
    print(f"Starting parallel cloud-native B2 indexing with {num_threads} threads...")
    
    categories = symbol_table.categories
    
    try:
        batch_count = 0
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for i in range(0, len(keys_to_process), batch_size):
                chunk_keys = keys_to_process[i:i+batch_size]
                worker_args = [(key, bucket_name, categories, b2_config) for key in chunk_keys]
                
                futures_results = list(executor.map(process_b2_html_worker, worker_args))
                
                batch_expressions = []
                for res in futures_results:
                    if res:
                        key, math_list = res
                        b2_key_path = map_to_b2_key(key)
                        for expr in math_list:
                            batch_expressions.append((expr['bit_vector'], expr['latex'], b2_key_path))
                
                db.insert_math_expressions(batch_expressions)
                mapped_chunk_keys = [map_to_b2_key(k) for k in chunk_keys]
                file_tracker.mark_batch_processed(mapped_chunk_keys)
                
                batch_count += 1
                stats.update_progress(
                    files_processed=len(chunk_keys),
                    batch_num=batch_count
                )
    except Exception as e:
        print(f"Unexpected error in B2 processing loop: {e}")
        traceback.print_exc()
        
    print(f"B2 Preprocessing completed. Processed {stats.processed_files} files.")
    return {}
