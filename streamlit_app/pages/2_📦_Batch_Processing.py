"""
📦 Batch Processing Page - Enhanced Version
"""

import streamlit as st
from pathlib import Path
import sys
import tempfile
import time
import zipfile
import io
import shutil
from typing import List, Dict
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Use adapter for compatibility
from utils.adapter import PDFConverter, ADOBE_API_CREDENTIALS
from utils.session import init_session_state, add_to_history, update_stats
from components.stats_cards import show_processing_stats, show_adobe_quota_sidebar
from utils.styles import apply_global_styles

# Import exception for Adobe conversion errors
from src.converter import AdobeConversionError

# Page config
st.set_page_config(
    page_title="Batch Processing - xAI PDF Converter",
    page_icon="📦",
    layout="wide"
)

# Apply global styles
apply_global_styles()

# Enhanced styles for batch processing
st.markdown("""
<style>
    .file-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 0.5rem;
    }
    .stats-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }
    .stats-card h2 {
        margin: 0;
        font-size: 2rem;
        color: #495057;
    }
    .stats-card p {
        margin: 0.5rem 0 0 0;
        color: #6c757d;
        font-size: 0.9rem;
    }
    .success-banner {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin: 1rem 0;
    }
    .download-section {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .file-group {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .progress-container {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session
init_session_state()

# Show Adobe quota in sidebar
show_adobe_quota_sidebar()

# Modern header
st.markdown("""
<div class="page-header">
    <h1>📦 Batch Processing</h1>
    <p>Process multiple PDFs simultaneously with consolidated reports and cross-document analysis</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")


def format_size(size_bytes: float) -> str:
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes:.0f} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f} KB"
    else:
        return f"{size_bytes/(1024*1024):.2f} MB"


def format_time(seconds: float) -> str:
    """Format time in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"


# Upload section
col_upload, col_preview = st.columns([2, 1])

with col_upload:
    st.markdown("### 📁 Upload Multiple PDFs")

    uploaded_files = st.file_uploader(
        "Drag and drop PDF files here",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload multiple PDF files to process in batch"
    )

with col_preview:
    if uploaded_files:
        total_size = sum(f.size for f in uploaded_files)

        st.markdown("### 📊 Upload Summary")
        st.markdown(f"""
        <div class="stats-card">
            <h2>{len(uploaded_files)}</h2>
            <p>Files Selected</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="stats-card" style="margin-top: 0.5rem;">
            <h2>{format_size(total_size)}</h2>
            <p>Total Size</p>
        </div>
        """, unsafe_allow_html=True)

# File list with details
if uploaded_files:
    with st.expander(f"📋 View All Files ({len(uploaded_files)})", expanded=False):
        # Sort options
        sort_option = st.selectbox(
            "Sort by",
            ["Name (A-Z)", "Name (Z-A)", "Size (Largest)", "Size (Smallest)"],
            label_visibility="collapsed"
        )

        # Sort files
        sorted_files = list(uploaded_files)
        if sort_option == "Name (A-Z)":
            sorted_files.sort(key=lambda x: x.name.lower())
        elif sort_option == "Name (Z-A)":
            sorted_files.sort(key=lambda x: x.name.lower(), reverse=True)
        elif sort_option == "Size (Largest)":
            sorted_files.sort(key=lambda x: x.size, reverse=True)
        elif sort_option == "Size (Smallest)":
            sorted_files.sort(key=lambda x: x.size)

        # Display files in a table-like format
        for idx, file in enumerate(sorted_files, 1):
            col1, col2, col3 = st.columns([0.5, 3, 1])
            with col1:
                st.write(f"**{idx}.**")
            with col2:
                st.write(f"📄 {file.name}")
            with col3:
                st.write(format_size(file.size))

st.markdown("---")

# Options section
col_options1, col_options2 = st.columns(2)

with col_options1:
    st.markdown("### ⚙️ Processing Options")

    operation = st.radio(
        "Select Operation",
        ["Convert + Analyze", "Convert Only", "Analyze Only"],
        index=0,
        help="Choose what to do with the PDFs"
    )

    # Show what will be generated
    st.markdown("**Output files:**")
    if operation == "Convert + Analyze":
        st.markdown("- 📄 DOCX files (one per PDF)")
        st.markdown("- 📊 Excel reports (one per PDF)")
        st.markdown("- 📋 Consolidated report")
    elif operation == "Convert Only":
        st.markdown("- 📄 DOCX files (one per PDF)")
    else:
        st.markdown("- 📊 Excel reports (one per PDF)")
        st.markdown("- 📋 Consolidated report")

with col_options2:
    st.markdown("### 🎯 Advanced Settings")

    grouping_keywords = st.text_area(
        "Grouping Keywords (one per line)",
        placeholder="Vantiv\nWorldPay\nFifth Third",
        help="Keywords to group in analysis reports"
    )

    if grouping_keywords:
        keywords_list = [k.strip() for k in grouping_keywords.split('\n') if k.strip()]
        st.info(f"🏷️ {len(keywords_list)} keywords configured")

st.markdown("---")

# Processing section
if uploaded_files:
    col_btn, col_estimate = st.columns([1, 2])

    with col_btn:
        process_button = st.button(
            f"🚀 Process {len(uploaded_files)} Files",
            type="primary",
            use_container_width=True
        )

    with col_estimate:
        # Estimate processing time (rough: ~10s per file for convert+analyze)
        if operation == "Convert + Analyze":
            est_time = len(uploaded_files) * 10
        elif operation == "Convert Only":
            est_time = len(uploaded_files) * 5
        else:
            est_time = len(uploaded_files) * 3

        st.info(f"⏱️ Estimated time: {format_time(est_time)} | 🔧 Operation: {operation}")

    if process_button:
        # Create temp directory for PDFs
        temp_dir = Path(tempfile.mkdtemp(prefix='xai_batch_'))

        try:
            # Progress container
            st.markdown('<div class="progress-container">', unsafe_allow_html=True)

            # Upload phase
            with st.status("📤 Uploading files...", expanded=True) as status:
                pdf_paths = []
                total_upload_size = 0

                for idx, file in enumerate(uploaded_files):
                    tmp_path = temp_dir / file.name
                    with open(tmp_path, 'wb') as f:
                        f.write(file.getbuffer())
                    pdf_paths.append(tmp_path)
                    total_upload_size += file.size
                    st.write(f"✓ {file.name}")

                status.update(label=f"✅ {len(pdf_paths)} files uploaded ({format_size(total_upload_size)})", state="complete")

            # Create output directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path(st.session_state.settings['output_directory']) / f"batch_{timestamp}"
            output_dir.mkdir(parents=True, exist_ok=True)

            # Prepare options
            keywords = [k.strip() for k in grouping_keywords.split('\n') if k.strip()] if grouping_keywords else None

            # Check Adobe API
            if operation != "Analyze Only" and not ADOBE_API_CREDENTIALS:
                st.error("❌ Adobe API credentials not configured. Please configure in Settings.")
                st.stop()

            # Processing phase
            start_time = time.time()

            # Processing options
            do_conversion = operation in ["Convert Only", "Convert + Analyze"]
            do_analysis = operation in ["Analyze Only", "Convert + Analyze"]

            # Progress tracking
            progress_bar = st.progress(0, text="🚀 Starting batch processing...")

            col_status1, col_status2, col_status3, col_status4 = st.columns(4)
            metric_processed = col_status1.empty()
            metric_findings = col_status2.empty()
            metric_speed = col_status3.empty()
            metric_eta = col_status4.empty()

            current_file_display = st.empty()

            # Initialize converter
            converter = PDFConverter(
                adobe_api_keys=ADOBE_API_CREDENTIALS if do_conversion else None,
                use_ocr=False,
                preserve_layout=True,
                verbose=False
            )

            results = {
                'successful': [],
                'failed': [],
                'total_findings': 0,
                'total_pages': 0,
                'docx_files': [],
                'excel_files': [],
                'file_details': []
            }

            # Data collection for consolidated report
            all_findings_by_pdf = {}
            all_images_by_pdf = {}

            # Check if user has already chosen to use fallback for batch
            use_fallback_batch = st.session_state.get('use_pdf2docx_fallback_batch', False)
            adobe_failed_once = False

            file_times = []

            # Process each PDF
            for idx, pdf_path in enumerate(pdf_paths):
                file_start_time = time.time()
                current_file_display.markdown(f"📄 **Processing:** `{pdf_path.name}`")

                file_findings = 0
                file_pages = 0

                try:
                    # Conversion
                    docx_path = None
                    if do_conversion:
                        try:
                            docx_path = converter.convert_pdf_to_docx(
                                pdf_path,
                                output_dir / f"{pdf_path.stem}.docx",
                                allow_fallback=use_fallback_batch
                            )
                            if docx_path and docx_path.exists():
                                results['docx_files'].append(docx_path)
                        except AdobeConversionError as adobe_err:
                            if not adobe_failed_once:
                                adobe_failed_once = True
                                progress_bar.progress(0)
                                st.warning(f"⚠️ **Conversion Adobe échouée pour {pdf_path.name}:** {adobe_err}")

                                if adobe_err.can_fallback:
                                    st.markdown("""
                                    ---
                                    ### 🔄 Option de secours pour le batch

                                    La conversion Adobe a échoué. Voulez-vous utiliser **pdf2docx** pour tous les fichiers restants ?

                                    **Note:** La qualité sera inférieure à Adobe.
                                    """)

                                    col_yes, col_no = st.columns(2)
                                    with col_yes:
                                        if st.button("✅ Oui, utiliser pdf2docx pour tout", type="primary", key="batch_fallback_yes"):
                                            st.session_state['use_pdf2docx_fallback_batch'] = True
                                            st.rerun()
                                    with col_no:
                                        if st.button("❌ Non, annuler le batch", type="secondary", key="batch_fallback_no"):
                                            st.session_state['use_pdf2docx_fallback_batch'] = False
                                            st.error("Batch annulé par l'utilisateur.")
                                            st.stop()
                                    st.stop()
                                else:
                                    st.error("❌ Aucune méthode de conversion disponible.")
                                    st.stop()
                            else:
                                raise

                    # Analysis
                    if do_analysis:
                        converter.analyze_sensitive_info(
                            pdf_path if not docx_path else docx_path,
                            grouping_keywords=keywords
                        )

                        from src.analysis.report_generator import create_excel_report

                        excel_path = output_dir / f"{pdf_path.stem} - analysis.xlsx"

                        create_excel_report(
                            report_path=excel_path,
                            pdf_path=pdf_path,
                            images_by_page=converter.images_by_page,
                            sensitive_info_by_page=converter.sensitive_info_by_page,
                            grouping_keywords=keywords
                        )

                        if excel_path.exists():
                            results['excel_files'].append(excel_path)

                        doc_filename = f"{pdf_path.stem}.docx"
                        all_findings_by_pdf[doc_filename] = converter.sensitive_info_by_page.copy()
                        all_images_by_pdf[doc_filename] = converter.images_by_page.copy()

                        file_findings = sum(len(findings) for findings in converter.sensitive_info_by_page.values())
                        file_pages = len(converter.sensitive_info_by_page)

                        results['total_findings'] += file_findings
                        results['total_pages'] += file_pages

                    results['successful'].append(pdf_path.name)

                    # Store file details
                    results['file_details'].append({
                        'name': pdf_path.name,
                        'status': 'success',
                        'findings': file_findings,
                        'pages': file_pages,
                        'time': time.time() - file_start_time
                    })

                except Exception as e:
                    results['failed'].append({'file': pdf_path.name, 'error': str(e)})
                    results['file_details'].append({
                        'name': pdf_path.name,
                        'status': 'failed',
                        'error': str(e),
                        'time': time.time() - file_start_time
                    })

                # Track timing
                file_time = time.time() - file_start_time
                file_times.append(file_time)

                # Update progress
                progress = (idx + 1) / len(pdf_paths)
                progress_bar.progress(progress, text=f"Processing {idx + 1}/{len(pdf_paths)} files...")

                # Update metrics
                metric_processed.metric("✅ Processed", f"{idx + 1}/{len(pdf_paths)}")
                metric_findings.metric("🔍 Findings", results['total_findings'])

                if file_times:
                    avg_time = sum(file_times) / len(file_times)
                    speed = 1 / avg_time if avg_time > 0 else 0
                    metric_speed.metric("⚡ Speed", f"{speed:.1f} files/min" if speed < 1 else f"{speed*60:.0f} files/min")

                    remaining = len(pdf_paths) - (idx + 1)
                    eta = avg_time * remaining
                    metric_eta.metric("⏳ ETA", format_time(eta) if remaining > 0 else "Done!")

            # Generate consolidated report
            if do_analysis and all_findings_by_pdf:
                current_file_display.markdown("📊 **Creating consolidated report...**")

                try:
                    from src.analysis.report_generator import create_consolidated_batch_report

                    consolidated_path = output_dir / "📋 Consolidated Report.xlsx"
                    create_consolidated_batch_report(
                        all_findings_by_pdf,
                        all_images_by_pdf,
                        consolidated_path,
                        grouping_keywords=keywords
                    )
                    if consolidated_path.exists():
                        results['excel_files'].insert(0, consolidated_path)  # Add at beginning
                except Exception as e:
                    st.warning(f"⚠️ Could not create consolidated report: {e}")

            processing_time = time.time() - start_time
            current_file_display.empty()
            progress_bar.progress(1.0, text="✅ Processing complete!")

            st.markdown('</div>', unsafe_allow_html=True)

            # Reset fallback flag
            if 'use_pdf2docx_fallback_batch' in st.session_state:
                del st.session_state['use_pdf2docx_fallback_batch']

            # ============================================================
            # RESULTS SECTION
            # ============================================================

            st.markdown("---")

            # Success banner
            success_rate = len(results['successful']) / len(pdf_paths) * 100
            st.markdown(f"""
            <div class="success-banner">
                <h2 style="margin:0;">✅ Batch Processing Complete!</h2>
                <p style="margin:0.5rem 0 0 0; font-size: 1.1rem;">
                    {len(results['successful'])}/{len(pdf_paths)} files processed successfully ({success_rate:.0f}%) in {format_time(processing_time)}
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Stats row
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric("✅ Successful", len(results['successful']))
            with col2:
                st.metric("❌ Failed", len(results['failed']))
            with col3:
                st.metric("📄 Pages", results['total_pages'])
            with col4:
                st.metric("🔍 Findings", results['total_findings'])
            with col5:
                avg_speed = len(pdf_paths) / processing_time * 60 if processing_time > 0 else 0
                st.metric("⚡ Avg Speed", f"{avg_speed:.1f}/min")

            # Detailed results
            if results['failed']:
                with st.expander(f"❌ Failed Files ({len(results['failed'])})", expanded=True):
                    for failure in results['failed']:
                        st.error(f"**{failure['file']}**: {failure['error']}")

            if results['successful']:
                with st.expander(f"✅ Successful Files ({len(results['successful'])})"):
                    for detail in results['file_details']:
                        if detail['status'] == 'success':
                            col1, col2, col3 = st.columns([3, 1, 1])
                            with col1:
                                st.write(f"✓ {detail['name']}")
                            with col2:
                                st.write(f"🔍 {detail.get('findings', 0)}")
                            with col3:
                                st.write(f"⏱️ {detail['time']:.1f}s")

            # ============================================================
            # DOWNLOAD SECTION
            # ============================================================

            st.markdown("### 💾 Download Results")

            output_files = list(output_dir.glob('*'))

            if output_files:
                # Calculate total size
                total_output_size = sum(f.stat().st_size for f in output_files)

                # Create ZIP with all files
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for file in output_files:
                        zip_file.write(file, file.name)
                zip_buffer.seek(0)
                zip_size = len(zip_buffer.getvalue())

                # Main download button
                col_dl1, col_dl2 = st.columns([2, 1])

                with col_dl1:
                    st.download_button(
                        label=f"📦 Download All ({len(output_files)} files, {format_size(zip_size)})",
                        data=zip_buffer,
                        file_name=f"batch_results_{timestamp}.zip",
                        mime="application/zip",
                        type="primary",
                        use_container_width=True
                    )

                with col_dl2:
                    st.info(f"📁 {len(output_files)} files | {format_size(total_output_size)}")

                # Organized file downloads
                st.markdown("---")

                # Separate files by type
                docx_files = [f for f in output_files if f.suffix.lower() == '.docx']
                excel_files = [f for f in output_files if f.suffix.lower() == '.xlsx']
                other_files = [f for f in output_files if f.suffix.lower() not in ['.docx', '.xlsx']]

                # DOCX files
                if docx_files:
                    with st.expander(f"📄 Word Documents ({len(docx_files)})"):
                        for file in sorted(docx_files, key=lambda x: x.name.lower()):
                            col1, col2, col3 = st.columns([3, 1, 1])
                            with col1:
                                st.write(f"📄 {file.name}")
                            with col2:
                                st.write(format_size(file.stat().st_size))
                            with col3:
                                with open(file, 'rb') as f:
                                    st.download_button(
                                        label="⬇️",
                                        data=f.read(),
                                        file_name=file.name,
                                        key=f"dl_docx_{file.name}"
                                    )

                # Excel files
                if excel_files:
                    with st.expander(f"📊 Excel Reports ({len(excel_files)})", expanded=True):
                        # Consolidated report first (if exists)
                        consolidated = [f for f in excel_files if 'consolidated' in f.name.lower()]
                        individual = [f for f in excel_files if 'consolidated' not in f.name.lower()]

                        if consolidated:
                            st.markdown("**📋 Consolidated Report:**")
                            for file in consolidated:
                                col1, col2, col3 = st.columns([3, 1, 1])
                                with col1:
                                    st.write(f"📋 {file.name}")
                                with col2:
                                    st.write(format_size(file.stat().st_size))
                                with col3:
                                    with open(file, 'rb') as f:
                                        st.download_button(
                                            label="⬇️",
                                            data=f.read(),
                                            file_name=file.name,
                                            key=f"dl_excel_{file.name}",
                                            type="primary"
                                        )
                            st.markdown("---")

                        if individual:
                            st.markdown("**📊 Individual Reports:**")
                            for file in sorted(individual, key=lambda x: x.name.lower()):
                                col1, col2, col3 = st.columns([3, 1, 1])
                                with col1:
                                    st.write(f"📊 {file.name}")
                                with col2:
                                    st.write(format_size(file.stat().st_size))
                                with col3:
                                    with open(file, 'rb') as f:
                                        st.download_button(
                                            label="⬇️",
                                            data=f.read(),
                                            file_name=file.name,
                                            key=f"dl_excel_{file.name}"
                                        )

                # Other files
                if other_files:
                    with st.expander(f"📁 Other Files ({len(other_files)})"):
                        for file in sorted(other_files, key=lambda x: x.name.lower()):
                            col1, col2, col3 = st.columns([3, 1, 1])
                            with col1:
                                st.write(f"📁 {file.name}")
                            with col2:
                                st.write(format_size(file.stat().st_size))
                            with col3:
                                with open(file, 'rb') as f:
                                    st.download_button(
                                        label="⬇️",
                                        data=f.read(),
                                        file_name=file.name,
                                        key=f"dl_other_{file.name}"
                                    )

            # Update session stats
            update_stats(
                pdfs_count=len(results['successful']),
                pages_count=results['total_pages'],
                findings_count=results['total_findings']
            )

            # Add to history
            add_to_history(
                pdf_name=f"Batch ({len(uploaded_files)} files)",
                operation=operation,
                status='success' if not results['failed'] else 'partial',
                details={
                    'successful': len(results['successful']),
                    'failed': len(results['failed']),
                    'processing_time': processing_time,
                    'total_findings': results['total_findings'],
                    'total_pages': results['total_pages']
                }
            )

        except Exception as e:
            st.error(f"❌ Batch processing failed: {str(e)}")

            import traceback
            with st.expander("🔍 Error Details"):
                st.code(traceback.format_exc())

            add_to_history(
                pdf_name=f"Batch ({len(uploaded_files)} files)",
                operation=operation,
                status='error',
                details={'error': str(e)}
            )

        finally:
            # Cleanup temp files
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

else:
    # No files uploaded - show helpful information
    st.info("👆 Upload PDF files to get started")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### 🚀 Quick Start

        1. **Upload** multiple PDF files
        2. **Select** operation type
        3. **Click** Process
        4. **Download** results as ZIP
        """)

    with col2:
        st.markdown("""
        ### ✨ Features

        - ⚡ Fast parallel processing
        - 📦 One-click ZIP download
        - 📋 Consolidated reports
        - 🔍 Sensitive info detection
        """)

    with st.expander("💡 Tips & Best Practices"):
        st.markdown("""
        **Performance Tips:**
        - Process up to 50 files at once for best performance
        - Larger PDFs take longer to convert
        - Adobe conversion provides best quality

        **Grouping Keywords:**
        - Add company names to group findings
        - One keyword per line
        - Case-insensitive matching

        **Output Files:**
        - **DOCX**: Converted Word documents
        - **Excel Reports**: Findings per document
        - **Consolidated Report**: All findings in one file
        """)
