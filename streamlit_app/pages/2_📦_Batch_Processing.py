"""
📦 Batch Processing Page
"""

import streamlit as st
from pathlib import Path
import sys
import tempfile
import time
from typing import List

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Use adapter for compatibility
from utils.adapter import PDFConverter, ADOBE_API_CREDENTIALS
from utils.session import init_session_state, add_to_history, update_stats
from components.stats_cards import show_processing_stats, show_adobe_quota_sidebar
from utils.styles import apply_global_styles

# Page config
st.set_page_config(
    page_title="Batch Processing - xAI PDF Converter",
    page_icon="📦",
    layout="wide"
)

# Apply global styles
apply_global_styles()

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

# Upload section
st.markdown("### 📁 Upload Multiple PDFs")

uploaded_files = st.file_uploader(
    "Choose PDF files",
    type=['pdf'],
    accept_multiple_files=True,
    help="Upload multiple PDF files to process in batch"
)

if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} file(s) uploaded")

    # Show file list
    with st.expander(f"📋 View Files ({len(uploaded_files)})"):
        total_size = 0
        for idx, file in enumerate(uploaded_files, 1):
            file_size = file.size / 1024  # KB
            total_size += file_size
            st.write(f"{idx}. **{file.name}** ({file_size:.1f} KB)")

        st.info(f"Total size: {total_size:.1f} KB")

st.markdown("---")

# Options section
col_options1, col_options2 = st.columns(2)

with col_options1:
    st.markdown("### ⚙️ Processing Options")

    operation = st.radio(
        "Select Operation",
        ["Convert Only", "Analyze Only", "Convert + Analyze"],
        index=2,
        help="Choose what to do with the PDFs"
    )

with col_options2:
    st.markdown("### 🎯 Advanced Settings")

    grouping_keywords = st.text_area(
        "Grouping Keywords (one per line)",
        placeholder="Vantiv\nWorldPay\nFifth Third",
        help="Keywords to group in analysis reports"
    )

st.markdown("---")

# Processing section
if uploaded_files:
    st.markdown("### 🚀 Start Processing")

    col_btn, col_info = st.columns([1, 2])

    with col_btn:
        process_button = st.button(
            f"🚀 Process {len(uploaded_files)} Files",
            type="primary",
            width="stretch"
        )

    with col_info:
        st.info(f"Operation: {operation}")

    if process_button:
        # Create temp directory for PDFs
        temp_dir = Path(tempfile.mkdtemp(prefix='xai_batch_'))

        try:
            # Save all uploaded files
            st.write("📤 Uploading files...")
            progress_upload = st.progress(0)

            pdf_paths = []
            for idx, file in enumerate(uploaded_files):
                tmp_path = temp_dir / file.name
                with open(tmp_path, 'wb') as f:
                    f.write(file.getbuffer())
                pdf_paths.append(tmp_path)
                progress_upload.progress((idx + 1) / len(uploaded_files))

            st.success(f"✅ {len(pdf_paths)} files uploaded")

            # Create output directory
            output_dir = Path(st.session_state.settings['output_directory']) / f"batch_{int(time.time())}"
            output_dir.mkdir(parents=True, exist_ok=True)

            # Prepare options
            keywords = [k.strip() for k in grouping_keywords.split('\n') if k.strip()] if grouping_keywords else None

            # Check Adobe API
            if operation != "Analyze Only" and not ADOBE_API_CREDENTIALS:
                st.error("❌ Adobe API credentials not configured. Please configure in Settings.")
                st.stop()

            # Process batch
            st.markdown("---")
            st.markdown("### 🔄 Processing...")

            start_time = time.time()

            # Progress tracking
            progress_container = st.container()

            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
                current_file = st.empty()
                stats_row = st.empty()

                # Processing options
                do_conversion = operation in ["Convert Only", "Convert + Analyze"]
                do_analysis = operation in ["Analyze Only", "Convert + Analyze"]

                # Real-time stats tracking
                processed_count = [0]
                running_findings = [0]
                file_times = []

                def update_progress():
                    processed_count[0] += 1
                    progress = processed_count[0] / len(pdf_paths)
                    progress_bar.progress(progress)

                    # Calculate estimated time remaining
                    if file_times:
                        avg_time = sum(file_times) / len(file_times)
                        remaining_files = len(pdf_paths) - processed_count[0]
                        eta_seconds = avg_time * remaining_files
                        eta_str = f"~{eta_seconds:.0f}s restant" if eta_seconds > 0 else "Finalisation..."
                    else:
                        eta_str = "Calcul..."

                    status_text.text(f"📊 {processed_count[0]}/{len(pdf_paths)} fichiers | {eta_str}")

                    # Update real-time stats
                    stats_row.markdown(f"""
                    <div style="background: #f0f4ff; padding: 0.75rem 1rem; border-radius: 8px; display: flex; gap: 2rem;">
                        <span>🔍 <strong>{running_findings[0]}</strong> détections</span>
                        <span>✅ <strong>{processed_count[0]}</strong> traités</span>
                        <span>⏳ <strong>{len(pdf_paths) - processed_count[0]}</strong> en attente</span>
                    </div>
                    """, unsafe_allow_html=True)

                status_text.text("🚀 Démarrage du traitement...")

                # PDFConverter already imported from utils.adapter at top of file

                # Initialize converter
                converter = PDFConverter(
                    adobe_api_keys=ADOBE_API_CREDENTIALS if do_conversion else None,
                    use_ocr=False,  # Adobe handles OCR automatically
                    preserve_layout=True,
                    verbose=False
                )

                results = {
                    'successful': [],
                    'failed': [],
                    'total_findings': 0,
                    'total_pages': 0
                }

                # Data collection for consolidated report
                all_findings_by_pdf = {}
                all_images_by_pdf = {}

                # Process each PDF
                for idx, pdf_path in enumerate(pdf_paths):
                    file_start_time = time.time()
                    current_file.markdown(f"📄 **En cours:** `{pdf_path.name}`")

                    try:
                        # Conversion
                        docx_path = None
                        if do_conversion:
                            docx_path = converter.convert_pdf_to_docx(
                                pdf_path,
                                output_dir / f"{pdf_path.stem}.docx"
                            )

                        # Analysis
                        if do_analysis:
                            converter.analyze_sensitive_info(
                                pdf_path if not docx_path else docx_path,
                                grouping_keywords=keywords
                            )

                            # Generate individual report
                            from src.analysis.report_generator import create_excel_report

                            excel_path = output_dir / f"{pdf_path.stem} - analysis.xlsx"

                            create_excel_report(
                                report_path=excel_path,
                                pdf_path=pdf_path,
                                images_by_page=converter.images_by_page,
                                sensitive_info_by_page=converter.sensitive_info_by_page,
                                grouping_keywords=keywords
                            )

                            # Collect data for consolidated report (always enabled)
                            doc_filename = f"{pdf_path.stem}.docx"
                            all_findings_by_pdf[doc_filename] = converter.sensitive_info_by_page.copy()
                            all_images_by_pdf[doc_filename] = converter.images_by_page.copy()

                            # Count findings
                            total_findings = sum(len(findings) for findings in converter.sensitive_info_by_page.values())
                            results['total_findings'] += total_findings
                            results['total_pages'] += len(converter.sensitive_info_by_page)

                            # Update running findings count for real-time display
                            running_findings[0] += total_findings

                        results['successful'].append(pdf_path.name)

                    except Exception as e:
                        results['failed'].append({'file': pdf_path.name, 'error': str(e)})

                    # Track file processing time for ETA calculation
                    file_times.append(time.time() - file_start_time)

                    # Update progress
                    update_progress()

                # Generate consolidated report (always enabled for batch with analysis)
                if do_analysis and all_findings_by_pdf:
                    status_text.text("📊 Creating consolidated report...")

                    try:
                        from src.analysis.report_generator import create_consolidated_batch_report

                        consolidated_path = output_dir / "consolidated statements.xlsx"
                        create_consolidated_batch_report(
                            all_findings_by_pdf,
                            all_images_by_pdf,
                            consolidated_path,
                            grouping_keywords=keywords
                        )
                        st.success(f"✅ Consolidated report created: {consolidated_path.name}")
                    except Exception as e:
                        st.warning(f"⚠️ Could not create consolidated report: {e}")

            processing_time = time.time() - start_time

            # Results
            st.markdown("---")
            st.markdown("### ✅ Processing Complete!")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "✅ Successful",
                    len(results['successful'])
                )

            with col2:
                st.metric(
                    "❌ Failed",
                    len(results['failed'])
                )

            with col3:
                st.metric(
                    "⏱️ Time",
                    f"{processing_time:.1f}s"
                )

            # Detailed results
            if results['successful']:
                with st.expander(f"✅ Successful Files ({len(results['successful'])})"):
                    for file_name in results['successful']:
                        st.write(f"✓ {file_name}")

            if results['failed']:
                with st.expander(f"❌ Failed Files ({len(results['failed'])})"):
                    for failure in results['failed']:
                        st.error(f"✗ {failure['file']}: {failure['error']}")

            # Statistics
            if do_analysis:
                st.markdown("### 📊 Analysis Statistics")

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Total Findings", results['total_findings'])

                with col2:
                    st.metric("Total Pages", results['total_pages'])

            # Download results
            st.markdown("### 💾 Download Results")

            st.info(f"📁 Results saved to: {output_dir}")

            # List output files
            output_files = list(output_dir.glob('*'))
            if output_files:
                st.write(f"**{len(output_files)} file(s) generated:**")
                for file in output_files:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(f"📄 {file.name}")
                    with col2:
                        with open(file, 'rb') as f:
                            st.download_button(
                                label="⬇️",
                                data=f,
                                file_name=file.name,
                                key=f"download_{file.name}"
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
                    'processing_time': processing_time
                }
            )

        except Exception as e:
            st.error(f"❌ Batch processing failed: {str(e)}")

            add_to_history(
                pdf_name=f"Batch ({len(uploaded_files)} files)",
                operation=operation,
                status='error',
                details={'error': str(e)}
            )

        finally:
            # Cleanup temp files
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

else:
    # No files uploaded
    st.info("👆 Upload PDF files to get started")

    with st.expander("💡 How to use Batch Processing"):
        st.markdown("""
        **Batch Processing** allows you to process multiple PDFs at once:

        1. **Upload** multiple PDF files using the file uploader
        2. **Select** the operation:
           - **Convert Only**: Convert all PDFs to DOCX
           - **Analyze Only**: Detect sensitive information in all PDFs
           - **Convert + Analyze**: Do both (recommended)
        3. **Configure** options:
           - **OCR**: Enable for scanned PDFs
           - **Consolidated Report**: Create a single report combining all PDFs
           - **Grouping Keywords**: Organize companies in reports
        4. **Click** "Process Files" to start batch processing
        5. **Download** individual results or the entire batch

        **Benefits:**
        - Process 10+ PDFs in one go
        - Consolidated reporting across all documents
        - Automatic deduplication of findings
        - Batch download of all results

        **Tip:** Use consolidated reports to identify sensitive information that appears across multiple documents!
        """)
