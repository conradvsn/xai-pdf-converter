"""
📄 Single PDF Processing Page
"""

import streamlit as st
from pathlib import Path
import sys
import tempfile
import time

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

# Initialize session
init_session_state()

# Show Adobe quota in sidebar
show_adobe_quota_sidebar()

# Modern header
st.markdown("""
<div class="page-header">
    <h1>📄 Single PDF Processing</h1>
    <p>Convert and analyze individual PDF files with precision and detailed reporting</p>
</div>
""", unsafe_allow_html=True)
st.markdown("Upload and process a single PDF file with conversion and analysis options.")
st.markdown("---")

# Main layout
col_upload, col_options = st.columns([1, 1])

with col_upload:
    st.markdown("### 📁 Upload PDF")

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload a PDF file to convert and/or analyze"
    )

    if uploaded_file:
        # Display file info
        file_size = uploaded_file.size / 1024  # KB
        st.info(f"📎 **{uploaded_file.name}** ({file_size:.1f} KB)")

        # File preview info
        with st.expander("📋 File Details"):
            st.write(f"**Name:** {uploaded_file.name}")
            st.write(f"**Size:** {file_size:.2f} KB")
            st.write(f"**Type:** {uploaded_file.type}")

with col_options:
    st.markdown("### ⚙️ Processing Options")

    # Operation mode
    operation = st.radio(
        "Select Operation",
        ["Convert to DOCX", "Analyze Only", "Convert + Analyze"],
        index=2,
        help="Choose what to do with the PDF"
    )

    # Advanced options in expander
    with st.expander("🔧 Advanced Options"):
        grouping_keywords = st.text_input(
            "Grouping Keywords (comma-separated)",
            placeholder="e.g., Vantiv, WorldPay, Fifth Third",
            help="Keywords to group in analysis report"
        )

st.markdown("---")

# Processing section
if uploaded_file:
    col_process, col_status = st.columns([1, 2])

    with col_process:
        process_button = st.button(
            "🚀 Start Processing",
            type="primary",
            width="stretch"
        )

    with col_status:
        status_placeholder = st.empty()

    if process_button:
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_pdf_path = Path(tmp_file.name)

        try:
            # Create output directory
            output_dir = Path(st.session_state.settings['output_directory'])
            output_dir.mkdir(parents=True, exist_ok=True)

            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Initialize converter
            status_text.text("🔧 Initializing converter...")
            progress_bar.progress(10)

            # Check if Adobe API is configured
            if not ADOBE_API_CREDENTIALS and operation in ["Convert to DOCX", "Convert + Analyze"]:
                st.error("❌ Adobe API credentials not configured. Please configure in Settings.")
                st.stop()

            converter = PDFConverter(
                adobe_api_keys=ADOBE_API_CREDENTIALS if operation != "Analyze Only" else None,
                use_ocr=False,  # Adobe handles OCR automatically
                preserve_layout=True,
                verbose=False
            )

            start_time = time.time()

            # Step 1: Conversion (if needed)
            docx_path = None
            if operation in ["Convert to DOCX", "Convert + Analyze"]:
                status_text.text("📄 Converting PDF to DOCX (Adobe PDF Services)...")
                progress_bar.progress(30)

                # Check if user has already chosen to use fallback
                use_fallback = st.session_state.get('use_pdf2docx_fallback', False)

                try:
                    with st.spinner("Converting PDF to DOCX with Adobe..."):
                        docx_path = converter.convert_pdf_to_docx(
                            tmp_pdf_path,
                            output_dir / f"{uploaded_file.name.replace('.pdf', '.docx')}",
                            allow_fallback=use_fallback
                        )
                except AdobeConversionError as adobe_err:
                    # Adobe conversion failed - show warning and ask user
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

                # Reset fallback flag after successful conversion
                if 'use_pdf2docx_fallback' in st.session_state:
                    del st.session_state['use_pdf2docx_fallback']

                if docx_path and docx_path.exists():
                    st.success(f"✅ Conversion complete: {docx_path.name}")
                else:
                    st.error("❌ Conversion failed")
                    st.stop()

                progress_bar.progress(50)

            # Step 2: Analysis (if needed)
            analysis_results = None
            excel_path = None

            if operation in ["Analyze Only", "Convert + Analyze"]:
                status_text.text("🔍 Analyzing sensitive information...")
                progress_bar.progress(60)

                # Parse grouping keywords
                keywords = [k.strip() for k in grouping_keywords.split(',')] if grouping_keywords else None

                with st.spinner("Analyzing document..."):
                    analysis_results = converter.analyze_sensitive_info(
                        tmp_pdf_path if operation == "Analyze Only" else docx_path,
                        grouping_keywords=keywords
                    )

                progress_bar.progress(80)

                # Generate Excel report
                if analysis_results:
                    status_text.text("📊 Generating Excel report...")

                    from src.analysis.report_generator import create_excel_report

                    excel_path = output_dir / f"{uploaded_file.name.replace('.pdf', ' - analysis.xlsx')}"

                    create_excel_report(
                        report_path=excel_path,
                        pdf_path=tmp_pdf_path,
                        images_by_page=converter.images_by_page,
                        sensitive_info_by_page=converter.sensitive_info_by_page,
                        grouping_keywords=keywords
                    )

                    if excel_path and excel_path.exists():
                        st.success(f"✅ Analysis complete: {excel_path.name}")
                    else:
                        st.warning("⚠️ Analysis completed but report generation failed")

                progress_bar.progress(100)

            processing_time = time.time() - start_time
            status_text.text(f"✅ Processing complete in {processing_time:.1f}s")

            # Calculate statistics
            total_findings = sum(len(findings) for findings in converter.sensitive_info_by_page.values())
            findings_by_type = {}

            for page_findings in converter.sensitive_info_by_page.values():
                for finding in page_findings:
                    finding_type = finding['type']
                    findings_by_type[finding_type] = findings_by_type.get(finding_type, 0) + 1

            companies_count = findings_by_type.get('company_name', 0)
            persons_count = findings_by_type.get('person_name', 0)

            # Update session stats
            update_stats(
                pdfs_count=1,
                pages_count=len(converter.sensitive_info_by_page),
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
                    'pages': len(converter.sensitive_info_by_page)
                }
            )

            # Save results
            result_data = {
                'total_findings': total_findings,
                'pages_count': len(converter.sensitive_info_by_page),
                'processing_time': processing_time,
                'findings_by_type': findings_by_type,
                'docx_path': str(docx_path) if docx_path else None,
                'excel_path': str(excel_path) if excel_path else None
            }

            save_result(uploaded_file.name, result_data)

            # Display results
            st.markdown("---")
            st.markdown("### 📊 Processing Results")

            show_processing_stats(result_data)

            # Download buttons
            st.markdown("### 💾 Download Results")

            col1, col2 = st.columns(2)

            with col1:
                if docx_path and docx_path.exists():
                    with open(docx_path, 'rb') as f:
                        st.download_button(
                            label="📥 Download DOCX",
                            data=f,
                            file_name=docx_path.name,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            width="stretch"
                        )

            with col2:
                if excel_path and excel_path.exists():
                    with open(excel_path, 'rb') as f:
                        st.download_button(
                            label="📥 Download Excel Report",
                            data=f,
                            file_name=excel_path.name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            width="stretch"
                        )

            # Preview findings
            if analysis_results and total_findings > 0:
                st.markdown("---")
                st.markdown("### 🔍 Preview Findings")

                # Group findings by type
                findings_preview = {}
                for page_num, findings in converter.sensitive_info_by_page.items():
                    for finding in findings[:100]:  # Limit preview
                        f_type = finding['type']
                        if f_type not in findings_preview:
                            findings_preview[f_type] = []
                        findings_preview[f_type].append(finding)

                # Display in tabs
                tabs = st.tabs(list(findings_preview.keys()))

                for idx, (f_type, findings) in enumerate(findings_preview.items()):
                    with tabs[idx]:
                        st.write(f"Found **{len(findings)}** items")

                        # Show sample (first 20)
                        for finding in findings[:20]:
                            st.text(f"Page {finding['page']}: {finding['value']}")

                        if len(findings) > 20:
                            st.info(f"... and {len(findings) - 20} more items. See Excel report for full list.")

        except Exception as e:
            st.error(f"❌ Processing failed: {str(e)}")

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
    # Show placeholder when no file uploaded
    st.info("👆 Upload a PDF file to get started")

    # Show example
    with st.expander("💡 How to use"):
        st.markdown("""
        1. **Upload** a PDF file using the file uploader
        2. **Select** the operation you want to perform:
           - **Convert to DOCX**: Only convert the PDF to Word format
           - **Analyze Only**: Only detect sensitive information
           - **Convert + Analyze**: Do both (recommended)
        3. **Configure** advanced options if needed (OCR, layout, keywords)
        4. **Click** "Start Processing" to begin
        5. **Download** the results (DOCX and/or Excel report)

        **Tip:** Use grouping keywords to organize companies in the report (e.g., "Vantiv, WorldPay, Fifth Third")
        """)
