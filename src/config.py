#!/usr/bin/env python3
"""
Configuration et imports pour xAI PDF Converter
"""

import os
import sys

# CRITICAL: Set these BEFORE any other imports to suppress verbose library messages
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
os.environ['PADDLEOCR_LOGGING_LEVEL'] = 'ERROR'

import logging
import warnings
from pathlib import Path
from contextlib import contextmanager
from io import StringIO

# Suppress ALL warnings globally
warnings.filterwarnings("ignore")

# Disable root logger to prevent duplicate messages
logging.getLogger().handlers = []
logging.getLogger().setLevel(logging.ERROR)

# Suppress all verbose logging from third-party libraries
logging.getLogger('paddleocr').setLevel(logging.ERROR)
logging.getLogger('ppocr').setLevel(logging.ERROR)
logging.getLogger('PIL').setLevel(logging.ERROR)
logging.getLogger('pikepdf').setLevel(logging.ERROR)
logging.getLogger('matplotlib').setLevel(logging.ERROR)
logging.getLogger('shapely').setLevel(logging.ERROR)

# Supprimer les warnings PyPDF2 concernant les PDFs mal formés (non critique)
warnings.filterwarnings("ignore", category=UserWarning, module="PyPDF2")
warnings.filterwarnings("ignore", message=".*incorrect startxref pointer.*")
warnings.filterwarnings("ignore", message=".*startxref.*")

# Try to import Adobe PDF Services SDK (BEST quality, industry standard)
try:
    from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
    from adobe.pdfservices.operation.pdf_services import PDFServices
    from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
    from adobe.pdfservices.operation.io.cloud_asset import CloudAsset
    from adobe.pdfservices.operation.io.stream_asset import StreamAsset
    from adobe.pdfservices.operation.pdfjobs.jobs.export_pdf_job import ExportPDFJob
    from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_params import ExportPDFParams
    from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_target_format import ExportPDFTargetFormat
    from adobe.pdfservices.operation.pdfjobs.result.export_pdf_result import ExportPDFResult
    ADOBE_PDF_AVAILABLE = True
except ImportError:
    ADOBE_PDF_AVAILABLE = False
    ServicePrincipalCredentials = None
    PDFServices = None

# Try to import pdf2docx (fallback if Adobe not available)
try:
    from pdf2docx import Converter
    PDF2DOCX_AVAILABLE = True
except ImportError:
    PDF2DOCX_AVAILABLE = False
    Converter = None

# Try to import PyPDF2 for text extraction
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    PyPDF2 = None

# Try to import phonenumbers for phone validation
try:
    import phonenumbers
    from phonenumbers import PhoneNumberFormat
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    PHONENUMBERS_AVAILABLE = False
    phonenumbers = None
    PhoneNumberFormat = None

# Try to import openpyxl for Excel reports
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    Workbook = None
    Font = None
    Alignment = None
    get_column_letter = None

# Try to import python-docx for Word document post-processing
try:
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    PYTHON_DOCX_AVAILABLE = True
except ImportError:
    PYTHON_DOCX_AVAILABLE = False
    Document = None
    Pt = None
    Inches = None
    RGBColor = None
    OxmlElement = None
    qn = None
    WD_ALIGN_PARAGRAPH = None

# Try to import pdfplumber for advanced table extraction
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    pdfplumber = None

# Try to import tqdm for progress bars
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    tqdm = None

# Try to import spaCy for NLP-based detection
SPACY_AVAILABLE = False
SPACY_NLP = None
try:
    import spacy

    # Try method 1: Load via spacy.load() (works if model linked)
    try:
        SPACY_NLP = spacy.load('en_core_web_sm')
        SPACY_AVAILABLE = True
        print("✅ spaCy model loaded via spacy.load()")
    except OSError:
        # Method 2: Import model package directly (for Streamlit Cloud)
        print("⚠️ Trying alternative loading method...")
        try:
            import en_core_web_sm
            SPACY_NLP = en_core_web_sm.load()
            SPACY_AVAILABLE = True
            print("✅ spaCy model loaded via direct import")
        except Exception as e:
            print(f"❌ Failed to load spaCy model: {e}")
            SPACY_AVAILABLE = False
            SPACY_NLP = None
except ImportError as e:
    print(f"❌ spaCy not available: {e}")
    SPACY_AVAILABLE = False
    SPACY_NLP = None

# ==================== OCR LIBRARIES ====================
# Try to import OCR libraries (optional, only for scanned PDFs)
PADDLEOCR_AVAILABLE = False
PPSTRUCTURE_AVAILABLE = False

# Essayer d'importer PaddleOCR (peut échouer à cause de dépendances manquantes)
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
    # Essayer d'importer PPStructure séparément
    try:
        from paddleocr import PPStructure
        PPSTRUCTURE_AVAILABLE = True
    except (ImportError, RuntimeError, AttributeError):
        PPSTRUCTURE_AVAILABLE = False
except (ImportError, RuntimeError, ModuleNotFoundError):
    PADDLEOCR_AVAILABLE = False
    PPSTRUCTURE_AVAILABLE = False
    PaddleOCR = None

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    easyocr = None

try:
    import pytesseract
    from pytesseract import TesseractError
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    pytesseract = None
    TesseractError = None

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    convert_from_path = None

# Try to import OCRmyPDF (recommended for scanned PDFs)
try:
    import ocrmypdf
    OCRMYPDF_AVAILABLE = True
except ImportError:
    OCRMYPDF_AVAILABLE = False
    ocrmypdf = None

# Determine best available OCR engine
OCR_AVAILABLE = OCRMYPDF_AVAILABLE or PADDLEOCR_AVAILABLE or EASYOCR_AVAILABLE or PYTESSERACT_AVAILABLE

if OCR_AVAILABLE and not PDF2IMAGE_AVAILABLE and not OCRMYPDF_AVAILABLE:
    print("⚠️  WARNING: pdf2image not available. Install with: pip install pdf2image")
    print("   OCR will not work without it (unless using OCRmyPDF).")
    OCR_AVAILABLE = False

# Configuration du logging - désactivé car géré par logging_system.py
# Le basicConfig est désactivé pour éviter les messages dupliqués
# logging.basicConfig() est remplacé par logging_system.py
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)  # Ne montrer que les erreurs critiques dans config

# Supprimer les warnings PyPDF2/pikepdf dès le démarrage (avant toute utilisation)
logging.getLogger('PyPDF2').setLevel(logging.ERROR)
logging.getLogger('pikepdf').setLevel(logging.ERROR)


def configure_logging(verbose: bool = False) -> None:
    """
    Configure logging levels based on verbose mode.
    
    Args:
        verbose: If True, show all INFO logs. If False, only WARNING and ERROR.
    """
    if verbose:
        # Mode verbose : tout afficher
        logging.getLogger().setLevel(logging.INFO)
        logger.setLevel(logging.INFO)
        logging.getLogger('pdf2docx').setLevel(logging.INFO)
    else:
        # Mode simple : silence tout sauf warnings/errors
        logging.getLogger().setLevel(logging.WARNING)
        logger.setLevel(logging.WARNING)
        logging.getLogger('pdf2docx').setLevel(logging.ERROR)
        
        # Désactiver aussi les logs de pdfplumber si présent
        logging.getLogger('pdfplumber').setLevel(logging.ERROR)
        logging.getLogger('PIL').setLevel(logging.ERROR)  # Pillow (images)
    
    # Supprimer les warnings PyPDF2 (startxref pointer, etc.)
    logging.getLogger('PyPDF2').setLevel(logging.ERROR)
    logging.getLogger('pikepdf').setLevel(logging.ERROR)


@contextmanager
def suppress_output(verbose: bool = False):
    """
    Context manager to suppress stdout/stderr in non-verbose mode.
    
    Args:
        verbose: If True, don't suppress output. If False, suppress it.
        
    Yields:
        None
    """
    if verbose:
        # Don't suppress in verbose mode
        yield
    else:
        # Suppress stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = StringIO()
            sys.stderr = StringIO()
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

