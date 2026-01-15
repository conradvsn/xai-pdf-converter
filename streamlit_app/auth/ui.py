"""
Authentication UI Components
Beautiful login/signup forms following best practices
"""

import streamlit as st
from typing import Optional
import re

from auth.client import (
    sign_in_with_magic_link,
    sign_out,
    get_user,
    is_authenticated,
    get_user_profile
)


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def show_login_page():
    """Display the login/signup page"""

    # Check if already authenticated
    if is_authenticated():
        user = get_user()
        st.success(f"✅ You're signed in as **{user.get('email')}**")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Go to Dashboard", type="primary", use_container_width=True):
                st.switch_page("Home.py")

            if st.button("Sign Out", use_container_width=True):
                sign_out()
                st.rerun()
        return

    # Custom CSS for beautiful forms
    st.markdown("""
    <style>
        .auth-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
        }

        .auth-header {
            text-align: center;
            margin-bottom: 2rem;
        }

        .auth-header h1 {
            font-size: 2rem;
            color: #1e293b;
            margin-bottom: 0.5rem;
        }

        .auth-header p {
            color: #64748b;
            font-size: 1rem;
        }

        .divider {
            display: flex;
            align-items: center;
            text-align: center;
            margin: 1.5rem 0;
        }

        .divider::before,
        .divider::after {
            content: '';
            flex: 1;
            border-bottom: 1px solid #e2e8f0;
        }

        .divider span {
            padding: 0 1rem;
            color: #94a3b8;
            font-size: 0.875rem;
        }

        .social-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            background: white;
            color: #1e293b;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }

        .social-btn:hover {
            background: #f8fafc;
            border-color: #cbd5e1;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="auth-header">
        <h1>🔐 Welcome Back</h1>
        <p>Sign in to access your PDF converter</p>
    </div>
    """, unsafe_allow_html=True)

    # Simple magic link form
    _show_magic_link_form()


def _show_magic_link_form():
    """Display magic link login form"""

    with st.form("magic_link_form", clear_on_submit=False):
        email = st.text_input(
            "Email",
            placeholder="you@company.com",
            key="login_email"
        )

        submitted = st.form_submit_button("Send Sign-In Link", type="primary", use_container_width=True)

        if submitted:
            if not email:
                st.error("Please enter your email address")
            elif not validate_email(email):
                st.error("Please enter a valid email address")
            else:
                with st.spinner("Sending link..."):
                    success, message = sign_in_with_magic_link(email)

                if success:
                    st.success(message)
                    st.info("Check your inbox and click the link to sign in.")
                else:
                    st.error(message)


def show_user_menu():
    """Display user menu in sidebar"""

    if not is_authenticated():
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔐 Account")
        if st.sidebar.button("Sign In", use_container_width=True):
            st.switch_page("pages/0_🔐_Login.py")
        return

    user = get_user()
    if not user:
        return

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👤 Account")

    # User info
    email = user.get('email', 'User')
    full_name = user.get('full_name', '')

    display_name = full_name if full_name else email.split('@')[0]

    st.sidebar.markdown(f"**{display_name}**")
    st.sidebar.caption(email)

    # Actions
    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("Profile", use_container_width=True, key="profile_btn"):
            st.switch_page("pages/5_👤_Profile.py")

    with col2:
        if st.button("Sign Out", use_container_width=True, key="signout_btn"):
            sign_out()
            st.rerun()
