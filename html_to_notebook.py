#!/usr/bin/python3
# html_to_notebook.py
"""
Convert HTML exported from Jupyter Notebook back to .ipynb format.

This script parses HTML files exported from JupyterLab and reconstructs
the original notebook structure with markdown and code cells.
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Callable

try:
    from bs4 import BeautifulSoup
    import nbformat
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Install with: pip install beautifulsoup4 nbformat")
    sys.exit(1)

def info_print(*args, **kwargs):
    """Print info messages to stderr"""
    print(*args, **kwargs, file=sys.stderr)

class NotebookConverter:
    """Converts HTML exported from Jupyter to .ipynb format."""
    
    def __init__(self, verbose=False):
        self.notebook_version = 4
        self.kernel_spec = {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        }
        self.verbose = verbose
        
    def html_to_notebook(self, html_paths: List[Union[str, Path]]) -> nbformat.NotebookNode:
        """
        Convert HTML file(s) to Jupyter notebook.
        
        Args:
            html_paths: List of paths to input HTML files
            
        Returns:
            Notebook object with all cells from input files
        """
        all_cells = []
        
        for html_path in html_paths:
            html_path = Path(html_path)
            if not html_path.exists():
                print(f"Warning: HTML file not found: {html_path}", file=sys.stderr)
                continue
                
            # Parse HTML and extract cells
            with open(html_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                
            cells = self._extract_cells(soup)
            all_cells.extend(cells)
            if self.verbose:
                info_print(f"Extracted {len(cells)} cells from {html_path}")
        
        notebook = self._create_notebook(all_cells)
        if self.verbose:
            info_print(f"Total: {len(all_cells)} cells")
        return notebook
    
    def _extract_cells(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract all cells from parsed HTML."""
        cells = []
        
        # Find all cell containers - updated selector for current JupyterLab
        # Try both old and new selectors for backward compatibility
        cell_divs = soup.find_all('div', class_=re.compile(r'jp-Cell.*jp-Notebook-cell'))
        
        if not cell_divs:
            # Try older selector format
            cell_divs = soup.find_all('div', class_=lambda x: x and 'jp-Cell' in x and 'jp-Notebook-cell' in x)
        
        if self.verbose:
            info_print(f"Found {len(cell_divs)} cell divs")
        
        for i, cell_div in enumerate(cell_divs):
            cell_classes = ' '.join(cell_div.get('class', []))
            
            if self.verbose:
                info_print(f"Cell {i}: classes = {cell_classes[:50]}...")
            
            if 'jp-MarkdownCell' in cell_classes:
                cell = self._extract_markdown_cell(cell_div)
            elif 'jp-CodeCell' in cell_classes:
                cell = self._extract_code_cell(cell_div)
            else:
                continue  # Skip other cell types
                
            if cell:  # Only add non-empty cells
                cells.append(cell)
                if self.verbose:
                    info_print(f"  Extracted {cell['cell_type']} cell")
                
        return cells
    
    def _extract_markdown_cell(self, cell_div) -> Optional[Dict]:
        """Extract markdown cell content."""
        # Find the rendered markdown content
        markdown_div = cell_div.find('div', class_='jp-RenderedMarkdown')
        if not markdown_div:
            if self.verbose:
                info_print("  No jp-RenderedMarkdown div found")
            return None
            
        # Convert HTML back to markdown
        markdown_source = self._html_to_markdown(markdown_div)
        
        # Remove paragraph symbols
        markdown_source = self._remove_paragraph_symbols(markdown_source)
        
        if not markdown_source.strip():
            return None
        
        # Split into lines and add newline to each (except possibly the last)
        lines = markdown_source.split('\n')
        source_lines = []
        for i, line in enumerate(lines):
            if i < len(lines) - 1:
                source_lines.append(line + '\n')
            else:
                # Last line might or might not have a newline
                if line:  # If there's content on the last line
                    source_lines.append(line)
                elif source_lines:  # If last line is empty but there are previous lines
                    # Add newline to previous line if it doesn't have one
                    if not source_lines[-1].endswith('\n'):
                        source_lines[-1] += '\n'
        
        return {
            'cell_type': 'markdown',
            'metadata': {},
            'source': source_lines  # List of strings with \n characters
        }
    
    def _extract_code_cell(self, cell_div) -> Optional[Dict]:
        """Extract code cell content."""
        # Try both new and old structures for backward compatibility
        code_container = None
        
        # Try new JupyterLab structure first
        code_container = cell_div.find('div', class_='jp-CodeMirrorEditor')
        
        # Fall back to older structure
        if not code_container:
            code_container = cell_div.find('div', class_='CodeMirror')
            
        if not code_container:
            if self.verbose:
                info_print("  No code container (jp-CodeMirrorEditor or CodeMirror) found")
            return None
            
        # Look for the highlighted code
        highlight_div = code_container.find('div', class_='highlight')
        if not highlight_div:
            if self.verbose:
                info_print("  No highlight div found")
            return None
            
        # Extract code from <pre> tag, removing HTML markup
        pre_tag = highlight_div.find('pre')
        if not pre_tag:
            if self.verbose:
                info_print("  No pre tag found")
            return None
            
        code_source = self._extract_code_from_html(pre_tag)
        
        # Remove paragraph symbols
        code_source = self._remove_paragraph_symbols(code_source)
        
        if not code_source.strip():
            return None
        
        # Split into lines and add newline to each (except possibly the last)
        lines = code_source.split('\n')
        source_lines = []
        for i, line in enumerate(lines):
            if i < len(lines) - 1:
                source_lines.append(line + '\n')
            else:
                # Last line might or might not have a newline
                if line:  # If there's content on the last line
                    source_lines.append(line + '\n')
                # If last line is empty, we don't add it
        
        # Look for execution count
        execution_count = None
        prompt_div = cell_div.find('div', class_='jp-InputPrompt')
        if prompt_div:
            prompt_text = prompt_div.get_text().strip()
            match = re.match(r'In\s*\[(\d+)\]:', prompt_text)
            if match:
                execution_count = int(match.group(1))
        
        return {
            'cell_type': 'code',
            'execution_count': execution_count,
            'metadata': {},
            'outputs': [],  # No outputs - will be regenerated
            'source': source_lines  # List of strings with \n characters
        }
    
    def _remove_paragraph_symbols(self, text: str) -> str:
        """Remove paragraph symbols (¶) from text."""
        # Remove all occurrences of the paragraph symbol
        text = text.replace('¶', '')
        
        # Also remove any trailing whitespace that might have been before the symbol
        lines = text.split('\n')
        lines = [line.rstrip() for line in lines]
        
        return '\n'.join(lines)
    
    def _html_to_markdown(self, element) -> str:
        """Convert HTML element back to markdown format."""
        if not element:
            return ""
        
        # Handle different HTML elements and convert to markdown
        result = []
        
        for child in element.children:
            if hasattr(child, 'name') and child.name is not None:  # It's a tag
                text = self._convert_html_tag_to_markdown(child)
                if text:
                    result.append(text)
            else:  # It's text
                text = str(child).strip()
                if text:
                    result.append(text)
        
        # Join and clean up
        markdown_text = ''.join(result)
        markdown_text = html.unescape(markdown_text)
        
        # Clean up excessive whitespace
        markdown_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', markdown_text)
        markdown_text = re.sub(r' +', ' ', markdown_text)
        
        return markdown_text.strip()
    
    def _convert_html_tag_to_markdown(self, tag) -> str:
        """Convert HTML tag to markdown equivalent."""
        if not tag.name:
            return str(tag)
            
        tag_name = tag.name.lower()
        
        # Handle headers separately since they need special processing
        if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            # For headers, look for and remove paragraph symbols
            text_content = tag.get_text()
            text_content = text_content.replace('¶', '').strip()
            prefix = '#' * int(tag_name[1])
            return f"{prefix} {text_content}\n"
        
        text_content = tag.get_text()
        
        # Define tag converters as a dictionary of functions
        def convert_strong():
            return f"**{text_content}**"
        
        def convert_em():
            return f"*{text_content}*"
        
        def convert_code():
            return f"`{text_content}`"
        
        def convert_pre():
            return f"```\n{text_content}\n```\n"
        
        def convert_p():
            return f"{text_content}\n"
        
        def convert_br():
            return '\n'
        
        def convert_a():
            href = tag.get('href', '')
            return f"[{text_content}]({href})" if href else text_content
        
        def convert_ul():
            items = []
            for li in tag.find_all('li', recursive=False):
                items.append(f"- {li.get_text().strip()}")
            return '\n'.join(items) + '\n'
        
        def convert_ol():
            items = []
            for i, li in enumerate(tag.find_all('li', recursive=False), 1):
                items.append(f"{i}. {li.get_text().strip()}")
            return '\n'.join(items) + '\n'
        
        def convert_blockquote():
            lines = text_content.split('\n')
            quoted_lines = [f"> {line}" for line in lines if line.strip()]
            return '\n'.join(quoted_lines) + '\n'
        
        def convert_div_span():
            # For divs and spans, recursively process children
            result = []
            for child in tag.children:
                if hasattr(child, 'name') and child.name is not None:
                    child_text = self._convert_html_tag_to_markdown(child)
                    if child_text:
                        result.append(child_text)
                else:
                    child_text = str(child).strip()
                    if child_text:
                        result.append(child_text)
            return ''.join(result)
        
        def default_converter():
            return text_content
        
        # Dictionary mapping tag names to converter functions
        tag_converters = {
            'strong': convert_strong,
            'b': convert_strong,
            'em': convert_em,
            'i': convert_em,
            'code': convert_code,
            'pre': convert_pre,
            'p': convert_p,
            'br': convert_br,
            'a': convert_a,
            'ul': convert_ul,
            'ol': convert_ol,
            'blockquote': convert_blockquote,
            'div': convert_div_span,
            'span': convert_div_span,
        }
        
        # Get the appropriate converter function or use default
        converter = tag_converters.get(tag_name, default_converter)
        return converter()
    
    def _extract_code_from_html(self, pre_tag) -> str:
        """Extract Python code from HTML, removing syntax highlighting markup."""
        # Look for any elements that might contain the paragraph symbol
        # and remove them before extracting text
        for elem in pre_tag.find_all(class_=lambda x: x and 'jp-' in str(x)):
            if elem.string == '¶':
                elem.decompose()
        
        # Simple approach: get_text() works well for most cases
        code_text = pre_tag.get_text()
        
        # Clean up HTML entities
        code_text = html.unescape(code_text)
        
        # Split into lines and clean up
        lines = code_text.split('\n')
        lines = [line.rstrip() for line in lines]
        
        # Remove empty lines at start and end
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
            
        return '\n'.join(lines)
    
    def _create_notebook(self, cells: List[Dict]) -> nbformat.NotebookNode:
        """Create notebook structure with extracted cells."""
        notebook = nbformat.v4.new_notebook()
        
        # Set metadata
        notebook.metadata = {
            'kernelspec': self.kernel_spec,
            'language_info': {
                'name': 'python',
                'version': '3.8.0',
                'mimetype': 'text/x-python',
                'codemirror_mode': {'name': 'ipython', 'version': 3},
                'pygments_lexer': 'ipython3',
                'nbconvert_exporter': 'python',
                'file_extension': '.py'
            }
        }
        
        # Add cells
        for cell_data in cells:
            cell_type_handlers = {
                'markdown': lambda: nbformat.v4.new_markdown_cell(
                    source=cell_data['source'],
                    metadata=cell_data['metadata']
                ),
                'code': lambda: nbformat.v4.new_code_cell(
                    source=cell_data['source'],
                    metadata=cell_data['metadata'],
                    execution_count=cell_data.get('execution_count')
                )
            }
            
            create_cell = cell_type_handlers.get(cell_data['cell_type'])
            if create_cell:
                notebook.cells.append(create_cell())
            
        return notebook


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(
        description="Convert HTML exported from Jupyter Notebook to .ipynb format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python html_to_notebook.py notebook.html
  python html_to_notebook.py notebook.html -o converted.ipynb
  python html_to_notebook.py file1.html file2.html > combined.ipynb
        """
    )
    
    parser.add_argument(
        'html_files', 
        nargs='+', 
        help='HTML file(s) to convert'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output notebook file (writes to stdout if not specified)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output for debugging'
    )
    
    args = parser.parse_args()
    
    converter = NotebookConverter(verbose=args.verbose)
    
    try:
        html_paths = [Path(f) for f in args.html_files]
        notebook = converter.html_to_notebook(html_paths)
        
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w', encoding='utf-8') as f:
                nbformat.write(notebook, f)
            if not args.verbose:
                info_print(f"Notebook written to {output_path}")
        else:
            # Write to stdout
            nbformat.write(notebook, sys.stdout)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
