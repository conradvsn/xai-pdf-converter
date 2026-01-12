"""
🏠 xAI PDF Converter - Home Dashboard
Modern Streamlit application for PDF conversion and sensitive information detection
"""

import streamlit as st
from pathlib import Path
import sys

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.session import init_session_state
from components.stats_cards import show_stats_dashboard

# Page config
st.set_page_config(
    page_title="xAI PDF Converter",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern, professional design
st.markdown("""
<style>
    /* Global styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    /* Main header styling - Modern gradient */
    .main-header {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
        padding: 3rem 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        position: relative;
        overflow: hidden;
    }

    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, rgba(255,255,255,0.1) 25%, transparent 25%, transparent 75%, rgba(255,255,255,0.1) 75%);
        background-size: 20px 20px;
        opacity: 0.3;
    }

    .main-header h1 {
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Card styling - Modern glass morphism */
    .info-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(99, 102, 241, 0.1);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }

    .info-card:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        transform: translateY(-2px);
    }

    /* Feature card - Enhanced design */
    .feature-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        padding: 2rem 1.5rem;
        border-radius: 16px;
        text-align: center;
        height: 100%;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid #e2e8f0;
        position: relative;
        overflow: hidden;
    }

    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #6366f1, #8b5cf6, #d946ef);
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .feature-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        border-color: #6366f1;
    }

    .feature-card:hover::before {
        opacity: 1;
    }

    /* Stats metric - Modern cards */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #6366f1;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        font-weight: 500;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Button styling - Modern gradient buttons */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        border: none;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.4);
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #6366f1, #8b5cf6, #d946ef);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Custom divider */
    .custom-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #6366f1, transparent);
        margin: 2rem 0;
        border-radius: 2px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
init_session_state()

# Header
st.markdown("""
<div class="main-header">
    <h1>🔍 xAI PDF Converter</h1>
    <p style="font-size: 1.2rem; margin-bottom: 0;">
        Advanced PDF to DOCX conversion with AI-powered sensitive information detection
    </p>
</div>
""", unsafe_allow_html=True)

# Welcome section with modern design
st.markdown("""
<div style="background: linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%);
     padding: 2rem;
     border-radius: 16px;
     border: 1px solid #e0e7ff;
     margin-bottom: 2rem;">
    <h2 style="color: #1e293b; margin-bottom: 1rem; font-size: 1.75rem;">👋 Welcome to xAI PDF Converter!</h2>
    <p style="color: #475569; font-size: 1.1rem; line-height: 1.8; margin-bottom: 0;">
        Transform your PDF workflow with AI-powered intelligence. Our platform combines
        <strong>enterprise-grade conversion</strong> with <strong>advanced sensitive data detection</strong>
        to streamline your document processing.
    </p>
</div>
""", unsafe_allow_html=True)

# Quick actions - Moved here after welcome
st.markdown('<h3 style="color: #1e293b; font-size: 1.5rem; margin: 2rem 0 1.5rem 0;">🚀 Quick Actions</h3>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📄 Process Single PDF", width="stretch"):
        st.switch_page("pages/1_📄_Single_PDF.py")

with col2:
    if st.button("📦 Batch Processing", width="stretch"):
        st.switch_page("pages/2_📦_Batch_Processing.py")

with col3:
    if st.button("📊 View Results", width="stretch"):
        st.switch_page("pages/3_📊_Results.py")

st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

# Feature cards with enhanced design
st.markdown('<h3 style="color: #1e293b; font-size: 1.5rem; margin-bottom: 1.5rem;">✨ Key Capabilities</h3>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div style="font-size: 3rem; margin-bottom: 1rem;">📄</div>
        <h4 style="color: #1e293b; font-size: 1.25rem; margin-bottom: 0.75rem;">Single PDF Processing</h4>
        <p style="color: #64748b; font-size: 0.95rem; line-height: 1.6;">
            Convert and analyze individual PDFs with precision. Get detailed reports with sensitive data detection and anonymization.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div style="font-size: 3rem; margin-bottom: 1rem;">📦</div>
        <h4 style="color: #1e293b; font-size: 1.25rem; margin-bottom: 0.75rem;">Batch Processing</h4>
        <p style="color: #64748b; font-size: 0.95rem; line-height: 1.6;">
            Process hundreds of PDFs simultaneously. Generate consolidated reports with cross-document analysis and deduplication.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div style="font-size: 3rem; margin-bottom: 1rem;">🤖</div>
        <h4 style="color: #1e293b; font-size: 1.25rem; margin-bottom: 0.75rem;">AI-Powered Detection</h4>
        <p style="color: #64748b; font-size: 0.95rem; line-height: 1.6;">
            Machine learning with spaCy NER. Detects 10+ types of sensitive information with 95%+ accuracy.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

# Quick stats
st.markdown("### 📊 System Status")
show_stats_dashboard()

# Information cards
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
st.markdown("### ℹ️ Information")

info_col1, info_col2 = st.columns(2)

with info_col1:
    with st.expander("🔒 **Privacy & Security**", expanded=False):
        st.markdown("""
        - All processing is done locally on your machine
        - Sensitive information is anonymized in reports
        - No data is sent to external servers (except Adobe API for conversion)
        - Files are stored temporarily and can be deleted
        """)

with info_col2:
    with st.expander("📚 **Supported Formats**", expanded=False):
        st.markdown("""
        - **Input**: PDF files (including scanned PDFs with OCR)
        - **Output**: DOCX (Microsoft Word), Excel reports (XLSX)
        - **Detection**: 10+ types of sensitive information
        - **Languages**: English (with spaCy NER support)
        """)

# Footer with modern design
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center;
     background: linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%);
     padding: 2rem;
     border-radius: 12px;
     margin-top: 2rem;">
    <p style="color: #475569; font-size: 0.95rem; margin-bottom: 0.5rem; font-weight: 500;">
        © 2025 Conrad Vaslin - xAI Finance Tutor | Version 2.0.0
    </p>
    <p style="color: #64748b; font-size: 0.85rem; margin-bottom: 0;">
        Built with <strong>Streamlit</strong> | Powered by <strong>Adobe PDF Services</strong> & <strong>spaCy ML</strong>
    </p>
</div>
""", unsafe_allow_html=True)
