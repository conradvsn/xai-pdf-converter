"""
Statistics dashboard components
"""

import streamlit as st
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from utils.adapter import ADOBE_API_CREDENTIALS
    adobe_keys_count = len(ADOBE_API_CREDENTIALS)
except:
    adobe_keys_count = 0

def show_stats_dashboard():
    """Display main statistics dashboard"""

    # Get stats from session state
    stats = st.session_state.get('stats', {
        'total_pdfs_processed': 0,
        'total_pages_analyzed': 0,
        'total_findings': 0,
        'total_companies_detected': 0,
        'total_persons_detected': 0,
        'last_processed': None
    })

    # Create 4 columns for metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📄 PDFs Processed",
            value=stats['total_pdfs_processed'],
            delta=f"+{stats.get('last_batch_count', 0)}" if stats.get('last_batch_count', 0) > 0 else None
        )

    with col2:
        st.metric(
            label="📃 Pages Analyzed",
            value=stats['total_pages_analyzed'],
            delta=None
        )

    with col3:
        st.metric(
            label="🔍 Findings Detected",
            value=stats['total_findings'],
            delta=None
        )

    with col4:
        st.metric(
            label="🏢 Companies Found",
            value=stats['total_companies_detected'],
            delta=None
        )

    # System status row
    st.markdown("#### 🔧 System Status")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Adobe API status
        if adobe_keys_count > 0:
            st.success(f"✅ Adobe API: {adobe_keys_count} key(s)")
        else:
            st.warning("⚠️ Adobe API: Not configured")

    with col2:
        # spaCy status
        try:
            import spacy
            st.success("✅ spaCy: Available")
        except ImportError:
            st.warning("⚠️ spaCy: Not installed")

    with col3:
        # OCR status
        try:
            from adobe.pdfservices.operation.pdf_services import PDFServices
            st.success("✅ OCR: Available")
        except ImportError:
            st.warning("⚠️ OCR: Not available")

    with col4:
        # Output directory
        output_dir = Path(st.session_state.settings.get('output_directory', '~/Downloads/xAI_Output'))
        if output_dir.exists():
            st.success("✅ Output: Ready")
        else:
            st.info("ℹ️ Output: Will be created")

def show_processing_stats(results: dict):
    """Display statistics for a processing result"""

    if not results:
        st.info("No processing results available.")
        return

    # Summary metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Total Items Found",
            value=results.get('total_findings', 0)
        )

    with col2:
        st.metric(
            label="Pages Processed",
            value=results.get('pages_count', 0)
        )

    with col3:
        processing_time = results.get('processing_time', 0)
        st.metric(
            label="Processing Time",
            value=f"{processing_time:.1f}s"
        )

    # Breakdown by type
    if 'findings_by_type' in results:
        st.markdown("#### 📊 Findings Breakdown")

        findings = results['findings_by_type']

        # Create bar chart data
        chart_data = {
            'Type': [],
            'Count': []
        }

        type_labels = {
            'company_name': '🏢 Company Names',
            'person_name': '👤 Person Names',
            'email': '📧 Emails',
            'phone': '📞 Phone Numbers',
            'address': '📍 Addresses',
            'ssn': '🔢 SSN',
            'irs_ein': '🏛️ IRS EIN',
            'credit_card': '💳 Credit Cards',
            'website': '🌐 Websites'
        }

        for type_key, count in findings.items():
            if count > 0:
                chart_data['Type'].append(type_labels.get(type_key, type_key))
                chart_data['Count'].append(count)

        if chart_data['Type']:
            st.bar_chart(chart_data, x='Type', y='Count')
        else:
            st.info("No findings detected in this document.")

def show_recent_activity():
    """Display recent processing activity"""

    history = st.session_state.get('processing_history', [])

    if not history:
        st.info("No recent activity.")
        return

    st.markdown("#### 📜 Recent Activity")

    for entry in history[:5]:  # Show last 5
        timestamp = entry['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
        pdf_name = entry['pdf_name']
        operation = entry['operation']
        status = entry['status']

        # Status icon
        if status == 'success':
            icon = '✅'
            color = 'green'
        elif status == 'error':
            icon = '❌'
            color = 'red'
        else:
            icon = '⏳'
            color = 'orange'

        with st.expander(f"{icon} {pdf_name} - {operation} ({timestamp})"):
            st.markdown(f"**Status:** :{color}[{status.upper()}]")
            if 'details' in entry and entry['details']:
                st.json(entry['details'])
