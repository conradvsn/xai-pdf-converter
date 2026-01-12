#!/usr/bin/env python3
"""
Settings menu handlers for xAI PDF Converter
Implements the interactive configuration interface.

Author: Conrad Vaslin - xAI Finance Tutor
Copyright: © 2025 Conrad Vaslin - All Rights Reserved
"""

from pathlib import Path
from src.settings import get_settings


def handle_set_output_directory():
    """Handle setting the default output directory."""
    settings = get_settings()
    current = settings.get('output_directory', 'output')

    print("\n" + "─" * 80)
    print("📁 SET OUTPUT DIRECTORY")
    print("─" * 80)
    print(f"Current: {current}")
    print()

    new_dir = input("Enter new output directory (or press Enter to keep current): ").strip()

    if new_dir:
        settings.set('output_directory', new_dir)
        print(f"✓ Output directory set to: {new_dir}")
    else:
        print("✓ Keeping current setting")

    input("\nPress Enter to continue...")


def handle_toggle_verbose_logging():
    """Handle toggling verbose logging."""
    settings = get_settings()
    current = settings.get('verbose_logging', False)

    print("\n" + "─" * 80)
    print("📋 VERBOSE LOGGING")
    print("─" * 80)
    print(f"Current: {'Enabled' if current else 'Disabled'}")
    print()

    choice = input("Enable verbose logging? (y/n): ").strip().lower()

    if choice in ['y', 'n']:
        new_value = (choice == 'y')
        settings.set('verbose_logging', new_value)
        print(f"✓ Verbose logging {'enabled' if new_value else 'disabled'}")
    else:
        print("✓ Keeping current setting")

    input("\nPress Enter to continue...")


def handle_set_pages_per_chunk():
    """Handle setting pages per chunk for parallelization."""
    settings = get_settings()
    current = settings.get('pages_per_chunk', 10)

    print("\n" + "─" * 80)
    print("⚙️  PARALLELIZATION SETTINGS")
    print("─" * 80)
    print(f"Current pages per chunk: {current}")
    print()
    print("Higher values = less overhead, lower values = better parallelization")
    print("Recommended: 10-20 for most documents")
    print()

    try:
        new_value = input("Enter pages per chunk (or press Enter to keep current): ").strip()

        if new_value:
            pages = int(new_value)
            if 1 <= pages <= 100:
                settings.set('pages_per_chunk', pages)
                print(f"✓ Pages per chunk set to: {pages}")
            else:
                print("❌ Value must be between 1 and 100")
        else:
            print("✓ Keeping current setting")

    except ValueError:
        print("❌ Invalid number")

    input("\nPress Enter to continue...")


def handle_set_ocr_language():
    """Handle setting OCR language."""
    settings = get_settings()
    current = settings.get('ocr_language', 'en')

    print("\n" + "─" * 80)
    print("🌐 OCR LANGUAGE SETTINGS")
    print("─" * 80)
    print(f"Current language: {current}")
    print()
    print("Common language codes:")
    print("  en  - English")
    print("  fr  - French")
    print("  es  - Spanish")
    print("  de  - German")
    print("  it  - Italian")
    print("  pt  - Portuguese")
    print("  zh  - Chinese")
    print("  ja  - Japanese")
    print()

    new_lang = input("Enter language code (or press Enter to keep current): ").strip().lower()

    if new_lang:
        settings.set('ocr_language', new_lang)
        print(f"✓ OCR language set to: {new_lang}")
    else:
        print("✓ Keeping current setting")

    input("\nPress Enter to continue...")


def handle_configure_grouping_keywords():
    """Handle configuring default grouping keywords."""
    settings = get_settings()
    current = settings.get('grouping_keywords', [])

    print("\n" + "─" * 80)
    print("🔑 KEYWORD GROUPING SETTINGS")
    print("─" * 80)
    print(f"Current keywords: {', '.join(current) if current else 'None'}")
    print()
    print("Keywords help group similar entries in reports.")
    print("Example: 'vantiv' groups 'Vantiv Inc', 'Vantiv LLC', etc.")
    print()

    keywords_input = input("Enter keywords (comma-separated, or press Enter to clear): ").strip()

    if keywords_input:
        keywords = [kw.strip() for kw in keywords_input.split(',') if kw.strip()]
        settings.set('grouping_keywords', keywords)
        print(f"✓ Grouping keywords set to: {', '.join(keywords)}")
    else:
        settings.set('grouping_keywords', [])
        print("✓ Grouping keywords cleared")

    input("\nPress Enter to continue...")


def handle_set_detection_thresholds():
    """Handle setting detection thresholds."""
    settings = get_settings()

    print("\n" + "─" * 80)
    print("🎯 DETECTION THRESHOLDS")
    print("─" * 80)

    # Person name length
    min_person = settings.get('detection_thresholds.min_person_name_length', 5)
    max_person = settings.get('detection_thresholds.max_person_name_length', 40)

    print(f"\n1. Person name length: {min_person}-{max_person} characters")
    print("2. Phone validation: " + ("Enabled" if settings.get('detection_thresholds.phone_number_validation', True) else "Disabled"))
    print("3. Email validation: " + ("Enabled" if settings.get('detection_thresholds.email_validation', True) else "Disabled"))
    print("4. Anonymization: " + ("Enabled" if settings.get('enable_anonymization', True) else "Disabled"))
    print("5. Deduplication: " + ("Enabled" if settings.get('enable_deduplication', True) else "Disabled"))
    print("\n0. Back")

    print("─" * 80)

    choice = input("➤ Configure option (0-5): ").strip()

    if choice == '1':
        try:
            min_val = input(f"Min person name length (current: {min_person}): ").strip()
            max_val = input(f"Max person name length (current: {max_person}): ").strip()

            if min_val:
                settings.set('detection_thresholds.min_person_name_length', int(min_val), save=False)
            if max_val:
                settings.set('detection_thresholds.max_person_name_length', int(max_val), save=False)

            settings.save()
            print("✓ Person name length thresholds updated")

        except ValueError:
            print("❌ Invalid number")

    elif choice == '2':
        toggle = input("Enable phone validation? (y/n): ").strip().lower()
        if toggle in ['y', 'n']:
            settings.set('detection_thresholds.phone_number_validation', toggle == 'y')
            print("✓ Phone validation updated")

    elif choice == '3':
        toggle = input("Enable email validation? (y/n): ").strip().lower()
        if toggle in ['y', 'n']:
            settings.set('detection_thresholds.email_validation', toggle == 'y')
            print("✓ Email validation updated")

    elif choice == '4':
        toggle = input("Enable anonymization? (y/n): ").strip().lower()
        if toggle in ['y', 'n']:
            settings.set('enable_anonymization', toggle == 'y')
            print("✓ Anonymization updated")

    elif choice == '5':
        toggle = input("Enable deduplication? (y/n): ").strip().lower()
        if toggle in ['y', 'n']:
            settings.set('enable_deduplication', toggle == 'y')
            print("✓ Deduplication updated")

    input("\nPress Enter to continue...")


def handle_toggle_progress_bars():
    """Handle toggling progress bars."""
    settings = get_settings()
    current = settings.get('show_progress_bars', True)

    print("\n" + "─" * 80)
    print("📊 PROGRESS BARS")
    print("─" * 80)
    print(f"Current: {'Enabled' if current else 'Disabled'}")
    print()

    choice = input("Enable progress bars? (y/n): ").strip().lower()

    if choice in ['y', 'n']:
        new_value = (choice == 'y')
        settings.set('show_progress_bars', new_value)
        print(f"✓ Progress bars {'enabled' if new_value else 'disabled'}")
    else:
        print("✓ Keeping current setting")

    input("\nPress Enter to continue...")


def handle_set_report_format():
    """Handle setting report format."""
    settings = get_settings()
    current = settings.get('report_format', 'excel')

    print("\n" + "─" * 80)
    print("📄 REPORT FORMAT")
    print("─" * 80)
    print(f"Current format: {current.upper()}")
    print()
    print("Available formats:")
    print("  1. Excel (.xlsx) - Full featured, recommended")
    print("  2. CSV (.csv) - Simple, portable")
    print("  3. JSON (.json) - Machine readable")
    print()

    choice = input("Select format (1-3, or press Enter to keep current): ").strip()

    format_map = {
        '1': 'excel',
        '2': 'csv',
        '3': 'json'
    }

    if choice in format_map:
        new_format = format_map[choice]
        settings.set('report_format', new_format)
        print(f"✓ Report format set to: {new_format.upper()}")
    else:
        print("✓ Keeping current setting")

    input("\nPress Enter to continue...")


def handle_view_all_settings():
    """Display all current settings."""
    settings = get_settings()

    print("\n" + "=" * 80)
    print(" " * 28 + "ALL SETTINGS")
    print("=" * 80)

    print("\n📁 DIRECTORIES:")
    print(f"  PDF Directory:     {settings.get('pdf_directory')}")
    print(f"  Output Directory:  {settings.get('output_directory')}")

    print("\n⚙️  CONVERSION:")
    print(f"  Pages per chunk:   {settings.get('pages_per_chunk')}")
    print(f"  OCR Language:      {settings.get('ocr_language')}")
    print(f"  OCR Engine:        {settings.get('ocr_engine_preference')}")

    print("\n📋 ANALYSIS:")
    thresholds = settings.get('detection_thresholds', {})
    print(f"  Person name length: {thresholds.get('min_person_name_length')}-{thresholds.get('max_person_name_length')} chars")
    print(f"  Phone validation:  {thresholds.get('phone_number_validation')}")
    print(f"  Email validation:  {thresholds.get('email_validation')}")
    print(f"  Anonymization:     {settings.get('enable_anonymization')}")
    print(f"  Deduplication:     {settings.get('enable_deduplication')}")

    keywords = settings.get('grouping_keywords', [])
    print(f"  Grouping keywords: {', '.join(keywords) if keywords else 'None'}")

    print("\n📊 REPORTS:")
    print(f"  Format:            {settings.get('report_format').upper()}")
    print(f"  Consolidated:      {settings.get('consolidated_reports')}")
    print(f"  Include images:    {settings.get('include_images_in_report')}")

    print("\n🎨 UI:")
    print(f"  Progress bars:     {settings.get('show_progress_bars')}")
    print(f"  Verbose logging:   {settings.get('verbose_logging')}")
    print(f"  Show file sizes:   {settings.get('show_file_sizes')}")

    print("\n👤 DEVELOPER:")
    print(f"  {settings.get('developer')} - {settings.get('developer_role')}")
    print(f"  {settings.get('copyright')}")

    print("\n" + "=" * 80)
    input("\nPress Enter to continue...")


def handle_reset_settings():
    """Handle resetting all settings to defaults."""
    print("\n" + "─" * 80)
    print("⚠️  RESET ALL SETTINGS")
    print("─" * 80)
    print("This will reset ALL settings to their default values.")
    print()

    confirm = input("Are you sure? (yes/no): ").strip().lower()

    if confirm == 'yes':
        settings = get_settings()
        if settings.reset():
            print("✓ All settings reset to defaults")
        else:
            print("❌ Error resetting settings")
    else:
        print("✓ Reset cancelled")

    input("\nPress Enter to continue...")
