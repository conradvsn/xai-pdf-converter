#!/usr/bin/env python3
"""
Batch processing functions for xAI PDF Converter
"""

import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.config import configure_logging, TQDM_AVAILABLE, logger
from src.utils import get_pdf_directory, get_output_directory, list_pdf_files
from src.converter import SECPDFConverter  # Will import from original file initially

# Delay between Adobe API calls (to avoid rate limiting)
BATCH_CONVERSION_DELAY = 2.0  # seconds


def process_batch(
    do_conversion: bool = True,
    do_analysis: bool = True,
    grouping_keywords: Optional[List[str]] = None,
    verbose: bool = False,
    create_consolidated_report: bool = True
) -> Dict[str, Any]:
    """
    Process all PDFs in the pdf/ directory and organize outputs in output/.

    Args:
        do_conversion: Whether to convert PDFs to Word documents
        do_analysis: Whether to analyze PDFs for sensitive information
        grouping_keywords: Optional list of keywords for grouping analysis results
        verbose: If True, show detailed logs. If False (default), show simple progress only.
        create_consolidated_report: Whether to create a consolidated report for all PDFs (default: True)

    Returns:
        dict: Summary of processed files with success/failure counts
    """
    # Configure logging based on verbose mode
    configure_logging(verbose=verbose)
    
    pdf_dir = get_pdf_directory()
    output_dir = get_output_directory()
    
    pdf_files = list_pdf_files(pdf_dir)
    
    if not pdf_files:
        print("\n" + "=" * 70)
        print("⚠️  No PDF files found in the 'pdf/' directory.")
        print("=" * 70)
        print(f"\n   📁 Please place your PDF files in: {pdf_dir.absolute()}")
        return {
            'total': 0,
            'success': 0,
            'failed': 0,
            'results': []
        }
    
    # Header - toujours affiché, mais moins détaillé en mode simple
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "📦 BATCH PROCESSING" + " " * 28 + "║")
    print("╚" + "═" * 68 + "╝")
    print(f"\n   📂 Input directory:  {pdf_dir.absolute()}")
    print(f"   📂 Output directory: {output_dir.absolute()}")
    print(f"   📄 PDF files found:  {len(pdf_files)}")
    print(f"   🔄 Conversion:       {'✓ Enabled' if do_conversion else '✗ Disabled'}")
    print(f"   🔍 Analysis:         {'✓ Enabled' if do_analysis else '✗ Disabled'}")
    if grouping_keywords:
        print(f"   🔑 Keywords:         {', '.join(grouping_keywords)}")
    print("\n" + "─" * 70)
    
    results = {
        'total': len(pdf_files),
        'success': 0,
        'failed': 0,
        'results': []
    }

    # Data collection for consolidated report
    all_findings_by_pdf = {}
    all_images_by_pdf = {}

    # Progress bar pour mode simple
    if not verbose and TQDM_AVAILABLE:
        from tqdm import tqdm
        file_iterator = tqdm(pdf_files, desc="Processing PDFs", unit="file", ncols=80, leave=True)
    else:
        file_iterator = pdf_files
    
    for idx, pdf_file in enumerate(file_iterator, 1):
        pdf_name = pdf_file.stem
        
        # Toujours afficher le header de fichier
        if verbose:
            print(f"\n[{idx}/{len(pdf_files)}] Processing: {pdf_file.name}")
            print("─" * 70)
        else:
            # Mode simple : affichage minimal
            if TQDM_AVAILABLE:
                file_iterator.set_description(f"Processing: {pdf_file.name[:50]}")
            else:
                print(f"\n[{idx}/{len(pdf_files)}] {pdf_file.name}")
        
        # Create output subdirectory for this PDF
        pdf_output_dir = output_dir / pdf_name
        pdf_output_dir.mkdir(exist_ok=True)
        
        # Define output paths
        docx_path = pdf_output_dir / f"{pdf_name}.docx" if do_conversion else None
        analysis_path = pdf_output_dir / f"{pdf_name}_analysis.xlsx" if do_analysis else None
        
        result = {
            'pdf': pdf_file.name,
            'conversion': None,
            'analysis': None,
            'error': None
        }
        
        try:
            converter = SECPDFConverter(pdf_file, docx_path, verbose=verbose)
            
            # Convert if requested
            if do_conversion:
                try:
                    if verbose:
                        print(f"   ⚙️  Converting to Word...")
                    converter.convert()
                    result['conversion'] = 'success'
                    if verbose:
                        print(f"   ✓ Conversion complete: {docx_path.name}")

                    # Small delay between conversions to avoid API rate limiting
                    if idx < len(pdf_files):  # Not the last file
                        time.sleep(BATCH_CONVERSION_DELAY)

                except Exception as e:
                    result['conversion'] = 'failed'
                    result['error'] = str(e)
                    logger.error(f"Conversion failed for {pdf_file.name}: {e}")
                    if verbose:
                        print(f"   ❌ Conversion failed: {e}")
            
            # Analyze if requested
            if do_analysis:
                try:
                    if verbose:
                        print(f"   🔍 Analyzing document...")
                    report_path = converter.analyze_and_create_report(
                        report_path=analysis_path,
                        grouping_keywords=grouping_keywords,
                        verbose=verbose
                    )
                    result['analysis'] = 'success'

                    # Collect data for consolidated report
                    if create_consolidated_report:
                        doc_filename = f"{pdf_name}.docx"
                        all_findings_by_pdf[doc_filename] = converter.sensitive_info_by_page.copy()
                        all_images_by_pdf[doc_filename] = converter.images_by_page.copy()

                    total_images = sum(converter.images_by_page.values())
                    total_sensitive = sum(len(findings) for findings in converter.sensitive_info_by_page.values())

                    if verbose:
                        print(f"   ✓ Analysis complete: {report_path.name}")
                        print(f"      • Images: {total_images}, Sensitive items: {total_sensitive}")
                except Exception as e:
                    result['analysis'] = 'failed'
                    if not result['error']:
                        result['error'] = str(e)
                    logger.error(f"Analysis failed for {pdf_file.name}: {e}")
                    if verbose:
                        print(f"   ❌ Analysis failed: {e}")
            
            # Determine overall success
            if do_conversion and do_analysis:
                overall_success = result['conversion'] == 'success' and result['analysis'] == 'success'
            elif do_conversion:
                overall_success = result['conversion'] == 'success'
            elif do_analysis:
                overall_success = result['analysis'] == 'success'
            else:
                overall_success = False
            
            if overall_success:
                results['success'] += 1
                if not verbose:
                    # Mode simple : afficher succès
                    status_msg = "✓"
                    if TQDM_AVAILABLE:
                        file_iterator.set_postfix(status=status_msg)
                    else:
                        print(f"   ✓ Done")
            else:
                results['failed'] += 1
                if not verbose:
                    status_msg = "✗"
                    if TQDM_AVAILABLE:
                        file_iterator.set_postfix(status=status_msg)
                    else:
                        print(f"   ✗ Failed")
            
        except Exception as e:
            result['error'] = str(e)
            results['failed'] += 1
            logger.error(f"Failed to process {pdf_file.name}: {e}")
            if verbose:
                print(f"   ❌ Error: {e}")
            elif not TQDM_AVAILABLE:
                print(f"   ✗ Error: {e}")
        
        results['results'].append(result)

    # Generate consolidated report if requested
    if create_consolidated_report and do_analysis and all_findings_by_pdf:
        from src.analysis.report_generator import create_consolidated_batch_report

        print("\n" + "─" * 70)
        print("   📊 Creating consolidated analysis report...")

        consolidated_report_path = output_dir / "consolidated statements.xlsx"
        try:
            create_consolidated_batch_report(
                all_findings_by_pdf,
                all_images_by_pdf,
                consolidated_report_path,
                grouping_keywords=grouping_keywords
            )
            print(f"   ✓ Consolidated report saved: {consolidated_report_path.name}")
        except Exception as e:
            logger.error(f"Failed to create consolidated report: {e}")
            print(f"   ⚠️  Warning: Consolidated report creation failed: {e}")

    # Print summary - toujours affiché de la même manière
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "📊 BATCH SUMMARY" + " " * 33 + "║")
    print("╚" + "═" * 68 + "╝")
    print(f"\n   ✅ Successful: {results['success']}/{results['total']}")
    print(f"   ❌ Failed:     {results['failed']}/{results['total']}")
    print(f"\n   📁 All outputs saved to: {output_dir.absolute()}")
    if results['failed'] > 0:
        print("\n   ⚠️  Failed files:")
        for res in results['results']:
            if res['error']:
                print(f"      • {res['pdf']}: {res['error']}")
    
    return results

