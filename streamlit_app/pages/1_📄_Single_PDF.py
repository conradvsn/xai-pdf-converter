"""
📄 Single PDF Processing Page - Enhanced Version
"""

import streamlit as st
from pathlib import Path
import sys
import tempfile
import time
import zipfile
import io
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Use adapter for compatibility
from utils.adapter import PDFConverter, ADOBE_API_CREDENTIALS
from utils.session import init_session_state, add_to_history, update_stats, save_result
from components.stats_cards import show_processing_stats, show_adobe_quota_sidebar
from utils.styles import apply_global_styles

# Import exception for Adobe conversion errors
from src.converter import AdobeConversionError

# Page config
st.set_page_config(
    page_title="Single PDF - xAI PDF Converter",
    page_icon="📄",
    layout="wide"
)

# Apply global styles
apply_global_styles()

# Enhanced styles
st.markdown("""
<style>
    .file-info-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    .file-info-card h3 {
        margin: 0 0 0.5rem 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    .file-info-card h2 {
        margin: 0;
        font-size: 1.4rem;
        word-break: break-all;
    }
    .file-info-card .size {
        margin-top: 0.5rem;
        opacity: 0.8;
        font-size: 0.9rem;
    }
    .stats-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
    }
    .stats-card h2 {
        margin: 0;
        font-size: 1.8rem;
        color: #495057;
    }
    .stats-card p {
        margin: 0.25rem 0 0 0;
        color: #6c757d;
        font-size: 0.85rem;
    }
    .success-banner {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin: 1rem 0;
    }
    .download-card {
        background: white;
        border: 2px solid #e9ecef;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.2s;
    }
    .download-card:hover {
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }
    .step-indicator {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1rem;
        background: #f8f9fa;
        border-radius: 8px;
        margin: 0.25rem 0;
    }
    .step-indicator.active {
        background: #e7f1ff;
        border-left: 3px solid #667eea;
    }
    .step-indicator.complete {
        background: #e6f7ef;
        border-left: 3px solid #38ef7d;
    }
    .finding-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        background: #667eea;
        color: white;
        border-radius: 20px;
        font-size: 0.85rem;
        margin: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session
init_session_state()

# Show Adobe quota in sidebar
show_adobe_quota_sidebar()


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
    else:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"


# Modern header
st.markdown("""
<div class="page-header">
    <h1>📄 Single PDF Processing</h1>
    <p>Convert and analyze individual PDF files with precision and detailed reporting</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# Main layout
col_upload, col_options = st.columns([1, 1])

with col_upload:
    st.markdown("### 📁 Upload PDF")

    uploaded_file = st.file_uploader(
        "Drag and drop a PDF file here",
        type=['pdf'],
        help="Upload a PDF file to convert and/or analyze"
    )

    if uploaded_file:
        file_size = uploaded_file.size

        # Beautiful file info card
        st.markdown(f"""
        <div class="file-info-card">
            <h3>📄 Selected File</h3>
            <h2>{uploaded_file.name}</h2>
            <div class="size">📦 {format_size(file_size)}</div>
        </div>
        """, unsafe_allow_html=True)

with col_options:
    st.markdown("### ⚙️ Processing Options")

    # Operation mode with better descriptions
    operation = st.radio(
        "Select Operation",
        ["Convert + Analyze", "Convert to DOCX", "Analyze Only"],
        index=0,
        help="Choose what to do with the PDF"
    )

    # Show what will be generated
    st.markdown("**Output files:**")
    if operation == "Convert + Analyze":
        st.markdown("- 📄 Word document (DOCX)")
        st.markdown("- 📊 Excel analysis report")
    elif operation == "Convert to DOCX":
        st.markdown("- 📄 Word document (DOCX)")
    else:
        st.markdown("- 📊 Excel analysis report")

    # Advanced options
    with st.expander("🎯 Advanced Options"):
        grouping_keywords = st.text_input(
            "Grouping Keywords (comma-separated)",
            placeholder="e.g., Vantiv, WorldPay, Fifth Third",
            help="Keywords to group in analysis report"
        )

        if grouping_keywords:
            keywords_list = [k.strip() for k in grouping_keywords.split(',') if k.strip()]
            st.info(f"🏷️ {len(keywords_list)} keywords: {', '.join(keywords_list)}")

st.markdown("---")

# Processing section
if uploaded_file:
    # Estimate time
    est_time = 5 if operation == "Convert to DOCX" else 8 if operation == "Analyze Only" else 12

    col_btn, col_info = st.columns([1, 2])

    with col_btn:
        process_button = st.button(
            "🚀 Start Processing",
            type="primary",
            use_container_width=True
        )

    with col_info:
        st.info(f"⏱️ Estimated time: ~{est_time}s | 🔧 {operation}")

    if process_button:
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_pdf_path = Path(tmp_file.name)

        try:
            # Create output directory
            output_dir = Path(st.session_state.settings['output_directory'])
            output_dir.mkdir(parents=True, exist_ok=True)

            # Check if Adobe API is configured
            if not ADOBE_API_CREDENTIALS and operation in ["Convert to DOCX", "Convert + Analyze"]:
                st.error("❌ Adobe API credentials not configured. Please configure in Settings.")
                st.stop()

            # Processing container
            st.markdown("### 🔄 Processing...")

            # Progress with steps
            progress_bar = st.progress(0, text="Initializing...")

            col_step1, col_step2, col_step3 = st.columns(3)

            with col_step1:
                step1_placeholder = st.empty()
            with col_step2:
                step2_placeholder = st.empty()
            with col_step3:
                step3_placeholder = st.empty()

            def update_step(step_num, status="active"):
                steps = [
                    ("1️⃣ Initialize", step1_placeholder),
                    ("2️⃣ Convert", step2_placeholder),
                    ("3️⃣ Analyze", step3_placeholder)
                ]

                for i, (label, placeholder) in enumerate(steps):
                    if i + 1 < step_num:
                        placeholder.success(f"✅ {label}")
                    elif i + 1 == step_num:
                        if status == "active":
                            placeholder.info(f"⏳ {label}")
                        elif status == "complete":
                            placeholder.success(f"✅ {label}")
                    else:
                        placeholder.empty()

            # Step 1: Initialize
            update_step(1, "active")
            progress_bar.progress(10, text="🔧 Initializing converter...")

            converter = PDFConverter(
                adobe_api_keys=ADOBE_API_CREDENTIALS if operation != "Analyze Only" else None,
                use_ocr=False,
                preserve_layout=True,
                verbose=False
            )

            start_time = time.time()
            update_step(1, "complete")

            # Step 2: Conversion (if needed)
            docx_path = None
            if operation in ["Convert to DOCX", "Convert + Analyze"]:
                update_step(2, "active")
                progress_bar.progress(30, text="📄 Converting PDF to DOCX...")

                use_fallback = st.session_state.get('use_pdf2docx_fallback', False)

                try:
                    docx_path = converter.convert_pdf_to_docx(
                        tmp_pdf_path,
                        output_dir / f"{uploaded_file.name.replace('.pdf', '.docx')}",
                        allow_fallback=use_fallback
                    )
                except AdobeConversionError as adobe_err:
                    progress_bar.progress(0)
                    st.warning(f"⚠️ **Conversion Adobe échouée:** {adobe_err}")

                    if adobe_err.can_fallback:
                        st.markdown("""
                        ---
                        ### 🔄 Option de secours disponible

                        La conversion Adobe a échoué, mais vous pouvez utiliser **pdf2docx** comme méthode alternative.

                        **Note:** La qualité de pdf2docx est généralement inférieure à Adobe:
                        - ❌ Moins bonne préservation de la mise en page
                        - ❌ Problèmes possibles avec les tableaux complexes
                        - ❌ Pas de support OCR natif pour les PDFs scannés

                        **Voulez-vous utiliser pdf2docx pour ce fichier ?**
                        """)

                        col_yes, col_no = st.columns(2)
                        with col_yes:
                            if st.button("✅ Oui, utiliser pdf2docx", type="primary", key="fallback_yes"):
                                st.session_state['use_pdf2docx_fallback'] = True
                                st.rerun()
                        with col_no:
                            if st.button("❌ Non, annuler", type="secondary", key="fallback_no"):
                                st.session_state['use_pdf2docx_fallback'] = False
                                st.error("Conversion annulée par l'utilisateur.")
                                st.stop()
                        st.stop()
                    else:
                        st.error("""
                        ❌ **Aucune méthode de conversion disponible.**

                        Veuillez configurer Adobe PDF Services dans les paramètres ou installer pdf2docx:
                        ```
                        pip install pdf2docx
                        ```
                        """)
                        st.stop()

                if 'use_pdf2docx_fallback' in st.session_state:
                    del st.session_state['use_pdf2docx_fallback']

                if not (docx_path and docx_path.exists()):
                    st.error("❌ Conversion failed")
                    st.stop()

                update_step(2, "complete")
                progress_bar.progress(50, text="✅ Conversion complete!")

            # Step 3: Analysis (if needed)
            analysis_results = None
            excel_path = None

            if operation in ["Analyze Only", "Convert + Analyze"]:
                update_step(3, "active")
                progress_bar.progress(60, text="🔍 Analyzing sensitive information...")

                keywords = [k.strip() for k in grouping_keywords.split(',')] if grouping_keywords else None

                analysis_results = converter.analyze_sensitive_info(
                    tmp_pdf_path if operation == "Analyze Only" else docx_path,
                    grouping_keywords=keywords
                )

                progress_bar.progress(80, text="📊 Generating Excel report...")

                if analysis_results:
                    from src.analysis.report_generator import create_excel_report

                    excel_path = output_dir / f"{uploaded_file.name.replace('.pdf', ' - analysis.xlsx')}"

                    create_excel_report(
                        report_path=excel_path,
                        pdf_path=tmp_pdf_path,
                        images_by_page=converter.images_by_page,
                        sensitive_info_by_page=converter.sensitive_info_by_page,
                        grouping_keywords=keywords
                    )

                update_step(3, "complete")

            progress_bar.progress(100, text="✅ Processing complete!")

            processing_time = time.time() - start_time

            # Calculate statistics
            total_findings = sum(len(findings) for findings in converter.sensitive_info_by_page.values())
            findings_by_type = {}

            for page_findings in converter.sensitive_info_by_page.values():
                for finding in page_findings:
                    finding_type = finding['type']
                    findings_by_type[finding_type] = findings_by_type.get(finding_type, 0) + 1

            pages_count = len(converter.sensitive_info_by_page)
            companies_count = findings_by_type.get('company_name', 0)
            persons_count = findings_by_type.get('person_name', 0)

            # Update session stats
            update_stats(
                pdfs_count=1,
                pages_count=pages_count,
                findings_count=total_findings,
                companies_count=companies_count,
                persons_count=persons_count
            )

            # Add to history
            add_to_history(
                pdf_name=uploaded_file.name,
                operation=operation,
                status='success',
                details={
                    'processing_time': processing_time,
                    'total_findings': total_findings,
                    'pages': pages_count
                }
            )

            # Save results
            result_data = {
                'total_findings': total_findings,
                'pages_count': pages_count,
                'processing_time': processing_time,
                'findings_by_type': findings_by_type,
                'docx_path': str(docx_path) if docx_path else None,
                'excel_path': str(excel_path) if excel_path else None
            }

            save_result(uploaded_file.name, result_data)

            # ============================================================
            # RESULTS SECTION
            # ============================================================

            st.markdown("---")

            # Success banner
            st.markdown(f"""
            <div class="success-banner">
                <h2 style="margin:0;">✅ Processing Complete!</h2>
                <p style="margin:0.5rem 0 0 0; font-size: 1.1rem;">
                    {uploaded_file.name} processed in {format_time(processing_time)}
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Stats cards
            if operation in ["Analyze Only", "Convert + Analyze"]:
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.markdown(f"""
                    <div class="stats-card">
                        <h2>{pages_count}</h2>
                        <p>📄 Pages</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div class="stats-card">
                        <h2>{total_findings}</h2>
                        <p>🔍 Findings</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                    <div class="stats-card">
                        <h2>{companies_count}</h2>
                        <p>🏢 Companies</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col4:
                    st.markdown(f"""
                    <div class="stats-card">
                        <h2>{persons_count}</h2>
                        <p>👤 Persons</p>
                    </div>
                    """, unsafe_allow_html=True)

            # ============================================================
            # DOWNLOAD SECTION
            # ============================================================

            st.markdown("### 💾 Download Results")

            # Prepare files for download
            output_files = []
            if docx_path and docx_path.exists():
                output_files.append(('docx', docx_path))
            if excel_path and excel_path.exists():
                output_files.append(('excel', excel_path))

            if len(output_files) > 1:
                # Create ZIP with all files
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for _, file_path in output_files:
                        zip_file.write(file_path, file_path.name)
                zip_buffer.seek(0)

                # Download All button
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label=f"📦 Download All ({len(output_files)} files)",
                    data=zip_buffer,
                    file_name=f"{uploaded_file.name.replace('.pdf', '')}_{timestamp}.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True
                )

                st.markdown("---")

            # Individual download buttons
            col1, col2 = st.columns(2)

            with col1:
                if docx_path and docx_path.exists():
                    docx_size = docx_path.stat().st_size
                    with open(docx_path, 'rb') as f:
                        docx_data = f.read()

                    st.markdown(f"""
                    <div style="text-align: center; margin-bottom: 0.5rem;">
                        <span style="font-size: 2rem;">📄</span><br>
                        <strong>Word Document</strong><br>
                        <span style="color: #6c757d; font-size: 0.85rem;">{format_size(docx_size)}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    st.download_button(
                        label="⬇️ Download DOCX",
                        data=docx_data,
                        file_name=docx_path.name,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )

            with col2:
                if excel_path and excel_path.exists():
                    excel_size = excel_path.stat().st_size
                    with open(excel_path, 'rb') as f:
                        excel_data = f.read()

                    st.markdown(f"""
                    <div style="text-align: center; margin-bottom: 0.5rem;">
                        <span style="font-size: 2rem;">📊</span><br>
                        <strong>Excel Report</strong><br>
                        <span style="color: #6c757d; font-size: 0.85rem;">{format_size(excel_size)}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    st.download_button(
                        label="⬇️ Download Excel",
                        data=excel_data,
                        file_name=excel_path.name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

            # ============================================================
            # FINDINGS PREVIEW
            # ============================================================

            if analysis_results and total_findings > 0:
                st.markdown("---")
                st.markdown("### 🔍 Findings Preview")

                # Summary badges
                st.markdown("**Found categories:**")
                badges_html = ""
                for f_type, count in sorted(findings_by_type.items(), key=lambda x: x[1], reverse=True):
                    display_type = f_type.replace('_', ' ').title()
                    badges_html += f'<span class="finding-badge">{display_type}: {count}</span>'
                st.markdown(badges_html, unsafe_allow_html=True)

                st.markdown("")

                # Group findings by type
                findings_preview = {}
                for page_num, findings in converter.sensitive_info_by_page.items():
                    for finding in findings:
                        f_type = finding['type']
                        if f_type not in findings_preview:
                            findings_preview[f_type] = []
                        if len(findings_preview[f_type]) < 50:  # Limit preview
                            findings_preview[f_type].append(finding)

                # Display in tabs
                if findings_preview:
                    tab_names = [f"{k.replace('_', ' ').title()} ({len(v)})" for k, v in findings_preview.items()]
                    tabs = st.tabs(tab_names)

                    for idx, (f_type, findings) in enumerate(findings_preview.items()):
                        with tabs[idx]:
                            # Show as a clean table
                            for finding in findings[:20]:
                                col1, col2 = st.columns([1, 4])
                                with col1:
                                    st.caption(f"Page {finding['page']}")
                                with col2:
                                    st.text(finding['value'])

                            if len(findings) > 20:
                                remaining = findings_by_type.get(f_type, 0) - 20
                                st.info(f"📋 {remaining} more items in Excel report")

        except Exception as e:
            st.error(f"❌ Processing failed: {str(e)}")

            import traceback
            with st.expander("🔍 Error Details"):
                st.code(traceback.format_exc())

            add_to_history(
                pdf_name=uploaded_file.name,
                operation=operation,
                status='error',
                details={'error': str(e)}
            )

        finally:
            # Cleanup temp file
            if tmp_pdf_path.exists():
                tmp_pdf_path.unlink()

else:
    # No file uploaded - show helpful information
    st.info("👆 Upload a PDF file to get started")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### 🚀 Quick Start

        1. **Upload** a PDF file
        2. **Select** operation type
        3. **Click** Process
        4. **Download** results
        """)

    with col2:
        st.markdown("""
        ### ✨ Features

        - 🔄 PDF to DOCX conversion
        - 🔍 Sensitive info detection
        - 📊 Detailed Excel reports
        - ⚡ Fast processing
        """)

    with st.expander("💡 Tips & Best Practices"):
        st.markdown("""
        **Conversion Tips:**
        - Adobe conversion provides the best quality
        - Complex layouts and tables are preserved
        - Scanned PDFs are automatically OCR'd

        **Analysis Features:**
        - Detects company names, person names, addresses
        - Finds emails, phone numbers, SSNs
        - Identifies financial information

        **Grouping Keywords:**
        - Add company names to organize findings
        - Separate keywords with commas
        - Case-insensitive matching
        """)

    # Show what's detected
    with st.expander("🔍 What We Detect"):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            **🏢 Organizations**
            - Company names
            - Bank names
            - Institution names
            """)

        with col2:
            st.markdown("""
            **👤 Personal Info**
            - Person names
            - Email addresses
            - Phone numbers
            """)

        with col3:
            st.markdown("""
            **💰 Financial**
            - Account numbers
            - SSN / Tax IDs
            - Monetary amounts
            """)
