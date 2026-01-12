"""
Session state management for Streamlit app
"""

import streamlit as st
from pathlib import Path
from datetime import datetime

def init_session_state():
    """Initialize all session state variables"""

    # Processing history
    if 'processing_history' not in st.session_state:
        st.session_state.processing_history = []

    # Current processing status
    if 'current_processing' not in st.session_state:
        st.session_state.current_processing = None

    # Settings
    if 'settings' not in st.session_state:
        st.session_state.settings = {
            'adobe_api_keys': [],
            'use_ocr': True,
            'grouping_keywords': [],
            'output_directory': str(Path.home() / 'Downloads' / 'xAI_Output'),
            'verbose_mode': False,
            'preserve_layout': True
        }

    # Statistics
    if 'stats' not in st.session_state:
        st.session_state.stats = {
            'total_pdfs_processed': 0,
            'total_pages_analyzed': 0,
            'total_findings': 0,
            'total_companies_detected': 0,
            'total_persons_detected': 0,
            'last_processed': None
        }

    # File uploads
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []

    # Results cache
    if 'results_cache' not in st.session_state:
        st.session_state.results_cache = {}

def add_to_history(pdf_name: str, operation: str, status: str, details: dict = None):
    """Add an operation to processing history"""
    entry = {
        'timestamp': datetime.now(),
        'pdf_name': pdf_name,
        'operation': operation,
        'status': status,
        'details': details or {}
    }
    st.session_state.processing_history.insert(0, entry)  # Most recent first

    # Keep only last 100 entries
    if len(st.session_state.processing_history) > 100:
        st.session_state.processing_history = st.session_state.processing_history[:100]

def update_stats(pdfs_count: int = 0, pages_count: int = 0, findings_count: int = 0,
                companies_count: int = 0, persons_count: int = 0):
    """Update global statistics"""
    st.session_state.stats['total_pdfs_processed'] += pdfs_count
    st.session_state.stats['total_pages_analyzed'] += pages_count
    st.session_state.stats['total_findings'] += findings_count
    st.session_state.stats['total_companies_detected'] += companies_count
    st.session_state.stats['total_persons_detected'] += persons_count
    st.session_state.stats['last_processed'] = datetime.now()

def get_stats():
    """Get current statistics"""
    return st.session_state.stats

def clear_history():
    """Clear processing history"""
    st.session_state.processing_history = []

def get_history(limit: int = 10):
    """Get recent processing history"""
    return st.session_state.processing_history[:limit]

def save_result(file_id: str, result_data: dict):
    """Cache processing results"""
    st.session_state.results_cache[file_id] = result_data

def get_result(file_id: str):
    """Retrieve cached result"""
    return st.session_state.results_cache.get(file_id)

def update_setting(key: str, value):
    """Update a specific setting"""
    if key in st.session_state.settings:
        st.session_state.settings[key] = value

def get_setting(key: str, default=None):
    """Get a specific setting"""
    return st.session_state.settings.get(key, default)
