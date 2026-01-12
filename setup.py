#!/usr/bin/env python3
"""
Setup script for xAI PDF Converter
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README if available
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="xai-pdf-converter",
    version="1.0.0",
    description="PDF to DOCX converter with structure preservation and sensitive information detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="xAI PDF Converter Team",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    install_requires=[
        "PyPDF2>=3.0.0",
        "pdf2docx>=0.5.0",
        "python-docx>=0.8.11",
        "openpyxl>=3.1.0",
    ],
    extras_require={
        "ocr": [
            "pdf2image>=1.16.0",
            "Pillow>=10.0.0",
        ],
        "paddleocr": [
            "paddlepaddle>=2.5.0",
            "paddleocr>=2.7.0",
        ],
        "easyocr": [
            "easyocr>=1.7.0",
        ],
        "tesseract": [
            "pytesseract>=0.3.10",
        ],
        "all": [
            "pdfplumber>=0.10.0",
            "tqdm>=4.66.0",
            "phonenumbers>=8.13.0",
            "pdf2image>=1.16.0",
            "Pillow>=10.0.0",
        ],
    },
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "xai-pdf-converter=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)





