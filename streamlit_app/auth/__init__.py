"""
Authentication Module for xAI PDF Converter
Uses Supabase Auth for secure user management
"""

from auth.client import (
    get_supabase_client,
    sign_in_with_magic_link,
    sign_out,
    get_user,
    get_session,
    is_authenticated
)

from auth.middleware import require_auth, get_current_user

from auth.ui import show_login_page, show_user_menu

__all__ = [
    'get_supabase_client',
    'sign_in_with_magic_link',
    'sign_out',
    'get_user',
    'get_session',
    'is_authenticated',
    'require_auth',
    'get_current_user',
    'show_login_page',
    'show_user_menu'
]
