#!/usr/bin/env python3
"""
Enhanced user interface with colors and modern styling
Author: Conrad Vaslin - xAI Finance Tutor
Copyright: © 2025 Conrad Vaslin - All Rights Reserved
"""

from typing import Optional
from src.config import (
    OCR_AVAILABLE, PDF2DOCX_AVAILABLE, PYPDF2_AVAILABLE, OPENPYXL_AVAILABLE,
    PADDLEOCR_AVAILABLE, EASYOCR_AVAILABLE, PYTESSERACT_AVAILABLE,
    PDF2IMAGE_AVAILABLE, TQDM_AVAILABLE, PHONENUMBERS_AVAILABLE,
    PDFPLUMBER_AVAILABLE, PYTHON_DOCX_AVAILABLE
)


# ANSI Color Codes for terminal
class Colors:
    """Terminal color codes for enhanced visuals"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright foreground colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'


def print_header(text: str, color: str = Colors.BRIGHT_CYAN, width: int = 80):
    """Print a styled header"""
    print("\n" + color + "═" * width + Colors.RESET)
    print(color + Colors.BOLD + text.center(width) + Colors.RESET)
    print(color + "═" * width + Colors.RESET)


def print_section(title: str, color: str = Colors.BRIGHT_BLUE, width: int = 80):
    """Print a section divider"""
    print("\n" + color + "─" * width + Colors.RESET)
    print(color + Colors.BOLD + f"  {title}" + Colors.RESET)
    print(color + "─" * width + Colors.RESET)


def print_option(number: str, text: str, status: Optional[str] = None):
    """Print a menu option with styling"""
    number_colored = f"{Colors.BRIGHT_YELLOW}{number}{Colors.RESET}"

    if status:
        if "✅" in status or "Available" in status:
            status_colored = f"{Colors.BRIGHT_GREEN}{status}{Colors.RESET}"
        elif "❌" in status or "Not installed" in status:
            status_colored = f"{Colors.BRIGHT_RED}{status}{Colors.RESET}"
        else:
            status_colored = f"{Colors.YELLOW}{status}{Colors.RESET}"

        print(f"  {number_colored}. {Colors.WHITE}{text:<40}{Colors.RESET} {status_colored}")
    else:
        print(f"  {number_colored}. {Colors.WHITE}{text}{Colors.RESET}")


def print_success(message: str):
    """Print a success message"""
    print(f"{Colors.BRIGHT_GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str):
    """Print an error message"""
    print(f"{Colors.BRIGHT_RED}✗ {message}{Colors.RESET}")


def print_warning(message: str):
    """Print a warning message"""
    print(f"{Colors.BRIGHT_YELLOW}⚠ {message}{Colors.RESET}")


def print_info(message: str):
    """Print an info message"""
    print(f"{Colors.BRIGHT_CYAN}ℹ {message}{Colors.RESET}")


def print_box(lines: list, color: str = Colors.BRIGHT_CYAN, width: int = 76):
    """Print text in a box"""
    print(f"\n{color}╔{'═' * width}╗{Colors.RESET}")
    for line in lines:
        padding = width - len(line)
        print(f"{color}║{Colors.RESET} {line}{' ' * padding} {color}║{Colors.RESET}")
    print(f"{color}╚{'═' * width}╝{Colors.RESET}")


def show_main_menu_enhanced():
    """
    Enhanced main menu with colors and modern styling
    """
    # Check capabilities
    ocr_status = "✅ Available" if OCR_AVAILABLE else "❌ Not installed"
    conversion_status = "✅ Available" if PDF2DOCX_AVAILABLE else "❌ Not installed"
    analysis_status = "✅ Available" if (PYPDF2_AVAILABLE and OPENPYXL_AVAILABLE) else "❌ Not installed"

    # Header
    print_header("🚀 xAI PDF CONVERTER 🚀", Colors.BRIGHT_CYAN)

    # Single File Operations
    print_section("📄 SINGLE FILE OPERATIONS", Colors.BRIGHT_BLUE)
    print_option("1", "Convert PDF → Word", conversion_status)
    print_option("2", "Convert PDF → Word + Analysis", conversion_status)
    print_option("3", "Analyze PDF Only (Excel Report)", analysis_status)
    print_option("4", "OCR: Scanned PDF → Word", ocr_status)

    # Batch Processing
    print_section("📦 BATCH PROCESSING (Multiple PDFs)", Colors.BRIGHT_MAGENTA)
    print_option("5", "Batch: Convert All PDFs")
    print_option("6", "Batch: Convert + Analyze All")
    print_option("7", "Batch: Analyze All PDFs")

    # Settings & Info
    print_section("⚙️  SETTINGS & INFO", Colors.BRIGHT_GREEN)
    print_option("8", "View System Status")
    print_option("9", "Configure Settings")
    print_option("0", "Exit")

    # Footer
    print("\n" + Colors.BRIGHT_CYAN + "═" * 80 + Colors.RESET)
    footer_text = "© 2025 Conrad Vaslin - xAI Finance Tutor  |  Version 2.0.0"
    print(Colors.CYAN + Colors.BOLD + footer_text.center(80) + Colors.RESET)
    print(Colors.BRIGHT_CYAN + "═" * 80 + Colors.RESET + "\n")

    choice = input(f"{Colors.BRIGHT_YELLOW}➤ Your choice (0-9): {Colors.RESET}").strip()
    return choice


def show_system_status_enhanced():
    """
    Enhanced system status with colors and progress indicators
    """
    print_header("SYSTEM STATUS", Colors.BRIGHT_CYAN)

    # Core dependencies
    print_section("🔧 CORE DEPENDENCIES", Colors.BRIGHT_BLUE)
    deps = [
        ("PyPDF2", PYPDF2_AVAILABLE, "PDF text extraction"),
        ("pdf2docx", PDF2DOCX_AVAILABLE, "PDF to Word conversion"),
        ("python-docx", PYTHON_DOCX_AVAILABLE, "Word document processing"),
        ("openpyxl", OPENPYXL_AVAILABLE, "Excel report generation"),
        ("pdfplumber", PDFPLUMBER_AVAILABLE, "Advanced table extraction"),
    ]

    for name, available, description in deps:
        status = f"{Colors.BRIGHT_GREEN}✅{Colors.RESET}" if available else f"{Colors.BRIGHT_RED}❌{Colors.RESET}"
        print(f"  {status} {Colors.WHITE}{name:<20}{Colors.RESET} {Colors.DIM}- {description}{Colors.RESET}")

    # Optional dependencies
    print_section("🎨 OPTIONAL FEATURES", Colors.BRIGHT_MAGENTA)
    opt_deps = [
        ("tqdm", TQDM_AVAILABLE, "Progress bars"),
        ("phonenumbers", PHONENUMBERS_AVAILABLE, "Phone number validation"),
    ]

    for name, available, description in opt_deps:
        status = f"{Colors.BRIGHT_GREEN}✅{Colors.RESET}" if available else f"{Colors.BRIGHT_YELLOW}⚠️ {Colors.RESET}"
        print(f"  {status} {Colors.WHITE}{name:<20}{Colors.RESET} {Colors.DIM}- {description}{Colors.RESET}")

    # OCR capabilities
    print_section("🔍 OCR ENGINES (for scanned PDFs)", Colors.BRIGHT_GREEN)
    ocr_engines = [
        ("PaddleOCR", PADDLEOCR_AVAILABLE, "🏆 Best quality + table detection"),
        ("EasyOCR", EASYOCR_AVAILABLE, "⭐ Good quality, easy setup"),
        ("Tesseract", PYTESSERACT_AVAILABLE, "✓  Basic OCR"),
        ("pdf2image", PDF2IMAGE_AVAILABLE, "Required for all OCR methods"),
    ]

    for name, available, description in ocr_engines:
        status = f"{Colors.BRIGHT_GREEN}✅{Colors.RESET}" if available else f"{Colors.BRIGHT_RED}❌{Colors.RESET}"
        print(f"  {status} {Colors.WHITE}{name:<20}{Colors.RESET} {Colors.DIM}- {description}{Colors.RESET}")

    # Summary
    print_section("📊 SUMMARY", Colors.BRIGHT_CYAN)
    total_features = len(deps) + len(opt_deps) + len(ocr_engines)
    available_features = sum([
        sum([1 for _, av, _ in deps if av]),
        sum([1 for _, av, _ in opt_deps if av]),
        sum([1 for _, av, _ in ocr_engines if av]),
    ])

    percentage = (available_features / total_features) * 100
    bar_length = 40
    filled = int(bar_length * available_features / total_features)
    bar = "█" * filled + "░" * (bar_length - filled)

    if percentage >= 80:
        bar_color = Colors.BRIGHT_GREEN
    elif percentage >= 50:
        bar_color = Colors.BRIGHT_YELLOW
    else:
        bar_color = Colors.BRIGHT_RED

    print(f"  {bar_color}{bar}{Colors.RESET} {bar_color}{percentage:.0f}%{Colors.RESET}")
    print(f"  {Colors.WHITE}{available_features}/{total_features} features available{Colors.RESET}")

    if available_features < total_features:
        print_section("💡 INSTALLATION GUIDE", Colors.BRIGHT_YELLOW)
        if not PDF2DOCX_AVAILABLE:
            print(f"   {Colors.YELLOW}pip install pdf2docx{Colors.RESET}")
        if not OPENPYXL_AVAILABLE:
            print(f"   {Colors.YELLOW}pip install openpyxl{Colors.RESET}")
        if not TQDM_AVAILABLE:
            print(f"   {Colors.YELLOW}pip install tqdm{Colors.RESET}")
        if not OCR_AVAILABLE:
            print(f"   {Colors.YELLOW}pip install paddlepaddle paddleocr{Colors.RESET}  (recommended)")
            print(f"   {Colors.YELLOW}pip install pdf2image pillow{Colors.RESET}")

    # Credits
    print_section("👤 DEVELOPED BY", Colors.BRIGHT_CYAN)
    print_box([
        f"{Colors.BOLD}Conrad Vaslin{Colors.RESET} - xAI Finance Tutor",
        "© 2025 Conrad Vaslin - All Rights Reserved",
        "Version 2.0.0 - Modular Architecture"
    ], Colors.BRIGHT_CYAN)

    print(Colors.BRIGHT_CYAN + "═" * 80 + Colors.RESET)
    input(f"\n{Colors.BRIGHT_YELLOW}Press Enter to continue...{Colors.RESET}")


def show_settings_menu_enhanced():
    """
    Enhanced settings menu with colors
    """
    print_header("SETTINGS", Colors.BRIGHT_CYAN)

    print_section("⚙️  CONVERSION SETTINGS", Colors.BRIGHT_BLUE)
    print_option("1", "Set default output directory")
    print_option("2", "Enable/disable verbose logging")
    print_option("3", "Configure parallelization (pages per chunk)")
    print_option("4", "Set OCR language")

    print_section("📋 ANALYSIS SETTINGS", Colors.BRIGHT_MAGENTA)
    print_option("5", "Configure keyword grouping")
    print_option("6", "Set detection thresholds")

    print_section("🎨 DISPLAY SETTINGS", Colors.BRIGHT_GREEN)
    print_option("7", "Toggle progress bars")
    print_option("8", "Set report format (Excel/CSV/JSON)")

    print_section("📊 OTHER", Colors.BRIGHT_CYAN)
    print_option("9", "View all settings")
    print_option("R", "Reset to defaults")

    print("\n" + Colors.BRIGHT_CYAN + "─" * 80 + Colors.RESET)
    print_option("0", "Back to main menu")
    print(Colors.BRIGHT_CYAN + "═" * 80 + Colors.RESET + "\n")

    choice = input(f"{Colors.BRIGHT_YELLOW}➤ Your choice (0-9, R): {Colors.RESET}").strip()
    return choice


def show_progress_header(operation: str, file_name: str):
    """Show a styled header for operations"""
    print_header(f"🔄 {operation.upper()}", Colors.BRIGHT_CYAN)
    print(f"{Colors.BRIGHT_BLUE}📄 File:{Colors.RESET} {Colors.WHITE}{file_name}{Colors.RESET}")
    print(Colors.BRIGHT_CYAN + "─" * 80 + Colors.RESET)


def show_completion_summary(
    operation: str,
    input_file: str,
    output_files: list,
    stats: dict = None
):
    """Show a styled completion summary"""
    print_header("✅ SUCCESS!", Colors.BRIGHT_GREEN)

    print(f"{Colors.BRIGHT_BLUE}📄 Input:{Colors.RESET}  {Colors.WHITE}{input_file}{Colors.RESET}")

    if output_files:
        print(f"\n{Colors.BRIGHT_BLUE}📝 Output:{Colors.RESET}")
        for output_file in output_files:
            print(f"   {Colors.BRIGHT_GREEN}✓{Colors.RESET} {Colors.WHITE}{output_file}{Colors.RESET}")

    if stats:
        print(f"\n{Colors.BRIGHT_BLUE}📊 Statistics:{Colors.RESET}")
        for key, value in stats.items():
            print(f"   {Colors.CYAN}•{Colors.RESET} {Colors.WHITE}{key}:{Colors.RESET} {Colors.BRIGHT_YELLOW}{value}{Colors.RESET}")

    print(Colors.BRIGHT_GREEN + "═" * 80 + Colors.RESET)
    input(f"\n{Colors.BRIGHT_YELLOW}Press Enter to continue...{Colors.RESET}")


def show_error_message(error_title: str, error_message: str, suggestions: list = None):
    """Show a styled error message"""
    print_header("❌ ERROR", Colors.BRIGHT_RED)

    print(f"{Colors.BRIGHT_RED}Error:{Colors.RESET} {Colors.WHITE}{error_message}{Colors.RESET}")

    if suggestions:
        print(f"\n{Colors.BRIGHT_YELLOW}💡 Suggestions:{Colors.RESET}")
        for suggestion in suggestions:
            print(f"   {Colors.YELLOW}•{Colors.RESET} {Colors.WHITE}{suggestion}{Colors.RESET}")

    print(Colors.BRIGHT_RED + "═" * 80 + Colors.RESET)
    input(f"\n{Colors.BRIGHT_YELLOW}Press Enter to continue...{Colors.RESET}")
