"""
Utility functions for Streamlit Application
"""

from .session import (
    init_session_state,
    add_to_history,
    update_stats,
    get_stats,
    clear_history,
    get_history,
    save_result,
    get_result,
    update_setting,
    get_setting
)

__all__ = [
    'init_session_state',
    'add_to_history',
    'update_stats',
    'get_stats',
    'clear_history',
    'get_history',
    'save_result',
    'get_result',
    'update_setting',
    'get_setting'
]
