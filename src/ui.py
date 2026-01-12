#!/usr/bin/env python3
"""
User interface functions for xAI PDF Converter
"""

from typing import Optional

from src.config import (
    OCR_AVAILABLE, PDF2DOCX_AVAILABLE, PYPDF2_AVAILABLE, OPENPYXL_AVAILABLE,
    PADDLEOCR_AVAILABLE, EASYOCR_AVAILABLE, PYTESSERACT_AVAILABLE,
    PDF2IMAGE_AVAILABLE, TQDM_AVAILABLE, PHONENUMBERS_AVAILABLE,
    PDFPLUMBER_AVAILABLE, PYTHON_DOCX_AVAILABLE, ADOBE_PDF_AVAILABLE
)
from src.utils import select_pdf_file, get_grouping_keywords, get_output_directory


def show_main_menu():
    """
    Menu principal moderne avec catégories claires et informations sur les dépendances.
    """
    # Vérifier les capacités disponibles
    from src.adobe_converter import is_adobe_available

    if is_adobe_available():
        conversion_status = "Adobe conversion"
    elif PDF2DOCX_AVAILABLE:
        conversion_status = "pdf2docx"
    else:
        conversion_status = "Not installed"

    ocr_status = "Available" if OCR_AVAILABLE else "Not installed"
    analysis_status = "Available" if (PYPDF2_AVAILABLE and OPENPYXL_AVAILABLE) else "Not installed"
    
    print("\n" + "="*80)
    print(" " * 25 + "🚀 xAI PDF CONVERTER 🚀")
    print("="*80)
    
    # Section 1: Single File Operations
    print("\n" + "─" * 80)
    print("  📄 SINGLE FILE OPERATIONS")
    print("─" * 80)
    print(f"  1. Convert PDF → Word              [{conversion_status}]")
    print(f"  2. Convert PDF → Word + Analysis   [{conversion_status}]")
    print(f"  3. Analyze PDF Only (Excel Report) [{analysis_status}]")

    # Note: Adobe handles OCR automatically, no separate option needed
    if not is_adobe_available():
        print(f"  4. OCR: Scanned PDF → Word         [{ocr_status}]")

    # Section 2: Batch Processing
    print("\n" + "─" * 80)
    print("  📦 BATCH PROCESSING (Multiple PDFs)")
    print("─" * 80)
    print("  5. Batch: Convert All PDFs")
    print("  6. Batch: Convert + Analyze All")
    print("  7. Batch: Analyze All PDFs")

    # Section 3: Settings & Info
    print("\n" + "─" * 80)
    print("  ⚙️  SETTINGS & INFO")
    print("─" * 80)
    print("  8. View System Status")
    print("  S. Configure Settings")
    print("  0. Exit")

    print("\n" + "="*80)
    print("  © 2025 Conrad Vaslin - xAI Finance Tutor  |  Version 2.0.0")
    print("="*80)

    choice = input("➤ Your choice (0-9): ").strip()
    return choice


def show_system_status():
    """
    Affiche le statut des dépendances et des capacités du système.
    """
    print("\n" + "="*80)
    print(" " * 28 + "SYSTEM STATUS")
    print("="*80)
    
    # Core dependencies
    from src.adobe_converter import is_adobe_available

    print("\n🔧 CORE CONVERSION:")
    print(f"  {'✅' if is_adobe_available() else '❌'} {'Adobe PDF Services':<20} - 🏆 INDUSTRY STANDARD (Best Quality)")
    if is_adobe_available():
        print(f"     └─ Status: Ready (500 free conversions/month)")
    else:
        print(f"     └─ Status: Not configured (see option 9 for setup)")

    print("\n🔧 FALLBACK CONVERSION:")
    print(f"  {'✅' if PDF2DOCX_AVAILABLE else '❌'} {'pdf2docx':<20} - Fallback option (lower quality)")

    print("\n🔧 OTHER DEPENDENCIES:")
    deps = [
        ("PyPDF2", PYPDF2_AVAILABLE, "PDF text extraction"),
        ("python-docx", PYTHON_DOCX_AVAILABLE, "Word document processing"),
        ("openpyxl", OPENPYXL_AVAILABLE, "Excel report generation"),
        ("pdfplumber", PDFPLUMBER_AVAILABLE, "Advanced table extraction"),
    ]
    
    for name, available, description in deps:
        status = "✅" if available else "❌"
        print(f"  {status} {name:20} - {description}")
    
    # Optional dependencies
    print("\n🎨 OPTIONAL FEATURES:")
    opt_deps = [
        ("tqdm", TQDM_AVAILABLE, "Progress bars"),
        ("phonenumbers", PHONENUMBERS_AVAILABLE, "Phone number validation"),
    ]
    
    for name, available, description in opt_deps:
        status = "✅" if available else "⚠️ "
        print(f"  {status} {name:20} - {description}")
    
    # OCR capabilities
    print("\n🔍 OCR ENGINES (for scanned PDFs):")
    ocr_engines = [
        ("PaddleOCR", PADDLEOCR_AVAILABLE, "🏆 Best quality + table detection"),
        ("EasyOCR", EASYOCR_AVAILABLE, "⭐ Good quality, easy setup"),
        ("Tesseract", PYTESSERACT_AVAILABLE, "✓  Basic OCR"),
        ("pdf2image", PDF2IMAGE_AVAILABLE, "Required for all OCR methods"),
    ]
    
    for name, available, description in ocr_engines:
        status = "✅" if available else "❌"
        print(f"  {status} {name:20} - {description}")
    
    # Summary
    print("\n" + "─"*80)
    total_features = len(deps) + len(opt_deps) + len(ocr_engines)
    available_features = sum([
        sum([1 for _, av, _ in deps if av]),
        sum([1 for _, av, _ in opt_deps if av]),
        sum([1 for _, av, _ in ocr_engines if av]),
    ])
    
    print(f"📊 SUMMARY: {available_features}/{total_features} features available")
    
    if not is_adobe_available():
        print("\n" + "─"*80)
        print("💡 RECOMMENDED: Setup Adobe PDF Services for best quality")
        print("─"*80)
        print("\n1️⃣  Install SDK:")
        print("   pip install pdfservices-sdk")
        print("\n2️⃣  Get FREE credentials (500 conversions/month):")
        print("   https://acrobatservices.adobe.com/dc-integration-creation-app-cdn/main.html")
        print("\n3️⃣  Set environment variables:")
        print("   export ADOBE_CLIENT_ID='your_client_id'")
        print("   export ADOBE_CLIENT_SECRET='your_client_secret'")
        print("\n   OR create 'pdfservices-api-credentials.json' in project root")

    if available_features < total_features:
        print("\n💡 To install optional/fallback dependencies:")
        if not PDF2DOCX_AVAILABLE:
            print("   pip install pdf2docx  (fallback if Adobe not available)")
        if not OPENPYXL_AVAILABLE:
            print("   pip install openpyxl")
        if not OCR_AVAILABLE:
            print("   pip install paddlepaddle paddleocr  (recommended)")
            print("   pip install pdf2image pillow")

    # Credits
    print("\n" + "─"*80)
    print("👤 DEVELOPED BY:")
    print("   Conrad Vaslin - xAI Finance Tutor")
    print("   © 2025 Conrad Vaslin - All Rights Reserved")
    print("   Version 2.0.0 - Modular Architecture")

    print("="*80)
    input("\n Press Enter to continue...")


def show_settings_menu():
    """
    Menu de configuration avec options persistantes.
    """
    print("\n" + "="*80)
    print(" " * 30 + "SETTINGS")
    print("="*80)

    print("\n⚙️  CONVERSION SETTINGS:")
    print("  1. Set default output directory")
    print("  2. Enable/disable verbose logging")
    print("  3. Configure parallelization (pages per chunk)")
    print("  4. Set OCR language")

    print("\n📋 ANALYSIS SETTINGS:")
    print("  5. Configure keyword grouping")
    print("  6. Set detection thresholds")

    print("\n🎨 DISPLAY SETTINGS:")
    print("  7. Toggle progress bars")
    print("  8. Set report format (Excel/CSV/JSON)")

    print("\n📊 OTHER:")
    print("  9. View all settings")
    print("  R. Reset to defaults")

    print("\n  0. Back to main menu")
    print("="*80)

    choice = input("➤ Your choice (0-9, R): ").strip()
    return choice


def handle_single_convert(use_ocr=False):
    """
    Gère la conversion d'un seul fichier PDF avec UI améliorée.
    """
    from src.converter import SECPDFConverter  # Import here to avoid circular dependency
    from pathlib import Path

    pdf_file = select_pdf_file()
    if not pdf_file:
        return

    # Créer automatiquement le chemin de sortie dans un sous-dossier (comme en batch)
    output_dir = get_output_directory()
    pdf_path = Path(pdf_file)
    pdf_name = pdf_path.stem  # Nom sans extension

    # Créer sous-dossier: output/nom_du_pdf/
    pdf_output_dir = output_dir / pdf_name
    pdf_output_dir.mkdir(exist_ok=True)

    # Fichier de sortie: output/nom_du_pdf/nom_du_pdf.docx
    docx_file = str(pdf_output_dir / f"{pdf_name}.docx")

    if use_ocr:
        if not OCR_AVAILABLE:
            print("\n❌ OCR is not installed.")
            print("\nInstall ONE of these (in order of quality):")
            print("  🏆 pip install paddlepaddle paddleocr  (BEST)")
            print("  ⭐ pip install easyocr                 (GOOD)")
            print("  ✓  pip install pytesseract             (OK)")
            print("\nAlso required:")
            print("  pip install pdf2image pillow")
            input("\nPress Enter to continue...")
            return
    
    try:
        print("\n" + "="*80)
        print(" " * 28 + "🔄 CONVERTING...")
        print("="*80)
        
        converter = SECPDFConverter(pdf_file, docx_file, verbose=True)
        
        if use_ocr:
            converter.convert(use_ocr=True, auto_detect_scanned=False)
        else:
            converter.convert()
        
        print("\n" + "="*80)
        print(" " * 28 + "✅ SUCCESS!")
        print("="*80)
        print(f"  📄 Input:  {converter.pdf_path.name}")
        print(f"  📝 Output: {converter.docx_path.name}")
        print(f"  📁 Location: {converter.docx_path.parent}")
        print("="*80)
        
    except Exception as e:
        print("\n" + "="*80)
        print(" " * 28 + "❌ ERROR")
        print("="*80)
        print(f"  {e}")
        print("="*80)
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to continue...")


def handle_single_convert_analyze():
    """
    Gère la conversion + analyse d'un seul fichier.
    """
    from src.converter import SECPDFConverter  # Import here to avoid circular dependency
    from pathlib import Path

    pdf_file = select_pdf_file()
    if not pdf_file:
        return

    # Créer automatiquement le chemin de sortie dans un sous-dossier (comme en batch)
    output_dir = get_output_directory()
    pdf_path = Path(pdf_file)
    pdf_name = pdf_path.stem  # Nom sans extension

    # Créer sous-dossier: output/nom_du_pdf/
    pdf_output_dir = output_dir / pdf_name
    pdf_output_dir.mkdir(exist_ok=True)

    # Fichiers de sortie dans le sous-dossier
    docx_file = str(pdf_output_dir / f"{pdf_name}.docx")
    report_path = pdf_output_dir / f"{pdf_name}_ANALYSE.xlsx"

    # Keyword grouping
    grouping_keywords = get_grouping_keywords()

    try:
        print("\n" + "="*80)
        print(" " * 25 + "🔄 CONVERTING + ANALYZING...")
        print("="*80)

        converter = SECPDFConverter(pdf_file, docx_file, verbose=True)

        # Conversion
        print("\n📄 Step 1/2: Converting to Word...")
        converter.convert()

        # Analysis - SE FAIT SUR LE PDF (pas sur le DOCX)
        print("\n🔍 Step 2/2: Analyzing PDF document...")
        report_path = converter.analyze_and_create_report(
            report_path=report_path,
            grouping_keywords=grouping_keywords,
            verbose=True
        )
        
        total_images = sum(converter.images_by_page.values())
        total_sensitive = sum(len(findings) for findings in converter.sensitive_info_by_page.values())
        
        print("\n" + "="*80)
        print(" " * 28 + "✅ SUCCESS!")
        print("="*80)
        print(f"  📄 Input PDF:  {converter.pdf_path.name}")
        print(f"  📝 Word file:  {converter.docx_path.name}")
        print(f"  📊 Report:     {report_path.name}")
        print(f"  📁 Location:   {converter.docx_path.parent}")
        print("\n📈 ANALYSIS SUMMARY:")
        print(f"  • Images detected:        {total_images}")
        print(f"  • Sensitive items:        {total_sensitive}")
        print(f"  • Pages with images:      {len(converter.images_by_page)}")
        print(f"  • Pages with info:        {len(converter.sensitive_info_by_page)}")
        print("="*80)
        
    except Exception as e:
        print("\n" + "="*80)
        print(" " * 28 + "❌ ERROR")
        print("="*80)
        print(f"  {e}")
        print("="*80)
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to continue...")


def handle_analyze_only():
    """
    Gère l'analyse seule d'un fichier PDF.
    """
    from src.converter import SECPDFConverter  # Import here to avoid circular dependency
    from pathlib import Path

    pdf_file = select_pdf_file()
    if not pdf_file:
        return

    # Créer le rapport dans un sous-dossier (comme en batch)
    output_dir = get_output_directory()
    pdf_path = Path(pdf_file)
    pdf_name = pdf_path.stem  # Nom sans extension

    # Créer sous-dossier: output/nom_du_pdf/
    pdf_output_dir = output_dir / pdf_name
    pdf_output_dir.mkdir(exist_ok=True)

    # Rapport dans le sous-dossier
    report_path = pdf_output_dir / f"{pdf_name}_ANALYSE.xlsx"

    grouping_keywords = get_grouping_keywords()

    try:
        print("\n" + "="*80)
        print(" " * 28 + "🔍 ANALYZING PDF...")
        print("="*80)

        # L'analyse se fait directement sur le PDF, pas besoin de DOCX
        converter = SECPDFConverter(pdf_file, verbose=True)
        report_path = converter.analyze_and_create_report(
            report_path=report_path,
            grouping_keywords=grouping_keywords,
            verbose=True
        )
        
        total_images = sum(converter.images_by_page.values())
        total_sensitive = sum(len(findings) for findings in converter.sensitive_info_by_page.values())
        
        print("\n" + "="*80)
        print(" " * 25 + "✅ ANALYSIS COMPLETE!")
        print("="*80)
        print(f"  📄 Input PDF:  {converter.pdf_path.name}")
        print(f"  📊 Report:     {report_path.name}")
        print(f"  📁 Location:   {report_path.parent}")
        print("\n📈 SUMMARY:")
        print(f"  • Images detected:        {total_images}")
        print(f"  • Sensitive items:        {total_sensitive}")
        print(f"  • Pages with images:      {len(converter.images_by_page)}")
        print(f"  • Pages with info:        {len(converter.sensitive_info_by_page)}")
        print("="*80)
        
    except Exception as e:
        print("\n" + "="*80)
        print(" " * 28 + "❌ ERROR")
        print("="*80)
        print(f"  {e}")
        print("="*80)
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to continue...")
