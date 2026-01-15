"""
📊 Results and History Page
"""

import streamlit as st
from pathlib import Path
import sys
import pandas as pd
from datetime import datetime, timedelta

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.session import init_session_state, get_history, clear_history, get_stats
from components.stats_cards import show_recent_activity
from utils.styles import apply_global_styles

# Page config
st.set_page_config(
    page_title="Results - xAI PDF Converter",
    page_icon="📊",
    layout="wide"
)

# Apply global styles
apply_global_styles()

# Initialize session
init_session_state()

# Import auth after page config
from auth.middleware import require_auth
from auth.ui import show_user_menu

# Require authentication
if not require_auth():
    st.stop()

# Show user menu in sidebar
show_user_menu()

# Modern header
st.markdown("""
<div class="page-header">
    <h1>📊 Results & History</h1>
    <p>Track your processing history, view statistics, and access previous results</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Statistics overview
st.markdown("### 📈 Overall Statistics")

stats = get_stats()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="📄 Total PDFs Processed",
        value=stats['total_pdfs_processed']
    )

with col2:
    st.metric(
        label="📃 Total Pages Analyzed",
        value=stats['total_pages_analyzed']
    )

with col3:
    st.metric(
        label="🔍 Total Findings",
        value=stats['total_findings']
    )

with col4:
    st.metric(
        label="🏢 Companies Detected",
        value=stats['total_companies_detected']
    )

# Last processed
if stats['last_processed']:
    time_ago = datetime.now() - stats['last_processed']
    if time_ago.days > 0:
        last_text = f"{time_ago.days} day(s) ago"
    elif time_ago.seconds > 3600:
        last_text = f"{time_ago.seconds // 3600} hour(s) ago"
    elif time_ago.seconds > 60:
        last_text = f"{time_ago.seconds // 60} minute(s) ago"
    else:
        last_text = "Just now"

    st.info(f"🕐 Last processed: {last_text}")

st.markdown("---")

# Processing history
st.markdown("### 📜 Processing History")

history = get_history(limit=50)

if history:
    # Filter options
    col_filter1, col_filter2, col_filter3 = st.columns([2, 2, 1])

    with col_filter1:
        status_filter = st.multiselect(
            "Filter by Status",
            ["success", "error", "partial"],
            default=["success", "error", "partial"]
        )

    with col_filter2:
        operation_filter = st.multiselect(
            "Filter by Operation",
            ["Convert to DOCX", "Analyze Only", "Convert + Analyze", "Convert Only"],
            default=["Convert to DOCX", "Analyze Only", "Convert + Analyze", "Convert Only"]
        )

    with col_filter3:
        if st.button("🗑️ Clear History", width="stretch"):
            if st.session_state.get('confirm_clear'):
                clear_history()
                st.success("✅ History cleared!")
                st.rerun()
            else:
                st.session_state['confirm_clear'] = True
                st.warning("⚠️ Click again to confirm")

    # Filter history
    filtered_history = [
        entry for entry in history
        if entry['status'] in status_filter and entry['operation'] in operation_filter
    ]

    if filtered_history:
        st.write(f"Showing **{len(filtered_history)}** of **{len(history)}** entries")

        # Create DataFrame for better display
        history_data = []
        for entry in filtered_history:
            history_data.append({
                'Timestamp': entry['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                'File': entry['pdf_name'],
                'Operation': entry['operation'],
                'Status': entry['status'].upper(),
                'Details': str(entry.get('details', {}))
            })

        df = pd.DataFrame(history_data)

        # Display with color coding
        def highlight_status(row):
            if row['Status'] == 'SUCCESS':
                return ['background-color: #d4edda'] * len(row)
            elif row['Status'] == 'ERROR':
                return ['background-color: #f8d7da'] * len(row)
            else:
                return ['background-color: #fff3cd'] * len(row)

        st.dataframe(
            df.style.apply(highlight_status, axis=1),
            width="stretch",
            hide_index=True
        )

        # Detailed view in expanders
        st.markdown("#### 🔍 Detailed View")

        for idx, entry in enumerate(filtered_history[:10]):  # Show first 10 detailed
            timestamp = entry['timestamp'].strftime("%Y-%m-%d %H:%M:%S")

            # Status icon
            if entry['status'] == 'success':
                icon = '✅'
            elif entry['status'] == 'error':
                icon = '❌'
            else:
                icon = '⚠️'

            with st.expander(f"{icon} {entry['pdf_name']} - {timestamp}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Operation:**", entry['operation'])
                    st.write("**Status:**", entry['status'].upper())

                with col2:
                    if 'details' in entry and entry['details']:
                        if 'processing_time' in entry['details']:
                            st.write("**Time:**", f"{entry['details']['processing_time']:.1f}s")
                        if 'total_findings' in entry['details']:
                            st.write("**Findings:**", entry['details']['total_findings'])
                        if 'pages' in entry['details']:
                            st.write("**Pages:**", entry['details']['pages'])

                # Show full details
                if 'details' in entry and entry['details']:
                    st.json(entry['details'])

    else:
        st.info("No entries match the selected filters.")

else:
    st.info("📭 No processing history yet. Process some PDFs to see results here!")

st.markdown("---")

# Output directory browser
st.markdown("### 📁 Output Files")

# Detect if running on Streamlit Cloud
import os
is_cloud = (
    os.getenv('STREAMLIT_RUNTIME_ENVIRONMENT') == 'cloud' or
    os.path.exists('/mount/src') or
    os.path.exists('/home/appuser')
)

if is_cloud:
    # On cloud, files are downloaded directly - no persistent storage
    st.info("""
    **☁️ Cloud Mode - Direct Downloads**

    On Streamlit Cloud, all processed files are:
    - ✅ Available for immediate download after processing
    - 💾 Downloaded directly to your browser
    - 🔄 Temporary (cleaned up after session ends)

    💡 Tip: Download your files right after processing!
    """)
else:
    # Local mode - show file browser
    output_dir = Path(st.session_state.settings['output_directory'])

    if output_dir.exists():
        # List all subdirectories (batch folders)
        batch_folders = [d for d in output_dir.iterdir() if d.is_dir()]
        batch_folders.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # List all files in main directory
        main_files = [f for f in output_dir.iterdir() if f.is_file()]
        main_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        total_files = len(main_files) + sum(len(list(d.glob('*'))) for d in batch_folders)

        st.info(f"📂 Output directory: `{output_dir}`")
        st.write(f"**{total_files}** file(s) in **{len(batch_folders) + 1}** location(s)")

        # Tabs for main files and batch folders
        if batch_folders:
            tabs = st.tabs(["📄 Recent Files"] + [f"📦 {d.name}" for d in batch_folders[:5]])

            # Main files tab
            with tabs[0]:
                if main_files:
                    for file in main_files[:20]:  # Show first 20
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                        with col1:
                            st.text(f"📄 {file.name}")

                        with col2:
                            file_size = file.stat().st_size / 1024  # KB
                            st.text(f"{file_size:.1f} KB")

                        with col3:
                            mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                            time_diff = datetime.now() - mod_time
                            if time_diff.days > 0:
                                st.text(f"{time_diff.days}d ago")
                            elif time_diff.seconds > 3600:
                                st.text(f"{time_diff.seconds // 3600}h ago")
                            else:
                                st.text(f"{time_diff.seconds // 60}m ago")

                        with col4:
                            with open(file, 'rb') as f:
                                st.download_button(
                                    label="⬇️",
                                    data=f,
                                    file_name=file.name,
                                    key=f"download_main_{file.name}"
                                )

                    if len(main_files) > 20:
                        st.info(f"... and {len(main_files) - 20} more files")
                else:
                    st.info("No files in main directory")

            # Batch folder tabs
            for idx, folder in enumerate(batch_folders[:5], 1):
                with tabs[idx]:
                    folder_files = list(folder.glob('*'))

                    if folder_files:
                        st.write(f"**{len(folder_files)}** file(s)")

                        for file in folder_files[:20]:
                            col1, col2, col3 = st.columns([4, 1, 1])

                            with col1:
                                st.text(f"📄 {file.name}")

                            with col2:
                                file_size = file.stat().st_size / 1024
                                st.text(f"{file_size:.1f} KB")

                            with col3:
                                with open(file, 'rb') as f:
                                    st.download_button(
                                        label="⬇️",
                                        data=f,
                                        file_name=file.name,
                                        key=f"download_batch_{folder.name}_{file.name}"
                                    )

                        if len(folder_files) > 20:
                            st.info(f"... and {len(folder_files) - 20} more files")
                    else:
                        st.info("Empty folder")

        else:
            # No batch folders, just show main files
            if main_files:
                for file in main_files[:30]:
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                    with col1:
                        st.text(f"📄 {file.name}")

                    with col2:
                        file_size = file.stat().st_size / 1024
                        st.text(f"{file_size:.1f} KB")

                    with col3:
                        mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                        st.text(mod_time.strftime("%Y-%m-%d %H:%M"))

                    with col4:
                        with open(file, 'rb') as f:
                            st.download_button(
                                label="⬇️",
                                data=f,
                                file_name=file.name,
                                key=f"download_{file.name}"
                            )

                if len(main_files) > 30:
                    st.info(f"... and {len(main_files) - 30} more files")
            else:
                st.info("No output files yet. Process some PDFs to see results here!")

    else:
        st.warning(f"⚠️ Output directory does not exist: `{output_dir}`")
        if st.button("📁 Create Output Directory"):
            output_dir.mkdir(parents=True, exist_ok=True)
            st.success(f"✅ Created: {output_dir}")
            st.rerun()
