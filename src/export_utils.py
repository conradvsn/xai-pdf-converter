#!/usr/bin/env python3
"""
Export utilities for CSV and JSON report formats
Author: Conrad Vaslin - xAI Finance Tutor
Copyright: © 2025 Conrad Vaslin - All Rights Reserved
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class ReportExporter:
    """
    Handles exporting analysis reports to multiple formats
    """

    @staticmethod
    def export_to_csv(
        findings: Dict[tuple, List[int]],
        output_path: Path,
        anonymization_map: Optional[Dict[str, str]] = None,
        include_anonymized: bool = True
    ) -> Path:
        """
        Export findings to CSV format

        Args:
            findings: Dictionary of (info_type, info_value) -> pages
            output_path: Output CSV file path
            anonymization_map: Mapping of original -> anonymized values
            include_anonymized: Whether to include anonymization column

        Returns:
            Path: Path to created CSV file
        """
        # Prepare headers
        headers = ["Information Type", "Information", "Pages"]
        if include_anonymized and anonymization_map:
            headers.append("Anonymized Information")

        # Prepare rows
        rows = []
        for (info_type, info_value), pages in sorted(findings.items()):
            pages_str = ", ".join([f"p.{p}" for p in sorted(pages)])

            row = [info_type, info_value, pages_str]

            if include_anonymized and anonymization_map:
                anonymized = anonymization_map.get(info_value, "")
                row.append(anonymized)

            rows.append(row)

        # Write CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

        return output_path

    @staticmethod
    def export_to_json(
        findings: Dict[tuple, List[int]],
        output_path: Path,
        anonymization_map: Optional[Dict[str, str]] = None,
        include_metadata: bool = True
    ) -> Path:
        """
        Export findings to JSON format

        Args:
            findings: Dictionary of (info_type, info_value) -> pages
            output_path: Output JSON file path
            anonymization_map: Mapping of original -> anonymized values
            include_metadata: Whether to include metadata

        Returns:
            Path: Path to created JSON file
        """
        # Prepare findings data
        findings_list = []

        for (info_type, info_value), pages in sorted(findings.items()):
            entry = {
                "type": info_type,
                "value": info_value,
                "pages": sorted(pages),
                "occurrences": len(pages)
            }

            if anonymization_map and info_value in anonymization_map:
                entry["anonymized"] = anonymization_map[info_value]

            findings_list.append(entry)

        # Prepare full report
        report = {
            "findings": findings_list,
            "summary": {
                "total_items": len(findings_list),
                "total_occurrences": sum(len(pages) for pages in findings.values()),
                "types": {}
            }
        }

        # Count by type
        for info_type, _ in findings.keys():
            if info_type not in report["summary"]["types"]:
                report["summary"]["types"][info_type] = 0
            report["summary"]["types"][info_type] += 1

        # Add metadata
        if include_metadata:
            report["metadata"] = {
                "generated_at": datetime.now().isoformat(),
                "generator": "xAI PDF Converter v2.0.0",
                "author": "Conrad Vaslin - xAI Finance Tutor"
            }

        # Write JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return output_path

    @staticmethod
    def export_consolidated_csv(
        consolidated_findings: Dict[tuple, List[Dict]],
        output_path: Path,
        anonymization_map: Optional[Dict[str, str]] = None
    ) -> Path:
        """
        Export consolidated batch findings to CSV

        Args:
            consolidated_findings: Dictionary of (type, value) -> list of occurrences
            output_path: Output CSV path
            anonymization_map: Anonymization mapping

        Returns:
            Path: Path to created CSV file
        """
        headers = ["Information Type", "Information", "Documents", "Pages"]
        if anonymization_map:
            headers.append("Anonymized Information")

        rows = []

        for (info_type, info_value), occurrences in sorted(consolidated_findings.items()):
            # Get unique documents
            documents = sorted(list(set([occ['document'] for occ in occurrences])))
            documents_str = ", ".join(documents)

            # Group pages by document
            pages_by_doc = {}
            for occ in occurrences:
                doc = occ['document']
                if doc not in pages_by_doc:
                    pages_by_doc[doc] = []
                pages_by_doc[doc].extend(occ['pages'])

            # Format pages string
            pages_parts = []
            for doc in sorted(pages_by_doc.keys()):
                pages = sorted(set(pages_by_doc[doc]))
                pages_str = ", ".join([f"p.{p}" for p in pages])
                pages_parts.append(f"{doc} {pages_str}")

            pages_full_str = "; ".join(pages_parts)

            row = [info_type, info_value, documents_str, pages_full_str]

            if anonymization_map:
                anonymized = anonymization_map.get(info_value, "")
                row.append(anonymized)

            rows.append(row)

        # Write CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

        return output_path

    @staticmethod
    def export_consolidated_json(
        consolidated_findings: Dict[tuple, List[Dict]],
        output_path: Path,
        anonymization_map: Optional[Dict[str, str]] = None
    ) -> Path:
        """
        Export consolidated batch findings to JSON

        Args:
            consolidated_findings: Dictionary of (type, value) -> list of occurrences
            output_path: Output JSON path
            anonymization_map: Anonymization mapping

        Returns:
            Path: Path to created JSON file
        """
        findings_list = []

        for (info_type, info_value), occurrences in sorted(consolidated_findings.items()):
            entry = {
                "type": info_type,
                "value": info_value,
                "occurrences": []
            }

            # Group by document
            by_document = {}
            for occ in occurrences:
                doc = occ['document']
                if doc not in by_document:
                    by_document[doc] = []
                by_document[doc].extend(occ['pages'])

            # Create occurrence entries
            for doc, pages in sorted(by_document.items()):
                entry["occurrences"].append({
                    "document": doc,
                    "pages": sorted(set(pages))
                })

            entry["total_occurrences"] = sum(len(occ["pages"]) for occ in entry["occurrences"])
            entry["document_count"] = len(entry["occurrences"])

            if anonymization_map and info_value in anonymization_map:
                entry["anonymized"] = anonymization_map[info_value]

            findings_list.append(entry)

        # Prepare full report
        report = {
            "findings": findings_list,
            "summary": {
                "total_items": len(findings_list),
                "total_documents": len(set([
                    occ['document']
                    for _, occurrences in consolidated_findings.items()
                    for occ in occurrences
                ])),
                "types": {}
            },
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator": "xAI PDF Converter v2.0.0",
                "author": "Conrad Vaslin - xAI Finance Tutor"
            }
        }

        # Count by type
        for info_type, _ in consolidated_findings.keys():
            if info_type not in report["summary"]["types"]:
                report["summary"]["types"][info_type] = 0
            report["summary"]["types"][info_type] += 1

        # Write JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return output_path

    @staticmethod
    def get_export_formats() -> List[str]:
        """Get list of supported export formats"""
        return ["excel", "csv", "json"]

    @staticmethod
    def export_report(
        findings: Dict[tuple, List[int]],
        output_path: Path,
        format: str = "excel",
        anonymization_map: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Path:
        """
        Export report in specified format

        Args:
            findings: Findings dictionary
            output_path: Base output path (extension will be adjusted)
            format: Export format (excel, csv, json)
            anonymization_map: Anonymization mapping
            **kwargs: Additional format-specific arguments

        Returns:
            Path: Path to created file
        """
        # Adjust file extension
        base_path = output_path.with_suffix('')

        if format == "csv":
            csv_path = base_path.with_suffix('.csv')
            return ReportExporter.export_to_csv(
                findings,
                csv_path,
                anonymization_map,
                **kwargs
            )

        elif format == "json":
            json_path = base_path.with_suffix('.json')
            return ReportExporter.export_to_json(
                findings,
                json_path,
                anonymization_map,
                **kwargs
            )

        elif format == "excel":
            # Excel export handled by report_generator.py
            xlsx_path = base_path.with_suffix('.xlsx')
            return xlsx_path

        else:
            raise ValueError(f"Unsupported format: {format}. Use one of: {ReportExporter.get_export_formats()}")


def create_multi_format_reports(
    findings: Dict[tuple, List[int]],
    base_output_path: Path,
    formats: List[str],
    anonymization_map: Optional[Dict[str, str]] = None
) -> Dict[str, Path]:
    """
    Create reports in multiple formats at once

    Args:
        findings: Findings dictionary
        base_output_path: Base output path (without extension)
        formats: List of formats to create (e.g., ['excel', 'csv', 'json'])
        anonymization_map: Anonymization mapping

    Returns:
        Dict[str, Path]: Dictionary of format -> output path
    """
    created_files = {}
    base_path = base_output_path.with_suffix('')

    for format in formats:
        try:
            output_path = ReportExporter.export_report(
                findings,
                base_path,
                format,
                anonymization_map
            )
            created_files[format] = output_path
        except Exception as e:
            print(f"Warning: Failed to create {format} report: {e}")

    return created_files
