#!/usr/bin/env python3
"""
Main entry point for xAI PDF Converter
Uses the new modular structure.
"""

import sys
import os
import warnings
from pathlib import Path

# Disable verbose third-party library messages
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
warnings.filterwarnings('ignore')

# Suppress pikepdf logging
import logging
logging.getLogger('pikepdf').setLevel(logging.ERROR)
logging.getLogger('PIL').setLevel(logging.ERROR)
logging.getLogger('paddleocr').setLevel(logging.ERROR)
logging.getLogger('ppocr').setLevel(logging.ERROR)

from src.config import configure_logging
from src.settings import get_settings

# Use standard UI (no colors)
from src.ui import (
    show_main_menu, show_system_status, show_settings_menu,
    handle_single_convert, handle_single_convert_analyze, handle_analyze_only
)
from src.batch_processor import process_batch
from src.utils import get_grouping_keywords
from src.settings_handlers import (
    handle_set_output_directory, handle_toggle_verbose_logging,
    handle_set_pages_per_chunk, handle_set_ocr_language,
    handle_configure_grouping_keywords, handle_set_detection_thresholds,
    handle_toggle_progress_bars, handle_set_report_format,
    handle_view_all_settings, handle_reset_settings
)
from src.logging_system import setup_logging, get_logging_system


def main():
    """
    Main function avec menu interactif amélioré.
    """
    # Initialize enhanced logging system
    settings = get_settings()
    verbose = settings.get('verbose_logging', False)
    logger = setup_logging(verbose=verbose, console=True)

    # Check for command-line arguments (batch mode)
    if len(sys.argv) > 1:
        # Legacy support for command-line usage
        batchmode = True
        doconversion = True
        doanalysis = True
        verbose = False
        grouping_keywords = None
        
        # Parse arguments
        if sys.argv[1].endswith('.pdf') and Path(sys.argv[1]).exists():
            batchmode = False
        elif '--batch' in sys.argv or '--no-batch' in sys.argv:
            batchmode = '--batch' in sys.argv
        elif '--conversion-only' in sys.argv:
            doanalysis = False
        elif '--analysis-only' in sys.argv:
            doconversion = False
        elif '--keywords' in ' '.join(sys.argv):
            for arg in sys.argv:
                if arg.startswith('--keywords='):
                    keywords_str = arg.split('=', 1)[1]
                    grouping_keywords = [kw.strip() for kw in keywords_str.split(',') if kw.strip()]
        
        if batchmode:
            configure_logging(verbose=verbose)
            results = process_batch(
                do_conversion=doconversion,
                do_analysis=doanalysis,
                grouping_keywords=grouping_keywords,
                verbose=verbose
            )
            return
    
    # Interactive menu mode
    while True:
        try:
            choice = show_main_menu()
            
            if choice == '1':
                handle_single_convert(use_ocr=False)
            
            elif choice == '2':
                handle_single_convert_analyze()
            
            elif choice == '3':
                handle_analyze_only()
            
            elif choice == '4':
                handle_single_convert(use_ocr=True)

            elif choice == '5':
                # Batch convert (no analysis, so no consolidated report)
                configure_logging(verbose=False)
                results = process_batch(
                    do_conversion=True,
                    do_analysis=False,
                    verbose=False,
                    create_consolidated_report=False
                )

            elif choice == '6':
                # Batch convert + analyze (WITH consolidated report)
                grouping_keywords = get_grouping_keywords()
                configure_logging(verbose=False)
                results = process_batch(
                    do_conversion=True,
                    do_analysis=True,
                    grouping_keywords=grouping_keywords,
                    verbose=False,
                    create_consolidated_report=True
                )

            elif choice == '7':
                # Batch analyze (WITH consolidated report)
                grouping_keywords = get_grouping_keywords()
                configure_logging(verbose=False)
                results = process_batch(
                    do_conversion=False,
                    do_analysis=True,
                    grouping_keywords=grouping_keywords,
                    verbose=False,
                    create_consolidated_report=True
                )

            elif choice == '8':
                show_system_status()

            elif choice.upper() == 'S':
                # Settings submenu
                while True:
                    settings_choice = show_settings_menu()

                    if settings_choice == '1':
                        handle_set_output_directory()
                    elif settings_choice == '2':
                        handle_toggle_verbose_logging()
                    elif settings_choice == '3':
                        handle_set_pages_per_chunk()
                    elif settings_choice == '4':
                        handle_set_ocr_language()
                    elif settings_choice == '5':
                        handle_configure_grouping_keywords()
                    elif settings_choice == '6':
                        handle_set_detection_thresholds()
                    elif settings_choice == '7':
                        handle_toggle_progress_bars()
                    elif settings_choice == '8':
                        handle_set_report_format()
                    elif settings_choice == '9':
                        handle_view_all_settings()
                    elif settings_choice == 'r' or settings_choice == 'R':
                        handle_reset_settings()
                    elif settings_choice == '0':
                        break
                    else:
                        print("\n❌ Invalid choice. Please select 0-9.")
                        input("Press Enter to continue...")
            
            elif choice == '0':
                print("\n" + "="*80)
                print(" " * 30 + "👋 Goodbye!")
                print("="*80 + "\n")
                break
            
            else:
                print("\n❌ Invalid choice. Please select 0-9.")
                input("Press Enter to continue...")
        
        except KeyboardInterrupt:
            print("\n\n" + "="*80)
            print(" " * 28 + "⚠️  Interrupted")
            print("="*80)
            confirm = input("\nDo you want to exit? (y/n): ").strip().lower()
            if confirm == 'y':
                break
        
        except Exception as e:
            print("\n" + "="*80)
            print(" " * 28 + "❌ ERROR")
            print("="*80)
            print(f"  {e}")
            print("="*80)
            import traceback
            traceback.print_exc()
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()





