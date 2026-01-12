"""
Integration tests for xAI PDF Converter
Author: Conrad Vaslin - xAI Finance Tutor
"""

import pytest
from pathlib import Path
from src.settings import get_settings
from src.logging_system import get_logging_system, setup_logging
from src.progress_utils import PDFValidator, validate_pdf_batch


class TestIntegration:
    """Integration tests for end-to-end workflows"""

    def test_settings_and_logging_integration(self, tmp_path):
        """Test settings and logging work together"""
        # Setup logging
        logger = setup_logging(verbose=False, console=False)

        # Get settings
        settings = get_settings()

        # Verify developer info
        assert settings.get('developer') == 'Conrad Vaslin'

        # Get logging system
        log_system = get_logging_system()

        # Log an operation
        log_system.log_conversion("test.pdf", "test.docx", True, 10.5)

        # Verify logs directory created
        logs_dir = Path("logs")
        assert logs_dir.exists()

    def test_pdf_validation_workflow(self):
        """Test complete PDF validation workflow"""
        pdf_dir = Path("pdf")

        if not pdf_dir.exists():
            pytest.skip("pdf/ directory not found")

        pdf_files = list(pdf_dir.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF files found")

        # Validate first PDF
        test_pdf = pdf_files[0]
        is_valid, error, metadata = PDFValidator.validate_pdf(test_pdf)

        # Get validation report
        report = PDFValidator.get_validation_report(test_pdf)

        assert "PDF VALIDATION REPORT" in report
        assert metadata['file_exists'] == True

    def test_settings_persistence(self, tmp_path):
        """Test settings persist across instances"""
        from src.settings import Settings

        config_path = tmp_path / "test_config.json"

        # Create and modify settings
        settings1 = Settings(config_path)
        settings1.set('test_value', 'hello')

        # Create new instance
        settings2 = Settings(config_path)

        # Verify persistence
        assert settings2.get('test_value') == 'hello'

    def test_export_multiple_formats(self, tmp_path):
        """Test exporting to multiple formats"""
        from src.export_utils import create_multi_format_reports

        findings = {
            ("company_name", "Test Company"): [1, 2, 3]
        }

        base_path = tmp_path / "test_report"
        formats = ['csv', 'json']

        created = create_multi_format_reports(
            findings,
            base_path,
            formats,
            None
        )

        # Verify both formats created
        assert 'csv' in created
        assert 'json' in created
        assert created['csv'].exists()
        assert created['json'].exists()

    def test_logging_and_audit_trail(self, tmp_path):
        """Test logging creates audit trail"""
        log_system = get_logging_system()

        # Log multiple operations
        log_system.log_operation_start("test_op", {"file": "test.pdf"})
        log_system.log_conversion("test.pdf", "test.docx", True, 5.0)
        log_system.log_operation_end("test_op", True, {"status": "complete"})

        # Verify audit trail exists
        audit_log = Path("logs/audit_trail.log")
        assert audit_log.exists()

        # Verify content
        with open(audit_log, 'r') as f:
            content = f.read()

        assert "START" in content
        assert "END" in content
        assert "test_op" in content

    def test_full_workflow_with_real_pdf(self):
        """Test complete workflow if PDFs available"""
        pdf_dir = Path("pdf")

        if not pdf_dir.exists() or not list(pdf_dir.glob("*.pdf")):
            pytest.skip("No PDFs available for integration test")

        # Get settings
        settings = get_settings()
        assert settings.get('developer') == 'Conrad Vaslin'

        # Setup logging
        logger = setup_logging(verbose=False, console=False)

        # Find and validate PDF
        pdf_files = list(pdf_dir.glob("*.pdf"))
        test_pdf = pdf_files[0]

        is_valid, error, metadata = PDFValidator.validate_pdf(test_pdf)

        if is_valid:
            # PDF is valid
            assert metadata['page_count'] > 0
            assert metadata['file_size'] > 0

        # Log the validation
        log_system = get_logging_system()
        log_system.log_operation_end(
            "validation",
            is_valid,
            {"pdf": str(test_pdf), "pages": metadata['page_count']}
        )

    def test_error_logging(self):
        """Test error logging integration"""
        log_system = get_logging_system()

        # Log an error
        log_system.log_error(
            "TestError",
            "This is a test error",
            {"context": "integration_test"}
        )

        # Verify error log exists
        error_log = Path("logs/errors.log")
        assert error_log.exists()

        # Verify content
        with open(error_log, 'r') as f:
            content = f.read()

        assert "TestError" in content
        assert "test error" in content
