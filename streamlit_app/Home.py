"""
🏠 xAI PDF Converter - Home Dashboard
Modern Streamlit application for PDF conversion and sensitive information detection
"""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime

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

# Enhanced styles for home page
st.markdown("""
<style>
    .hero-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .hero-section h1 {
        font-size: 3rem;
        margin: 0 0 1rem 0;
        font-weight: 700;
    }
    .hero-section p {
        font-size: 1.25rem;
        opacity: 0.95;
        margin: 0;
        max-width: 600px;
        margin: 0 auto;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(255,255,255,0.2);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        margin-top: 1.5rem;
    }
    .action-card {
        background: white;
        border: 2px solid #e9ecef;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        height: 100%;
    }
    .action-card:hover {
        border-color: #667eea;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
        transform: translateY(-2px);
    }
    .action-card .icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    .action-card h3 {
        color: #1e293b;
        font-size: 1.2rem;
        margin: 0 0 0.5rem 0;
    }
    .action-card p {
        color: #64748b;
        font-size: 0.9rem;
        margin: 0;
        line-height: 1.5;
    }
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin: 1.5rem 0;
    }
    .stat-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
    }
    .stat-card .number {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
        margin: 0;
    }
    .stat-card .label {
        color: #64748b;
        font-size: 0.85rem;
        margin: 0.25rem 0 0 0;
    }
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.5rem;
        margin: 1.5rem 0;
    }
    .feature-item {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 1.5rem;
    }
    .feature-item .icon {
        font-size: 2rem;
        margin-bottom: 0.75rem;
    }
    .feature-item h4 {
        color: #1e293b;
        font-size: 1.1rem;
        margin: 0 0 0.5rem 0;
    }
    .feature-item p {
        color: #64748b;
        font-size: 0.9rem;
        margin: 0;
        line-height: 1.5;
    }
    .tech-badge {
        display: inline-block;
        background: #f1f5f9;
        color: #475569;
        padding: 0.4rem 0.8rem;
        border-radius: 6px;
        font-size: 0.85rem;
        margin: 0.25rem;
    }
    .getting-started {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 1px solid #86efac;
        border-radius: 16px;
        padding: 2rem;
        margin: 2rem 0;
    }
    .getting-started h3 {
        color: #166534;
        margin: 0 0 1rem 0;
    }
    .step-list {
        display: flex;
        gap: 2rem;
        flex-wrap: wrap;
    }
    .step-item {
        flex: 1;
        min-width: 200px;
        display: flex;
        align-items: flex-start;
        gap: 1rem;
    }
    .step-number {
        background: #22c55e;
        color: white;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        flex-shrink: 0;
    }
    .step-content h4 {
        color: #166534;
        margin: 0 0 0.25rem 0;
        font-size: 1rem;
    }
    .step-content p {
        color: #4ade80;
        margin: 0;
        font-size: 0.85rem;
    }
    .recent-activity {
        background: #f8fafc;
        border-radius: 12px;
        padding: 1.5rem;
    }
    .activity-item {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 0.75rem 0;
        border-bottom: 1px solid #e2e8f0;
    }
    .activity-item:last-child {
        border-bottom: none;
    }
    .footer-section {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        margin-top: 2rem;
        text-align: center;
    }
    .footer-section p {
        margin: 0.25rem 0;
        opacity: 0.9;
    }
    .footer-section a {
        color: #93c5fd;
        text-decoration: none;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
init_session_state()

# Show Adobe quota in sidebar
show_adobe_quota_sidebar()

# Sidebar enhancements
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🔗 Quick Links")
    st.page_link("pages/1_📄_Single_PDF.py", label="📄 Single PDF", icon="📄")
    st.page_link("pages/2_📦_Batch_Processing.py", label="📦 Batch Processing", icon="📦")
    st.page_link("pages/3_📊_Results.py", label="📊 Results", icon="📊")
    st.page_link("pages/4_⚙️_Settings.py", label="⚙️ Settings", icon="⚙️")

# Hero Section
st.markdown("""
<div class="hero-section">
    <h1>🔍 xAI PDF Converter</h1>
    <p>Enterprise-grade PDF conversion with AI-powered sensitive information detection</p>
    <div class="hero-badge">✨ Powered by Adobe PDF Services & spaCy ML</div>
</div>
""", unsafe_allow_html=True)

# Quick Stats Row
stats = st.session_state.get('stats', {})
pdfs_processed = stats.get('pdfs_processed', 0)
pages_processed = stats.get('pages_processed', 0)
findings_detected = stats.get('findings_detected', 0)
history = st.session_state.get('history', [])

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <p class="number">{pdfs_processed}</p>
        <p class="label">📄 PDFs Processed</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card">
        <p class="number">{pages_processed}</p>
        <p class="label">📑 Pages Analyzed</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card">
        <p class="number">{findings_detected}</p>
        <p class="label">🔍 Findings Detected</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card">
        <p class="number">{len(history)}</p>
        <p class="label">📋 Recent Sessions</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("")

# Quick Actions
st.markdown("### 🚀 Quick Actions")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="action-card">
        <div class="icon">📄</div>
        <h3>Single PDF</h3>
        <p>Convert and analyze one PDF file with detailed reporting</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Process Single PDF", type="primary", use_container_width=True, key="btn_single"):
        st.switch_page("pages/1_📄_Single_PDF.py")

with col2:
    st.markdown("""
    <div class="action-card">
        <div class="icon">📦</div>
        <h3>Batch Processing</h3>
        <p>Process multiple PDFs with consolidated reports</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Start Batch Processing", type="primary", use_container_width=True, key="btn_batch"):
        st.switch_page("pages/2_📦_Batch_Processing.py")

with col3:
    st.markdown("""
    <div class="action-card">
        <div class="icon">📊</div>
        <h3>View Results</h3>
        <p>Browse processing history and download reports</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("View All Results", type="primary", use_container_width=True, key="btn_results"):
        st.switch_page("pages/3_📊_Results.py")

# Getting Started Section
st.markdown("""
<div class="getting-started">
    <h3>🎯 Getting Started</h3>
    <div class="step-list">
        <div class="step-item">
            <div class="step-number">1</div>
            <div class="step-content">
                <h4>Upload PDF</h4>
                <p>Drag & drop your file</p>
            </div>
        </div>
        <div class="step-item">
            <div class="step-number">2</div>
            <div class="step-content">
                <h4>Select Operation</h4>
                <p>Convert, Analyze, or Both</p>
            </div>
        </div>
        <div class="step-item">
            <div class="step-number">3</div>
            <div class="step-content">
                <h4>Process</h4>
                <p>Click Start Processing</p>
            </div>
        </div>
        <div class="step-item">
            <div class="step-number">4</div>
            <div class="step-content">
                <h4>Download</h4>
                <p>Get DOCX & Excel reports</p>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Features Grid
st.markdown("### ✨ Key Features")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-item">
        <div class="icon">🔄</div>
        <h4>PDF to DOCX Conversion</h4>
        <p>High-fidelity conversion preserving layouts, tables, and formatting using Adobe's industry-standard technology.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-item">
        <div class="icon">🤖</div>
        <h4>AI-Powered Detection</h4>
        <p>Machine learning with spaCy NER detects 10+ types of sensitive information with 95%+ accuracy.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-item">
        <div class="icon">📊</div>
        <h4>Detailed Reports</h4>
        <p>Excel reports with findings organized by type, page, and custom grouping keywords.</p>
    </div>
    """, unsafe_allow_html=True)

col4, col5, col6 = st.columns(3)

with col4:
    st.markdown("""
    <div class="feature-item">
        <div class="icon">📦</div>
        <h4>Batch Processing</h4>
        <p>Process hundreds of PDFs simultaneously with consolidated cross-document analysis.</p>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown("""
    <div class="feature-item">
        <div class="icon">🔒</div>
        <h4>Privacy First</h4>
        <p>All processing done locally. Sensitive data anonymized in reports. No external data sharing.</p>
    </div>
    """, unsafe_allow_html=True)

with col6:
    st.markdown("""
    <div class="feature-item">
        <div class="icon">⚡</div>
        <h4>Fast & Efficient</h4>
        <p>Optimized processing with parallel conversion for large batches and real-time progress tracking.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Detection Capabilities & Info
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 🔍 What We Detect")

    with st.expander("**🏢 Organizations & Companies**", expanded=True):
        st.markdown("""
        - Company names and legal entities
        - Bank and financial institutions
        - Government agencies
        - Healthcare organizations
        """)

    with st.expander("**👤 Personal Information**"):
        st.markdown("""
        - Person names (first, last, full)
        - Email addresses
        - Phone numbers (various formats)
        - Physical addresses
        """)

    with st.expander("**💰 Financial Data**"):
        st.markdown("""
        - Account numbers
        - SSN / Tax IDs
        - Credit card numbers
        - Monetary amounts
        """)

with col_right:
    st.markdown("### 🛠️ Technology Stack")

    st.markdown("""
    <div style="margin: 1rem 0;">
        <span class="tech-badge">🔴 Adobe PDF Services</span>
        <span class="tech-badge">🧠 spaCy NLP</span>
        <span class="tech-badge">🐍 Python</span>
        <span class="tech-badge">🎨 Streamlit</span>
        <span class="tech-badge">📊 OpenPyXL</span>
        <span class="tech-badge">📄 python-docx</span>
        <span class="tech-badge">🔍 pdfplumber</span>
        <span class="tech-badge">📷 OCR Support</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    with st.expander("**📋 Supported Formats**"):
        st.markdown("""
        **Input:**
        - PDF files (native digital)
        - Scanned PDFs (with OCR)

        **Output:**
        - DOCX (Microsoft Word)
        - XLSX (Excel reports)
        - ZIP (batch downloads)
        """)

    with st.expander("**🔒 Privacy & Security**"):
        st.markdown("""
        - ✅ Local processing on your machine
        - ✅ Sensitive data anonymized in reports
        - ✅ No data sent to external servers*
        - ✅ Temporary files auto-deleted

        *Except Adobe API for PDF conversion
        """)

# Recent Activity (if any)
if history:
    st.markdown("---")
    st.markdown("### 📋 Recent Activity")

    # Show last 5 items
    recent = history[-5:][::-1]

    for item in recent:
        status_icon = "✅" if item.get('status') == 'success' else "⚠️" if item.get('status') == 'partial' else "❌"
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

        with col1:
            st.write(f"📄 **{item.get('pdf_name', 'Unknown')}**")
        with col2:
            st.write(f"🔧 {item.get('operation', 'N/A')}")
        with col3:
            st.write(status_icon)
        with col4:
            timestamp = item.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    st.caption(dt.strftime("%H:%M"))
                except:
                    st.caption("")

# Footer
st.markdown("""
<div class="footer-section">
    <p style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;">
        xAI PDF Converter v2.0.0
    </p>
    <p style="font-size: 0.9rem; opacity: 0.8;">
        © 2025 Conrad Vaslin - xAI Finance Tutor
    </p>
    <p style="font-size: 0.85rem; margin-top: 1rem;">
        Built with ❤️ using <strong>Streamlit</strong> |
        Powered by <strong>Adobe PDF Services</strong> & <strong>spaCy ML</strong>
    </p>
</div>
""", unsafe_allow_html=True)
