"""
Cloud Storage Module for Persistent Data
Uses Supabase for storing usage tracking and credentials on Streamlit Cloud
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import streamlit as st


# Check if Supabase is available
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None


class CloudStorage:
    """
    Cloud storage for persistent data across Streamlit Cloud sessions.

    Uses Supabase for:
    - Usage tracking (conversions per account per month)
    - API credentials storage (optional, more secure than secrets.toml)
    """

    def __init__(self):
        self.client: Optional[Client] = None
        self.is_connected = False
        self._init_client()

    def _init_client(self):
        """Initialize Supabase client from Streamlit secrets"""
        if not SUPABASE_AVAILABLE:
            return

        try:
            # Try to get Supabase credentials from Streamlit secrets
            if hasattr(st, 'secrets') and 'supabase' in st.secrets:
                url = st.secrets['supabase']['url']
                key = st.secrets['supabase']['key']
                self.client = create_client(url, key)
                self.is_connected = True
        except Exception as e:
            # Supabase not configured - fallback to local storage
            self.is_connected = False

    def get_usage(self, account_name: str) -> Dict[str, Any]:
        """
        Get usage data for an account from cloud storage.

        Args:
            account_name: Name of the Adobe account

        Returns:
            Dict with 'month' and 'count' keys, or empty dict if not found
        """
        if not self.is_connected:
            return {}

        try:
            current_month = datetime.now().strftime('%Y-%m')

            response = self.client.table('adobe_usage').select('*').eq(
                'account_name', account_name
            ).eq('month', current_month).execute()

            if response.data and len(response.data) > 0:
                return {
                    'month': response.data[0]['month'],
                    'count': response.data[0]['count']
                }
            return {'month': current_month, 'count': 0}

        except Exception as e:
            return {}

    def get_all_usage(self) -> Dict[str, Dict[str, Any]]:
        """
        Get usage data for all accounts from cloud storage.

        Returns:
            Dict mapping account_name to usage data
        """
        if not self.is_connected:
            return {}

        try:
            current_month = datetime.now().strftime('%Y-%m')

            response = self.client.table('adobe_usage').select('*').eq(
                'month', current_month
            ).execute()

            result = {}
            if response.data:
                for row in response.data:
                    result[row['account_name']] = {
                        'month': row['month'],
                        'count': row['count']
                    }
            return result

        except Exception as e:
            return {}

    def record_usage(self, account_name: str) -> bool:
        """
        Record a conversion usage for an account.

        Args:
            account_name: Name of the Adobe account

        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            return False

        try:
            current_month = datetime.now().strftime('%Y-%m')

            # Check if record exists
            response = self.client.table('adobe_usage').select('*').eq(
                'account_name', account_name
            ).eq('month', current_month).execute()

            if response.data and len(response.data) > 0:
                # Update existing record
                new_count = response.data[0]['count'] + 1
                self.client.table('adobe_usage').update({
                    'count': new_count,
                    'updated_at': datetime.now().isoformat()
                }).eq('account_name', account_name).eq('month', current_month).execute()
            else:
                # Insert new record
                self.client.table('adobe_usage').insert({
                    'account_name': account_name,
                    'month': current_month,
                    'count': 1,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }).execute()

            return True

        except Exception as e:
            return False

    def get_credentials(self) -> List[Dict[str, Any]]:
        """
        Get Adobe credentials from cloud storage.

        Returns:
            List of credential dicts with name, client_id, client_secret, monthly_limit
        """
        if not self.is_connected:
            return []

        try:
            response = self.client.table('adobe_credentials').select(
                'name', 'client_id', 'client_secret', 'monthly_limit'
            ).execute()

            return response.data if response.data else []

        except Exception as e:
            return []

    def save_credentials(self, credentials: List[Dict[str, Any]]) -> bool:
        """
        Save Adobe credentials to cloud storage.

        Args:
            credentials: List of credential dicts

        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            return False

        try:
            # Clear existing credentials
            self.client.table('adobe_credentials').delete().neq('id', 0).execute()

            # Insert new credentials
            for cred in credentials:
                self.client.table('adobe_credentials').insert({
                    'name': cred['name'],
                    'client_id': cred['client_id'],
                    'client_secret': cred['client_secret'],
                    'monthly_limit': cred.get('monthly_limit', 500),
                    'created_at': datetime.now().isoformat()
                }).execute()

            return True

        except Exception as e:
            return False


# Singleton instance
_cloud_storage: Optional[CloudStorage] = None


def get_cloud_storage() -> CloudStorage:
    """Get or create the singleton cloud storage instance"""
    global _cloud_storage

    if _cloud_storage is None:
        _cloud_storage = CloudStorage()

    return _cloud_storage


def is_cloud_storage_available() -> bool:
    """Check if cloud storage is available and connected"""
    storage = get_cloud_storage()
    return storage.is_connected
