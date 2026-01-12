#!/usr/bin/env python3
"""
Progress tracking and PDF validation utilities
Author: Conrad Vaslin - xAI Finance Tutor
Copyright: © 2025 Conrad Vaslin - All Rights Reserved
"""

import PyPDF2
from pathlib import Path
from typing import Optional, Tuple
from src.config import TQDM_AVAILABLE

if TQDM_AVAILABLE:
    from tqdm import tqdm
else:
    # Fallback when tqdm is not available
    class tqdm:
        def __init__(self, iterable=None, total=None, desc=None, **kwargs):
            self.iterable = iterable
            self.total = total
            self.desc = desc
            self.n = 0

        def __iter__(self):
            if self.iterable:
                for item in self.iterable:
                    yield item
                    self.update(1)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def update(self, n=1):
            self.n += n
            if self.total:
                print(f"\r{self.desc}: {self.n}/{self.total}", end='', flush=True)


class PDFValidator:
    """
    Validates PDF files before processing
    """

    @staticmethod
    def validate_pdf(pdf_path: Path) -> Tuple[bool, Optional[str], dict]:
        """
        Validate a PDF file

        Args:
            pdf_path: Path to PDF file

        Returns:
            Tuple of (is_valid, error_message, metadata)
        """
        metadata = {
            "file_size": 0,
            "page_count": 0,
            "is_encrypted": False,
            "has_text": False,
            "pdf_version": None,
            "file_exists": False
        }

        # Check if file exists
        if not pdf_path.exists():
            return False, f"File not found: {pdf_path}", metadata

        metadata["file_exists"] = True

        # Check if it's a file (not a directory)
        if not pdf_path.is_file():
            return False, f"Path is not a file: {pdf_path}", metadata

        # Check file extension
        if pdf_path.suffix.lower() != '.pdf':
            return False, f"Not a PDF file (extension: {pdf_path.suffix})", metadata

        # Check file size
        try:
            file_size = pdf_path.stat().st_size
            metadata["file_size"] = file_size

            if file_size == 0:
                return False, "PDF file is empty (0 bytes)", metadata

            if file_size < 100:
                return False, f"PDF file too small ({file_size} bytes), likely corrupt", metadata

            # Maximum 500MB
            if file_size > 500 * 1024 * 1024:
                return False, f"PDF file too large ({file_size / (1024*1024):.1f} MB), max 500MB", metadata

        except Exception as e:
            return False, f"Error checking file size: {e}", metadata

        # Try to open with PyPDF2
        try:
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)

                # Check if encrypted
                if pdf_reader.is_encrypted:
                    metadata["is_encrypted"] = True
                    return False, "PDF is password-protected", metadata

                # Get page count
                page_count = len(pdf_reader.pages)
                metadata["page_count"] = page_count

                if page_count == 0:
                    return False, "PDF has 0 pages", metadata

                # Get PDF version
                if hasattr(pdf_reader, 'pdf_header'):
                    metadata["pdf_version"] = pdf_reader.pdf_header

                # Check if PDF has extractable text
                has_text = False
                pages_to_check = min(3, page_count)  # Check first 3 pages

                for i in range(pages_to_check):
                    try:
                        text = pdf_reader.pages[i].extract_text()
                        if text and text.strip():
                            has_text = True
                            break
                    except:
                        pass

                metadata["has_text"] = has_text

                # All checks passed
                return True, None, metadata

        except PyPDF2.errors.PdfReadError as e:
            return False, f"Invalid or corrupted PDF: {e}", metadata

        except Exception as e:
            return False, f"Error reading PDF: {e}", metadata

    @staticmethod
    def get_validation_report(pdf_path: Path) -> str:
        """
        Get a formatted validation report

        Args:
            pdf_path: Path to PDF file

        Returns:
            str: Formatted validation report
        """
        is_valid, error, metadata = PDFValidator.validate_pdf(pdf_path)

        report = []
        report.append("═" * 80)
        report.append(f"PDF VALIDATION REPORT: {pdf_path.name}")
        report.append("═" * 80)

        if is_valid:
            report.append("✅ Status: VALID")
        else:
            report.append(f"❌ Status: INVALID")
            report.append(f"❌ Error: {error}")

        report.append("")
        report.append("📊 Metadata:")

        if metadata["file_exists"]:
            size_mb = metadata["file_size"] / (1024 * 1024)
            report.append(f"  • File size: {size_mb:.2f} MB")

        if metadata["page_count"] > 0:
            report.append(f"  • Pages: {metadata['page_count']}")

        if metadata["pdf_version"]:
            report.append(f"  • PDF version: {metadata['pdf_version']}")

        report.append(f"  • Encrypted: {'Yes' if metadata['is_encrypted'] else 'No'}")
        report.append(f"  • Has text: {'Yes' if metadata['has_text'] else 'No (may need OCR)'}")

        report.append("═" * 80)

        return "\n".join(report)


class ProgressTracker:
    """
    Manages progress tracking for operations
    """

    def __init__(self, use_tqdm: bool = True):
        """
        Initialize progress tracker

        Args:
            use_tqdm: Whether to use tqdm for progress bars
        """
        self.use_tqdm = use_tqdm and TQDM_AVAILABLE

    def track_operation(
        self,
        items,
        desc: str,
        unit: str = "file"
    ):
        """
        Track progress for an operation

        Args:
            items: Iterable of items to process
            desc: Description of operation
            unit: Unit name for progress

        Returns:
            Iterator with progress tracking
        """
        if self.use_tqdm:
            return tqdm(
                items,
                desc=desc,
                unit=unit,
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
                colour='cyan'
            )
        else:
            # Fallback: simple counter
            total = len(items) if hasattr(items, '__len__') else None
            return self._simple_progress(items, desc, total)

    def _simple_progress(self, items, desc, total):
        """
        Simple progress counter without tqdm

        Args:
            items: Items to iterate
            desc: Description
            total: Total count

        Yields:
            Items with progress printing
        """
        count = 0
        for item in items:
            count += 1
            if total:
                print(f"\r{desc}: {count}/{total}", end='', flush=True)
            else:
                print(f"\r{desc}: {count}", end='', flush=True)
            yield item
        print()  # New line after completion

    def create_progress_bar(
        self,
        total: int,
        desc: str,
        unit: str = "it"
    ):
        """
        Create a progress bar for manual updates

        Args:
            total: Total number of items
            desc: Description
            unit: Unit name

        Returns:
            Progress bar object
        """
        if self.use_tqdm:
            return tqdm(
                total=total,
                desc=desc,
                unit=unit,
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
                colour='green'
            )
        else:
            return SimpleProgress(total, desc)


class SimpleProgress:
    """
    Simple progress tracker fallback
    """

    def __init__(self, total: int, desc: str):
        self.total = total
        self.desc = desc
        self.current = 0

    def update(self, n: int = 1):
        """Update progress"""
        self.current += n
        print(f"\r{self.desc}: {self.current}/{self.total}", end='', flush=True)

    def close(self):
        """Close progress tracker"""
        print()  # New line

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def validate_pdf_batch(pdf_files: list) -> Tuple[list, list]:
    """
    Validate a batch of PDF files

    Args:
        pdf_files: List of PDF file paths

    Returns:
        Tuple of (valid_files, invalid_files_with_reasons)
    """
    valid_files = []
    invalid_files = []

    tracker = ProgressTracker()

    print("\n🔍 Validating PDF files...")

    for pdf_file in tracker.track_operation(pdf_files, "Validating", "file"):
        is_valid, error, metadata = PDFValidator.validate_pdf(Path(pdf_file))

        if is_valid:
            valid_files.append(pdf_file)
        else:
            invalid_files.append({
                "file": pdf_file,
                "error": error,
                "metadata": metadata
            })

    return valid_files, invalid_files
