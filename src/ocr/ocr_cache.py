#!/usr/bin/env python3
"""
OCR Cache Module - Manages OCR cache for performance
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class OCRCache:
    """Gère le cache OCR pour éviter de retraiter les mêmes pages."""
    
    def __init__(self, pdf_path: Path, verbose: bool = False):
        """
        Initialise le cache OCR basé sur un hash du PDF.
        
        Args:
            pdf_path: Chemin vers le fichier PDF
            verbose: Si True, affiche les logs détaillés
        """
        self.pdf_path = pdf_path
        self.verbose = verbose
        self.cache: Dict[str, any] = {}
        self.cache_file: Optional[Path] = None
        self._init_cache()
    
    def _init_cache(self) -> None:
        """Initialise le cache OCR basé sur un hash du PDF."""
        try:
            # Calculer un hash du PDF pour le cache
            with open(self.pdf_path, 'rb') as f:
                pdf_hash = hashlib.md5(f.read()).hexdigest()
            
            # Créer un dossier de cache si nécessaire
            cache_dir = Path.home() / '.xaipdf_cache'
            cache_dir.mkdir(exist_ok=True)
            
            self.cache_file = cache_dir / f"ocr_cache_{pdf_hash}.json"
            
            # Charger le cache existant
            if self.cache_file.exists():
                try:
                    with open(self.cache_file, 'r') as f:
                        self.cache = json.load(f)
                    if self.verbose:
                        logger.info(f"📦 Loaded OCR cache: {len(self.cache)} pages cached")
                except Exception:
                    self.cache = {}
            else:
                self.cache = {}
        except Exception as e:
            logger.warning(f"Could not initialize OCR cache: {e}")
            self.cache = {}
            self.cache_file = None
    
    def save(self) -> None:
        """Sauvegarde le cache OCR."""
        if not self.cache_file:
            return
        
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f)
        except Exception as e:
            logger.warning(f"Could not save OCR cache: {e}")
    
    def get_cache_key(self, page_num: int, dpi: int, lang: str) -> str:
        """
        Génère une clé unique pour le cache OCR d'une page.
        
        Args:
            page_num: Numéro de page
            dpi: Résolution DPI
            lang: Langue OCR
        
        Returns:
            str: Clé de cache
        """
        return f"{page_num}_{dpi}_{lang}"
    
    def get(self, key: str) -> Optional[any]:
        """Récupère une valeur du cache."""
        return self.cache.get(key)
    
    def set(self, key: str, value: any) -> None:
        """Définit une valeur dans le cache."""
        self.cache[key] = value





