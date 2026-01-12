"""
Unit tests for export utilities
Author: Conrad Vaslin - xAI Finance Tutor
"""

import pytest
import json
import csv
from pathlib import Path
from src.export_utils import ReportExporter


class TestExportUtils:
    """Test export functionality"""

    @pytest.fixture
    def sample_findings(self):
        """Create sample findings data"""
        return {
            ("company_name", "Vantiv LLC"): [5, 12, 23],
            ("person_name", "John Smith"): [3, 15],
            ("email", "john@example.com"): [7, 18, 22]
        }

    @pytest.fixture
    def sample_anonymization(self):
        """Create sample anonymization map"""
        return {
            "Vantiv LLC": "Company_Alpha",
            "John Smith": "Person_Beta",
            "john@example.com": "Email_Gamma"
        }

    def test_export_to_csv(self, tmp_path, sample_findings, sample_anonymization):
        """Test CSV export"""
        output_path = tmp_path / "test_report.csv"

        result = ReportExporter.export_to_csv(
            sample_findings,
            output_path,
            sample_anonymization,
            include_anonymized=True
        )

        # Verify file created
        assert output_path.exists()
        assert result == output_path

        # Verify content
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Check header
        assert rows[0][0] == "Information Type"
        assert rows[0][1] == "Information"
        assert rows[0][2] == "Pages"
        assert rows[0][3] == "Anonymized Information"

        # Check data rows
        assert len(rows) == 4  # Header + 3 data rows

    def test_export_to_json(self, tmp_path, sample_findings, sample_anonymization):
        """Test JSON export"""
        output_path = tmp_path / "test_report.json"

        result = ReportExporter.export_to_json(
            sample_findings,
            output_path,
            sample_anonymization,
            include_metadata=True
        )

        # Verify file created
        assert output_path.exists()
        assert result == output_path

        # Verify content
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check structure
        assert 'findings' in data
        assert 'summary' in data
        assert 'metadata' in data

        # Check findings
        assert len(data['findings']) == 3

        # Check metadata
        assert 'Conrad Vaslin' in data['metadata']['author']

        # Check summary
        assert data['summary']['total_items'] == 3

    def test_export_without_anonymization(self, tmp_path, sample_findings):
        """Test export without anonymization"""
        output_path = tmp_path / "test_report.json"

        ReportExporter.export_to_json(
            sample_findings,
            output_path,
            anonymization_map=None
        )

        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Verify no anonymization field
        for finding in data['findings']:
            if 'anonymized' in finding:
                pytest.fail("Anonymized field should not be present")

    def test_get_export_formats(self):
        """Test getting supported formats"""
        formats = ReportExporter.get_export_formats()

        assert 'excel' in formats
        assert 'csv' in formats
        assert 'json' in formats

    def test_export_consolidated_csv(self, tmp_path):
        """Test consolidated CSV export"""
        consolidated = {
            ("company_name", "Vantiv LLC"): [
                {'document': 'doc1.docx', 'pages': [5, 12]},
                {'document': 'doc2.docx', 'pages': [3]}
            ]
        }

        output_path = tmp_path / "consolidated.csv"
        anonymization = {"Vantiv LLC": "Company_Alpha"}

        ReportExporter.export_consolidated_csv(
            consolidated,
            output_path,
            anonymization
        )

        assert output_path.exists()

        # Verify content
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Check header
        assert "Documents" in rows[0]
        assert "Pages" in rows[0]
        assert "Anonymized Information" in rows[0]

    def test_export_consolidated_json(self, tmp_path):
        """Test consolidated JSON export"""
        consolidated = {
            ("company_name", "Vantiv LLC"): [
                {'document': 'doc1.docx', 'pages': [5, 12]},
                {'document': 'doc2.docx', 'pages': [3]}
            ]
        }

        output_path = tmp_path / "consolidated.json"
        anonymization = {"Vantiv LLC": "Company_Alpha"}

        ReportExporter.export_consolidated_json(
            consolidated,
            output_path,
            anonymization
        )

        assert output_path.exists()

        # Verify content
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert 'findings' in data
        assert 'summary' in data
        assert data['summary']['total_documents'] == 2

    def test_csv_encoding(self, tmp_path, sample_findings):
        """Test CSV handles special characters"""
        # Add finding with special characters
        findings = {
            ("company_name", "Société Française"): [1],
            ("person_name", "José García"): [2]
        }

        output_path = tmp_path / "test_utf8.csv"
        ReportExporter.export_to_csv(findings, output_path, None, False)

        # Read back and verify
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "Société Française" in content
        assert "José García" in content

    def test_json_structure(self, tmp_path, sample_findings, sample_anonymization):
        """Test JSON structure is correct"""
        output_path = tmp_path / "test_structure.json"

        ReportExporter.export_to_json(
            sample_findings,
            output_path,
            sample_anonymization
        )

        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Verify each finding has required fields
        for finding in data['findings']:
            assert 'type' in finding
            assert 'value' in finding
            assert 'pages' in finding
            assert 'occurrences' in finding
            assert isinstance(finding['pages'], list)
            assert isinstance(finding['occurrences'], int)
