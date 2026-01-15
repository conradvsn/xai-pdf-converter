"""
⚙️ Settings Page
"""

import streamlit as st
from pathlib import Path
import sys
import json

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.session import init_session_state, update_setting, get_setting
from utils.adapter import ADOBE_API_CREDENTIALS, add_adobe_credential, get_adobe_credentials, reload_credentials
from utils.styles import apply_global_styles

# Page config
st.set_page_config(
    page_title="Settings - xAI PDF Converter",
    page_icon="⚙️",
    layout="wide"
)

# Apply global styles
apply_global_styles()

# Initialize session
init_session_state()

# IMPORTANT: Force reload credentials from Streamlit secrets
# This ensures credentials are loaded even if module was imported before Streamlit initialized
credentials = reload_credentials()

# Modern header
st.markdown("""
<div class="page-header">
    <h1>⚙️ Settings & Configuration</h1>
    <p>Manage your Adobe API credentials, output preferences, and application settings</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Detection Settings (moved to top as primary feature)
st.markdown("### 🔧 Detection Settings")

st.info("""
**Automatic Detection Enabled:**

The following information types are automatically detected in all PDFs:
- 🏢 **Company Names** - ML-powered with spaCy NER + regex patterns
- 👤 **Person Names** - Advanced cleaning and validation
- 📧 **Email Addresses** - Full validation with domain checks
- 📞 **Phone Numbers** - US and international formats
- 📍 **Addresses** - Full and partial address detection
- 🔢 **SSN** - Social Security Numbers (XXX-XX-XXXX)
- 🏛️ **IRS EIN** - Employer Identification Numbers (XX-XXXXXXX)
- 💳 **Credit Cards** - Multiple card types
- 🌐 **Websites/URLs** - Full URL extraction
- 📊 **Financial Codes** - CUSIP, ISIN, CIK, etc.
""")

# Grouping Keywords
st.markdown("#### 🎯 Default Grouping Keywords")

current_keywords = get_setting('grouping_keywords', [])

keywords_text = st.text_area(
    "Default Keywords (one per line)",
    value='\n'.join(current_keywords) if current_keywords else '',
    placeholder="Vantiv\nWorldPay\nFifth Third",
    help="Companies to group together in reports",
    height=150
)

if st.button("💾 Save Grouping Keywords"):
    new_keywords = [k.strip() for k in keywords_text.split('\n') if k.strip()]
    update_setting('grouping_keywords', new_keywords)
    st.success("✅ Grouping keywords saved!")

st.markdown("---")

# Adobe API Configuration
st.markdown("### 🔑 Adobe PDF Services API")

adobe_key_count = len(credentials)

if adobe_key_count > 0:
    st.success(f"✅ {adobe_key_count} Adobe API key(s) configured")
else:
    st.error("❌ No Adobe API keys configured. Conversion features are disabled.")

    st.info("""
    **For Streamlit Cloud deployment:**

    1. Go to your app settings on [share.streamlit.io](https://share.streamlit.io)
    2. Navigate to "Secrets" section
    3. Add your credentials in TOML format:

    ```toml
    [[adobe_credentials]]
    name = "account_1"
    client_id = "your_client_id_here"
    client_secret = "your_client_secret_here"
    monthly_limit = 500

    [[adobe_credentials]]
    name = "account_2"
    client_id = "your_second_client_id"
    client_secret = "your_second_client_secret"
    monthly_limit = 500
    ```

    4. Save and restart the app

    **For local development:**

    Create `streamlit_app/adobe_credentials_pool.json`:
    ```json
    {
      "credentials": [
        {
          "name": "account_1",
          "client_id": "your_client_id",
          "client_secret": "your_client_secret",
          "monthly_limit": 500
        }
      ]
    }
    ```
    """)

    st.markdown("**Get Adobe API credentials:**")
    st.markdown("""
    1. Go to [Adobe Developer Console](https://developer.adobe.com/console)
    2. Create a new project
    3. Add "PDF Services API"
    4. Copy your Client ID and Client Secret
    """)

st.markdown("---")

# Output Settings
st.markdown("### 📁 File Output")

# Detect if running on Streamlit Cloud
import os
# More reliable detection: check for Streamlit Cloud specific paths/env vars
is_cloud = (
    os.getenv('STREAMLIT_RUNTIME_ENVIRONMENT') == 'cloud' or
    os.path.exists('/mount/src') or
    os.path.exists('/home/appuser')
)

if is_cloud:
    # Streamlit Cloud - files are downloaded directly
    st.info("""
    **☁️ Cloud Deployment Mode**

    Your app is running on Streamlit Cloud. Processed files are:
    - ✅ **Automatically available for download** after processing
    - 💾 **Downloaded directly to your browser** (no server storage needed)
    - 🔄 **Temporary files** are cleaned up automatically after session ends

    No output directory configuration needed - just process your PDFs and download the results!
    """)
else:
    # Local deployment - allow directory configuration
    st.info("""
    **💻 Local Deployment Mode**

    Configure where processed files will be saved on your local machine.
    """)

    current_output = get_setting('output_directory', str(Path.home() / 'Downloads' / 'xAI_Output'))

    new_output = st.text_input(
        "Output Directory Path",
        value=current_output,
        help="Directory where processed files will be saved locally",
        placeholder="/path/to/your/output/folder"
    )

    if new_output != current_output:
        if st.button("💾 Update Output Directory"):
            update_setting('output_directory', new_output)
            st.success(f"✅ Output directory updated to: {new_output}")
            st.rerun()

    # Check if directory exists
    output_path = Path(new_output)
    if output_path.exists():
        st.success(f"✅ Directory exists and ready: `{output_path}`")
    else:
        st.warning(f"⚠️ Directory does not exist yet: `{output_path}`")
        if st.button("📁 Create Directory Now"):
            try:
                output_path.mkdir(parents=True, exist_ok=True)
                st.success("✅ Directory created successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Could not create directory: {e}")

st.markdown("---")

# System Information
st.markdown("### 💻 System Information")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Python Environment**")

    # Check dependencies
    dependencies = {
        'PyPDF2': False,
        'spaCy': False,
        'openpyxl': False,
        'python-docx': False,
        'Adobe PDF Services': False,
        'Pillow': False
    }

    try:
        import PyPDF2
        dependencies['PyPDF2'] = True
    except ImportError:
        pass

    try:
        import spacy
        dependencies['spaCy'] = True
    except ImportError:
        pass

    try:
        import openpyxl
        dependencies['openpyxl'] = True
    except ImportError:
        pass

    try:
        from docx import Document
        dependencies['python-docx'] = True
    except ImportError:
        pass

    try:
        from adobe.pdfservices.operation.pdf_services import PDFServices
        dependencies['Adobe PDF Services'] = True
    except ImportError:
        pass

    try:
        from PIL import Image
        dependencies['Pillow'] = True
    except ImportError:
        pass

    for lib, installed in dependencies.items():
        if installed:
            st.success(f"✅ {lib}")
        else:
            st.error(f"❌ {lib}")

with col2:
    st.markdown("**Application Info**")

    st.write("**Version:** 2.0.0 (Streamlit)")
    st.write("**Author:** Conrad Vaslin")
    st.write("**Purpose:** xAI Finance Tutor")

    st.markdown("**Paths**")
    st.code(f"Home: {Path.home()}")
    st.code(f"App: {Path(__file__).parent.parent.parent}")

st.markdown("---")

# Cloud Storage Settings
st.markdown("### ☁️ Cloud Storage (Supabase)")

try:
    from utils.cloud_storage import is_cloud_storage_available
    cloud_connected = is_cloud_storage_available()
except Exception:
    cloud_connected = False

if cloud_connected:
    st.success("✅ Supabase connected - Usage tracking is persistent")
else:
    st.info("""
    **Enable Persistent Tracking with Supabase (Free)**

    1. Create a free account at [supabase.com](https://supabase.com)
    2. Create a new project
    3. Create these tables in SQL Editor:

    ```sql
    -- Usage tracking table
    CREATE TABLE adobe_usage (
        id SERIAL PRIMARY KEY,
        account_name TEXT NOT NULL,
        month TEXT NOT NULL,
        count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(account_name, month)
    );

    -- Optional: Credentials table (more secure than secrets.toml)
    CREATE TABLE adobe_credentials (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        client_id TEXT NOT NULL,
        client_secret TEXT NOT NULL,
        monthly_limit INTEGER DEFAULT 500,
        created_at TIMESTAMP DEFAULT NOW()
    );
    ```

    4. Add to Streamlit secrets:
    ```toml
    [supabase]
    url = "https://your-project.supabase.co"
    key = "your-anon-key"
    ```
    """)

st.markdown("---")

# Advanced Settings
with st.expander("🔬 Advanced Settings"):
    st.markdown("### ⚠️ Advanced Configuration")

    st.warning("⚠️ These settings are for advanced users only. Changing them may affect application behavior.")

    # Cache management
    st.markdown("#### 🗑️ Cache Management")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Clear Session Cache", width="stretch"):
            st.cache_data.clear()
            st.success("✅ Session cache cleared!")

    with col2:
        if st.button("🗑️ Clear Processing History", width="stretch"):
            from utils.session import clear_history
            clear_history()
            st.success("✅ History cleared!")

    # Export/Import settings
    st.markdown("#### 💾 Export/Import Settings")

    col1, col2 = st.columns(2)

    with col1:
        settings_json = json.dumps(st.session_state.settings, indent=2, default=str)

        st.download_button(
            label="📥 Export Settings",
            data=settings_json,
            file_name="xai_settings.json",
            mime="application/json",
            width="stretch"
        )

    with col2:
        uploaded_settings = st.file_uploader(
            "Import Settings",
            type=['json'],
            help="Upload previously exported settings"
        )

        if uploaded_settings:
            try:
                imported = json.load(uploaded_settings)
                st.session_state.settings.update(imported)
                st.success("✅ Settings imported!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Invalid settings file: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem 0;">
    <p>💡 Changes to settings take effect immediately unless otherwise noted.</p>
</div>
""", unsafe_allow_html=True)
