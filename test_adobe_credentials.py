#!/usr/bin/env python3
"""
Script de test pour vérifier la configuration Adobe PDF Services
"""

import os
import sys
from pathlib import Path

print("="*80)
print(" " * 25 + "🔍 ADOBE CREDENTIALS TEST")
print("="*80)
print()

# Test 1: Variables d'environnement
print("1️⃣  Checking environment variables...")
client_id = os.getenv('ADOBE_CLIENT_ID')
client_secret = os.getenv('ADOBE_CLIENT_SECRET')

if client_id:
    print(f"   ✅ ADOBE_CLIENT_ID is set (length: {len(client_id)})")
    print(f"      First 20 chars: {client_id[:20]}...")
else:
    print("   ❌ ADOBE_CLIENT_ID is NOT set")

if client_secret:
    print(f"   ✅ ADOBE_CLIENT_SECRET is set (length: {len(client_secret)})")
    print(f"      First 20 chars: {client_secret[:20]}...")
else:
    print("   ❌ ADOBE_CLIENT_SECRET is NOT set")

print()

# Test 2: Fichier credentials
print("2️⃣  Checking credentials file...")
creds_file = Path.cwd() / "pdfservices-api-credentials.json"

if creds_file.exists():
    print(f"   ✅ File exists: {creds_file}")
    try:
        import json
        with open(creds_file, 'r') as f:
            data = json.load(f)
            creds = data.get('client_credentials', {})
            file_client_id = creds.get('client_id')
            file_client_secret = creds.get('client_secret')

            if file_client_id:
                print(f"   ✅ client_id found in file (length: {len(file_client_id)})")
                print(f"      First 20 chars: {file_client_id[:20]}...")
            else:
                print("   ❌ client_id NOT found in file")

            if file_client_secret:
                print(f"   ✅ client_secret found in file (length: {len(file_client_secret)})")
                print(f"      First 20 chars: {file_client_secret[:20]}...")
            else:
                print("   ❌ client_secret NOT found in file")
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
else:
    print(f"   ❌ File does not exist: {creds_file}")

print()

# Test 3: Adobe SDK
print("3️⃣  Checking Adobe SDK installation...")
try:
    from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
    print("   ✅ Adobe PDF Services SDK is installed")

    # Try to create credentials
    if (client_id and client_secret) or (creds_file.exists()):
        print()
        print("4️⃣  Testing credential creation...")
        try:
            if client_id and client_secret:
                print("   Using environment variables...")
                creds = ServicePrincipalCredentials(
                    client_id=client_id,
                    client_secret=client_secret
                )
                print("   ✅ Credentials created successfully from environment!")
            elif creds_file.exists():
                print("   Using credentials file...")
                # Read again to create
                with open(creds_file, 'r') as f:
                    data = json.load(f)
                    file_creds = data.get('client_credentials', {})
                    creds = ServicePrincipalCredentials(
                        client_id=file_creds.get('client_id'),
                        client_secret=file_creds.get('client_secret')
                    )
                print("   ✅ Credentials created successfully from file!")
        except Exception as e:
            print(f"   ❌ Failed to create credentials: {e}")

except ImportError:
    print("   ❌ Adobe PDF Services SDK is NOT installed")
    print("      Install with: pip install pdfservices-sdk")

print()
print("="*80)
print()

# Summary
has_env_creds = bool(client_id and client_secret)
has_file_creds = creds_file.exists()

if has_env_creds or has_file_creds:
    print("✅ RESULT: Adobe credentials are configured!")
    if has_env_creds:
        print("   Method: Environment variables")
    if has_file_creds:
        print("   Method: Credentials file")
else:
    print("❌ RESULT: Adobe credentials are NOT configured")
    print()
    print("To configure credentials:")
    print()
    print("METHOD A - Environment variables (in your terminal):")
    print("   export ADOBE_CLIENT_ID='your_client_id'")
    print("   export ADOBE_CLIENT_SECRET='your_client_secret'")
    print()
    print("METHOD B - Credentials file:")
    print("   Create 'pdfservices-api-credentials.json' with:")
    print('   {')
    print('     "client_credentials": {')
    print('       "client_id": "your_client_id",')
    print('       "client_secret": "your_client_secret"')
    print('     }')
    print('   }')
    print()
    print("Get FREE credentials at:")
    print("https://acrobatservices.adobe.com/dc-integration-creation-app-cdn/main.html")

print()
print("="*80)
