#!/bin/bash
# Launch script for xAI PDF Converter Streamlit App

echo "🔍 xAI PDF Converter - Streamlit Application"
echo "=============================================="
echo ""

# Check if in correct directory
if [ ! -f "Home.py" ]; then
    echo "❌ Error: Please run this script from the streamlit_app directory"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

# Check if Streamlit is installed
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "⚠️  Streamlit not installed. Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Check if spaCy model is downloaded
if ! python3 -c "import spacy; spacy.load('en_core_web_sm')" &> /dev/null; then
    echo "⚠️  spaCy model not found. Downloading..."
    python3 -m spacy download en_core_web_sm
fi

echo "✅ All dependencies ready"
echo ""
echo "🚀 Launching Streamlit app..."
echo "   URL: http://localhost:8501"
echo ""
echo "   Press Ctrl+C to stop"
echo ""

# Launch Streamlit
streamlit run Home.py
