#!/usr/bin/env python3
"""
Accuracy Testing Framework for Sensitive Information Detection
Author: Conrad Vaslin - xAI Finance Tutor

This script tests the detection accuracy on real PDFs and generates metrics.
"""

import sys
import json
import time
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.analysis.sensitive_info_detector import detect_sensitive_information


# ============================================================================
# GROUND TRUTH DATA (to be manually verified/updated)
# Format: {filename: {type: [expected_values]}}
# ============================================================================
GROUND_TRUTH = {
    # Example format - update with actual verified values
    "December 31, 2016 Form 10-K.pdf": {
        "email": [],  # Add verified emails here
        "phone": [],  # Add verified phones here
        "address": [],  # Add verified addresses here
        "person_name": [],  # Add verified person names here
        "company_name": [],  # Add verified company names here
        # Financial identifiers
        "isin_code": [],
        "sedol_code": [],
        "figi_code": [],
        "lei_code": [],
        "patent_number": [],
        "sec_url": [],
    },
}


def run_detection_on_pdf(pdf_path: Path, verbose: bool = False) -> dict:
    """Run detection on a single PDF and return results."""
    start_time = time.time()

    try:
        findings_by_page = detect_sensitive_information(pdf_path, verbose=verbose)
        elapsed = time.time() - start_time

        # Flatten findings by type
        findings_by_type = defaultdict(list)
        total_findings = 0

        for page_num, page_findings in findings_by_page.items():
            for finding in page_findings:
                finding_type = finding['type']
                finding_value = finding['value']
                findings_by_type[finding_type].append({
                    'value': finding_value,
                    'page': finding.get('page', page_num)
                })
                total_findings += 1

        return {
            'success': True,
            'elapsed_time': elapsed,
            'total_findings': total_findings,
            'findings_by_type': dict(findings_by_type),
            'pages_analyzed': len(findings_by_page)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'elapsed_time': time.time() - start_time
        }


def calculate_metrics(detected: list, ground_truth: list) -> dict:
    """
    Calculate precision, recall, and F1 score.

    - Precision: Of all detected items, how many are correct?
    - Recall: Of all true items, how many were detected?
    - F1: Harmonic mean of precision and recall
    """
    detected_set = set(str(v).lower().strip() for v in detected)
    truth_set = set(str(v).lower().strip() for v in ground_truth)

    if not truth_set and not detected_set:
        return {'precision': 1.0, 'recall': 1.0, 'f1': 1.0, 'tp': 0, 'fp': 0, 'fn': 0}

    true_positives = len(detected_set & truth_set)
    false_positives = len(detected_set - truth_set)
    false_negatives = len(truth_set - detected_set)

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'tp': true_positives,
        'fp': false_positives,
        'fn': false_negatives,
        'detected': list(detected_set),
        'expected': list(truth_set),
        'missed': list(truth_set - detected_set),
        'false_alarms': list(detected_set - truth_set)
    }


def generate_report(results: dict, output_path: Path = None):
    """Generate a detailed accuracy report."""

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("ACCURACY TEST REPORT - Sensitive Information Detection")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    report_lines.append("")

    # Summary statistics
    total_pdfs = len(results)
    successful_pdfs = sum(1 for r in results.values() if r.get('success', False))
    total_time = sum(r.get('elapsed_time', 0) for r in results.values())
    total_findings = sum(r.get('total_findings', 0) for r in results.values() if r.get('success'))

    report_lines.append("SUMMARY")
    report_lines.append("-" * 40)
    report_lines.append(f"PDFs processed: {successful_pdfs}/{total_pdfs}")
    report_lines.append(f"Total processing time: {total_time:.2f}s")
    report_lines.append(f"Average time per PDF: {total_time/max(successful_pdfs,1):.2f}s")
    report_lines.append(f"Total findings: {total_findings}")
    report_lines.append("")

    # Aggregate findings by type
    all_findings_by_type = defaultdict(int)
    for pdf_name, result in results.items():
        if result.get('success'):
            for finding_type, findings in result.get('findings_by_type', {}).items():
                all_findings_by_type[finding_type] += len(findings)

    report_lines.append("FINDINGS BY TYPE (All PDFs)")
    report_lines.append("-" * 40)
    for finding_type, count in sorted(all_findings_by_type.items(), key=lambda x: -x[1]):
        report_lines.append(f"  {finding_type}: {count}")
    report_lines.append("")

    # Per-PDF details
    report_lines.append("=" * 80)
    report_lines.append("DETAILED RESULTS BY PDF")
    report_lines.append("=" * 80)

    for pdf_name, result in results.items():
        report_lines.append("")
        report_lines.append(f"FILE: {pdf_name}")
        report_lines.append("-" * 60)

        if not result.get('success'):
            report_lines.append(f"  ERROR: {result.get('error', 'Unknown error')}")
            continue

        report_lines.append(f"  Processing time: {result['elapsed_time']:.2f}s")
        report_lines.append(f"  Pages analyzed: {result['pages_analyzed']}")
        report_lines.append(f"  Total findings: {result['total_findings']}")
        report_lines.append("")

        # Findings by type for this PDF
        for finding_type, findings in sorted(result.get('findings_by_type', {}).items()):
            report_lines.append(f"  {finding_type} ({len(findings)}):")

            # Deduplicate values for display
            unique_values = {}
            for f in findings:
                val = f['value']
                if val not in unique_values:
                    unique_values[val] = []
                unique_values[val].append(f['page'])

            for value, pages in list(unique_values.items())[:10]:  # Show max 10 per type
                pages_str = ', '.join(map(str, sorted(set(pages))[:3]))
                if len(pages) > 3:
                    pages_str += f"... ({len(pages)} total)"
                report_lines.append(f"    - {value[:60]}{'...' if len(str(value)) > 60 else ''}")
                report_lines.append(f"      (pages: {pages_str})")

            if len(unique_values) > 10:
                report_lines.append(f"    ... and {len(unique_values) - 10} more")
            report_lines.append("")

    report = "\n".join(report_lines)

    # Print to console
    print(report)

    # Save to file if path provided
    if output_path:
        output_path.write_text(report)
        print(f"\nReport saved to: {output_path}")

    return report


def export_findings_json(results: dict, output_path: Path):
    """Export all findings to JSON for manual review/annotation."""
    export_data = {
        'generated': datetime.now().isoformat(),
        'pdfs': {}
    }

    for pdf_name, result in results.items():
        if result.get('success'):
            export_data['pdfs'][pdf_name] = {
                'elapsed_time': result['elapsed_time'],
                'total_findings': result['total_findings'],
                'findings_by_type': {
                    ftype: [f['value'] for f in findings]
                    for ftype, findings in result.get('findings_by_type', {}).items()
                }
            }

    output_path.write_text(json.dumps(export_data, indent=2, ensure_ascii=False))
    print(f"Findings exported to: {output_path}")


def main():
    """Main function to run accuracy tests."""
    print("\n" + "=" * 80)
    print("ACCURACY TESTING FRAMEWORK - Sensitive Information Detection")
    print("=" * 80 + "\n")

    # Find all PDFs
    pdf_dir = Path(__file__).parent / "pdf"
    if not pdf_dir.exists():
        print(f"ERROR: PDF directory not found: {pdf_dir}")
        return 1

    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"ERROR: No PDF files found in {pdf_dir}")
        return 1

    print(f"Found {len(pdf_files)} PDF files to analyze:")
    for pdf in pdf_files:
        print(f"  - {pdf.name}")
    print()

    # Run detection on each PDF
    results = {}
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] Processing: {pdf_path.name}...", end=" ", flush=True)
        result = run_detection_on_pdf(pdf_path, verbose=False)
        results[pdf_path.name] = result

        if result['success']:
            print(f"OK ({result['total_findings']} findings in {result['elapsed_time']:.1f}s)")
        else:
            print(f"FAILED: {result.get('error', 'Unknown')}")

    print()

    # Generate report
    report_path = Path(__file__).parent / "accuracy_report.txt"
    generate_report(results, report_path)

    # Export to JSON for annotation
    json_path = Path(__file__).parent / "detected_findings.json"
    export_findings_json(results, json_path)

    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("1. Review detected_findings.json")
    print("2. Manually verify findings and create ground truth")
    print("3. Update GROUND_TRUTH in this script")
    print("4. Re-run to calculate precision/recall/F1 metrics")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
