#!/usr/bin/env python3
"""
Test to verify that spaCy-detected companies are NOT filtered out by regex validation.
Tests the fix for: "Credit Suisse Securities" and "The Bank of Tokyo-Mitsubishi UFJ, Ltd."
"""

import sys
sys.path.insert(0, '/Users/conrad/Downloads/xAI/src')

from analysis.sensitive_info_detector import detect_sensitive_information

def test_spacy_companies():
    """Test that spaCy-detected companies with 'securities' in name are preserved."""

    # Test texts with companies that contain words in invalid_company_words
    test_cases = [
        {
            'text': """
            CREDIT SUISSE SECURITIES (USA) LLC
            Name of Registrant: Credit Suisse Securities (USA) LLC
            The underwriters for this offering include Credit Suisse Securities, which provided
            financial advisory services to the company.
            """,
            'expected_companies': ['Credit Suisse Securities (USA) LLC', 'Credit Suisse Securities'],
            'description': 'Credit Suisse Securities - contains "securities" in invalid_company_words'
        },
        {
            'text': """
            THE BANK OF TOKYO-MITSUBISHI UFJ, LTD.
            Name of Issuer: The Bank of Tokyo-Mitsubishi UFJ, Ltd.
            The Bank of Tokyo-Mitsubishi UFJ, Ltd. served as the lead bank for the transaction.
            Mitsubishi UFJ Financial Group is the parent company.
            """,
            'expected_companies': ['The Bank of Tokyo-Mitsubishi UFJ, Ltd.', 'Mitsubishi UFJ Financial Group'],
            'description': 'Tokyo-Mitsubishi Bank - complex hyphenated name'
        },
        {
            'text': """
            WorldPay Holdings, Inc. is a payment processing company.
            The registrant's name is WorldPay, Inc.
            Payment services are provided by WorldPay.
            """,
            'expected_companies': ['WorldPay Holdings, Inc.', 'WorldPay, Inc.', 'WorldPay'],
            'description': 'WorldPay - CamelCase single-word company'
        },
        {
            'text': """
            Goldman Sachs & Co. LLC acted as financial advisor.
            Morgan Stanley & Co. served as underwriter.
            JPMorgan Chase Bank provided the credit facility.
            """,
            'expected_companies': ['Goldman Sachs & Co. LLC', 'Morgan Stanley & Co.', 'JPMorgan Chase Bank'],
            'description': 'Major financial institutions with various formats'
        }
    ]

    print("=" * 80)
    print("TESTING SPACY-DETECTED COMPANIES - FIX VERIFICATION")
    print("=" * 80)
    print("\nUser requirement: 'regex ne doit pas le delete' (regex must not delete them)")
    print("Fix: Companies detected by spaCy skip ultra-strict regex filters\n")

    all_passed = True

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'─' * 80}")
        print(f"TEST {i}: {test_case['description']}")
        print(f"{'─' * 80}")

        # Run detection
        findings = detect_sensitive_information(test_case['text'], page_num=0, verbose=True)

        # Extract detected companies
        detected_companies = [f['value'] for f in findings if f['type'] == 'company_name']

        print(f"\n📝 Test text contains: {test_case['expected_companies']}")
        print(f"✓ Detected: {detected_companies}")

        # Check if expected companies were detected
        found_count = 0
        for expected in test_case['expected_companies']:
            # Check for exact match or partial match (some companies may have variations)
            found = any(expected.lower() in detected.lower() or detected.lower() in expected.lower()
                       for detected in detected_companies)
            if found:
                found_count += 1
                print(f"  ✅ FOUND: {expected}")
            else:
                print(f"  ❌ MISSING: {expected}")
                all_passed = False

        # Show detection rate
        detection_rate = (found_count / len(test_case['expected_companies']) * 100) if test_case['expected_companies'] else 0
        print(f"\n📊 Detection rate: {found_count}/{len(test_case['expected_companies'])} ({detection_rate:.0f}%)")

        if found_count == len(test_case['expected_companies']):
            print("✅ TEST PASSED")
        else:
            print("❌ TEST FAILED")

    print(f"\n{'=' * 80}")
    if all_passed:
        print("✅ ALL TESTS PASSED - spaCy companies are properly preserved!")
        print("   Companies with 'securities', 'statement', etc. are no longer filtered.")
    else:
        print("❌ SOME TESTS FAILED - Review the filtering logic")
    print("=" * 80)

    return all_passed

if __name__ == "__main__":
    success = test_spacy_companies()
    sys.exit(0 if success else 1)
