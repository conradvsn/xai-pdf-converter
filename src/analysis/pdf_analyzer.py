#!/usr/bin/env python3
"""
PDF Analysis Module - Basic PDF analysis functions
"""

from pathlib import Path
from typing import Dict, Optional

from src.config import PYPDF2_AVAILABLE, logger

if PYPDF2_AVAILABLE:
    import PyPDF2


def get_pdf_page_count(pdf_path: Path) -> Optional[int]:
    """
    Retourne le nombre total de pages du PDF.
    
    Args:
        pdf_path: Chemin vers le fichier PDF
    
    Returns:
        Optional[int]: Nombre de pages, ou None en cas d'erreur
    """
    if not PYPDF2_AVAILABLE:
        return None
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            return len(pdf_reader.pages)
    except Exception as e:
        logger.warning(f"Could not get page count: {e}")
        return None


def is_scanned_pdf(pdf_path: Path) -> bool:
    """
    Détecte automatiquement si le PDF est scanné (image-based).
    
    Args:
        pdf_path: Chemin vers le fichier PDF
    
    Returns:
        bool: True si scanné, False si texte normal
    """
    if not PYPDF2_AVAILABLE:
        logger.warning("Cannot detect PDF type without PyPDF2")
        return False
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Analyser les 3 premières pages
            pages_to_check = min(3, len(pdf_reader.pages))
            text_chars = 0
            
            for i in range(pages_to_check):
                page = pdf_reader.pages[i]
                text = page.extract_text()
                text_chars += len(text.strip())
            
            # Moyenne de caractères par page
            avg_chars_per_page = text_chars / pages_to_check if pages_to_check > 0 else 0
            
            # Seuil : < 100 caractères/page = probablement scanné
            is_scanned = avg_chars_per_page < 100
            
            if is_scanned:
                logger.info(f"📷 PDF detected as SCANNED (avg {avg_chars_per_page:.0f} chars/page)")
            else:
                logger.info(f"📄 PDF detected as TEXT-BASED (avg {avg_chars_per_page:.0f} chars/page)")
            
            return is_scanned
    
    except Exception as e:
        logger.warning(f"Could not detect PDF type: {e}")
        return False


def detect_images_in_pdf(pdf_path: Path) -> Dict[int, int]:
    """
    Détecte les images dans le PDF.
    
    Args:
        pdf_path: Chemin vers le fichier PDF
    
    Returns:
        Dict[int, int]: Dictionnaire {numéro_page: nombre_images}
    """
    images_by_page = {}
    
    if not PYPDF2_AVAILABLE:
        logger.warning("PyPDF2 is not available. Install with: pip install PyPDF2")
        return images_by_page
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                
                # Compter les images (méthode basique)
                try:
                    if '/XObject' in page['/Resources']:
                        xobjects = page['/Resources']['/XObject'].get_object()
                        image_count = sum(1 for obj in xobjects if xobjects[obj]['/Subtype'] == '/Image')
                        if image_count > 0:
                            images_by_page[page_num + 1] = image_count
                except (KeyError, AttributeError):
                    # Pas d'images sur cette page ou structure différente
                    pass
    except Exception as e:
        logger.warning(f"Error detecting images: {e}")
    
    return images_by_page


def map_language_code(lang_code: str) -> str:
    """
    Convertit les codes langue ISO en codes Tesseract.
    
    Args:
        lang_code: Code ISO (en, fr, de, etc.)
    
    Returns:
        str: Code Tesseract (eng, fra, deu, etc.)
    """
    lang_map = {
        'en': 'eng',
        'fr': 'fra',
        'de': 'deu',
        'es': 'spa',
        'it': 'ita',
        'pt': 'por',
        'nl': 'nld',
        'pl': 'pol',
        'ru': 'rus',
        'ja': 'jpn',
        'zh': 'chi_sim',
        'ar': 'ara',
    }
    
    return lang_map.get(lang_code, lang_code)  # Retourne le code tel quel si non mappé





