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
from components.stats_cards import show_stats_dashboard, show_adobe_quota_sidebar
from utils.styles import apply_global_styles

# Page config
st.set_page_config(
    page_title="xAI PDF Converter",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply shared global styles
apply_global_styles()

# Initialize session state
init_session_state()

# Import auth and require authentication
from auth.middleware import require_auth
from auth.ui import show_user_menu

# Require authentication - redirect to login if not signed in
if not require_auth():
    st.stop()

# Show user menu in sidebar
show_user_menu()

# Show Adobe quota in sidebar
show_adobe_quota_sidebar()

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
