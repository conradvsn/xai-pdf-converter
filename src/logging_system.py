#!/usr/bin/env python3
"""
Enhanced logging system with rotation and audit trails
Author: Conrad Vaslin - xAI Finance Tutor
Copyright: © 2025 Conrad Vaslin - All Rights Reserved
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional


class LoggingSystem:
    """
    Enhanced logging system with multiple handlers and rotation
    """

    def __init__(self, log_dir: Optional[Path] = None, enable_console: bool = True):
        """
        Initialize logging system

        Args:
            log_dir: Directory for log files (default: logs/)
            enable_console: Whether to enable console logging
        """
        if log_dir is None:
            log_dir = Path.cwd() / "logs"

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        self.enable_console = enable_console
        self.loggers = {}

        # Create formatters
        self.detailed_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        self.simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )

        self.audit_formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def get_logger(
        self,
        name: str,
        level: int = logging.INFO,
        log_to_file: bool = True,
        log_type: str = "main"
    ) -> logging.Logger:
        """
        Get or create a logger with specified configuration

        Args:
            name: Logger name
            level: Logging level
            log_to_file: Whether to log to file
            log_type: Type of log (main, conversion, analysis, audit, error)

        Returns:
            logging.Logger: Configured logger
        """
        if name in self.loggers:
            return self.loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.handlers = []  # Clear existing handlers

        # Console handler
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(self.simple_formatter)
            logger.addHandler(console_handler)

        # File handlers
        if log_to_file:
            if log_type == "main":
                # Main application log - rotates when 10MB
                file_path = self.log_dir / "xai_converter.log"
                file_handler = RotatingFileHandler(
                    file_path,
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=5,
                    encoding='utf-8'
                )
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(self.detailed_formatter)
                logger.addHandler(file_handler)

            elif log_type == "conversion":
                # Conversion logs - rotates daily
                file_path = self.log_dir / "conversions.log"
                file_handler = TimedRotatingFileHandler(
                    file_path,
                    when='midnight',
                    interval=1,
                    backupCount=30,  # Keep 30 days
                    encoding='utf-8'
                )
                file_handler.setLevel(logging.INFO)
                file_handler.setFormatter(self.detailed_formatter)
                logger.addHandler(file_handler)

            elif log_type == "analysis":
                # Analysis logs - rotates daily
                file_path = self.log_dir / "analysis.log"
                file_handler = TimedRotatingFileHandler(
                    file_path,
                    when='midnight',
                    interval=1,
                    backupCount=30,
                    encoding='utf-8'
                )
                file_handler.setLevel(logging.INFO)
                file_handler.setFormatter(self.detailed_formatter)
                logger.addHandler(file_handler)

            elif log_type == "audit":
                # Audit trail - never rotates, append only
                file_path = self.log_dir / "audit_trail.log"
                file_handler = logging.FileHandler(
                    file_path,
                    mode='a',
                    encoding='utf-8'
                )
                file_handler.setLevel(logging.INFO)
                file_handler.setFormatter(self.audit_formatter)
                logger.addHandler(file_handler)

            elif log_type == "error":
                # Error log - rotates when 5MB
                file_path = self.log_dir / "errors.log"
                file_handler = RotatingFileHandler(
                    file_path,
                    maxBytes=5*1024*1024,  # 5MB
                    backupCount=10,
                    encoding='utf-8'
                )
                file_handler.setLevel(logging.ERROR)
                file_handler.setFormatter(self.detailed_formatter)
                logger.addHandler(file_handler)

        self.loggers[name] = logger
        return logger

    def log_operation_start(self, operation: str, details: dict):
        """
        Log the start of an operation to audit trail

        Args:
            operation: Operation name
            details: Operation details
        """
        audit_logger = self.get_logger("audit", log_type="audit")
        details_str = " | ".join([f"{k}={v}" for k, v in details.items()])
        audit_logger.info(f"START | {operation} | {details_str}")

    def log_operation_end(self, operation: str, success: bool, details: dict):
        """
        Log the end of an operation to audit trail

        Args:
            operation: Operation name
            success: Whether operation succeeded
            details: Operation details
        """
        audit_logger = self.get_logger("audit", log_type="audit")
        status = "SUCCESS" if success else "FAILED"
        details_str = " | ".join([f"{k}={v}" for k, v in details.items()])
        audit_logger.info(f"END | {operation} | {status} | {details_str}")

    def log_conversion(self, pdf_file: str, docx_file: str, success: bool, duration: float):
        """
        Log a conversion operation

        Args:
            pdf_file: Input PDF file
            docx_file: Output DOCX file
            success: Whether conversion succeeded
            duration: Duration in seconds
        """
        logger = self.get_logger("conversion", log_type="conversion")
        status = "SUCCESS" if success else "FAILED"

        logger.info(f"{status} | PDF: {pdf_file} → DOCX: {docx_file} | Duration: {duration:.2f}s")

        # Also log to audit trail
        self.log_operation_end(
            "conversion",
            success,
            {
                "pdf": pdf_file,
                "docx": docx_file,
                "duration": f"{duration:.2f}s"
            }
        )

    def log_analysis(self, pdf_file: str, report_file: str, findings_count: int, success: bool):
        """
        Log an analysis operation

        Args:
            pdf_file: Input PDF file
            report_file: Output report file
            findings_count: Number of findings
            success: Whether analysis succeeded
        """
        logger = self.get_logger("analysis", log_type="analysis")
        status = "SUCCESS" if success else "FAILED"

        logger.info(f"{status} | PDF: {pdf_file} → Report: {report_file} | Findings: {findings_count}")

        # Also log to audit trail
        self.log_operation_end(
            "analysis",
            success,
            {
                "pdf": pdf_file,
                "report": report_file,
                "findings": findings_count
            }
        )

    def log_batch_operation(self, operation: str, file_count: int, success_count: int, duration: float):
        """
        Log a batch operation

        Args:
            operation: Operation type (conversion, analysis)
            file_count: Total files processed
            success_count: Successfully processed files
            duration: Total duration in seconds
        """
        logger = self.get_logger("main", log_type="main")

        logger.info(
            f"BATCH {operation.upper()} COMPLETED | "
            f"Files: {success_count}/{file_count} | "
            f"Duration: {duration:.2f}s"
        )

        # Audit trail
        self.log_operation_end(
            f"batch_{operation}",
            success_count == file_count,
            {
                "total_files": file_count,
                "successful": success_count,
                "failed": file_count - success_count,
                "duration": f"{duration:.2f}s"
            }
        )

    def log_error(self, error_type: str, error_message: str, context: dict = None):
        """
        Log an error with context

        Args:
            error_type: Type of error
            error_message: Error message
            context: Additional context
        """
        error_logger = self.get_logger("error", log_type="error")

        if context:
            context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
            error_logger.error(f"{error_type} | {error_message} | Context: {context_str}")
        else:
            error_logger.error(f"{error_type} | {error_message}")

    def get_log_stats(self) -> dict:
        """
        Get statistics about log files

        Returns:
            dict: Log file statistics
        """
        stats = {}

        log_files = {
            "Main Log": "xai_converter.log",
            "Conversions": "conversions.log",
            "Analysis": "analysis.log",
            "Audit Trail": "audit_trail.log",
            "Errors": "errors.log"
        }

        for name, filename in log_files.items():
            file_path = self.log_dir / filename
            if file_path.exists():
                size = file_path.stat().st_size
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.2f} MB"

                # Count lines
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        line_count = sum(1 for _ in f)
                except Exception:
                    # If file cannot be read, set count to 0
                    line_count = 0

                stats[name] = {
                    "path": str(file_path),
                    "size": size_str,
                    "lines": line_count
                }
            else:
                stats[name] = {
                    "path": str(file_path),
                    "size": "0 B",
                    "lines": 0
                }

        return stats

    def clear_old_logs(self, days: int = 30):
        """
        Clear log files older than specified days

        Args:
            days: Number of days to keep
        """
        import time

        current_time = time.time()
        cutoff_time = current_time - (days * 86400)

        deleted_count = 0

        for log_file in self.log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                deleted_count += 1

        logger = self.get_logger("main", log_type="main")
        logger.info(f"Cleared {deleted_count} old log files (older than {days} days)")


# Global logging system instance
_logging_system = None


def get_logging_system() -> LoggingSystem:
    """
    Get the global logging system instance (singleton)

    Returns:
        LoggingSystem: Global logging system instance
    """
    global _logging_system
    if _logging_system is None:
        _logging_system = LoggingSystem()
    return _logging_system


def setup_logging(verbose: bool = False, console: bool = True):
    """
    Setup logging for the application

    Args:
        verbose: Enable verbose logging
        console: Enable console output
    """
    global _logging_system
    _logging_system = LoggingSystem(enable_console=console)

    level = logging.DEBUG if verbose else logging.INFO

    # Setup main logger
    logger = _logging_system.get_logger("xai_converter", level=level, log_type="main")
    logger.info("=" * 80)
    logger.info("xAI PDF Converter Started")
    logger.info(f"Version: 2.0.0 | Developer: Conrad Vaslin - xAI Finance Tutor")
    logger.info("=" * 80)

    return logger
