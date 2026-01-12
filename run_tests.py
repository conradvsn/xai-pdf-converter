#!/usr/bin/env python3
"""
Test runner for xAI PDF Converter
Author: Conrad Vaslin - xAI Finance Tutor
Copyright: © 2025 Conrad Vaslin - All Rights Reserved
"""

import sys
import subprocess
from pathlib import Path


def check_pytest_installed():
    """Check if pytest is installed"""
    try:
        import pytest
        return True
    except ImportError:
        return False


def run_tests(args=None):
    """
    Run tests with pytest

    Args:
        args: Additional pytest arguments
    """
    if not check_pytest_installed():
        print("❌ pytest is not installed!")
        print("\nInstall with:")
        print("  pip install pytest")
        print("\nOptional (for coverage):")
        print("  pip install pytest-cov")
        return 1

    # Base command
    cmd = [sys.executable, "-m", "pytest"]

    # Add arguments
    if args:
        cmd.extend(args)

    print("=" * 80)
    print("Running xAI PDF Converter Tests")
    print("=" * 80)
    print(f"\nCommand: {' '.join(cmd)}\n")

    # Run tests
    result = subprocess.run(cmd)

    return result.returncode


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test runner for xAI PDF Converter"
    )

    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests"
    )

    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests"
    )

    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report (requires pytest-cov)"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )

    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip slow tests"
    )

    parser.add_argument(
        "pytest_args",
        nargs="*",
        help="Additional pytest arguments"
    )

    args = parser.parse_args()

    # Build pytest arguments
    pytest_args = []

    if args.unit:
        pytest_args.extend(["-m", "unit"])
    elif args.integration:
        pytest_args.extend(["-m", "integration"])

    if args.fast:
        pytest_args.extend(["-m", "not slow"])

    if args.coverage:
        pytest_args.extend([
            "--cov=src",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])

    if args.verbose:
        pytest_args.append("-vv")

    # Add user-provided arguments
    if args.pytest_args:
        pytest_args.extend(args.pytest_args)

    # Run tests
    return run_tests(pytest_args)


if __name__ == "__main__":
    sys.exit(main())
