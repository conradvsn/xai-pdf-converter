# 🔍 xAI PDF Converter - Streamlit Application

Modern, professional web interface for the xAI PDF Converter with AI-powered sensitive information detection.

## ✨ Features

### 📄 Single PDF Processing
- Upload and process individual PDF files
- Convert PDF to DOCX with layout preservation
- Detect sensitive information using AI/ML (spaCy)
- Generate detailed Excel reports with anonymization
- Real-time progress tracking
- Download results instantly

### 📦 Batch Processing
- Process multiple PDFs simultaneously
- Consolidated reporting across documents
- Automatic deduplication of findings
- Bulk download capabilities
- Progress tracking for each file

### 📊 Results & History
- View processing history with filters
- Track statistics (PDFs processed, findings, etc.)
- Browse and download previous results
- Export/import settings
- Clear cache and history

### ⚙️ Settings
- Configure Adobe PDF Services API
- Customize output directory
- Set default processing options
- Manage grouping keywords
- View system information

## 🚀 Quick Start

### Prerequisites

1. **Python 3.9+** installed
2. **Adobe PDF Services API** credentials (optional, for conversion)
3. **spaCy** English model: `python -m spacy download en_core_web_sm`

### Installation

1. Navigate to the streamlit_app directory:
```bash
cd /Users/conrad/Downloads/xAI/streamlit_app
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download spaCy model (if not already installed):
```bash
python -m spacy download en_core_web_sm
```

### Running the Application

```bash
streamlit run Home.py
```

The application will open in your default browser at `http://localhost:8501`

## 📁 Project Structure

```
streamlit_app/
├── Home.py                    # Main dashboard
├── pages/
│   ├── 1_📄_Single_PDF.py    # Single file processing
│   ├── 2_📦_Batch_Processing.py  # Batch processing
│   ├── 3_📊_Results.py        # History and results
│   └── 4_⚙️_Settings.py      # Configuration
├── components/
│   └── stats_cards.py         # Reusable UI components
├── utils/
│   └── session.py             # Session state management
├── .streamlit/
│   └── config.toml            # Theme configuration
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🎨 Design Philosophy

### Modern UI/UX
- **Gradient theme** with purple/violet color scheme
- **Card-based layout** for organized content
- **Responsive design** with proper spacing
- **Interactive elements** with hover effects
- **Clear visual hierarchy** and typography

### User Experience
- **Intuitive navigation** with emoji icons
- **Real-time feedback** with progress bars
- **Helpful tooltips** and expandable sections
- **Error handling** with clear messages
- **Mobile-friendly** responsive layout

### Performance
- **Session state** for efficient data management
- **Caching** for repeated operations
- **Lazy loading** for large datasets
- **Optimized file handling** with temp directories

## 🔧 Configuration

### Adobe API Setup

1. Go to [Adobe Developer Console](https://developer.adobe.com/console)
2. Create a new project
3. Add "PDF Services API"
4. Download credentials JSON
5. Upload in Settings page or configure in `src/config.py`

### Output Directory

Default: `~/Downloads/xAI_Output`

Change in Settings page or modify in session state.

### Processing Options

Configure defaults in Settings:
- **OCR**: Enable for scanned PDFs
- **Layout Preservation**: Maintain PDF layout in DOCX
- **Grouping Keywords**: Auto-organize companies in reports
- **Verbose Mode**: Show detailed logs

## 📊 Detected Information Types

The application detects and reports:

| Type | Icon | Description |
|------|------|-------------|
| Company Names | 🏢 | Using spaCy ML + regex patterns |
| Person Names | 👤 | Using spaCy NER + validation |
| Email Addresses | 📧 | With TLD validation |
| Phone Numbers | 📞 | US & International formats |
| Physical Addresses | 📍 | Street addresses with validation |
| SSN | 🔢 | Social Security Numbers |
| IRS EIN | 🏛️ | Employer Identification Numbers |
| Credit Cards | 💳 | With Luhn algorithm validation |
| Websites | 🌐 | URLs with protocol |

## 🎯 Use Cases

### Financial Document Analysis
- Analyze SEC filings (10-K, proxy statements)
- Detect company mentions in financial reports
- Track person names across documents
- Extract contact information

### Legal Document Processing
- Convert contracts to editable format
- Identify parties and entities
- Extract addresses and contact details
- Anonymize sensitive information

### Batch Document Review
- Process multiple agreements simultaneously
- Generate consolidated findings report
- Cross-document entity tracking
- Automated redaction preparation

## 🔒 Privacy & Security

- **Local Processing**: All analysis done on your machine
- **No External Calls**: Except Adobe API for conversion
- **Anonymization**: Reports include anonymized versions
- **Temporary Files**: Automatically cleaned up
- **No Data Storage**: Session-based, no persistent storage

## 🐛 Troubleshooting

### "Adobe API not configured"
→ Upload credentials in Settings page

### "spaCy not available"
→ Install: `python -m spacy download en_core_web_sm`

### "Upload failed"
→ Check file size limit (200 MB default in config.toml)

### "Processing error"
→ Check file format (must be valid PDF)
→ Enable verbose mode for detailed logs

### "No findings detected"
→ Check if PDF contains text (not just images)
→ Enable OCR for scanned PDFs

## 📚 Advanced Features

### Grouping Keywords
Organize companies by keywords:
```
Vantiv
WorldPay
Fifth Third
```

Reports will group all mentions under these categories.

### Consolidated Reports
In batch mode, creates single Excel with:
- Deduplicated findings across all PDFs
- Document tracking (which PDFs contain which entities)
- Page references grouped by document

### Anonymization
Excel reports include Column F with anonymized values:
- Company names → "Company A", "Company B", etc.
- Person names → "Person 1", "Person 2", etc.
- Consistent across pages (same entity = same alias)

## 🔄 Updates & Maintenance

### Updating Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Clearing Cache
Use Settings page → Advanced → Clear Cache

### Resetting Settings
Delete session state or use Settings page → Import/Export

## 📞 Support

For issues or questions:
- Check the **How to use** sections in each page
- Review this README
- Check error messages (enable verbose mode)
- Contact: Conrad Vaslin - xAI Finance Tutor

## 📝 Version History

### Version 2.0.0 (Streamlit)
- Complete UI rewrite with Streamlit
- Modern gradient theme
- Multi-page navigation
- Real-time progress tracking
- Enhanced statistics dashboard
- Batch processing improvements
- Consolidated reporting
- Settings management

### Version 1.0.0 (CLI)
- Original command-line interface
- Basic PDF conversion
- Sensitive information detection
- Excel report generation

## 🙏 Acknowledgments

**Built with:**
- [Streamlit](https://streamlit.io/) - Web framework
- [Adobe PDF Services](https://developer.adobe.com/document-services/apis/pdf-services/) - PDF conversion
- [spaCy](https://spacy.io/) - Natural language processing
- [python-docx](https://python-docx.readthedocs.io/) - DOCX generation
- [openpyxl](https://openpyxl.readthedocs.io/) - Excel reports

**Created by:** Conrad Vaslin
**Purpose:** xAI Finance Tutor
**Year:** 2025

---

**© 2025 Conrad Vaslin | xAI Finance Tutor**
