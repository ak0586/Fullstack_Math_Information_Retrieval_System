# Searhcing Module
from latex2mathml.converter import convert
import html
import re

class MathConverter:
    def __init__(self):
       pass
        
    def preprocess_latex(self,latex_input):
        """
        Preprocess LaTeX input to handle special cases, functions, and character replacements
        """
        # Fix function powers like \sin^2 x to {\sin}^2 x
        math_functions = ['sin', 'cos', 'tan', 'csc', 'sec', 'cot',
                       'log', 'ln', 'exp', 'lim', 'sup', 'inf']
        
        processed = latex_input
        
       
    
     
        processed = re.sub(r'\\mbox{\\boldmath\$(.*?)\$}', r'\\mathbf{\1}', processed)
        
        # Handle \bf{...} or {\bf ...} with \mathbf{...}
        processed = re.sub(r'\\bf{(.*?)}', r'\\mathbf{\1}', processed)
        processed = re.sub(r'{\\bf\s+(.*?)}', r'\\mathbf{\1}', processed)
        
        # Handle \boldmath{...} with \mathbf{...}
        processed = re.sub(r'\\boldmath{(.*?)}', r'\\mathbf{\1}', processed)
        
        # Replace two consecutive backslashes with a single backslash
        
        for func in math_functions:
            # Handle function with power
            pattern = f'\\\\{func}\\^(\\d+)'
            replacement = f'{{\\\\{func}}}^\\1'
            processed = re.sub(pattern, replacement, processed)
    
        char_replacements = {
            'Ï†': r'\phi',      # Sometimes appears as 'Ï†' in wrongly decoded text
            'Î³': r'\gamma',    # Sometimes appears as 'Î³' instead of 'γ'
            '\u03c6': r'\phi',  # Unicode φ
            '\u03b3': r'\gamma' # Unicode γ
        }
        
        for char, replacement in char_replacements.items():
            processed = processed.replace(char, replacement)
    
        # Remove %&#10; (commented newline) and replace &#10; with LaTeX newline \\
        processed = re.sub(r'%&#10;', '', processed)  # Remove %&#10;
        processed = re.sub(r'&#10;', r'\\\\', processed)  # Replace &#10; with \\ for LaTeX newline
    
        # Fix LaTeX array environment syntax
        processed = processed.replace(r'{array}[][c]', '{array}[l]')  # Change alignment to left
        processed = re.sub(r'\[\]\{.*?\}', '', processed)  # Remove empty []{} brackets
    
        html_chars = {
            r'\left&lt;':'⟨',
            r'\right&gt;':'⟩',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
        }
        
        for html_char, replacement in html_chars.items():
            processed = processed.replace(html_char, replacement)
    
        return processed
    
        
    def fix_function_in_mathml(self,mathml, func_name):
        """Helper function to fix a specific function in MathML"""
        # Create pattern for split letters (e.g., <mi>s</mi><mi>i</mi><mi>n</mi>)
        letters_pattern = ''.join([f'<mi>{letter}</mi>' for letter in func_name])
        
        # Pattern for function with power (e.g., <mi>s</mi><mi>i</mi><msup><mi>n</mi><mn>2</mn></msup>)
        power_pattern = ''.join([f'<mi>{letter}</mi>' for letter in func_name[:-1]]) + \
                       f'<msup><mi>{func_name[-1]}</mi>'
        
        # Replace patterns with correct function representation
        mathml = mathml.replace(letters_pattern, f'<mi mathvariant="normal">{func_name}</mi>')
        mathml = mathml.replace(power_pattern, 
                              f'<msup><mi mathvariant="normal">{func_name}</mi>')
        
        return mathml
        
    def enhance_mathml(self,mathml):
        """
        Enhance the converted MathML by fixing function representations
        """
        # List of functions to fix
        functions = ['sin', 'cos', 'tan', 'cot', 'sec', 'csc',
                'arcsin', 'arccos', 'arctan', 'sinh', 'cosh', 'tanh',
                'log', 'ln', 'exp', 'lim', 'sup', 'inf', 'max', 'min',
                'end','begin','vmatrix',]
        
        # Fix each function
        for func in functions:
            mathml = self.fix_function_in_mathml(mathml, func)
        
        return mathml
    
    def latex_to_mathml(self,latex_input):
        """
        Convert LaTeX to enhanced MathML
        
        Args:
            latex_input (str): LaTeX mathematical expression
        
        Returns:
            str: Enhanced MathML output
        """
        
        try:
            # First convert to MathML
            mathml = convert(latex_input)
            
            # Then enhance the output
            enhanced_mathml = self.enhance_mathml(mathml)
            
            return enhanced_mathml
            
        except Exception as e:
            return f"Error converting LaTeX: {str(e)}"

    def convert_to_mathml(self, input_string: str, input_type: str = 'latex') -> str:
        """
        Convert input string to MathML with improved support for LaTeX commands, symbols,
        and mathematical functions.
        
        Args:
            input_string: The input string to convert
            input_type: The type of input ('latex' or 'text')
        
        Returns:
            str: The converted MathML string
        """
        
        try:
            if input_type.lower() == 'text':
                input_string = self.convert_text_to_latex(input_string)
                print(f"Plain text Query latex: {input_string}")
                
            # Apply preprocessing with symbol replacements
            input_string = self.preprocess_latex(input_string)
            print(f"Preprocessed input: {input_string}")
            
            # Convert to MathML
            mathml_output = self.latex_to_mathml(input_string)
            
            # Clean up the MathML
            mathml_output = html.unescape(mathml_output)
            
            # Process mathematical functions to ensure proper MathML formatting
            
            return mathml_output
            
        except Exception as e:
            return f"An error occurred during MathML conversion: {str(e)}"
            
    def convert_text_to_latex(self, text_input: str) -> str:
        """
        Convert plain text to LaTeX.
        """
        replacements = [
            (r'(\d+|\w+)/(\d+|\w+)', r'\\frac{\1}{\2}'),
            (r'(\w)\^(\d+|\w+)', r'{{\1}}^{{\2}}'),
            (r'\s*=\s*', r' = '),
            (r'perp', r'\\perp'),
            (r'pi', r'\\pi'),
        ]

        for pattern, replacement in replacements:
            text_input = re.sub(pattern, replacement, text_input)

        return text_input

