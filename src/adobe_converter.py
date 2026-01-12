#!/usr/bin/env python3
"""
Adobe PDF Services converter - Industry-standard PDF to DOCX conversion
Uses Adobe's cloud-based API for highest quality results.
"""

import os
import json
from pathlib import Path
from typing import Optional
import logging

from src.config import (
    ADOBE_PDF_AVAILABLE,
    ServicePrincipalCredentials,
    PDFServices,
    PDFServicesMediaType,
    StreamAsset,
    ExportPDFJob,
    ExportPDFParams,
    ExportPDFTargetFormat,
    ExportPDFResult,
    logger
)

from src.adobe_credentials_manager import get_credentials_manager
from src.retry_utils import retry_operation

# Import ClientConfig for custom timeout configuration (v4+)
try:
    from adobe.pdfservices.operation.config.client_config import ClientConfig
    CLIENT_CONFIG_AVAILABLE = True
except ImportError:
    CLIENT_CONFIG_AVAILABLE = False
    ClientConfig = None

# Global variable to track current credential name
_current_credential_name = None

# Adobe API configuration
ADOBE_CONNECT_TIMEOUT = 30000    # 30 seconds - connection establishment
ADOBE_READ_TIMEOUT = 300000      # 300 seconds (5 minutes) - for large file uploads and processing
ADOBE_MAX_RETRIES = 3            # Maximum retry attempts
ADOBE_RETRY_DELAY = 5.0          # Initial delay between retries (seconds)


def _create_client_config():
    """
    Create ClientConfig with extended timeouts for large PDF files.

    Returns:
        ClientConfig with custom timeout settings, or None if not available
    """
    if not CLIENT_CONFIG_AVAILABLE or not ClientConfig:
        logger.warning("ClientConfig not available, using default Adobe timeouts")
        return None

    try:
        # Version 4.2.0+ uses direct constructor with keyword arguments
        client_config = ClientConfig(
            connect_timeout=ADOBE_CONNECT_TIMEOUT,
            read_timeout=ADOBE_READ_TIMEOUT
        )

        logger.debug(f"ClientConfig created: connect={ADOBE_CONNECT_TIMEOUT}ms, read={ADOBE_READ_TIMEOUT}ms")
        return client_config
    except Exception as e:
        logger.error(f"Failed to create ClientConfig: {e}")
        return None


def get_adobe_credentials():
    """
    Récupère les credentials Adobe avec rotation automatique pour éviter les limites.

    Returns:
        Tuple of (ServicePrincipalCredentials, credential_name) or (None, None)
    """
    global _current_credential_name

    if not ADOBE_PDF_AVAILABLE:
        return None, None

    # Use credentials manager with rotation
    manager = get_credentials_manager()
    creds_data = manager.get_current_credentials()

    if creds_data is None:
        logger.error("No Adobe credentials available or all accounts exhausted")
        return None, None

    cred_name, client_id, client_secret = creds_data

    try:
        credentials = ServicePrincipalCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        _current_credential_name = cred_name
        logger.debug(f"Using Adobe account: {cred_name}")
        return credentials, cred_name
    except Exception as e:
        logger.error(f"Failed to create credentials for {cred_name}: {e}")
        return None, None


def _convert_pdf_to_docx_adobe_impl(pdf_path: Path, docx_path: Path, verbose: bool = False, cred_name: str = None, credentials=None) -> bool:
    """
    Implementation of Adobe PDF to DOCX conversion (called by wrapper with retry logic).

    Args:
        pdf_path: Path to source PDF file
        docx_path: Output path for DOCX file
        verbose: Show detailed logs
        cred_name: Credential name for tracking
        credentials: Adobe credentials (ServicePrincipalCredentials)

    Returns:
        bool: True if conversion succeeded

    Raises:
        Exception: On any conversion error (for retry logic)
    """
    if verbose:
        logger.info(f"🚀 Starting Adobe PDF to DOCX conversion (using {cred_name})...")
        logger.info(f"   Input:  {pdf_path.name}")
        logger.info(f"   Output: {docx_path.name}")

    # Create ClientConfig with extended timeouts for large files
    client_config = _create_client_config()

    # Create PDF Services instance with custom config
    if client_config:
        pdf_services = PDFServices(credentials=credentials, client_config=client_config)
        if verbose:
            logger.info(f"   ⏱️  Using extended timeouts: {ADOBE_READ_TIMEOUT/1000:.0f}s read timeout")
    else:
        pdf_services = PDFServices(credentials=credentials)
        if verbose:
            logger.warning("   ⚠️  Using default Adobe timeouts (may timeout on large files)")

    # Read PDF file
    with open(pdf_path, 'rb') as file:
        input_stream = file.read()

    # Create an input asset from the stream
    input_asset = pdf_services.upload(
        input_stream=input_stream,
        mime_type=PDFServicesMediaType.PDF
    )

    # Create parameters for the export operation
    export_pdf_params = ExportPDFParams(
        target_format=ExportPDFTargetFormat.DOCX
    )

    # Create export job
    export_pdf_job = ExportPDFJob(
        input_asset=input_asset,
        export_pdf_params=export_pdf_params
    )

    # Submit job and get the job location
    location = pdf_services.submit(export_pdf_job)

    # Get job result (this is where timeouts typically occur with large files)
    pdf_services_response = pdf_services.get_job_result(
        location,
        ExportPDFResult
    )

    # Get the resulting asset
    result_asset = pdf_services_response.get_result().get_asset()

    # Download the result
    stream_asset: StreamAsset = pdf_services.get_content(result_asset)

    # Save the output file
    with open(docx_path, 'wb') as file:
        file.write(stream_asset.get_input_stream())

    if verbose:
        logger.info("✅ Adobe conversion completed successfully")

    # Record usage for quota tracking
    manager = get_credentials_manager()
    manager.record_usage(cred_name)

    return True


@retry_operation(
    max_attempts=ADOBE_MAX_RETRIES,
    delay=ADOBE_RETRY_DELAY,
    backoff_factor=2.0,
    max_delay=30.0,
    exceptions=(Exception,)
)
def convert_pdf_to_docx_adobe(pdf_path: Path, docx_path: Path, verbose: bool = False) -> bool:
    """
    Convertit un PDF en DOCX en utilisant Adobe PDF Services API avec retry automatique.

    Cette fonction utilise des timeouts étendus (120 secondes) et retry automatique
    avec backoff exponentiel pour gérer les fichiers PDF volumineux.

    Args:
        pdf_path: Chemin vers le fichier PDF source
        docx_path: Chemin de sortie pour le fichier DOCX
        verbose: Si True, affiche les logs détaillés

    Returns:
        bool: True si la conversion a réussi

    Raises:
        Exception: Si la conversion échoue après tous les retries
    """
    if not ADOBE_PDF_AVAILABLE:
        error_msg = "Adobe PDF Services SDK not installed"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Récupérer les credentials avec rotation
    credentials, cred_name = get_adobe_credentials()
    if not credentials:
        error_msg = "Adobe credentials not found. Please configure credentials."
        logger.error(error_msg)

        # Show detailed setup instructions
        print("\n" + "="*80)
        print(" " * 25 + "⚠️  ADOBE CREDENTIALS ERROR")
        print("="*80)
        print()
        print("Your Adobe credentials are not configured or invalid.")
        print()
        print("To fix this, follow these steps:")
        print()
        print("1️⃣  Get FREE credentials (500 conversions/month):")
        print("   https://acrobatservices.adobe.com/dc-integration-creation-app-cdn/main.html")
        print()
        print("2️⃣  Set environment variables:")
        print("   export ADOBE_CLIENT_ID='your_client_id'")
        print("   export ADOBE_CLIENT_SECRET='your_client_secret'")
        print()
        print("   OR create 'adobe_credentials_pool.json' with multiple accounts")
        print()
        print("="*80)
        print()

        raise RuntimeError(error_msg)

    try:
        # Call implementation with retry wrapper handling automatic retries
        return _convert_pdf_to_docx_adobe_impl(
            pdf_path=pdf_path,
            docx_path=docx_path,
            verbose=verbose,
            cred_name=cred_name,
            credentials=credentials
        )

    except Exception as e:
        error_msg = str(e)

        # Parse common errors and provide helpful messages (only on final failure)
        if "invalid_client" in error_msg.lower() or "invalid client_id" in error_msg.lower():
            logger.error("❌ Adobe credentials are invalid or missing")
            print("\n" + "="*80)
            print(" " * 25 + "⚠️  ADOBE CREDENTIALS ERROR")
            print("="*80)
            print("Your Adobe credentials are not configured or invalid.")
            print("See instructions above for setup.")
            print("="*80)
            print()

        elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
            logger.error("❌ Adobe API quota exceeded")
            print("\n" + "="*80)
            print(" " * 25 + "⚠️  ADOBE API LIMIT REACHED")
            print("="*80)
            print()
            print("You have reached your Adobe PDF Services quota.")
            print("Free tier: 500 conversions/month")
            print()
            print("Solutions:")
            print("  • Wait until next month for quota reset")
            print("  • Add more accounts to adobe_credentials_pool.json")
            print("  • Upgrade to paid tier for more conversions")
            print()
            print("="*80)
            print()

        elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            logger.error(f"❌ Adobe API timeout after {ADOBE_MAX_RETRIES} attempts")
            logger.error(f"   File may be too large: {pdf_path.name}")
            logger.error(f"   Current read timeout: {ADOBE_READ_TIMEOUT/1000:.0f} seconds")

        else:
            logger.error(f"❌ Adobe PDF conversion failed: {e}")
            if verbose:
                import traceback
                traceback.print_exc()

        # Re-raise the exception (no fallback to pdf2docx per user request)
        raise


def is_adobe_available() -> bool:
    """
    Vérifie si Adobe PDF Services est disponible et configuré.

    Returns:
        bool: True si Adobe est disponible
    """
    if not ADOBE_PDF_AVAILABLE:
        return False

    credentials, _ = get_adobe_credentials()
    return credentials is not None


def print_adobe_setup_instructions():
    """
    Affiche les instructions pour configurer Adobe PDF Services.
    """
    print("\n" + "="*80)
    print(" " * 25 + "📄 ADOBE PDF SERVICES SETUP")
    print("="*80)
    print()
    print("To use Adobe PDF Services (industry-standard conversion), you need:")
    print()
    print("1️⃣  Install the SDK:")
    print("   pip install pdfservices-sdk")
    print()
    print("2️⃣  Get free credentials from Adobe:")
    print("   https://acrobatservices.adobe.com/dc-integration-creation-app-cdn/main.html")
    print()
    print("3️⃣  Configure credentials (choose ONE method):")
    print()
    print("   METHOD A - Environment Variables (recommended):")
    print("   export ADOBE_CLIENT_ID='your_client_id'")
    print("   export ADOBE_CLIENT_SECRET='your_client_secret'")
    print()
    print("   METHOD B - Credentials File:")
    print("   Create 'pdfservices-api-credentials.json' with:")
    print("   {")
    print('     "client_credentials": {')
    print('       "client_id": "your_client_id",')
    print('       "client_secret": "your_client_secret"')
    print("     }")
    print("   }")
    print()
    print("="*80)
    print()
    print("💡 Adobe offers 500 FREE conversions per month!")
    print("   This is the same technology used by Adobe Acrobat.")
    print()
    print("="*80)


__all__ = [
    'convert_pdf_to_docx_adobe',
    'is_adobe_available',
    'get_adobe_credentials',
    'print_adobe_setup_instructions'
]
