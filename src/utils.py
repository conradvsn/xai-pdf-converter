#!/usr/bin/env python3
"""
Utilities and helper functions for xAI PDF Converter
"""

import logging
from pathlib import Path
from typing import Optional, List

from src.config import PDF2DOCX_AVAILABLE, Converter

logger = logging.getLogger(__name__)


def _convert_chunk(args: tuple) -> Optional[str]:
    """
    Convertit un chunk de pages du PDF en DOCX.
    Fonction helper pour multiprocessing (doit être au niveau module).
    
    Args:
        args: Tuple (pdf_path, output_path, start_page, end_page)
    
    Returns:
        Optional[str]: Chemin du fichier DOCX généré, ou None en cas d'erreur
    """
    pdf_path, output_path, start_page, end_page = args
    
    try:
        if not PDF2DOCX_AVAILABLE:
            logger.warning(f"pdf2docx not available for chunk {start_page}-{end_page}")
            return None
        
        # ⚠️ IMPORTANT : Désactiver les logs dans chaque processus worker
        # (multiprocessing n'hérite pas des paramètres de logging du processus parent)
        logging.getLogger('pdf2docx').setLevel(logging.ERROR)
        logging.getLogger('pdfplumber').setLevel(logging.ERROR)
        logging.getLogger('PIL').setLevel(logging.ERROR)
        
        converter = Converter(str(pdf_path))
        try:
            converter.convert(str(output_path), start=start_page, end=end_page)
            logger.info(f"✓ Converted pages {start_page}-{end_page}")
            return str(output_path)
        finally:
            converter.close()
    except Exception as e:
        logger.error(f"Error converting chunk {start_page}-{end_page}: {e}")
        return None


def get_pdf_directory() -> Path:
    """
    Get or create the PDF input directory.
    
    Returns:
        Path: Path to the PDF directory
    """
    pdf_dir = Path.cwd() / "pdf"
    pdf_dir.mkdir(exist_ok=True)
    return pdf_dir


def get_output_directory() -> Path:
    """
    Get or create the output directory.
    
    Returns:
        Path: Path to the output directory
    """
    output_dir = Path.cwd() / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


def list_pdf_files(directory: Optional[Path] = None) -> List[Path]:
    """
    List all PDF files in the specified directory (or current directory if None).
    
    Args:
        directory: Optional directory path. If None, uses current directory.
    
    Returns:
        List[Path]: Sorted list of PDF file paths
    """
    if directory is None:
        directory = Path.cwd()
    else:
        directory = Path(directory)
    
    if not directory.exists():
        return []
    
    pdf_files = sorted([f for f in directory.glob("*.pdf") if f.is_file()])
    return pdf_files


def select_pdf_file() -> Optional[str]:
    """
    Display list of PDFs from the pdf/ folder and allow selection by number.

    Returns:
        Optional[str]: Path to selected PDF file, or None if cancelled/no files
    """
    pdf_dir = get_pdf_directory()
    pdf_files = list_pdf_files(pdf_dir)

    if not pdf_files:
        print("\n" + "=" * 70)
        print(f"⚠️  No PDF files found in the pdf/ folder: {pdf_dir}")
        print("   Please add PDF files to the pdf/ directory.")
        print("=" * 70)
        return None
    
    print("\n" + "=" * 70)
    print(" " * 25 + "📄 AVAILABLE PDF FILES")
    print("=" * 70)
    
    for idx, pdf_file in enumerate(pdf_files, 1):
        file_size = pdf_file.stat().st_size / 1024  # Size in KB
        if file_size < 1024:
            size_str = f"{file_size:.1f} KB"
        else:
            size_str = f"{file_size / 1024:.2f} MB"
        print(f"  [{idx}] {pdf_file.name:<50} {size_str:>10}")
    
    print("=" * 70)
    
    while True:
        try:
            choice = input(f"\n👉 Select a file (1-{len(pdf_files)}) or press Enter to cancel: ").strip()
            if not choice:
                return None
            
            file_idx = int(choice) - 1
            if 0 <= file_idx < len(pdf_files):
                selected = pdf_files[file_idx]
                print(f"✓ Selected: {selected.name}")
                return str(selected)
            else:
                print(f"❌ Invalid number. Please choose between 1 and {len(pdf_files)}")
        except ValueError:
            print("❌ Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n\n⚠️  Operation cancelled.")
            return None


def get_grouping_keywords() -> Optional[List[str]]:
    """
    Ask user for keywords to group occurrences.
    
    Returns:
        Optional[List[str]]: List of keywords, or None if none provided
    """
    print("\n" + "─" * 70)
    print(" " * 15 + "🔑 KEYWORD GROUPING (Optional)")
    print("─" * 70)
    print("\n   Group occurrences containing the same keyword together.")
    print("   Example: 'vantiv' will group 'Vantiv Inc', 'Vantiv LLC', etc.")
    print("   All pages where these occur will be listed together.")
    print()
    print("─" * 70)
    
    keywords_input = input("   Keywords (comma-separated, or press Enter to skip): ").strip()
    
    if not keywords_input:
        return None
    
    keywords = [kw.strip() for kw in keywords_input.split(',') if kw.strip()]
    if keywords:
        print(f"   ✓ Grouping enabled for: {', '.join(keywords)}")
    return keywords if keywords else None

