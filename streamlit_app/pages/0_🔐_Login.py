"""
🔐 Login Page
Authentication entry point for the application
"""

import streamlit as st
from pathlib import Path
import sys

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.styles import apply_global_styles

# Page config - must be first Streamlit command
st.set_page_config(
    page_title="Login - xAI PDF Converter",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Apply styles
apply_global_styles()

# Import auth after page config
from auth.ui import show_login_page
from auth.client import handle_magic_link_callback

# Handle magic link callback (when user clicks link in email)
if handle_magic_link_callback():
    st.success("Successfully signed in!")
    st.switch_page("Home.py")

# Hide sidebar on login page
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        display: none;
    }

    [data-testid="stSidebarNav"] {
        display: none;
    }

    .block-container {
        max-width: 500px;
        padding-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)

# Show login page
show_login_page()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.875rem;">
    <p>© 2025 xAI PDF Converter by Conrad Vaslin</p>
    <p>Secure authentication powered by Supabase</p>
</div>
""", unsafe_allow_html=True)
