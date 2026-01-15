"""
Authentication Module for xAI PDF Converter
Uses Supabase Auth for secure user management
"""

from auth.client import (
    get_supabase_client,
    sign_up,
    sign_in,
    sign_in_with_google,
    sign_out,
    get_user,
    get_session,
    reset_password,
    update_password,
    is_authenticated
)

from auth.middleware import require_auth, get_current_user

from auth.ui import show_login_page, show_user_menu

__all__ = [
    'get_supabase_client',
    'sign_up',
    'sign_in',
    'sign_in_with_google',
    'sign_out',
    'get_user',
    'get_session',
    'reset_password',
    'update_password',
    'is_authenticated',
    'require_auth',
    'get_current_user',
    'show_login_page',
    'show_user_menu'
]
