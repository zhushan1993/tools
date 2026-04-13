# AI Space Tools Collection

A collection of utility tools for document processing and data manipulation.

## Tools Overview

### 1. PDF Tools
- **resize_pdf**: Resize PDF pages to uniform dimensions
- **markdown_to_pdf**: Convert Markdown files to PDF documents
- **pdf_to_md**: Convert PDF files to Markdown format
  - `handwrite_pdf`: Specialized for handwritten PDF conversion
  - `scan_pdf_ocr`: OCR processing for scanned PDF documents

### 2. Document Conversion
- **md_to_word**: Convert Markdown files to Microsoft Word (.docx) format
- **merge_csv**: Merge multiple CSV files into a single file

### 3. Audio Processing
- **m4a_to_md**: Convert M4A audio recordings to Markdown transcriptions

## Project Structure

```
tools/
├── resize_pdf/          # PDF resizing tool
│   ├── resize_pdf.py    # Main script
│   ├── requirements.txt # Python dependencies
│   └── .venv/           # Virtual environment (ignored)
├── markdown_to_pdf/     # Markdown to PDF converter
├── pdf_to_md/           # PDF to Markdown converter
│   ├── handwrite_pdf/   # Handwritten PDF processing
│   └── scan_pdf_ocr/    # Scanned PDF OCR
├── merge_csv/           # CSV merging tool
├── m4a_to_md/           # Audio to text converter
├── md_to_word/          # Markdown to Word converter
├── .gitignore           # Git ignore rules
├── .gitattributes       # Line ending configuration
├── requirements.txt     # Main Python dependencies (if applicable)
└── README.md            # This file
```

## Setup

Each tool has its own virtual environment and dependencies. Navigate to the tool directory and:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

### PDF Resizing
```bash
cd resize_pdf
python resize_pdf.py --input input.pdf --output output.pdf
```

### Markdown to PDF
```bash
cd markdown_to_pdf
python convert_to_pdf.py --input document.md --output document.pdf
```

### PDF to Markdown (OCR)
```bash
cd pdf_to_md/scan_pdf_ocr
python pdf_ocr_tool.py --input scanned.pdf --output text.md
```

### CSV Merging
```bash
cd merge_csv
python merge_csv.py --input-dir input/ --output merged.csv
```

### Audio to Markdown
```bash
cd m4a_to_md
python m4a_to_md.py --input recording.m4a --output transcript.md
```

## Dependencies

Each tool maintains its own `requirements.txt` file with specific dependencies. Common dependencies include:

- **PDF processing**: PyPDF2, reportlab, pdf2image
- **OCR**: paddleocr, pytesseract
- **Document conversion**: python-docx, markdown
- **Audio processing**: speech_recognition, pydub

## Notes

- Virtual environments are excluded from version control (see `.gitignore`)
- Input/output directories may contain sample files for testing
- Some tools require additional system dependencies (e.g., Tesseract for OCR)

## License

Tools are developed for personal/work use. Contact repository owner for licensing information.

## Contributing

Feel free to submit issues or pull requests for improvements.

---
*Last updated: 2026-04-13*