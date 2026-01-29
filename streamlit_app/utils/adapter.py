"""
Adapter module to bridge between existing codebase and Streamlit app
Provides consistent interfaces regardless of underlying implementation
"""

from pathlib import Path
import sys
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the wrapper
from utils.converter_wrapper import PDFConverter, AdobeConversionError
from src.config import ADOBE_PDF_AVAILABLE

# Adobe API credentials management
# Priority: Streamlit secrets > JSON file > empty list

ADOBE_API_CREDENTIALS = []

def _load_credentials():
    """Load credentials from Streamlit secrets or file"""
    global ADOBE_API_CREDENTIALS

    # Priority 1: Try Streamlit secrets (for deployed apps)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'adobe_credentials' in st.secrets:
            # Convert Streamlit secrets to list of dicts
            ADOBE_API_CREDENTIALS = list(st.secrets['adobe_credentials'])
            print(f"✅ [Adapter] Loaded {len(ADOBE_API_CREDENTIALS)} credentials from Streamlit secrets")
            return
    except Exception as e:
        print(f"⚠️ [Adapter] Streamlit secrets not available: {e}")

    # Priority 2: Try adobe_credentials_pool.json
    pool_file = Path(__file__).parent.parent / "adobe_credentials_pool.json"
    if pool_file.exists():
        try:
            with open(pool_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'credentials' in data:
                    ADOBE_API_CREDENTIALS = data['credentials']
                    print(f"✅ [Adapter] Loaded {len(ADOBE_API_CREDENTIALS)} credentials from pool file")
                    return
        except Exception as e:
            print(f"⚠️ [Adapter] Could not load from pool file: {e}")

    # Priority 3: Try adobe_credentials.json (legacy)
    adobe_creds_file = Path(__file__).parent.parent.parent / "adobe_credentials.json"
    if adobe_creds_file.exists():
        try:
            with open(adobe_creds_file, 'r') as f:
                stored_creds = json.load(f)
                if isinstance(stored_creds, list):
                    ADOBE_API_CREDENTIALS = stored_creds
                elif isinstance(stored_creds, dict):
                    ADOBE_API_CREDENTIALS = [stored_creds]
                print(f"✅ [Adapter] Loaded {len(ADOBE_API_CREDENTIALS)} credentials from legacy file")
                return
        except Exception as e:
            print(f"⚠️ [Adapter] Could not load from legacy file: {e}")

    print("⚠️ [Adapter] No credentials found")

# Load credentials on module import
_load_credentials()


def get_adobe_credentials():
    """Get Adobe API credentials, reload if empty"""
    global ADOBE_API_CREDENTIALS
    # If no credentials loaded yet, try loading again (for Streamlit Cloud)
    if not ADOBE_API_CREDENTIALS:
        _load_credentials()
    return ADOBE_API_CREDENTIALS


def reload_credentials():
    """Force reload credentials (useful after Streamlit initialization)"""
    _load_credentials()
    return ADOBE_API_CREDENTIALS


def add_adobe_credential(credential_dict):
    """Add an Adobe API credential"""
    global ADOBE_API_CREDENTIALS
    if credential_dict not in ADOBE_API_CREDENTIALS:
        ADOBE_API_CREDENTIALS.append(credential_dict)

        # Save to file (only works locally, not on Streamlit Cloud)
        adobe_creds_file = Path(__file__).parent.parent.parent / "adobe_credentials.json"
        try:
            with open(adobe_creds_file, 'w') as f:
                json.dump(ADOBE_API_CREDENTIALS, f, indent=2)
        except Exception as e:
            print(f"⚠️ [Adapter] Could not save credentials (read-only filesystem): {e}")

    return True


def clear_adobe_credentials():
    """Clear all Adobe API credentials"""
    global ADOBE_API_CREDENTIALS
    ADOBE_API_CREDENTIALS = []

    # Remove file (only works locally)
    adobe_creds_file = Path(__file__).parent.parent.parent / "adobe_credentials.json"
    if adobe_creds_file.exists():
        try:
            adobe_creds_file.unlink()
        except Exception as e:
            print(f"⚠️ [Adapter] Could not delete credentials file: {e}")

    return True
