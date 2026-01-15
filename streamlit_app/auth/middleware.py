"""
Authentication Middleware
Handles page protection and user context
"""

import streamlit as st
from typing import Optional, Dict, Any
from functools import wraps

from auth.client import get_user, is_authenticated


def require_auth(redirect_to_login: bool = True) -> bool:
    """
    Check if user is authenticated. If not, optionally redirect to login.

    Args:
        redirect_to_login: Whether to show login prompt if not authenticated

    Returns:
        True if authenticated, False otherwise
    """
    if is_authenticated():
        return True

    if redirect_to_login:
        st.warning("🔐 Please sign in to access this page")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Go to Login", type="primary", use_container_width=True):
                st.switch_page("pages/0_🔐_Login.py")

        st.stop()

    return False


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get the current authenticated user

    Returns:
        User dict with id, email, full_name or None
    """
    return get_user()


def get_user_id() -> Optional[str]:
    """
    Get the current user's ID

    Returns:
        User ID string or None
    """
    user = get_user()
    return user.get('id') if user else None


def protected_page(func):
    """
    Decorator to protect a page function.
    Usage:
        @protected_page
        def main():
            st.write("Protected content")
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if require_auth():
            return func(*args, **kwargs)
    return wrapper
