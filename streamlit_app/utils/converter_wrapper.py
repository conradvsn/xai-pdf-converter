"""
Wrapper for SECPDFConverter to provide Streamlit-compatible interface
"""

from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Force reload du module sensitive_info_detector (pour Streamlit Cloud)
import importlib
if 'src.analysis.sensitive_info_detector' in sys.modules:
    importlib.reload(sys.modules['src.analysis.sensitive_info_detector'])

from src.converter import SECPDFConverter, AdobeConversionError


class PDFConverter:
    """
    Wrapper around SECPDFConverter to provide a simpler interface for Streamlit
    """

    def __init__(self, adobe_api_keys=None, use_ocr=False, preserve_layout=True, verbose=False):
        """
        Initialize converter with settings

        Args:
            adobe_api_keys: List of Adobe API credentials (not used directly, but checked)
            use_ocr: Whether to use OCR for scanned PDFs
            preserve_layout: Whether to preserve PDF layout (always true for SECPDFConverter)
            verbose: Verbose output
        """
        self.adobe_api_keys = adobe_api_keys or []
        self.use_ocr = use_ocr
        self.preserve_layout = preserve_layout
        self.verbose = verbose

        # These will be populated after conversion/analysis
        self.sensitive_info_by_page = {}
        self.images_by_page = {}

        self._current_converter = None
        self._original_pdf_path = None  # Store original PDF path for analysis

    def convert_pdf_to_docx(self, pdf_path, output_path, allow_fallback=False):
        """
        Convert PDF to DOCX using Adobe PDF Services (default).
        If Adobe fails, raises AdobeConversionError unless allow_fallback=True.

        Args:
            pdf_path: Path to input PDF
            output_path: Path for output DOCX
            allow_fallback: If True, allows fallback to pdf2docx when Adobe fails
                           (should only be True after explicit user consent)

        Returns:
            Path to output DOCX file

        Raises:
            AdobeConversionError: When Adobe conversion fails and allow_fallback=False
        """
        pdf_path = Path(pdf_path)
        output_path = Path(output_path)

        # Store original PDF path for later analysis
        self._original_pdf_path = pdf_path

        # Create SECPDFConverter instance
        converter = SECPDFConverter(
            pdf_path=pdf_path,
            docx_path=output_path,
            verbose=self.verbose
        )

        # Convert - Adobe is ALWAYS used by default
        # If allow_fallback=False (default), will raise AdobeConversionError on failure
        converter.convert(
            use_ocr=self.use_ocr,
            auto_detect_scanned=True,
            allow_fallback=allow_fallback
        )

        # Store for later use
        self._current_converter = converter

        if output_path.exists():
            return output_path
        else:
            raise RuntimeError(f"Conversion failed - output file not created: {output_path}")

    def analyze_sensitive_info(self, file_path, grouping_keywords=None):
        """
        Analyze sensitive information in a file (PDF or DOCX)

        Args:
            file_path: Path to file to analyze (can be PDF or DOCX)
            grouping_keywords: Optional keywords for grouping

        Returns:
            Dictionary of findings by page
        """
        file_path = Path(file_path)

        # Determine the PDF path to analyze
        # If we have a stored original PDF from conversion, use that
        # Otherwise, assume file_path is the PDF
        if self._original_pdf_path is not None:
            pdf_to_analyze = self._original_pdf_path
        elif file_path.suffix.lower() == '.pdf':
            pdf_to_analyze = file_path
            self._original_pdf_path = pdf_to_analyze
        else:
            # file_path is a DOCX but we don't have the original PDF
            raise RuntimeError(
                "Cannot analyze DOCX file without original PDF. "
                "Please convert the PDF first using convert_pdf_to_docx()"
            )

        # Analyze using detect_sensitive_information directly
        from src.analysis.sensitive_info_detector import detect_sensitive_information
        from src.analysis.pdf_analyzer import detect_images_in_pdf

        # Get sensitive info from the PDF
        sensitive_info = detect_sensitive_information(
            pdf_path=pdf_to_analyze,
            verbose=self.verbose
        )

        # Get images from the PDF
        images_by_page = detect_images_in_pdf(pdf_to_analyze)

        # Store results
        self.sensitive_info_by_page = sensitive_info
        self.images_by_page = images_by_page

        return sensitive_info
