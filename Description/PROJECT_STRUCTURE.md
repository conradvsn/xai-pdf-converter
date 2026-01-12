# xAI PDF Converter - Project Structure

**Developer**: Conrad Vaslin - xAI Finance Tutor
**Version**: 2.0.0 - Modular Architecture
**Copyright**: © 2025 Conrad Vaslin - All Rights Reserved

---

## 📁 Directory Structure

```
xAI/
│
├── main.py                          # Entry point - Interactive menu system
├── config.json                      # Auto-generated user settings (persistent)
│
├── pdf/                             # Input directory for PDF files
│   ├── August 9, 2017 Form 8-K.pdf
│   ├── December 31, 2016 Form 10-K.pdf
│   ├── June 30, 2017 Form 10-Q.pdf
│   ├── March 15, 2017 Form- DEF 14A.pdf
│   └── March 31, 2017 Form 10-Q.pdf
│
├── output/                          # Generated DOCX and Excel files
│   ├── *.docx                       # Converted Word documents
│   ├── *_analysis.xlsx              # Individual PDF analysis reports
│   └── consolidated statements.xlsx # Batch analysis report (all PDFs)
│
├── src/                             # Source code (modular architecture)
│   │
│   ├── __init__.py                  # Package metadata (author: Conrad Vaslin)
│   ├── config.py                    # Configuration and dependency checks
│   ├── converter.py                 # Main PDF converter class
│   ├── batch_processor.py           # Batch processing with consolidated reports
│   ├── ui.py                        # User interface (menus, credits)
│   ├── utils.py                     # Utility functions
│   ├── settings.py                  # Persistent settings management (NEW!)
│   ├── settings_handlers.py         # Settings UI handlers (NEW!)
│   │
│   ├── analysis/                    # Sensitive information detection
│   │   ├── __init__.py
│   │   ├── sensitive_info_detector.py  # Person names, companies, PII, financial data
│   │   ├── pdf_analyzer.py             # PDF structure analysis, image detection
│   │   └── report_generator.py         # Excel reports with anonymization
│   │
│   ├── ocr/                         # OCR processing for scanned PDFs
│   │   ├── __init__.py
│   │   ├── ocr_processor.py         # PaddleOCR, EasyOCR, Tesseract support
│   │   └── ocr_cache.py             # OCR result caching
│   │
│   ├── layout/                      # Layout detection and rendering
│   │   ├── __init__.py
│   │   ├── layout_analyzer.py       # Detect tables, columns, headers
│   │   └── layout_renderer.py       # Preserve layout in Word documents
│   │
│   └── processing/                  # Document processing
│       ├── __init__.py
│       ├── document_processor.py    # Post-processing, cleanup
│       ├── pdf_extractor.py         # Text extraction from PDFs
│       └── text_processor.py        # Text cleaning and normalization
│
├── docs/                            # Documentation
│   └── (future documentation files)
│
├── README.md                        # Project overview with credits
├── CREDITS.md                       # Comprehensive attribution (NEW!)
├── IMPROVEMENTS.md                  # List of improvements made (NEW!)
├── PROJECT_STRUCTURE.md             # This file (NEW!)
├── requirements.txt                 # Python dependencies
│
└── xaipdfconverter.py              # Original monolithic file (kept for reference)
```

---

## 🎯 Key Features

### **Core Functionality**
- ✅ PDF → Word conversion with layout preservation
- ✅ OCR support for scanned documents
- ✅ Batch processing with consolidated reports
- ✅ Persistent user settings (config.json)

### **Analysis & Detection**
- ✅ Person names (with intelligent cleaning)
- ✅ Company names (with suffix preservation)
- ✅ Emails, phone numbers, addresses, SSNs
- ✅ Financial data (amounts, percentages)
- ✅ Executive signatures

### **Reporting & Anonymization**
- ✅ 6-column Excel reports
- ✅ Anonymization with consistent aliases
- ✅ Bidirectional prefix matching deduplication
- ✅ Consolidated batch reports
- ✅ Multi-document tracking
- ✅ Keyword-based grouping

### **User Experience**
- ✅ Interactive menu system
- ✅ Persistent settings (10 configuration options)
- ✅ Clear attribution to Conrad Vaslin
- ✅ Copyright protection
- ✅ Professional UI with helpful prompts

---

## 📋 Menu System

### **Main Menu**

```
================================================================================
                         🚀 xAI PDF CONVERTER 🚀
================================================================================

────────────────────────────────────────────────────────────────────────────────
  📄 SINGLE FILE OPERATIONS
────────────────────────────────────────────────────────────────────────────────
  1. Convert PDF → Word              [✅ Available]
  2. Convert PDF → Word + Analysis   [✅ Available]
  3. Analyze PDF Only (Excel Report) [✅ Available]
  4. OCR: Scanned PDF → Word         [✅ Available]

────────────────────────────────────────────────────────────────────────────────
  📦 BATCH PROCESSING (Multiple PDFs)
────────────────────────────────────────────────────────────────────────────────
  5. Batch: Convert All PDFs
  6. Batch: Convert + Analyze All
  7. Batch: Analyze All PDFs

────────────────────────────────────────────────────────────────────────────────
  ⚙️  SETTINGS & INFO
────────────────────────────────────────────────────────────────────────────────
  8. View System Status
  9. Configure Settings
  0. Exit

================================================================================
  © 2025 Conrad Vaslin - xAI Finance Tutor  |  Version 2.0.0
================================================================================
```

### **Settings Menu** (Option 9)

```
⚙️  CONVERSION SETTINGS:
  1. Set default output directory
  2. Enable/disable verbose logging
  3. Configure parallelization (pages per chunk)
  4. Set OCR language

📋 ANALYSIS SETTINGS:
  5. Configure keyword grouping
  6. Set detection thresholds

🎨 DISPLAY SETTINGS:
  7. Toggle progress bars
  8. Set report format (Excel/CSV/JSON)

📊 OTHER:
  9. View all settings
  R. Reset to defaults

  0. Back to main menu
```

---

## 🔧 Technical Stack

### **Core Libraries**:
- **PyPDF2** - PDF text extraction
- **pdf2docx** - PDF to DOCX conversion
- **python-docx** - Word document manipulation
- **openpyxl** - Excel report generation
- **pdfplumber** - Advanced table extraction

### **OCR Engines**:
- **PaddleOCR** - Best quality + table detection (recommended)
- **EasyOCR** - Good quality, easy setup
- **pytesseract** - Basic OCR

### **NLP & Validation**:
- **spaCy** - Named entity recognition
- **transformers** - Advanced NLP models
- **phonenumbers** - Phone number validation

---

## 💾 Configuration File (config.json)

Auto-generated on first run. Example:

```json
{
  "version": "2.0.0",
  "verbose_logging": false,
  "show_progress_bars": true,
  "pdf_directory": "pdf",
  "output_directory": "output",
  "pages_per_chunk": 10,
  "ocr_language": "en",
  "detection_thresholds": {
    "min_person_name_length": 5,
    "max_person_name_length": 40,
    "phone_number_validation": true,
    "email_validation": true
  },
  "enable_anonymization": true,
  "enable_deduplication": true,
  "grouping_keywords": [],
  "report_format": "excel",
  "consolidated_reports": true,
  "developer": "Conrad Vaslin",
  "developer_role": "xAI Finance Tutor",
  "copyright": "© 2025 Conrad Vaslin - All Rights Reserved"
}
```

---

## 📊 Report Formats

### **Single PDF Analysis Report**
Filename: `{pdf_name}_analysis.xlsx`

| Column A | Column B | Column C | Column D | Column E | Column F |
|----------|----------|----------|----------|----------|----------|
| Info Type | Info | (empty) | Document | Pages | Anonymized |
| company_name | Vantiv LLC | | file.docx | p.5, p.12 | Company_Alpha |
| person_name | John Smith | | file.docx | p.3 | Person_Beta |

### **Consolidated Batch Report**
Filename: `consolidated statements.xlsx`

| Column A | Column B | Column C | Column D | Column E | Column F |
|----------|----------|----------|----------|----------|----------|
| Info Type | Info | (empty) | Documents | Pages | Anonymized |
| company_name | Vantiv LLC | | file1.docx, file2.docx | file1 p.5; file2 p.3 | Company_Alpha |

---

## 🎓 Usage Examples

### **Example 1: Single File Conversion**
```
1. Place PDF in pdf/ folder
2. Run: python main.py
3. Select option 2 (Convert + Analysis)
4. Choose PDF from list
5. Get:
   - output/{pdf_name}.docx
   - output/{pdf_name}_analysis.xlsx
```

### **Example 2: Batch Processing**
```
1. Place multiple PDFs in pdf/ folder
2. Run: python main.py
3. Select option 6 (Batch: Convert + Analyze All)
4. Configure grouping keywords (optional)
5. Get:
   - output/{pdf1}.docx, {pdf2}.docx, ...
   - output/{pdf1}_analysis.xlsx, {pdf2}_analysis.xlsx, ...
   - output/consolidated statements.xlsx
```

### **Example 3: Configure Settings**
```
1. Run: python main.py
2. Select option 9 (Settings)
3. Configure preferences:
   - Set OCR language to "en"
   - Set pages per chunk to 15
   - Enable anonymization
   - Add grouping keywords: "vantiv,fidelity"
4. Settings saved to config.json
5. Use these settings for all future runs!
```

---

## 🏆 Credits & Attribution

This tool was developed by **Conrad Vaslin** (xAI Finance Tutor) specifically for the xAI team.

**Copyright**: © 2025 Conrad Vaslin - All Rights Reserved

Attribution is prominently displayed:
- Main menu footer
- System status screen (option 8)
- src/__init__.py module metadata
- CREDITS.md comprehensive attribution
- README.md credits section
- config.json developer fields

---

## 📞 Support

For questions, issues, or feature requests, contact:

**Conrad Vaslin**
xAI Finance Tutor

---

**Version**: 2.0.0 - Modular Architecture
**Last Updated**: January 2025
**Lines of Code**: ~7,500+ (modular version)

*This tool represents significant development effort to create a production-ready solution for financial document processing and analysis.*
