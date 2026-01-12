#!/usr/bin/env python3
"""
Layout Analyzer Module
Handles layout detection and analysis (columns, structure, blocks).
"""

from typing import Dict, List, Any, Optional
from src.config import logger


def analyze_page_structure(lines, words, img_width, img_height) -> Dict[str, Any]:
    """
    Analyse la structure de la page pour détecter colonnes, tableaux, titres.
    """
    structure = {
        'has_columns': False,
        'has_table': False,
        'column_count': 1,
        'table_regions': [],
        'title_lines': []
    }
    
    if not lines:
        return structure
    
    # Analyser la distribution horizontale des mots pour détecter les colonnes
    x_positions = [w['left'] for w in words if w.get('left', 0) > 0]
    if x_positions:
        x_min, x_max = min(x_positions), max(x_positions)
        x_range = x_max - x_min
        
        # Si les mots sont distribués sur moins de 60% de la largeur, probablement 2 colonnes
        if x_range < img_width * 0.6:
            # Analyser les clusters de positions X
            sorted_x = sorted(set(x_positions))
            if len(sorted_x) > 10:
                # Calculer les gaps entre positions
                gaps = []
                for i in range(1, len(sorted_x)):
                    gap = sorted_x[i] - sorted_x[i-1]
                    if gap > img_width * 0.15:  # Gap significatif
                        gaps.append((sorted_x[i-1], sorted_x[i]))
                
                if len(gaps) >= 1:
                    structure['has_columns'] = True
                    structure['column_count'] = 2
    
    # Détecter les tableaux (lignes avec plusieurs mots alignés verticalement)
    if len(lines) > 3:
        # Vérifier si plusieurs lignes ont des mots alignés verticalement
        vertical_alignment_count = 0
        for i in range(len(lines) - 1):
            if i + 1 < len(lines):
                line1_words = lines[i]
                line2_words = lines[i + 1]
                
                # Vérifier l'alignement vertical
                for w1 in line1_words:
                    for w2 in line2_words:
                        if abs(w1['left'] - w2['left']) < 20:  # Alignés à 20 pixels près
                            vertical_alignment_count += 1
                            break
                    if vertical_alignment_count > 0:
                        break
                
                if vertical_alignment_count > 3:
                    structure['has_table'] = True
                    break
    
    # Détecter les titres (lignes courtes, en majuscules, ou avec grande police)
    for line_idx, line in enumerate(lines):
        if not line:
            continue
        
        line_text = ' '.join([w['text'] for w in line])
        avg_height = sum(w['height'] for w in line) / len(line) if line else 0
        
        # Titre si : tout en majuscules ET court OU grande hauteur de police
        is_title = (
            (line_text.isupper() and len(line_text) < 100 and len(line_text.split()) < 15) or
            (avg_height > 20)  # Police plus grande
        )
        
        if is_title:
            structure['title_lines'].append(line_idx)
    
    return structure



def detect_column_structure(words, img_width) -> Dict[str, Any]:
    """
    Détecte la structure de colonnes en analysant TOUS les mots de la page.
    Utilise le clustering pour identifier les colonnes distinctes.
    
    Returns:
        dict avec 'has_columns', 'left_column_x', 'right_column_x', 'split_x'
    """
    if not words or len(words) < 20:
        return {'has_columns': False, 'split_x': img_width / 2}
    
    # Extraire toutes les positions X
    x_positions = [w['left'] for w in words]
    x_positions.sort()
    
    # Analyser la distribution pour trouver deux clusters
    # Approche: trouver le point de séparation optimal
    midpoint = img_width / 2
    tolerance = img_width * 0.15  # 15% de tolérance
    
    # Compter les mots à gauche et à droite du milieu
    left_count = sum(1 for x in x_positions if x < midpoint - tolerance)
    right_count = sum(1 for x in x_positions if x > midpoint + tolerance)
    center_count = len(x_positions) - left_count - right_count
    
    total = len(x_positions)
    
    # Si on a une bonne distribution 30-70% gauche et 30-70% droite, c'est probablement deux colonnes
    left_ratio = left_count / total if total > 0 else 0
    right_ratio = right_count / total if total > 0 else 0
    
    # Détection: au moins 25% des mots à gauche ET 25% à droite, avec moins de 20% au centre
    has_columns = (left_ratio >= 0.25 and right_ratio >= 0.25 and 
                  (center_count / total if total > 0 else 1) < 0.2)
    
    if has_columns:
        # Trouver le point de séparation optimal (entre les deux colonnes)
        # Utiliser la médiane des positions dans la zone centrale
        center_x = [x for x in x_positions if midpoint - tolerance <= x <= midpoint + tolerance]
        if center_x:
            split_x = sum(center_x) / len(center_x)
        else:
            split_x = midpoint
        
        # Calculer les positions moyennes des colonnes
        left_x = [x for x in x_positions if x < split_x]
        right_x = [x for x in x_positions if x >= split_x]
        
        left_column_x = sum(left_x) / len(left_x) if left_x else 0
        right_column_x = sum(right_x) / len(right_x) if right_x else img_width
        
        return {
            'has_columns': True,
            'split_x': split_x,
            'left_column_x': left_column_x,
            'right_column_x': right_column_x
        }
    else:
        return {'has_columns': False, 'split_x': midpoint}



def separate_lines_by_columns(lines, column_structure) -> List:
    """
    Sépare les mots de chaque ligne selon leur colonne.
    Retourne des lignes avec structure multi-colonnes.
    """
    split_x = column_structure['split_x']
    separated_lines = []
    
    for line in lines:
        if not line:
            separated_lines.append([])
            continue
        
        # Séparer les mots selon leur position X
        left_words = []
        right_words = []
        
        for word in line:
            word_x = word.get('left', 0)
            if word_x < split_x:
                left_words.append(word)
            else:
                right_words.append(word)
        
        # Si on a des mots des deux côtés, créer une structure multi-colonnes
        if left_words and right_words:
            separated_lines.append({
                'type': 'multi_column',
                'columns': [left_words, right_words],
                'all_words': line
            })
        elif left_words:
            # Seulement à gauche (peut être un header ou titre)
            separated_lines.append(left_words)
        elif right_words:
            # Seulement à droite
            separated_lines.append(right_words)
        else:
            separated_lines.append([])
    
    return separated_lines



def separate_columns_in_line(line) -> Any:
    """
    Détecte et sépare les colonnes dans une ligne.
    Retourne une structure qui préserve l'ordre des colonnes.
    """
    if not line or len(line) < 2:
        return line
    
    # Calculer les écarts entre les mots
    gaps = []
    for i in range(1, len(line)):
        prev_x_end = line[i-1]['left'] + line[i-1]['width']
        curr_x = line[i]['left']
        gap = curr_x - prev_x_end
        gaps.append(gap)
    
    if not gaps:
        return line
    
    # Trouver le gap le plus large (probable séparation de colonnes)
    max_gap = max(gaps)
    gap_threshold = max(50, max_gap * 0.3)  # Au moins 50px ou 30% du max gap
    
    # Si le gap max est significatif, c'est probablement deux colonnes
    if max_gap > gap_threshold:
        # Trouver l'index où se trouve le grand gap
        split_idx = gaps.index(max_gap) + 1
        
        # Séparer en deux colonnes
        left_col = line[:split_idx]
        right_col = line[split_idx:]
        
        # Retourner une structure qui indique les colonnes
        return {
            'type': 'multi_column',
            'columns': [left_col, right_col],
            'all_words': line  # Pour compatibilité
        }
    
    # Pas de colonnes multiples, retourner la ligne normale
    return line



def detect_layout_blocks(lines, page_width) -> List[Dict]:
    """
    Détecte les types de blocs (texte, tableau, titre) dans les lignes.
    
    Args:
        lines: Liste de lignes (chaque ligne = liste de mots)
        page_width: Largeur de la page en pixels
    
    Returns:
        Liste de blocs avec 'type' et 'lines'
    """
    blocks = []
    if not lines:
        return blocks
    
    current_block = None
    
    for line in lines:
        if not line:
            continue
        
        # Analyser la ligne pour déterminer son type
        line_type = classify_line(line, page_width)
        
        # Si même type que le bloc actuel, ajouter à ce bloc
        if current_block and current_block['type'] == line_type:
            current_block['lines'].append(line)
        else:
            # Nouveau bloc
            if current_block:
                blocks.append(current_block)
            current_block = {'type': line_type, 'lines': [line]}
    
    if current_block:
        blocks.append(current_block)
    
    return blocks



def classify_line(line, page_width) -> str:
    """
    Classifie une ligne comme 'table', 'title', ou 'text'.
    
    Args:
        line: Liste de mots (dicts)
        page_width: Largeur de la page en pixels
    
    Returns:
        'table', 'title', ou 'text'
    """
    if not line:
        return 'text'
    
    # Calculer les écarts entre les mots
    gaps = []
    text_content = ""
    for i, word in enumerate(line):
        if i > 0:
            gap = word['left'] - (line[i-1]['left'] + line[i-1]['width'])
            gaps.append(gap)
        text_content += word['text'] + " "
    
    # Détecter les grands écarts (colonnes)
    large_gaps = [g for g in gaps if g > 30]
    
    # Compter les chiffres
    digit_count = sum(c.isdigit() for c in text_content)
    digit_ratio = digit_count / len(text_content) if text_content else 0
    
    # Heuristique pour tableau : grands écarts OU beaucoup de chiffres
    if len(large_gaps) >= 1 or (len(line) > 3 and digit_ratio > 0.3):
        return 'table'
    
    # Heuristique pour titre : court, majuscules, ou centré
    text_stripped = text_content.strip()
    if (text_stripped.isupper() and len(text_stripped) < 100 and len(text_stripped) > 5) or \
       (len(text_stripped) < 80 and len(line) <= 5):
        # Vérifier si centré (position X proche du centre)
        first_word_x = line[0]['left']
        last_word_x = line[-1]['left'] + line[-1]['width']
        line_center = (first_word_x + last_word_x) / 2
        page_center = page_width / 2
        if abs(line_center - page_center) < page_width * 0.15:  # Tolérance 15%
            return 'title'
        elif text_stripped.isupper():
            return 'title'
    
    return 'text'



def group_words_into_lines(words) -> List[List[Dict]]:
    """
    Groupe les mots en lignes basées sur leur position Y.
    
    Args:
        words: Liste de mots de pdfplumber (dicts avec 'text', 'x0', 'top', etc.)
    
    Returns:
        Liste de lignes, chaque ligne = liste de mots triés par X
    """
    if not words:
        return []
    
    # Trier par Y puis X
    words_sorted = sorted(words, key=lambda w: (w.get('top', 0), w.get('x0', 0)))
    
    lines = []
    current_line = []
    current_y = None
    y_tolerance = 5  # Tolérance pour considérer que c'est la même ligne
    
    for word in words_sorted:
        word_y = word.get('top', 0)
        
        if current_y is None:
            current_y = word_y
            current_line.append(word)
        elif abs(word_y - current_y) <= y_tolerance:
            current_line.append(word)
        else:
            # Nouvelle ligne
            if current_line:
                current_line.sort(key=lambda w: w.get('x0', 0))
                lines.append(current_line)
            current_line = [word]
            current_y = word_y
    
    if current_line:
        current_line.sort(key=lambda w: w.get('x0', 0))
        lines.append(current_line)
    
    return lines



def detect_blocks_from_lines(lines, page_width) -> List[Dict]:
    """
    Détecte les types de blocs (texte, tableau, titre) à partir des lignes.
    
    Args:
        lines: Liste de lignes (chaque ligne = liste de mots)
        page_width: Largeur de la page en points
    
    Returns:
        Liste de blocs avec 'type' et 'lines' ou 'words'
    """
    blocks = []
    if not lines:
        return blocks
    
    current_block = None
    
    for line in lines:
        if not line:
            continue
        
        # Classifier la ligne
        line_type = classify_line_from_words(line, page_width)
        
        # Si même type que le bloc actuel, ajouter à ce bloc
        if current_block and current_block['type'] == line_type:
            if 'lines' in current_block:
                current_block['lines'].append(line)
            else:
                current_block['lines'] = [line]
        else:
            # Nouveau bloc
            if current_block:
                blocks.append(current_block)
            current_block = {'type': line_type, 'lines': [line]}
    
    if current_block:
        blocks.append(current_block)
    
    return blocks



def classify_line_from_words(line, page_width) -> str:
    """
    Classifie une ligne comme 'table', 'title', ou 'text'.
    
    Args:
        line: Liste de mots (dicts de pdfplumber)
        page_width: Largeur de la page en points
    
    Returns:
        'table', 'title', ou 'text'
    """
    if not line:
        return 'text'
    
    # Calculer les écarts entre les mots
    gaps = []
    text_content = ""
    for i, word in enumerate(line):
        if i > 0:
            prev_x1 = line[i-1].get('x1', 0)
            curr_x0 = word.get('x0', 0)
            gap = curr_x0 - prev_x1
            gaps.append(gap)
        text_content += word.get('text', '') + " "
    
    # Détecter les grands écarts (colonnes)
    large_gaps = [g for g in gaps if g > 20]  # 20 points = colonne
    
    # Compter les chiffres
    digit_count = sum(c.isdigit() for c in text_content)
    digit_ratio = digit_count / len(text_content) if text_content else 0
    
    # Heuristique pour tableau : grands écarts OU beaucoup de chiffres
    if len(large_gaps) >= 1 or (len(line) > 3 and digit_ratio > 0.3):
        return 'table'
    
    # Heuristique pour titre
    text_stripped = text_content.strip()
    if text_stripped.isupper() and len(text_stripped) < 100 and len(text_stripped) > 5:
        return 'title'
    
    return 'text'



def analyze_page_structure_from_words(words, lines, page_width, page_height) -> Dict[str, Any]:
    """Analyse la structure depuis les mots de pdfplumber."""
    structure = {
        'has_columns': False,
        'has_table': False,
        'column_count': 1,
        'table_regions': [],
        'title_lines': []
    }
    
    if not words or not lines:
        return structure
    
    # Analyser la distribution horizontale
    x_positions = [w.get('left', 0) for w in words]
    if x_positions:
        x_min, x_max = min(x_positions), max(x_positions)
        x_range = x_max - x_min
        
        # Si le texte est concentré sur moins de 70% de la largeur, probablement 2 colonnes
        if x_range < page_width * 0.7:
            # Vérifier les gaps pour confirmer les colonnes
            sorted_x = sorted(set(x_positions))
            large_gaps = []
            for i in range(1, len(sorted_x)):
                gap = sorted_x[i] - sorted_x[i-1]
                if gap > page_width * 0.2:  # Gap de plus de 20% de la largeur
                    large_gaps.append(gap)
            
            if len(large_gaps) >= 1:
                structure['has_columns'] = True
                structure['column_count'] = 2
    
    # Détecter les titres (police plus grande, ou texte en majuscules)
    for line_idx, line in enumerate(lines):
        if not line:
            continue
        
        line_text = ' '.join([w.get('text', '') for w in line])
        avg_font_size = sum(w.get('size', 10) for w in line) / len(line) if line else 10
        
        is_title = (
            (line_text.isupper() and len(line_text) < 100 and len(line_text.split()) < 15) or
            (avg_font_size > 12)  # Police plus grande
        )
        
        if is_title:
            structure['title_lines'].append(line_idx)
    
    return structure


