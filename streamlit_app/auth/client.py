"""
Supabase Authentication Client
Handles all authentication operations with Supabase
"""

import streamlit as st
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None


# Initialize Supabase client
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """Get or create Supabase client singleton"""
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    if not SUPABASE_AVAILABLE:
        return None

    try:
        if hasattr(st, 'secrets') and 'supabase' in st.secrets:
            url = st.secrets['supabase']['url']
            key = st.secrets['supabase']['key']
            _supabase_client = create_client(url, key)
            return _supabase_client
    except Exception as e:
        st.error(f"Failed to initialize Supabase: {e}")
        return None

    return None


def sign_up(email: str, password: str, full_name: str = "") -> Tuple[bool, str]:
    """
    Register a new user

    Args:
        email: User's email address
        password: User's password (min 6 characters)
        full_name: User's full name (optional)

    Returns:
        Tuple of (success: bool, message: str)
    """
    client = get_supabase_client()
    if not client:
        return False, "Authentication service unavailable"

    try:
        # Sign up with metadata
        response = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name
                }
            }
        })

        if response.user:
            # Store session in streamlit
            if response.session:
                st.session_state['supabase_session'] = {
                    'access_token': response.session.access_token,
                    'refresh_token': response.session.refresh_token,
                    'user': {
                        'id': response.user.id,
                        'email': response.user.email,
                        'full_name': full_name
                    }
                }
            return True, "Account created successfully! Please check your email to verify."
        else:
            return False, "Failed to create account"

    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower():
            return False, "This email is already registered"
        elif "password" in error_msg.lower():
            return False, "Password must be at least 6 characters"
        else:
            return False, f"Sign up failed: {error_msg}"


def sign_in(email: str, password: str) -> Tuple[bool, str]:
    """
    Sign in an existing user

    Args:
        email: User's email
        password: User's password

    Returns:
        Tuple of (success: bool, message: str)
    """
    client = get_supabase_client()
    if not client:
        return False, "Authentication service unavailable"

    try:
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response.user and response.session:
            # Store session
            st.session_state['supabase_session'] = {
                'access_token': response.session.access_token,
                'refresh_token': response.session.refresh_token,
                'user': {
                    'id': response.user.id,
                    'email': response.user.email,
                    'full_name': response.user.user_metadata.get('full_name', '')
                }
            }
            return True, "Signed in successfully!"
        else:
            return False, "Invalid credentials"

    except Exception as e:
        error_msg = str(e)
        if "invalid" in error_msg.lower() or "credentials" in error_msg.lower():
            return False, "Invalid email or password"
        elif "not confirmed" in error_msg.lower():
            return False, "Please verify your email before signing in"
        else:
            return False, f"Sign in failed: {error_msg}"


def sign_in_with_google() -> Tuple[bool, str, Optional[str]]:
    """
    Initiate Google OAuth sign in

    Returns:
        Tuple of (success: bool, message: str, auth_url: Optional[str])
    """
    client = get_supabase_client()
    if not client:
        return False, "Authentication service unavailable", None

    try:
        # Get the redirect URL for Google OAuth
        response = client.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": st.secrets.get('app_url', 'http://localhost:8501')
            }
        })

        if response.url:
            return True, "Redirecting to Google...", response.url
        else:
            return False, "Failed to initiate Google sign in", None

    except Exception as e:
        return False, f"Google sign in failed: {e}", None


def sign_out() -> Tuple[bool, str]:
    """
    Sign out the current user

    Returns:
        Tuple of (success: bool, message: str)
    """
    client = get_supabase_client()

    try:
        if client:
            client.auth.sign_out()

        # Clear session state
        if 'supabase_session' in st.session_state:
            del st.session_state['supabase_session']

        return True, "Signed out successfully"

    except Exception as e:
        # Still clear local session
        if 'supabase_session' in st.session_state:
            del st.session_state['supabase_session']
        return True, "Signed out"


def get_user() -> Optional[Dict[str, Any]]:
    """
    Get the current authenticated user

    Returns:
        User dict or None if not authenticated
    """
    if 'supabase_session' in st.session_state:
        session = st.session_state['supabase_session']
        return session.get('user')
    return None


def get_session() -> Optional[Dict[str, Any]]:
    """
    Get the current session

    Returns:
        Session dict or None
    """
    return st.session_state.get('supabase_session')


def is_authenticated() -> bool:
    """Check if user is currently authenticated"""
    return get_user() is not None


def reset_password(email: str) -> Tuple[bool, str]:
    """
    Send password reset email

    Args:
        email: User's email address

    Returns:
        Tuple of (success: bool, message: str)
    """
    client = get_supabase_client()
    if not client:
        return False, "Authentication service unavailable"

    try:
        client.auth.reset_password_email(email)
        return True, "Password reset email sent! Check your inbox."
    except Exception as e:
        return False, f"Failed to send reset email: {e}"


def update_password(new_password: str) -> Tuple[bool, str]:
    """
    Update password for authenticated user

    Args:
        new_password: New password (min 6 characters)

    Returns:
        Tuple of (success: bool, message: str)
    """
    client = get_supabase_client()
    if not client:
        return False, "Authentication service unavailable"

    try:
        client.auth.update_user({"password": new_password})
        return True, "Password updated successfully!"
    except Exception as e:
        return False, f"Failed to update password: {e}"


def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user profile from database

    Args:
        user_id: User's UUID

    Returns:
        Profile dict or None
    """
    client = get_supabase_client()
    if not client:
        return None

    try:
        response = client.table('user_profiles').select('*').eq('id', user_id).single().execute()
        return response.data
    except Exception:
        return None


def update_user_profile(user_id: str, data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Update user profile

    Args:
        user_id: User's UUID
        data: Profile data to update

    Returns:
        Tuple of (success: bool, message: str)
    """
    client = get_supabase_client()
    if not client:
        return False, "Database unavailable"

    try:
        data['updated_at'] = datetime.now().isoformat()
        client.table('user_profiles').update(data).eq('id', user_id).execute()
        return True, "Profile updated!"
    except Exception as e:
        return False, f"Failed to update profile: {e}"
