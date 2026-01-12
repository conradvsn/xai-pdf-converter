# 🔍 xAI PDF Converter

Advanced PDF to DOCX conversion with AI-powered sensitive information detection.

## 🚀 Features

- **PDF to DOCX Conversion** - Enterprise-grade conversion using Adobe PDF Services API
- **AI-Powered Detection** - ML-based sensitive information detection with spaCy NER
- **Batch Processing** - Process multiple PDFs with consolidated reporting
- **Anonymization** - Generate anonymized reports for privacy compliance
- **Modern UI** - Professional Streamlit web interface

## 📊 Detection Capabilities

- 🏢 Company Names (ML + regex)
- 👤 Person Names (advanced cleaning)
- 📧 Email Addresses
- 📞 Phone Numbers
- 📍 Addresses
- 🔢 SSN, EIN, Credit Cards
- 🌐 Websites/URLs
- 📊 Financial Codes (CUSIP, ISIN, CIK)

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Adobe PDF Services API credentials

### Setup

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/xai-pdf-converter.git
cd xai-pdf-converter
```

2. Install dependencies:
```bash
pip install -r streamlit_app/requirements.txt
python -m spacy download en_core_web_sm
```

3. Configure Adobe credentials:
   - Create `streamlit_app/adobe_credentials_pool.json`
   - Format:
   ```json
   {
     "credentials": [
       {
         "name": "account_1",
         "client_id": "YOUR_CLIENT_ID",
         "client_secret": "YOUR_CLIENT_SECRET",
         "monthly_limit": 500
       }
     ]
   }
   ```

## 🎯 Usage

### Local Development

```bash
cd streamlit_app
streamlit run Home.py
```

Or use the launch script:
```bash
cd streamlit_app
./run.sh
```

### Deploy to Streamlit Cloud

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Set main file path: `streamlit_app/Home.py`
5. Add secrets in Streamlit Cloud dashboard (Adobe credentials)

## 📁 Project Structure

```
xai-pdf-converter/
├── streamlit_app/          # Streamlit web application
│   ├── Home.py            # Main dashboard
│   ├── pages/             # Application pages
│   ├── components/        # Reusable UI components
│   ├── utils/             # Utility functions
│   └── requirements.txt   # Python dependencies
├── src/                   # Core functionality
│   ├── analysis/          # Detection and analysis
│   ├── conversion/        # PDF conversion
│   └── adobe_credentials_manager.py
└── pdf/                   # Input PDFs (not tracked)
```

## 🔒 Security

- **Credentials**: Never commit API credentials to Git
- **Privacy**: All processing done locally
- **Anonymization**: Sensitive data automatically anonymized in reports

## 📄 License

© 2025 Conrad Vaslin - xAI Finance Tutor

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a pull request.

## 📧 Contact

For questions or support, please open an issue on GitHub.
