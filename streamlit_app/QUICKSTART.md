# 🚀 Quick Start Guide

Get started with xAI PDF Converter Streamlit app in 3 minutes!

## 📋 Prerequisites

- **Python 3.9+** installed
- **pip** package manager
- (Optional) Adobe PDF Services API credentials

## ⚡ Quick Installation

### 1. Navigate to the app directory
```bash
cd /Users/conrad/Downloads/xAI/streamlit_app
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Download spaCy model
```bash
python -m spacy download en_core_web_sm
```

### 4. Launch the app
```bash
./run.sh
```

Or manually:
```bash
streamlit run Home.py
```

## 🎯 First Steps

### Processing Your First PDF

1. **Open the app** at `http://localhost:8501`

2. **Go to "📄 Single PDF"** page (sidebar)

3. **Upload a PDF file**

4. **Select operation:**
   - For conversion only → "Convert to DOCX"
   - For analysis only → "Analyze Only"
   - For both → "Convert + Analyze" ✅ (recommended)

5. **Click "🚀 Start Processing"**

6. **Download results:**
   - DOCX file (editable Word document)
   - Excel report (sensitive information findings)

### Example Output

**Excel Report Columns:**
- **A**: Information Type (company_name, person_name, email, etc.)
- **B**: Information (the actual value found)
- **C**: (empty spacing column)
- **D**: Document (filename)
- **E**: Pages (where it appears)
- **F**: Anonymized Information (Company A, Person 1, etc.)

## 🔧 Configuration (Optional)

### Adobe API for Conversion

If you want PDF → DOCX conversion:

1. Go to **⚙️ Settings** page
2. Scroll to **🔑 Adobe PDF Services API**
3. Click **➕ Add New Adobe API Key**
4. Upload your credentials JSON file
5. Save and restart the app

Without Adobe API, you can still use **Analyze Only** mode!

### Custom Output Directory

1. Go to **⚙️ Settings**
2. Change **📁 Output Directory**
3. Click **💾 Update**

Default: `~/Downloads/xAI_Output`

## 📦 Batch Processing

Process multiple PDFs at once:

1. Go to **📦 Batch Processing** page
2. Upload multiple PDF files (shift-click to select)
3. Choose options:
   - ✅ **Create consolidated report** (recommended)
   - Enter grouping keywords (e.g., "Vantiv, WorldPay")
4. Click **🚀 Process Files**
5. Download all results

**Consolidated Report** = Single Excel file with findings from all PDFs combined and deduplicated!

## 📊 View Results

Go to **📊 Results** page to:
- See processing history
- View overall statistics
- Browse all output files
- Download previous results
- Clear history/cache

## 💡 Tips & Tricks

### For Scanned PDFs
✅ Enable "Use OCR for scanned PDFs" in options

### For Financial Documents
📝 Add company names to "Grouping Keywords":
```
Vantiv
WorldPay
Fifth Third
Goldman Sachs
```

Reports will organize these companies together!

### For Large Batches
- Process 5-10 PDFs at a time for best performance
- Enable consolidated reporting to cross-reference findings
- Use verbose mode if you encounter issues

### Keyboard Shortcuts
- `Ctrl/Cmd + R` - Refresh page
- `Ctrl/Cmd + K` - Clear cache
- `Esc` - Close dialogs

## 🐛 Troubleshooting

### App won't start
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### "spaCy not available"
```bash
# Download the model
python -m spacy download en_core_web_sm
```

### "Adobe API not configured"
→ Either upload credentials in Settings, or use "Analyze Only" mode

### Upload fails
→ Check file size (max 200 MB)
→ Verify it's a valid PDF file

### No findings detected
→ PDF might be image-based (enable OCR)
→ PDF might not contain the types of information being detected

### Processing is slow
→ Normal for large PDFs (100+ pages)
→ Disable OCR if not needed
→ Process in smaller batches

## 🎓 Learning Resources

### Example Documents
Try with:
- SEC 10-K filings
- Proxy statements (DEF 14A)
- Annual reports
- Legal contracts
- Financial statements

Download samples from [SEC EDGAR](https://www.sec.gov/edgar/search/)

### Best Practices
1. **Start small** - Test with 1-2 PDFs first
2. **Check results** - Review Excel reports for accuracy
3. **Adjust keywords** - Fine-tune grouping for your use case
4. **Save settings** - Export settings for reuse

### Advanced Usage
- **API Mode**: Use the core modules programmatically
- **Custom Detection**: Modify regex patterns in `sensitive_info_detector.py`
- **Bulk Processing**: Use command-line batch_processor for 50+ PDFs

## 📞 Getting Help

### In-App Help
- Click **💡 How to use** expanders on each page
- Hover over (?) icons for tooltips
- Check Settings → System Information

### Documentation
- `README.md` - Full documentation
- `FIX_SUMMARY.md` - Recent fixes and improvements
- Source code comments

### Support
Contact: Conrad Vaslin - xAI Finance Tutor

---

## ✅ You're Ready!

1. ✅ Dependencies installed
2. ✅ App running at http://localhost:8501
3. ✅ Upload your first PDF
4. ✅ Get results in seconds!

**Happy analyzing! 🎉**
