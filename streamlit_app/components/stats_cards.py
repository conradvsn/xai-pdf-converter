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
except Exception:
    adobe_keys_count = 0


def get_adobe_quota_info():
    """Get Adobe API quota information from credentials manager or cloud storage"""
    try:
        # Try cloud storage first (for Streamlit Cloud)
        try:
            from utils.cloud_storage import get_cloud_storage, is_cloud_storage_available
            if is_cloud_storage_available():
                storage = get_cloud_storage()
                cloud_usage = storage.get_all_usage()

                # Get credentials info
                from utils.adapter import get_adobe_credentials
                credentials = get_adobe_credentials()

                if credentials:
                    summary = {}
                    for cred in credentials:
                        name = cred.get('name', 'default')
                        limit = cred.get('monthly_limit', 500)
                        usage_data = cloud_usage.get(name, {'count': 0})
                        used = usage_data.get('count', 0)

                        summary[name] = {
                            'used': used,
                            'limit': limit,
                            'remaining': limit - used,
                            'percentage': (used / limit * 100) if limit > 0 else 0
                        }

                    total_used = sum(data['used'] for data in summary.values())
                    total_limit = sum(data['limit'] for data in summary.values())

                    return {
                        'used': total_used,
                        'limit': total_limit,
                        'remaining': total_limit - total_used,
                        'percentage': (total_used / total_limit * 100) if total_limit > 0 else 0,
                        'accounts': summary,
                        'source': 'cloud'
                    }
        except Exception:
            pass  # Fall back to local storage

        # Fall back to local credentials manager
        from src.adobe_credentials_manager import get_credentials_manager
        manager = get_credentials_manager()
        summary = manager.get_usage_summary()

        total_used = sum(data['used'] for data in summary.values())
        total_limit = sum(data['limit'] for data in summary.values())
        total_remaining = total_limit - total_used
        percentage = (total_used / total_limit * 100) if total_limit > 0 else 0

        return {
            'used': total_used,
            'limit': total_limit,
            'remaining': total_remaining,
            'percentage': percentage,
            'accounts': summary,
            'source': 'local'
        }
    except Exception:
        return None


def show_adobe_quota_sidebar():
    """Display Adobe API quota in sidebar"""
    import os

    # Check if running on Streamlit Cloud
    is_cloud = (
        os.getenv('STREAMLIT_RUNTIME_ENVIRONMENT') == 'cloud' or
        os.path.exists('/mount/src') or
        os.path.exists('/home/appuser')
    )

    quota = get_adobe_quota_info()

    if quota is None:
        st.sidebar.warning("⚠️ Adobe quota unavailable")
        return

    st.sidebar.markdown("### 📊 Adobe API Quota")

    # Check if using cloud storage
    is_cloud_storage = quota.get('source') == 'cloud'

    # On cloud without cloud storage, show setup message
    if is_cloud and not is_cloud_storage and quota['used'] == 0:
        st.sidebar.info(f"☁️ {len(quota['accounts'])} account(s) configured")
        st.sidebar.caption("Set up Supabase for persistent tracking")
        with st.sidebar.expander("Available accounts"):
            for account_name, data in quota['accounts'].items():
                st.write(f"✅ **{account_name}**: {data['limit']}/month")
        return

    # Progress bar
    progress = quota['percentage'] / 100
    if progress > 0.9:
        st.sidebar.progress(progress, text=f"🔴 {quota['used']}/{quota['limit']}")
    elif progress > 0.7:
        st.sidebar.progress(progress, text=f"🟡 {quota['used']}/{quota['limit']}")
    else:
        st.sidebar.progress(progress, text=f"🟢 {quota['used']}/{quota['limit']}")

    # Show source indicator
    if is_cloud_storage:
        st.sidebar.caption(f"☁️ **{quota['remaining']}** remaining (cloud sync)")
    else:
        st.sidebar.caption(f"💾 **{quota['remaining']}** remaining (local)")

    # Show per-account breakdown
    with st.sidebar.expander("Account details"):
        for account_name, data in quota['accounts'].items():
            pct = data['percentage']
            icon = "🔴" if pct >= 90 else "🟡" if pct >= 70 else "🟢"
            st.write(f"{icon} **{account_name}**: {data['used']}/{data['limit']}")

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
