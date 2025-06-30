# html_to_notebook

Convert HTML exported from Jupyter Notebook back to `.ipynb` format.

## Overview

This tool converts HTML files exported from JupyterLab back to functional `.ipynb` notebooks, allowing you to recover the original notebook format from HTML exports.

### Why This Tool?

Sometimes you have HTML exports of Jupyter notebooks but need the original `.ipynb` format to:
- Continue development and run cells
- Modify and iterate on the analysis
- Share executable notebooks with colleagues
- Apply version control to notebook files

## Features

- **Extracts both markdown and code cells** from JupyterLab HTML exports
- **Preserves proper markdown formatting** (headers, lists, links, etc.)
- **Handles syntax-highlighted code properly** with correct spacing and newlines
- **Supports multiple input files** (concatenates cells from multiple HTML files)
- **Unix-style interface** - outputs to stdout by default
- **Clean code extraction** - removes HTML markup while preserving Python structure

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install beautifulsoup4 nbformat
```

## Usage

```bash
# Convert single file to stdout
python html_to_notebook.py notebook.html > notebook.ipynb

# Convert with specific output file
python html_to_notebook.py notebook.html -o converted.ipynb

# Combine multiple HTML files into one notebook
python html_to_notebook.py file1.html file2.html > combined.ipynb
```

## Examples

### Basic Conversion

```bash
# Convert JupyterLab HTML export back to notebook
python html_to_notebook.py exported_notebook.html > restored_notebook.ipynb
```

### Multiple Files

```bash
# Combine several HTML exports into one notebook
python html_to_notebook.py chapter1.html chapter2.html chapter3.html > complete_analysis.ipynb
```

### Specify Output File

```bash
# Write to specific output file
python html_to_notebook.py analysis.html -o analysis_restored.ipynb
```

## Technical Details

### How It Works

1. **Parse HTML** using BeautifulSoup to extract structured content
2. **Identify cell containers** by JupyterLab CSS classes (`jp-Cell`, `jp-Notebook-cell`)
3. **Extract and convert content:**
   - **Markdown cells**: Convert HTML back to markdown syntax (headers, lists, links)
   - **Code cells**: Remove syntax highlighting markup while preserving code structure
4. **Create notebook structure** using the nbformat library
5. **Output valid JSON** compatible with JupyterLab and Jupyter Notebook

### Supported Content

- **Markdown cells**: Headers, paragraphs, lists, links, emphasis, code blocks
- **Code cells**: Python code with proper spacing, indentation, and newlines
- **Cell metadata**: Basic notebook structure and kernel information

## Project Structure

```
html_to_notebook/
├── README.md
├── LICENSE
├── requirements.txt
├── html_to_notebook.py     # Main HTML to notebook converter
└── examples/
    ├── sample_input.html
    └── sample_output.ipynb
```

## Limitations

- **JupyterLab exports only**: Supports JupyterLab HTML exports, not classic Jupyter Notebook HTML
- **No output preservation**: Code cell outputs are not preserved (by design - run cells to regenerate)
- **Markdown complexity**: Some very complex markdown formatting may not convert perfectly
- **Cell execution state**: Execution counts and cell metadata are reset

## Troubleshooting

### Common Issues

**"No cells found"**
- Verify the HTML file is from JupyterLab (not classic Jupyter Notebook)
- Check that the HTML export contains the expected JupyterLab structure

**"Malformed JSON output"**
- Ensure you're not redirecting stderr to the output file
- Status messages go to stderr, only notebook JSON goes to stdout

**"Code formatting issues"**
- The tool handles most JupyterLab syntax highlighting, but complex cases may need manual review
- Check that the original HTML export was complete and not truncated

**"Missing dependencies"**
- Install required packages: `pip install beautifulsoup4 nbformat`

### Getting Help

1. Verify your HTML file is a complete JupyterLab export
2. Ensure all dependencies are installed correctly
3. Test with a simple notebook first to verify the tool is working
4. File an issue with a sample HTML file if problems persist

## Contributing

This project includes code written with assistance from AI tools (Claude and ChatGPT). Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Code partially generated with assistance from Claude (Anthropic) and ChatGPT (OpenAI)
- Built on top of the excellent `nbformat` and `beautifulsoup4` libraries
- Inspired by the need to recover notebooks from HTML exports