"""
Authentication UI Components
Beautiful login/signup forms following best practices
"""

import streamlit as st
from typing import Optional
import re

from auth.client import (
    sign_up,
    sign_in,
    sign_in_with_google,
    sign_out,
    reset_password,
    get_user,
    is_authenticated,
    get_user_profile
)


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, ""


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

    # Tabs for Login / Sign Up
    tab_login, tab_signup, tab_reset = st.tabs(["Sign In", "Create Account", "Reset Password"])

    with tab_login:
        _show_login_form()

    with tab_signup:
        _show_signup_form()

    with tab_reset:
        _show_reset_form()


def _show_login_form():
    """Display login form"""

    # Google Sign-In button
    if st.button("🔵 Continue with Google", use_container_width=True, type="secondary"):
        with st.spinner("Connecting to Google..."):
            success, message, auth_url = sign_in_with_google()

        if success and auth_url:
            st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
            st.info("Redirecting to Google...")
        else:
            st.error(message)

    # Divider
    st.markdown("""
    <div class="divider">
        <span>or continue with email</span>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        email = st.text_input(
            "Email",
            placeholder="you@company.com",
            key="login_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password"
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            remember = st.checkbox("Remember me", value=True)

        submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("Please fill in all fields")
            elif not validate_email(email):
                st.error("Please enter a valid email address")
            else:
                with st.spinner("Signing in..."):
                    success, message = sign_in(email, password)

                if success:
                    st.success(message)
                    st.balloons()
                    st.rerun()
                else:
                    st.error(message)


def _show_signup_form():
    """Display signup form"""

    # Google Sign-Up button
    if st.button("🔵 Sign up with Google", use_container_width=True, type="secondary", key="google_signup"):
        with st.spinner("Connecting to Google..."):
            success, message, auth_url = sign_in_with_google()

        if success and auth_url:
            st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
            st.info("Redirecting to Google...")
        else:
            st.error(message)

    # Divider
    st.markdown("""
    <div class="divider">
        <span>or sign up with email</span>
    </div>
    """, unsafe_allow_html=True)

    with st.form("signup_form", clear_on_submit=False):
        full_name = st.text_input(
            "Full Name",
            placeholder="John Doe",
            key="signup_name"
        )

        email = st.text_input(
            "Email",
            placeholder="you@company.com",
            key="signup_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Min. 6 characters",
            key="signup_password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Confirm your password",
            key="signup_confirm"
        )

        terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")

        submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)

        if submitted:
            # Validation
            if not all([full_name, email, password, confirm_password]):
                st.error("Please fill in all fields")
            elif not validate_email(email):
                st.error("Please enter a valid email address")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif not terms:
                st.error("Please accept the Terms of Service")
            else:
                valid, msg = validate_password(password)
                if not valid:
                    st.error(msg)
                else:
                    with st.spinner("Creating account..."):
                        success, message = sign_up(email, password, full_name)

                    if success:
                        st.success(message)
                        st.info("📧 Check your email to verify your account, then sign in.")
                    else:
                        st.error(message)


def _show_reset_form():
    """Display password reset form"""

    st.markdown("Enter your email to receive a password reset link.")

    with st.form("reset_form", clear_on_submit=True):
        email = st.text_input(
            "Email",
            placeholder="you@company.com",
            key="reset_email"
        )

        submitted = st.form_submit_button("Send Reset Link", type="primary", use_container_width=True)

        if submitted:
            if not email:
                st.error("Please enter your email address")
            elif not validate_email(email):
                st.error("Please enter a valid email address")
            else:
                with st.spinner("Sending reset link..."):
                    success, message = reset_password(email)

                if success:
                    st.success(message)
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
