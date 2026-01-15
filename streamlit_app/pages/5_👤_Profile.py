"""
👤 User Profile Page
Manage account settings and view history
"""

import streamlit as st
from pathlib import Path
import sys

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.styles import apply_global_styles

# Page config
st.set_page_config(
    page_title="Profile - xAI PDF Converter",
    page_icon="👤",
    layout="wide"
)

# Apply styles
apply_global_styles()

# Import auth
from auth.middleware import require_auth, get_current_user
from auth.client import (
    get_user_profile,
    update_user_profile,
    update_password,
    sign_out,
    get_supabase_client
)

# Require authentication
if not require_auth():
    st.stop()

# Get current user
user = get_current_user()
user_id = user.get('id')

# Header
st.markdown("""
<div class="page-header">
    <h1>👤 Your Profile</h1>
    <p>Manage your account settings and view your conversion history</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Load profile
profile = get_user_profile(user_id) if user_id else None

# Profile Section
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### Account Info")

    # Avatar placeholder
    avatar_url = profile.get('avatar_url', '') if profile else ''
    if avatar_url:
        st.image(avatar_url, width=150)
    else:
        st.markdown("""
        <div style="width: 150px; height: 150px; background: linear-gradient(135deg, #6366f1, #8b5cf6);
                    border-radius: 75px; display: flex; align-items: center; justify-content: center;
                    font-size: 4rem; color: white;">
            👤
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"**{user.get('email', 'User')}**")

with col2:
    st.markdown("### Edit Profile")

    with st.form("profile_form"):
        full_name = st.text_input(
            "Full Name",
            value=profile.get('full_name', '') if profile else user.get('full_name', ''),
            placeholder="Your full name"
        )

        company = st.text_input(
            "Company",
            value=profile.get('company', '') if profile else '',
            placeholder="Your company name"
        )

        if st.form_submit_button("Save Changes", type="primary"):
            if user_id:
                success, msg = update_user_profile(user_id, {
                    'full_name': full_name,
                    'company': company
                })
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

st.markdown("---")

# Password Section
st.markdown("### 🔑 Change Password")

with st.form("password_form"):
    new_password = st.text_input(
        "New Password",
        type="password",
        placeholder="Min. 6 characters"
    )

    confirm_password = st.text_input(
        "Confirm New Password",
        type="password",
        placeholder="Confirm password"
    )

    if st.form_submit_button("Update Password"):
        if not new_password or not confirm_password:
            st.error("Please fill in both fields")
        elif new_password != confirm_password:
            st.error("Passwords do not match")
        elif len(new_password) < 6:
            st.error("Password must be at least 6 characters")
        else:
            success, msg = update_password(new_password)
            if success:
                st.success(msg)
            else:
                st.error(msg)

st.markdown("---")

# Document History
st.markdown("### 📄 Your Documents")

client = get_supabase_client()
if client and user_id:
    try:
        response = client.table('user_documents').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(20).execute()
        documents = response.data

        if documents:
            for doc in documents:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.write(f"📄 **{doc.get('original_name', doc.get('filename', 'Unknown'))}**")
                with col2:
                    size_kb = (doc.get('file_size', 0) or 0) / 1024
                    st.caption(f"{size_kb:.1f} KB")
                with col3:
                    st.caption(f"{doc.get('findings_count', 0)} findings")
                with col4:
                    created = doc.get('created_at', '')[:10] if doc.get('created_at') else ''
                    st.caption(created)
        else:
            st.info("No documents yet. Start by converting a PDF!")
    except Exception as e:
        st.warning("Could not load document history")
else:
    st.info("Document history will appear here after your first conversion")

st.markdown("---")

# Danger Zone
with st.expander("⚠️ Danger Zone"):
    st.warning("These actions are irreversible!")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Sign Out of All Devices", use_container_width=True):
            sign_out()
            st.rerun()

    with col2:
        st.button("Delete Account", use_container_width=True, disabled=True)
        st.caption("Contact admin to delete your account")
