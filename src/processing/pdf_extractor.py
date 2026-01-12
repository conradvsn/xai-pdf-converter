#!/usr/bin/env python3
"""
PDF Extractor Module
Handles PDF text extraction and reconstruction.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from src.config import PDFPLUMBER_AVAILABLE, PYTHON_DOCX_AVAILABLE, logger

if PDFPLUMBER_AVAILABLE:
    import pdfplumber

if PYTHON_DOCX_AVAILABLE:
    from docx import Document

from src.layout.layout_analyzer import group_words_into_lines, detect_blocks_from_lines, classify_line_from_words
from src.layout.layout_renderer import create_table_from_words


def reconstruct_page_from_pdfplumber(doc: Document, page) -> None:
    """
    Reconstruit une page Word à partir des données pdfplumber.
    Préserve les positions spatiales, colonnes, tableaux et alignements.
    
    Args:
        doc: Document Word
        page: Page pdfplumber
    """
    # Extraire les mots avec leurs coordonnées
    words = page.extract_words(x_tolerance=3, y_tolerance=3)
    
    if not words:
        return
    
    # Extraire les tableaux
    tables = page.extract_tables()
    table_bboxes = []
    for table in tables:
        if table:
            # Calculer la bbox du tableau (première et dernière cellule)
            # Note: pdfplumber ne donne pas directement la bbox, on l'estime
            table_bboxes.append(None)  # On utilisera une heuristique différente
    
    # Grouper les mots par ligne (même Y)
    lines = group_words_into_lines(words)
    
    # Détecter les blocs (texte, tableaux, titres)
    blocks = detect_blocks_from_lines(lines, page.width)
    
    # Rendre chaque bloc dans Word
    for block in blocks:
        if block['type'] == 'table':
            # Créer un tableau Word à partir des lignes
            # Flatten toutes les lignes du bloc en une seule liste de mots
            all_words = []
            for line in block['lines']:
                all_words.extend(line)
            create_table_from_words(doc, all_words, page.width)
        elif block['type'] == 'title':
            # Titre formaté
            for line in block['lines']:
                text = " ".join([w.get('text', '') for w in line])
                if text.strip():
                    para = doc.add_paragraph(text.strip())
                    para.style = 'Heading 2'
                    for run in para.runs:
                        run.bold = True
        else:
            # Texte narratif normal
            for line in block['lines']:
                text = " ".join([w.get('text', '') for w in line])
                if text.strip():
                    doc.add_paragraph(text.strip())



def group_pdfplumber_words_by_lines(words, page_height, tolerance=5) -> List[List[Dict]]:
    """Groupe les mots de pdfplumber par lignes."""
    if not words:
        return []
    
    # Trier par position Y (top)
    sorted_words = sorted(words, key=lambda w: (w.get('top', 0), w.get('left', 0)))
    
    lines = []
    current_line = []
    current_y = None
    
    for word in sorted_words:
        word_y = word.get('top', 0)
        word_text = word.get('text', '').strip()
        
        if not word_text:
            continue
        
        if current_y is None:
            current_y = word_y
            current_line = [word]
        elif abs(word_y - current_y) <= tolerance:
            current_line.append(word)
        else:
            if current_line:
                lines.append(sorted(current_line, key=lambda w: w.get('left', 0)))
            current_line = [word]
            current_y = word_y
    
    if current_line:
        lines.append(sorted(current_line, key=lambda w: w.get('left', 0)))
    
    return lines


