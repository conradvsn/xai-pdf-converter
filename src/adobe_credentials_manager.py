#!/usr/bin/env python3
"""
Adobe Credentials Manager with Rotation
Manages multiple Adobe API credentials to avoid hitting rate limits
Author: Conrad Vaslin - xAI Finance Tutor
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta


class AdobeCredentialsManager:
    """
    Manages multiple Adobe API credentials with intelligent rotation

    Features:
    - Multiple credential sets support
    - Automatic rotation when limits are reached
    - Usage tracking per credential
    - Monthly quota management (500 conversions per account)
    """

    def __init__(self, credentials_file: Optional[Path] = None):
        """
        Initialize the credentials manager

        Args:
            credentials_file: Path to JSON file with multiple credentials
                             Default: adobe_credentials_pool.json
        """
        if credentials_file is None:
            # Try multiple locations in order of preference
            possible_locations = [
                Path.cwd() / "adobe_credentials_pool.json",  # Current directory
                Path(__file__).parent.parent / "adobe_credentials_pool.json",  # Project root
                Path(__file__).parent.parent / "streamlit_app" / "adobe_credentials_pool.json",  # Streamlit app dir
                Path.home() / ".adobe" / "credentials_pool.json",  # User home directory
            ]

            credentials_file = None
            for location in possible_locations:
                if location.exists():
                    credentials_file = location
                    break

            # If still None, use default (will fail gracefully)
            if credentials_file is None:
                credentials_file = Path.cwd() / "adobe_credentials_pool.json"

        self.credentials_file = Path(credentials_file)
        self.credentials_pool: List[Dict] = []
        self.current_index = 0
        self.usage_tracking_file = Path.cwd() / "adobe_usage_tracking.json"
        self.usage_data: Dict = {}

        # Load credentials
        self._load_credentials()
        self._load_usage_tracking()

    def _load_credentials(self):
        """
        Load credentials from Streamlit secrets, JSON file, or environment variables
        Priority: Streamlit secrets > JSON file > environment variables
        """
        # Priority 1: Try Streamlit secrets (for deployed apps)
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'adobe_credentials' in st.secrets:
                # Streamlit secrets format: list of credential dicts
                self.credentials_pool = list(st.secrets['adobe_credentials'])
                print(f"✅ Loaded {len(self.credentials_pool)} Adobe credential set(s) from Streamlit secrets")
                return
        except Exception:
            pass  # Streamlit not available or no secrets configured

        # Priority 2: Try to load from file (for local development)
        if self.credentials_file.exists():
            try:
                with open(self.credentials_file, 'r') as f:
                    data = json.load(f)
                    self.credentials_pool = data.get('credentials', [])
                    print(f"✅ Loaded {len(self.credentials_pool)} Adobe credential set(s) from file")
                    return
            except Exception as e:
                print(f"⚠️  Error loading credentials file: {e}")

        # Priority 3: Try environment variables
        client_id = os.getenv('ADOBE_CLIENT_ID')
        client_secret = os.getenv('ADOBE_CLIENT_SECRET')

        if client_id and client_secret:
            self.credentials_pool = [{
                'name': 'default',
                'client_id': client_id,
                'client_secret': client_secret,
                'monthly_limit': 500
            }]
            print("✅ Loaded 1 Adobe credential set from environment variables")
        else:
            print("⚠️  No Adobe credentials found (checked: Streamlit secrets, file, env vars)")
            self.credentials_pool = []

    def _load_usage_tracking(self):
        """
        Load usage tracking data
        """
        if self.usage_tracking_file.exists():
            try:
                with open(self.usage_tracking_file, 'r') as f:
                    self.usage_data = json.load(f)
            except Exception:
                self.usage_data = {}

        # Clean old months
        self._clean_old_usage_data()

    def _save_usage_tracking(self):
        """
        Save usage tracking data
        """
        try:
            with open(self.usage_tracking_file, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error saving usage tracking: {e}")

    def _clean_old_usage_data(self):
        """
        Remove usage data older than current month
        """
        current_month = datetime.now().strftime('%Y-%m')

        # Keep only current month data
        cleaned_data = {}
        for cred_name, data in self.usage_data.items():
            if data.get('month') == current_month:
                cleaned_data[cred_name] = data

        self.usage_data = cleaned_data

    def get_current_credentials(self) -> Optional[Tuple[str, str, str]]:
        """
        Get current credentials with automatic rotation if needed

        Returns:
            Tuple of (name, client_id, client_secret) or None
        """
        if not self.credentials_pool:
            return None

        # Try all credentials in rotation until we find one with quota
        attempts = 0
        max_attempts = len(self.credentials_pool)

        while attempts < max_attempts:
            creds = self.credentials_pool[self.current_index]
            cred_name = creds.get('name', f'account_{self.current_index}')

            # Check if this credential has quota remaining
            if self._has_quota_remaining(cred_name, creds.get('monthly_limit', 500)):
                return (
                    cred_name,
                    creds['client_id'],
                    creds['client_secret']
                )

            # No quota, rotate to next
            print(f"⚠️  Account '{cred_name}' has reached its monthly limit, rotating...")
            self._rotate_to_next()
            attempts += 1

        # All accounts exhausted
        print("❌ All Adobe accounts have reached their monthly limits!")
        return None

    def _has_quota_remaining(self, cred_name: str, monthly_limit: int) -> bool:
        """
        Check if credential has quota remaining for current month
        """
        current_month = datetime.now().strftime('%Y-%m')

        usage = self.usage_data.get(cred_name, {})

        # If it's a new month, reset
        if usage.get('month') != current_month:
            return True

        # Check usage
        usage_count = usage.get('count', 0)
        return usage_count < monthly_limit

    def record_usage(self, cred_name: str):
        """
        Record that a credential was used for a conversion
        """
        current_month = datetime.now().strftime('%Y-%m')

        if cred_name not in self.usage_data:
            self.usage_data[cred_name] = {
                'month': current_month,
                'count': 0
            }

        # If new month, reset
        if self.usage_data[cred_name]['month'] != current_month:
            self.usage_data[cred_name] = {
                'month': current_month,
                'count': 0
            }

        # Increment
        self.usage_data[cred_name]['count'] += 1
        self._save_usage_tracking()

    def _rotate_to_next(self):
        """
        Rotate to next credential in pool
        """
        self.current_index = (self.current_index + 1) % len(self.credentials_pool)

    def get_usage_summary(self) -> Dict:
        """
        Get usage summary for all credentials

        Returns:
            Dict with usage information per credential
        """
        current_month = datetime.now().strftime('%Y-%m')
        summary = {}

        for creds in self.credentials_pool:
            cred_name = creds.get('name', f'account_{self.credentials_pool.index(creds)}')
            monthly_limit = creds.get('monthly_limit', 500)

            usage = self.usage_data.get(cred_name, {})
            if usage.get('month') == current_month:
                count = usage.get('count', 0)
            else:
                count = 0

            summary[cred_name] = {
                'used': count,
                'limit': monthly_limit,
                'remaining': monthly_limit - count,
                'percentage': (count / monthly_limit * 100) if monthly_limit > 0 else 0
            }

        return summary

    def print_usage_summary(self):
        """
        Print a formatted usage summary
        """
        summary = self.get_usage_summary()

        print("\n" + "="*80)
        print(" " * 25 + "📊 ADOBE API USAGE SUMMARY")
        print("="*80)

        total_used = 0
        total_limit = 0

        for cred_name, data in summary.items():
            used = data['used']
            limit = data['limit']
            remaining = data['remaining']
            percentage = data['percentage']

            total_used += used
            total_limit += limit

            # Color coding
            if percentage >= 90:
                status = "🔴"
            elif percentage >= 70:
                status = "🟡"
            else:
                status = "🟢"

            print(f"\n{status} Account: {cred_name}")
            print(f"   Used: {used}/{limit} conversions ({percentage:.1f}%)")
            print(f"   Remaining: {remaining} conversions")

        print("\n" + "-"*80)
        total_percentage = (total_used / total_limit * 100) if total_limit > 0 else 0
        print(f"TOTAL: {total_used}/{total_limit} conversions ({total_percentage:.1f}%)")
        print("="*80)


# Singleton instance
_credentials_manager: Optional[AdobeCredentialsManager] = None


def get_credentials_manager() -> AdobeCredentialsManager:
    """
    Get or create the singleton credentials manager
    """
    global _credentials_manager

    if _credentials_manager is None:
        _credentials_manager = AdobeCredentialsManager()

    return _credentials_manager
