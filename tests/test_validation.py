"""
Unit tests for PDF validation
Author: Conrad Vaslin - xAI Finance Tutor
"""

import pytest
from pathlib import Path
from src.progress_utils import PDFValidator


class TestPDFValidation:
    """Test PDF validation functionality"""

    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file"""
        pdf_path = Path("/nonexistent/file.pdf")
        is_valid, error, metadata = PDFValidator.validate_pdf(pdf_path)

        assert is_valid == False
        assert "not found" in error.lower()
        assert metadata['file_exists'] == False

    def test_validate_directory(self, tmp_path):
        """Test validation fails for directory"""
        is_valid, error, metadata = PDFValidator.validate_pdf(tmp_path)

        assert is_valid == False
        assert "not a file" in error.lower()

    def test_validate_wrong_extension(self, tmp_path):
        """Test validation fails for non-PDF extension"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        is_valid, error, metadata = PDFValidator.validate_pdf(test_file)

        assert is_valid == False
        assert "not a pdf" in error.lower()

    def test_validate_empty_file(self, tmp_path):
        """Test validation fails for empty file"""
        test_file = tmp_path / "test.pdf"
        test_file.touch()

        is_valid, error, metadata = PDFValidator.validate_pdf(test_file)

        assert is_valid == False
        assert "empty" in error.lower()
        assert metadata['file_size'] == 0

    def test_validate_too_small_file(self, tmp_path):
        """Test validation fails for file that's too small"""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"small")

        is_valid, error, metadata = PDFValidator.validate_pdf(test_file)

        assert is_valid == False
        assert "too small" in error.lower()

    def test_validate_real_pdf(self):
        """Test validation of real PDF files if available"""
        pdf_dir = Path("pdf")

        if not pdf_dir.exists():
            pytest.skip("pdf/ directory not found")

        pdf_files = list(pdf_dir.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF files found in pdf/")

        # Test first PDF
        test_pdf = pdf_files[0]
        is_valid, error, metadata = PDFValidator.validate_pdf(test_pdf)

        # Should be valid (or have specific error)
        assert metadata['file_exists'] == True
        assert metadata['file_size'] > 0

        if is_valid:
            assert metadata['page_count'] > 0
            assert error is None

    def test_validation_report_format(self, tmp_path):
        """Test validation report format"""
        test_file = tmp_path / "test.pdf"
        test_file.touch()

        report = PDFValidator.get_validation_report(test_file)

        assert "PDF VALIDATION REPORT" in report
        assert test_file.name in report
        assert "Status:" in report
        assert "Metadata:" in report

    def test_batch_validation(self, tmp_path):
        """Test batch validation functionality"""
        from src.progress_utils import validate_pdf_batch

        # Create test files
        valid_marker = tmp_path / "valid.txt"  # Not really valid, just for structure
        invalid_marker = tmp_path / "invalid.txt"
        valid_marker.touch()
        invalid_marker.touch()

        pdf_files = [valid_marker, invalid_marker]
        valid_files, invalid_files = validate_pdf_batch(pdf_files)

        # All should be invalid since they're not PDFs
        assert len(invalid_files) == 2
        assert len(valid_files) == 0

    def test_metadata_structure(self, tmp_path):
        """Test that metadata has correct structure"""
        test_file = tmp_path / "test.pdf"
        test_file.touch()

        is_valid, error, metadata = PDFValidator.validate_pdf(test_file)

        # Verify metadata keys exist
        assert 'file_size' in metadata
        assert 'page_count' in metadata
        assert 'is_encrypted' in metadata
        assert 'has_text' in metadata
        assert 'pdf_version' in metadata
        assert 'file_exists' in metadata
