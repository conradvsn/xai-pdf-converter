#!/usr/bin/env python3
"""
Sensitive Information Detection Module - Complete Version
Ported from monolithic xaipdfconverter.py
Author: Conrad Vaslin - xAI Finance Tutor
"""

# VERSION FOR DEBUGGING STREAMLIT CLOUD CACHE ISSUES
DETECTOR_VERSION = "2025-01-15-PRODUCTION"

import re
from pathlib import Path
from typing import Dict, List, Any, Set

from src.config import (
    PYPDF2_AVAILABLE, PHONENUMBERS_AVAILABLE, TQDM_AVAILABLE,
    SPACY_AVAILABLE, SPACY_NLP, logger
)

if PYPDF2_AVAILABLE:
    import PyPDF2

if PHONENUMBERS_AVAILABLE:
    import phonenumbers
    from phonenumbers import PhoneNumberFormat

if TQDM_AVAILABLE:
    from tqdm import tqdm


# ===== CONSTANTS FOR DETECTION =====

DOCUMENT_STRUCTURE_TERMS = {
    'balance sheet', 'income statement', 'cash flow', 'table of contents',
    'statement of operations', 'notes to financial', 'management discussion',
    'risk factors', 'executive summary', 'business overview', 'legal proceedings',
    'market for', 'selected financial', 'quantitative and qualitative',
    'controls and procedures', 'financial statements', 'exhibits index',
    'consolidated balance', 'consolidated statements', 'stockholders equity',
    'comprehensive income', 'changes in', 'years ended', 'months ended',
    'unaudited consolidated', 'audited consolidated', 'condensed consolidated',
    'management discussion and analysis', 'form 10-k', 'form 10-q', 'form 8-k',
    'part i', 'part ii', 'part iii', 'part iv', 'item 1', 'item 2', 'item 3'
}

# Generic business terms that spaCy often flags as organizations
GENERIC_BUSINESS_TERMS = {
    'operations', 'management', 'board', 'committee', 'team', 'division',
    'department', 'group', 'unit', 'panel', 'council', 'assembly',
    'business combination', 'financial condition', 'operating results',
    'the business', 'the company', 'the registrant', 'the issuer',
    'securities', 'commission', 'exchange', 'trading', 'market',
    'segment', 'services', 'products', 'business', 'enterprise',
    'consolidated', 'combined', 'merged', 'acquired', 'subsidiary',
    'parent company', 'holding company', 'affiliated', 'related party',
    'operating segment', 'reportable segment', 'business segment',
    'common stock', 'preferred stock', 'class a', 'class b',
    'shareholders', 'stockholders', 'beneficial owners', 'insiders'
}

# Invalid first words for company names (articles, prepositions, conjunctions)
INVALID_COMPANY_FIRST_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'if', 'then', 'such', 'all',
    'any', 'each', 'every', 'some', 'no', 'this', 'that', 'these', 'those',
    'operations', 'management', 'financial', 'business', 'combined',
    'our', 'we', 'us', 'their', 'its', 'his', 'her', 'your',
    'securities', 'commission', 'exchange', 'consolidated', 'total',
    # Document section terms that should not start company names
    'board', 'compensation', 'corporate', 'competition', 'governance',
    'discussion', 'analysis', 'overview', 'summary', 'statement', 'report'
}

# Common person name false positives (document terms that look like names)
PERSON_NAME_FALSE_POSITIVES = {
    'balance sheet', 'income statement', 'cash flow statement',
    'table of contents', 'united states', 'new york', 'los angeles',
    'washington dc', 'the company', 'the registrant', 'the issuer',
    'securities exchange', 'exchange commission', 'internal revenue',
    'generally accepted', 'accounting principles', 'fair value',
    'stock option', 'stock compensation', 'stock award',
    'restricted stock', 'performance share', 'equity award',
    'executive compensation', 'board compensation', 'audit committee',
    'compensation committee', 'nominating committee', 'risk committee',
    'operations committee', 'investment committee', 'credit committee'
}

# Invalid words that should NEVER appear in a person name
INVALID_NAME_WORDS = {
    'and', 'or', 'the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for',
    'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be', 'been',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'shall',
    'should', 'may', 'might', 'must', 'can', 'could',
    'require', 'required', 'requirements', 'pursuant', 'accordance',
    'including', 'include', 'includes', 'such', 'other', 'any', 'all',
    'each', 'every', 'both', 'either', 'neither', 'none', 'not',
    'only', 'same', 'than', 'then', 'there', 'these', 'those', 'this',
    'that', 'which', 'who', 'whom', 'whose', 'what', 'when', 'where',
    'whether', 'applicable', 'provided', 'however', 'therefore',
    'furthermore', 'moreover', 'otherwise', 'unless', 'until', 'upon',
    'within', 'without', 'respect', 'regard', 'pursuant', 'subject'
}

# Legitimate first names that end in "-ing" (should NOT be rejected by gerund filter)
LEGITIMATE_ING_NAMES = {
    'irving', 'sterling', 'fleming', 'darling', 'manning', 'harding',
    'cumming', 'cummings', 'deming', 'fanning', 'goring', 'harding',
    'lansing', 'pickering', 'spalding', 'willing'
}

# Legitimate name prefixes with capital in middle (for McDonald, DeAngelo, etc.)
LEGITIMATE_NAME_PREFIXES = {
    'mc', 'mac', 'de', 'la', 'le', 'van', 'von', "o'"
}

# Keywords that can be first names (like "Grant") - need smart checking
KEYWORDS_AS_FIRST_NAMES = {
    'grant': ['date', 'notice', 'plan', 'program', 'agreement', 'award', 'awards'],  # Reject "Grant Date" but accept "Grant Williams"
    'award': ['date', 'notice', 'plan', 'agreement'],  # Very rare but possible as name
    'sterling': []  # Always accept (covered by LEGITIMATE_ING_NAMES)
}

# Common technical email prefixes that should NOT create person names
TECHNICAL_EMAIL_PREFIXES = {
    'admin', 'support', 'info', 'contact', 'sales', 'help', 'service',
    'noreply', 'no-reply', 'donotreply', 'webmaster', 'postmaster',
    'billing', 'accounts', 'finance', 'hr', 'legal', 'compliance'
}


def detect_sensitive_information(pdf_path: Path, verbose: bool = False) -> Dict[int, List[Dict[str, Any]]]:
    """
    Complete sensitive information detection - ported from monolithic version.
    Detects: emails, phones, addresses, SSN, credit cards, company names, person names, etc.
    
    Args:
        pdf_path: Path to PDF file
        verbose: If True, show detailed logs
    
    Returns:
        Dictionary mapping page numbers to lists of findings
    """
    sensitive_info_by_page = {}
    
    """
    Nouvelle stratégie de détection: approche pragmatique et robuste.

    Args:
        verbose: Si True, affiche les logs détaillés. Si False, utilise tqdm pour progress bar.
    """
    sensitive_info_by_page = {}

    # NOTE: Constants (DOCUMENT_STRUCTURE_TERMS, GENERIC_BUSINESS_TERMS, etc.)
    # are defined at module level (lines 30-85) to avoid memory waste on each function call

    if not PYPDF2_AVAILABLE:
        logger.warning("PyPDF2 is not available. Install with: pip install PyPDF2")
        return sensitive_info_by_page
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            # Progress indicator: tqdm en mode simple, print en mode verbose
            if verbose:
                # Mode verbose : afficher le message
                if total_pages > 10:
                    print(f"   📄 Analyzing {total_pages} pages...", end='', flush=True)
                page_iterator = range(total_pages)
            else:
                # Mode simple : utiliser tqdm si disponible
                if TQDM_AVAILABLE and total_pages > 5:
                    page_iterator = tqdm(range(total_pages), desc="   Analyzing pages", unit="page", 
                                        ncols=80, leave=False, disable=False)
                else:
                    page_iterator = range(total_pages)

            # ========== COMPILE ALL REGEX PATTERNS ONCE (PERFORMANCE OPTIMIZATION) ==========
            # These patterns are compiled once before the loop instead of on every page
            # Improves performance by 10x on large PDFs (100+ pages)

            # Email pattern and validation lists
            email_pattern = re.compile(r'\b[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}\b')
            valid_tlds = {
                'com', 'org', 'net', 'edu', 'gov', 'mil', 'int',
                'co', 'io', 'ai', 'biz', 'info', 'name', 'pro',
                'uk', 'us', 'ca', 'au', 'de', 'fr', 'jp', 'cn', 'in', 'br',
                'ru', 'nl', 'it', 'es', 'pl', 'se', 'ch', 'be', 'at'
            }
            fake_email_patterns = {
                'test@', 'example@', 'sample@', 'demo@', 'fake@',
                'noreply@', 'no-reply@', 'donotreply@',
                '@test.', '@example.', '@sample.', '@demo.', '@fake.',
                '@localhost', '@127.0.0.1', '@0.0.0.0',
                'admin@admin', 'user@user', 'email@email'
            }

            # Website/URL patterns
            url_with_protocol_pattern = re.compile(
                r'\b(https?://(?:www\.)?[a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+(?:/[^\s]*)?)\b',
                re.IGNORECASE
            )
            url_with_www_pattern = re.compile(
                r'\b(www\.[a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+(?:/[^\s]*)?)\b',
                re.IGNORECASE
            )
            url_domain_pattern = re.compile(
                r'\b([a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)*\.(?:com|org|net|edu|gov|io|co|ai|biz|info|us|uk|ca|au|de|fr|jp|cn))\b',
                re.IGNORECASE
            )

            # Phone patterns
            phone_us_pattern = re.compile(r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
            phone_intl_patterns = [
                re.compile(r'\+\d{1,3}\s*\(?0\)?\s*\d{1,4}\s*\d{3,4}\s*\d{3,4}\b'),
                re.compile(r'\+\d{1,3}\s+\d{1,4}\s+\d{3,4}\s+\d{3,4}\b'),
                re.compile(r'\+\d{1,3}\s*\d{6,14}\b'),
                re.compile(r'00\d{1,3}\s+\d{1,4}\s+\d{3,4}\s+\d{3,4}\b'),
                re.compile(r'\(?0\)?\s*\d{2,4}\s+\d{3,4}\s+\d{3,4}\b'),
            ]
            phone_with_ext_pattern = re.compile(
                r'(\+?\d{1,3}[\s\-\(\)]?\d{1,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4})\s*(?:ext|extension|ext\.|x\.?|#)\s*(\d{1,6})',
                re.IGNORECASE
            )

            # Address patterns (HEAVY - critical to compile once)
            address_pattern_abbr = re.compile(
                r'\b(\d{1,5})\s+'
                r'([A-Za-z](?:[A-Za-z\s\']{0,50})?)\s+'
                r'(Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Boulevard|Blvd\.?|Lane|Ln\.?|Drive|Dr\.?|Court|Ct\.?|Place|Pl\.?|Way|Circle|Cir\.?|Parkway|Pkwy\.?|Highway|Hwy\.?)'
                r'(?:\s*,?\s*(NE|NW|SE|SW|N|S|E|W))?'
                r'(?:\s*,?\s*(?:Room|Suite|Ste\.?|Apt\.?|Unit|#)\s*[A-Z0-9\-]+)?'
                r'\s*,?\s*'
                r'([A-Za-z][A-Za-z\s]{2,50}?)'
                r'\s*,?\s+'
                r'([A-Z]{2})\s+'
                r'(\d{5}(?:-\d{4})?)\b',
                re.IGNORECASE
            )
            address_pattern_full = re.compile(
                r'\b(\d{1,5})\s+'
                r'([A-Za-z](?:[A-Za-z\s\']{0,50})?)\s+'
                r'(Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Boulevard|Blvd\.?|Lane|Ln\.?|Drive|Dr\.?|Court|Ct\.?|Place|Pl\.?|Way|Circle|Cir\.?|Parkway|Pkwy\.?|Highway|Hwy\.?)'
                r'(?:\s*,?\s*(NE|NW|SE|SW|N|S|E|W))?'
                r'(?:\s*,?\s*(?:Room|Suite|Ste\.?|Apt\.?|Unit|#)\s*[A-Z0-9\-]+)?'
                r'\s*,?\s*'
                r'([A-Za-z][A-Za-z\s]{2,50}?)'
                r'\s*,?\s+'
                r'(Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|'
                r'Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|'
                r'Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New\s+Hampshire|New\s+Jersey|'
                r'New\s+Mexico|New\s+York|North\s+Carolina|North\s+Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|'
                r'Rhode\s+Island|South\s+Carolina|South\s+Dakota|Tennessee|Texas|Utah|Vermont|Virginia|'
                r'Washington|West\s+Virginia|Wisconsin|Wyoming|District\s+of\s+Columbia)\s+'
                r'(\d{5}(?:-\d{4})?)\b',
                re.IGNORECASE
            )
            zip_pattern = re.compile(r'\b(\d{5}(?:-\d{4})?)\b')

            # SSN and other ID patterns
            ssn_pattern = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
            cfn_context_pattern = re.compile(r'Commission\s+File\s+Number[:\s]+(\d{3}-\d{5})', re.IGNORECASE)
            ein_pattern = re.compile(r'\b(\d{2}-\d{7})\b')  # IRS Employer Identification Number: XX-XXXXXXX (2 digits - 7 digits)
            cik_context_pattern = re.compile(r'(?:CIK|Central\s+Index\s+Key|File\s+Number)[:\s]+(\d{7,10})', re.IGNORECASE)

            # Person name signature patterns
            person_signature_patterns = [
                re.compile(r'/s[/\s]+\s*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', re.IGNORECASE),
                re.compile(r'(?:signed|by)[:\s]+([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', re.IGNORECASE),
                re.compile(r'\(s\)\s*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', re.IGNORECASE),
            ]

            # Person name context patterns
            person_context_patterns = [
                re.compile(
                    r'(?:Director|Officer|Employee|Trustee|Beneficial\s+Owner|Shareholder|Stockholder|Member|Partner|Principal|Agent|Representative|Signatory|Authorized\s+Signatory)[:\s]+([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                    re.IGNORECASE
                ),
                re.compile(
                    r'(?:Name|Person|Individual|Contact)[:\s]+([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                    re.IGNORECASE
                ),
            ]

            # Person name list patterns
            name_list_patterns = [
                re.compile(r'\b([A-Z][a-z]+),\s+([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)\b'),
                re.compile(r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)\b'),
            ]

            # Company name patterns (VERY HEAVY - critical to compile once)
            company_suffixes = r'(?:Inc\.?|LLC|LLP|L\.L\.C\.|L\.L\.P\.|Corporation|Corp\.?|Corp|Incorporated|Inc|Ltd\.?|Limited|LP|L\.P\.|PC|P\.C\.|PLLC|PLC|Co\.?|Company|Companies|Group|Holdings|Holdings?|Enterprises|Partners|Partnership|Bank|Banks|Trust|Capital|Securities|Financial|Services|AG|S\.A\.|SA|GmbH|BV|NV|SpA|S\.p\.A\.)'

            company_context_patterns = [
                re.compile(
                    r'(?:Exact\s+name\s+of\s+registrant|'
                    r'Name\s+of\s+(?:the\s+)?(?:registrant|issuer|company|corporation)|'
                    r'(?:Registrant|Issuer|Company|Corporation)(?:\'s)?\s+name|'
                    r'Company\s+Name|'
                    r'Entity\s+Name)'
                    r'[:\s]+([A-Z][A-Za-z0-9\s&,\.\-]+?(?:,\s*)?' + company_suffixes + r')',
                    re.IGNORECASE
                ),
                re.compile(
                    r'(?:Registrant|Issuer|Company)[:\s]+([A-Z][A-Za-z0-9\s&,\.\-]+?(?:,\s*)?' + company_suffixes + r')',
                    re.IGNORECASE
                ),
            ]

            company_standalone_patterns = [
                re.compile(
                    r'(?<=[\.\n\(\s])([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,6}),?\s+' + company_suffixes + r'(?=[\.\n\)\s,])',
                    re.MULTILINE
                ),
                re.compile(
                    r'\b([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,6})\s+' + company_suffixes + r'\b',
                    re.MULTILINE
                ),
                re.compile(
                    r'\b([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){1,4})\s+(AG|S\.A\.|SA|GmbH|BV|NV|SpA|S\.p\.A\.)\b',
                    re.MULTILINE
                ),
            ]

            company_name_patterns_no_suffix = [
                re.compile(r'\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){1,4})\s+Bank\b'),
                re.compile(r'\b([A-Z][A-Za-z]+)\s+Bank\s+of\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)\b'),
                re.compile(r'\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)\s+(?:Financial|Capital|Securities|Asset\s+Management|Investment(?:s)?|Fund(?:s)?)\b'),
            ]

            # Known company names (CamelCase and single-word companies) - always detected with proper context
            # These are well-known companies that don't have traditional suffixes (Inc., LLC, etc.)
            known_company_names_pattern = re.compile(
                r'\b(WorldPay|JPMorgan|MasterCard|PayPal|eBay|LinkedIn|FedEx|DreamWorks|YouTube|'
                r'BlackRock|Bridgewater|Vanguard|Fidelity|Vantiv|Stripe|Square|Shopify|'
                r'Goldman|Lehman|Citigroup|Barclays|Deutsche|UBS|HSBC|BNP|Santander)\b'
            )

            # US states abbreviations (for address validation)
            valid_states_abbr = [
                'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
            ]

            # Inverse address pattern (for ZIP-first detection)
            inverse_pattern = re.compile(
                r'(\d{1,5})\s+'
                r'([A-Za-z\s]{3,50}?)\s+'
                r'(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl|Way|Circle|Cir|Parkway|Pkwy|Highway|Hwy)'
                r'\s+([A-Za-z\s]{3,40}?)[,\s]+'
                r'([A-Z]{2})\s*$',
                re.IGNORECASE
            )

            # Executive titles for person name detection
            executive_titles = [
                r'Chief\s+(?:Executive|Financial|Operating|Technology|Information|Marketing|Revenue|Accounting|Legal|Compliance|Risk|Investment)\s+Officer',
                r'CEO|CFO|CTO|COO|CIO|CMO|CRO|CAO|CLO|CCO|CRO',
                r'President',
                r'Vice\s+President',
                r'VP\s+(?:of|Finance|Operations|Sales|Marketing|Engineering)',
                r'Executive\s+Vice\s+President',
                r'EVP',
                r'Senior\s+Vice\s+President',
                r'SVP',
                r'Chairman',
                r'Chairman\s+of\s+the\s+Board',
                r'Vice\s+Chairman',
                r'Secretary',
                r'Treasurer',
                r'Controller',
                r'Chief\s+Controller',
                r'Managing\s+Director',
                r'General\s+Manager',
                r'Director',
                r'Executive\s+Director',
                r'Founder',
                r'Co-Founder',
                r'Chief\s+of\s+Staff',
                r'Head\s+of\s+(?:Finance|Operations|Sales|Marketing|Engineering|Legal)',
            ]
            exec_title_pattern = '|'.join(executive_titles)

            # Executive name patterns (name + title)
            exec_pattern = re.compile(
                r'\b([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[,:]\s*(' + exec_title_pattern + r')\b',
                re.IGNORECASE
            )
            exec_pattern_reverse = re.compile(
                r'\b(' + exec_title_pattern + r')\s*[:]\s*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
                re.IGNORECASE
            )
            officers_section_pattern = re.compile(
                r'(?:Officers?|Management|Executive\s+Officers?|Key\s+Personnel)[\s\S]{0,500}?'
                r'([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[,:]\s*(' + exec_title_pattern + r')\b',
                re.IGNORECASE | re.MULTILINE
            )

            # Additional person name patterns
            email_name_pattern = re.compile(r'\b([a-z]+\.?[a-z]+)\.([a-z]+)@', re.IGNORECASE)
            general_name_pattern = re.compile(r'\b([A-Z][a-z]{2,15})\s+([A-Z]\.?\s*)?([A-Z][a-z]{2,20})\b')

            # End of compiled patterns
            # ========================================================================

            for page_num in page_iterator:
                page = pdf_reader.pages[page_num]
                page_findings = []
                
                try:
                    text = page.extract_text()
                    if not text or len(text.strip()) < 10:
                        continue
                    
                    # Normalize text
                    text = re.sub(r'\s+', ' ', text)
                    text = text.strip()
                    
                    # ===== EMAILS - IMPROVED WITH VALIDATION =====
                    # Patterns compiled once before loop (lines 154-167)

                    for match in email_pattern.finditer(text):
                        email = match.group().strip().lower()

                        # Validation 1: Check TLD
                        tld = email.split('.')[-1] if '.' in email else ''
                        if tld not in valid_tlds:
                            continue  # Skip invalid TLD

                        # Validation 2: Reject fake/test emails
                        if any(fake in email for fake in fake_email_patterns):
                            continue

                        # Validation 3: Basic structure validation
                        if email.count('@') != 1:
                            continue  # Must have exactly one @

                        local, domain = email.split('@')
                        if len(local) < 1 or len(domain) < 3:
                            continue  # Too short

                        if domain.count('.') < 1:
                            continue  # Domain must have at least one dot

                        # Validation 4: Reject suspicious patterns
                        if '..' in email or email.startswith('.') or email.endswith('.'):
                            continue  # Invalid dot placement

                        if '--' in email or '__' in email:
                            continue  # Suspicious patterns

                        # Validation 5: Check length constraints
                        if len(email) > 254 or len(local) > 64:
                            continue  # Exceeds RFC 5321 limits

                        # Valid email - add to findings
                        page_findings.append({'type': 'email', 'value': email, 'page': page_num + 1})

                    # ===== WEBSITES / URLs - COMPREHENSIVE DETECTION =====
                    websites_found = set()

                    # Pattern 1: URLs with protocol (http://, https://)
                    # REMOVED (duplicate): url_with_protocol_pattern = re.compile(
                    # REMOVED (duplicate): r'\b(https?://(?:www\.)?[a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+(?:/[^\s]*)?)\b',
                    # REMOVED (duplicate): re.IGNORECASE
                    # REMOVED (duplicate): )

                    # Pattern 2: URLs with www. (without protocol)
                    # REMOVED (duplicate): url_with_www_pattern = re.compile(
                    # REMOVED (duplicate): r'\b(www\.[a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+(?:/[^\s]*)?)\b',
                    # REMOVED (duplicate): re.IGNORECASE
                    # REMOVED (duplicate): )

                    # Pattern 3: Domain names (with common TLDs)
                    # REMOVED (duplicate): url_domain_pattern = re.compile(
                    # REMOVED (duplicate): r'\b([a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)*\.(?:com|org|net|edu|gov|io|co|ai|biz|info|us|uk|ca|au|de|fr|jp|cn))\b',
                    # REMOVED (duplicate): re.IGNORECASE
                    # REMOVED (duplicate): )

                    # Valid TLDs for website detection
                    valid_web_tlds = {
                        'com', 'org', 'net', 'edu', 'gov', 'mil', 'int',
                        'co', 'io', 'ai', 'biz', 'info', 'name', 'pro',
                        'uk', 'us', 'ca', 'au', 'de', 'fr', 'jp', 'cn', 'in', 'br',
                        'ru', 'nl', 'it', 'es', 'pl', 'se', 'ch', 'be', 'at', 'nz',
                        'kr', 'sg', 'hk', 'tw', 'mx', 'za', 'ae', 'il', 'th', 'my'
                    }

                    # URLs with protocol
                    for match in url_with_protocol_pattern.finditer(text):
                        url = match.group(1).strip()
                        # Clean trailing punctuation
                        url = re.sub(r'[.,;:)\]]+$', '', url)
                        if len(url) > 10:  # Minimum reasonable URL length
                            websites_found.add(url.lower())

                    # URLs with www
                    for match in url_with_www_pattern.finditer(text):
                        url = match.group(1).strip()
                        # Clean trailing punctuation
                        url = re.sub(r'[.,;:)\]]+$', '', url)
                        if len(url) > 7:  # www.x.y minimum
                            websites_found.add(url.lower())

                    # Domain names (more selective)
                    for match in url_domain_pattern.finditer(text):
                        domain = match.group(1).strip().lower()

                        # Validate TLD
                        tld = domain.split('.')[-1] if '.' in domain else ''
                        if tld not in valid_web_tlds:
                            continue

                        # Skip if it's just a common word + TLD (avoid false positives)
                        base_name = domain.split('.')[0]
                        if base_name in {'www', 'http', 'https', 'ftp', 'mail', 'email'}:
                            continue

                        # Must have at least one dot and reasonable length
                        if domain.count('.') >= 1 and len(domain) > 5:
                            # Check if it looks like a real domain (not a sentence fragment)
                            if not re.search(r'[^a-z0-9\.-]', domain):
                                websites_found.add(domain)

                    # Add all unique websites to findings
                    for website in websites_found:
                        page_findings.append({'type': 'website', 'value': website, 'page': page_num + 1})

                    # ===== PHONES - VERSION AMÉLIORÉE (US + International) =====
                    phones_found = set()
                    
                    # Pattern 1: Numéros US (format standard)
                    # REMOVED (duplicate): phone_us_pattern = re.compile(r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
                    for match in phone_us_pattern.finditer(text):
                        phone = match.group().strip()
                        cleaned = re.sub(r'[^\d]', '', phone)
                        if len(cleaned) == 10:
                            if PHONENUMBERS_AVAILABLE:
                                try:
                                    parsed = phonenumbers.parse(phone, "US")
                                    if phonenumbers.is_valid_number(parsed):
                                        formatted = phonenumbers.format_number(parsed, PhoneNumberFormat.NATIONAL)
                                        phones_found.add(formatted)
                                except Exception:
                                    # If parsing fails, add raw phone number
                                    phones_found.add(phone)
                            else:
                                phones_found.add(phone)
                    
                    # Pattern 2: Numéros internationaux avec indicatif pays (+XX ou 00XX)
                    # Format: +44 (0)20 7638 0129 ou +44 20 7638 0129 ou +1 555 123 4567
                    phone_international_patterns = [
                        # Format: +XX (0)XX XXXX XXXX (UK, etc.)
                        re.compile(r'\+\d{1,3}\s*\(?0\)?\s*\d{1,4}\s*\d{3,4}\s*\d{3,4}\b'),
                        # Format: +XX XX XXXX XXXX (standard international)
                        re.compile(r'\+\d{1,3}\s+\d{1,4}\s+\d{3,4}\s+\d{3,4}\b'),
                        # Format: +XX XXXXXXXXXX (sans espaces)
                        re.compile(r'\+\d{1,3}\s*\d{6,14}\b'),
                        # Format: 00XX XX XXXX XXXX (format européen avec 00)
                        re.compile(r'00\d{1,3}\s+\d{1,4}\s+\d{3,4}\s+\d{3,4}\b'),
                        # Format: (0)XX XXXX XXXX (UK local avec 0 optionnel)
                        re.compile(r'\(?0\)?\s*\d{2,4}\s+\d{3,4}\s+\d{3,4}\b'),
                    ]
                    
                    for pattern in phone_international_patterns:
                        for match in pattern.finditer(text):
                            phone = match.group().strip()
                            phone = re.sub(r'\s+', ' ', phone)  # Normaliser les espaces
                            
                            # Validation basique: doit avoir entre 7 et 15 chiffres (sans le +)
                            digits_only = re.sub(r'[^\d]', '', phone)
                            if 7 <= len(digits_only) <= 15:
                                # Vérifier le contexte pour éviter les faux positifs
                                context_start = max(0, match.start() - 50)
                                context_end = min(len(text), match.end() + 50)
                                context = text[context_start:context_end].lower()
                                
                                # Indicateurs positifs (suggèrent que c'est un numéro de téléphone)
                                positive_indicators = [
                                    'phone', 'tel', 'telephone', 'call', 'contact', 'mobile',
                                    'fax', 'telefax', 't:', 'p:', 'f:', 'm:'
                                ]
                                
                                # Indicateurs négatifs (exclure)
                                negative_indicators = [
                                    'file number', 'commission file', 'cik', 'ein',
                                    'employer identification', 'tax id', 'ssn'
                                ]
                                
                                has_positive = any(ind in context for ind in positive_indicators)
                                has_negative = any(ind in context for ind in negative_indicators)
                                
                                # Si phonenumbers est disponible, valider le numéro
                                if PHONENUMBERS_AVAILABLE:
                                    try:
                                        # Essayer de parser le numéro (peut être n'importe quel pays)
                                        parsed = phonenumbers.parse(phone, None)  # None = auto-detect country
                                        if phonenumbers.is_valid_number(parsed):
                                            # Formater en format international
                                            formatted = phonenumbers.format_number(parsed, PhoneNumberFormat.INTERNATIONAL)
                                            phones_found.add(formatted)
                                        elif has_positive and not has_negative:
                                            # Si le contexte est positif, accepter même si la validation échoue
                                            phones_found.add(phone)
                                    except Exception:
                                        # Si le parsing échoue mais que le contexte est positif, accepter
                                        if has_positive and not has_negative:
                                            phones_found.add(phone)
                                else:
                                    # Sans phonenumbers, accepter si contexte positif
                                    if has_positive and not has_negative:
                                        phones_found.add(phone)
                    
                    # Pattern 3: Numéros avec extensions (ex: +1 555 123 4567 ext. 123)
                    # REMOVED (duplicate): phone_with_ext_pattern = re.compile(
                    # REMOVED (duplicate): r'(\+?\d{1,3}[\s\-\(\)]?\d{1,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4})\s*(?:ext|extension|ext\.|x\.?|#)\s*(\d{1,6})',
                    # REMOVED (duplicate): re.IGNORECASE
                    # REMOVED (duplicate): )
                    
                    for match in phone_with_ext_pattern.finditer(text):
                        phone_base = match.group(1).strip()
                        extension = match.group(2).strip()
                        phone_with_ext = f"{phone_base} ext. {extension}"
                        
                        # Valider le numéro de base
                        digits_only = re.sub(r'[^\d]', '', phone_base)
                        if 7 <= len(digits_only) <= 15:
                            if PHONENUMBERS_AVAILABLE:
                                try:
                                    parsed = phonenumbers.parse(phone_base, None)
                                    if phonenumbers.is_valid_number(parsed):
                                        formatted_base = phonenumbers.format_number(parsed, PhoneNumberFormat.INTERNATIONAL)
                                        phones_found.add(f"{formatted_base} ext. {extension}")
                                except Exception:
                                    # If parsing fails, add raw phone with extension
                                    phones_found.add(phone_with_ext)
                            else:
                                phones_found.add(phone_with_ext)
                    
                    # Ajouter tous les numéros trouvés (with intelligent filtering)
                    for phone in phones_found:
                        # INTELLIGENT FILTER: Reject date-like patterns (e.g., "025 2024 2023")
                        # These are often table numbers containing years
                        year_pattern = re.search(r'\b(202[0-9]|201[0-9])\b', phone)
                        if year_pattern:
                            # Contains a year - likely a date or table reference, not a phone
                            continue
                        page_findings.append({'type': 'phone', 'value': phone, 'page': page_num + 1})
                    
                    # ===== ADDRESSES COMPLÈTES - VERSION ROBUSTE POUR PDF =====

                    addresses_found = set()

                    # États US (abréviations et noms complets)
                    valid_states_abbr = [
                        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
                    ]

                    # Mapping des noms complets vers abréviations
                    state_full_names = {
                        'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
                        'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
                        'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
                        'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
                        'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
                        'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
                        'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
                        'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
                        'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
                        'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
                        'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
                        'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
                        'wisconsin': 'WI', 'wyoming': 'WY', 'district of columbia': 'DC'
                    }

                    # ÉTAPE 1: Normaliser AGRESSIVEMENT le texte
                    # Remplacer TOUS les types d'espaces (nbsp, tabs, newlines) par un seul espace
                    text_clean = text.replace('\n', ' ')
                    text_clean = text_clean.replace('\r', ' ')
                    text_clean = text_clean.replace('\t', ' ')
                    text_clean = re.sub(r'\s+', ' ', text_clean)  # Multiple espaces -> 1 espace
                    text_clean = text_clean.strip()

                    # ÉTAPE 2: Pattern d'adresse complète AMÉLIORÉ
                    # Gère: directions (NE, NW), room/suite, townships, noms d'états complets

                    # Pattern 1: Avec abréviations d'état (OH, DC, etc.)
                    # Format flexible: gère les directions et Room/Suite à différentes positions
                    # Permet les noms de rue d'une seule lettre (A Street, F Street, etc.)
                    # REMOVED (duplicate): address_pattern_abbr = re.compile(
                    # REMOVED (duplicate): r'\b(\d{1,5})\s+'  # Numéro de rue
                    # REMOVED (duplicate): r'([A-Za-z](?:[A-Za-z\s\']{0,50})?)\s+'  # Nom de rue - PERMET 1 lettre seule (F Street, etc.)
                    # REMOVED (duplicate): r'(Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Boulevard|Blvd\.?|Lane|Ln\.?|Drive|Dr\.?|Court|Ct\.?|Place|Pl\.?|Way|Circle|Cir\.?|Parkway|Pkwy\.?|Highway|Hwy\.?)'  # Type de rue
                    # REMOVED (duplicate): r'(?:\s*,?\s*(NE|NW|SE|SW|N|S|E|W))?'  # Direction optionnelle après type de rue
                    # REMOVED (duplicate): r'(?:\s*,?\s*(?:Room|Suite|Ste\.?|Apt\.?|Unit|#)\s*[A-Z0-9\-]+)?'  # Room/Suite optionnel
                    # REMOVED (duplicate): r'\s*,?\s*'  # Virgules/espaces flexibles
                    # REMOVED (duplicate): r'([A-Za-z][A-Za-z\s]{2,50}?)'  # Ville/Township (flexible)
                    # REMOVED (duplicate): r'\s*,?\s+'  # Virgules/espaces avant état
                    # REMOVED (duplicate): r'([A-Z]{2})\s+'  # État (abréviation 2 lettres)
                    # REMOVED (duplicate): r'(\d{5}(?:-\d{4})?)\b',  # ZIP code
                    # REMOVED (duplicate): re.IGNORECASE
                    # REMOVED (duplicate): )

                    # Pattern 2: Avec noms d'états complets (Ohio, Washington, etc.)
                    # Permet les noms de rue d'une seule lettre (A Street, F Street, etc.)
                    # REMOVED (duplicate): address_pattern_full = re.compile(
                    # REMOVED (duplicate): r'\b(\d{1,5})\s+'  # Numéro de rue
                    # REMOVED (duplicate): r'([A-Za-z](?:[A-Za-z\s\']{0,50})?)\s+'  # Nom de rue - PERMET 1 lettre seule (F Street, etc.)
                    # REMOVED (duplicate): r'(Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Boulevard|Blvd\.?|Lane|Ln\.?|Drive|Dr\.?|Court|Ct\.?|Place|Pl\.?|Way|Circle|Cir\.?|Parkway|Pkwy\.?|Highway|Hwy\.?)'  # Type de rue
                    # REMOVED (duplicate): r'(?:\s*,?\s*(NE|NW|SE|SW|N|S|E|W))?'  # Direction optionnelle
                    # REMOVED (duplicate): r'(?:\s*,?\s*(?:Room|Suite|Ste\.?|Apt\.?|Unit|#)\s*[A-Z0-9\-]+)?'  # Room/Suite optionnel
                    # REMOVED (duplicate): r'\s*,?\s*'  # Virgules/espaces flexibles
                    # REMOVED (duplicate): r'([A-Za-z][A-Za-z\s]{2,50}?)'  # Ville/Township (flexible)
                    # REMOVED (duplicate): r'\s*,?\s+'  # Virgules/espaces avant état
                    # REMOVED (duplicate): r'(Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|'
                    # REMOVED (duplicate): r'Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|'
                    # REMOVED (duplicate): r'Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New\s+Hampshire|New\s+Jersey|'
                    # REMOVED (duplicate): r'New\s+Mexico|New\s+York|North\s+Carolina|North\s+Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|'
                    # REMOVED (duplicate): r'Rhode\s+Island|South\s+Carolina|South\s+Dakota|Tennessee|Texas|Utah|Vermont|Virginia|'
                    # REMOVED (duplicate): r'Washington|West\s+Virginia|Wisconsin|Wyoming|District\s+of\s+Columbia)\s+'  # État (nom complet)
                    # REMOVED (duplicate): r'(\d{5}(?:-\d{4})?)\b',  # ZIP code
                    # REMOVED (duplicate): re.IGNORECASE
                    # REMOVED (duplicate): )

                    # Traiter le pattern avec abréviations d'état
                    for match in address_pattern_abbr.finditer(text_clean):
                        street_num = match.group(1)
                        street_name = match.group(2).strip()
                        street_type = match.group(3)
                        direction = match.group(4).strip() if match.group(4) else ''
                        city = match.group(5).strip()
                        state = match.group(6).upper()
                        zip_code = match.group(7)

                        # Validation de l'état
                        if state not in valid_states_abbr:
                            continue

                        # Nettoyer le nom de rue
                        street_name = re.sub(r'\s+', ' ', street_name).strip()

                        # Nettoyer la ville - garder seulement les mots capitalisés et "Township"
                        city_words = city.split()
                        city_clean_parts = []
                        for word in city_words:
                            if word and len(word) > 1:
                                # Garder les mots capitalisés ou "Township"
                                if word[0].isupper() or word.lower() in ['township', 'city', 'village']:
                                    city_clean_parts.append(word)

                        if not city_clean_parts:
                            continue

                        city_clean = ' '.join(city_clean_parts)

                        # Construire l'adresse avec direction si présente
                        if direction:
                            address = f"{street_num} {street_name} {street_type}, {direction}, {city_clean}, {state} {zip_code}"
                        else:
                            address = f"{street_num} {street_name} {street_type}, {city_clean}, {state} {zip_code}"

                        # Validation de longueur
                        if not (20 <= len(address) <= 200):
                            continue

                        # Filtrer les faux positifs évidents (mais GARDER Washington DC)
                        address_upper = address.upper()
                        bad_keywords = [
                            'COMMISSION FILE', 'SECURITIES ACT', 'EXCHANGE ACT',
                            'TABLE OF CONTENTS', 'WALL STREET', 'BALANCE SHEET'
                        ]

                        if any(bad in address_upper for bad in bad_keywords):
                            continue

                        addresses_found.add(address)

                    # Traiter le pattern avec noms d'états complets (Ohio, Washington, etc.)
                    for match in address_pattern_full.finditer(text_clean):
                        street_num = match.group(1)
                        street_name = match.group(2).strip()
                        street_type = match.group(3)
                        direction = match.group(4).strip() if match.group(4) else ''
                        city = match.group(5).strip()
                        state_full = match.group(6).strip()
                        zip_code = match.group(7)

                        # Convertir le nom d'état complet en abréviation
                        state = state_full_names.get(state_full.lower(), state_full[:2].upper())

                        # Nettoyer le nom de rue
                        street_name = re.sub(r'\s+', ' ', street_name).strip()

                        # Nettoyer la ville
                        city_words = city.split()
                        city_clean_parts = []
                        for word in city_words:
                            if word and len(word) > 1:
                                if word[0].isupper() or word.lower() in ['township', 'city', 'village']:
                                    city_clean_parts.append(word)

                        if not city_clean_parts:
                            continue

                        city_clean = ' '.join(city_clean_parts)

                        # Construire l'adresse
                        if direction:
                            address = f"{street_num} {street_name} {street_type}, {direction}, {city_clean}, {state} {zip_code}"
                        else:
                            address = f"{street_num} {street_name} {street_type}, {city_clean}, {state} {zip_code}"

                        # Validation de longueur
                        if not (20 <= len(address) <= 200):
                            continue

                        # Filtrer les faux positifs
                        address_upper = address.upper()
                        bad_keywords = [
                            'COMMISSION FILE', 'SECURITIES ACT', 'EXCHANGE ACT',
                            'TABLE OF CONTENTS', 'WALL STREET', 'BALANCE SHEET'
                        ]

                        if any(bad in address_upper for bad in bad_keywords):
                            continue

                        addresses_found.add(address)
                    
                    # Si le pattern direct ne trouve rien, essayer la méthode inverse (ZIP d'abord)
                    if not addresses_found:
                    # REMOVED (duplicate): zip_pattern = re.compile(r'\b(\d{5}(?:-\d{4})?)\b')
                        
                        for zip_match in zip_pattern.finditer(text_clean):
                            zip_code = zip_match.group(1)
                            zip_pos = zip_match.start()
                            
                            # Prendre 250 caractères AVANT le ZIP
                            context_before = text_clean[max(0, zip_pos - 250):zip_pos]
                            
                            # Chercher : "Numéro Nom Type Ville, État"
                            # Pattern inverse plus flexible
                            # DUPLICATE: inverse_pattern = re.compile(
                                # DUPLICATE: r'(\d{1,5})\s+'
                                # DUPLICATE: r'([A-Za-z\s]{3,50}?)\s+'
                                # DUPLICATE: r'(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl|Way|Circle|Cir|Parkway|Pkwy|Highway|Hwy)'
                                # DUPLICATE: r'\s+([A-Za-z\s]{3,40}?)[,\s]+'
                                # DUPLICATE: r'([A-Z]{2})\s*$',
                                # DUPLICATE: re.IGNORECASE
                            # DUPLICATE: )
                            
                            addr_match = inverse_pattern.search(context_before)
                            
                            if addr_match and addr_match.group(5) in valid_states_abbr:
                                street_num = addr_match.group(1)
                                street_name = addr_match.group(2).strip()
                                street_type = addr_match.group(3)
                                city = addr_match.group(4).strip()
                                state = addr_match.group(5)
                                
                                # Nettoyer
                                street_name = re.sub(r'\s+', ' ', street_name).strip()
                                city_words = city.split()
                                city_clean = ' '.join([w for w in city_words if w and w[0].isupper()])
                                
                                if city_clean:
                                    address = f"{street_num} {street_name} {street_type} {city_clean} {state} {zip_code}"
                                    
                                    if 25 <= len(address) <= 150:
                                        if 'WASHINGTON' not in address.upper():
                                            addresses_found.add(address)
                    
                    for address in addresses_found:
                        page_findings.append({'type': 'address', 'value': address, 'page': page_num + 1})
                    
                    # ===== SSN =====
                    # REMOVED (duplicate): ssn_pattern = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
                    for match in ssn_pattern.finditer(text):
                        ssn = match.group().strip()
                        page_findings.append({'type': 'ssn', 'value': ssn, 'page': page_num + 1})
                    
                    # ===== CREDIT CARDS =====
                    # DÉSACTIVÉ - Ne plus détecter les cartes de crédit
                    # credit_card_pattern = re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b')
                    # for match in credit_card_pattern.finditer(text):
                    #     cc = match.group().strip()
                    #     page_findings.append({'type': 'credit_card', 'value': cc, 'page': page_num + 1})
                    
                    # ===== COMPANY IDENTIFICATION =====
                    # 🔧 Chercher d'abord les Commission File Numbers de manière explicite
                    commission_numbers_found = set()
                    # REMOVED (duplicate): cfn_context_pattern = re.compile(r'Commission\s+File\s+Number[:\s]+(\d{3}-\d{5})', re.IGNORECASE)
                    for match in cfn_context_pattern.finditer(text):
                        commission_numbers_found.add(match.group(1))
                        page_findings.append({'type': 'commission_file_number', 'value': match.group(1), 'page': page_num + 1})
                    
                    # 🔧 IRS Employer Identification Numbers (EIN): XX-XXXXXXX
                    # Pattern compiled before loop (line 234)
                    for match in ein_pattern.finditer(text):
                        ein = match.group(1)
                        # Vérifier le contexte pour confirmer que c'est un EIN
                        context = text[max(0, match.start() - 60):match.end() + 60]
                        is_ein_context = bool(re.search(r'(?:I\.?R\.?S\.?|Employer\s+Identification|EIN|Tax\s+ID)', context, re.IGNORECASE))
                        
                        if is_ein_context:
                            page_findings.append({'type': 'irs_ein', 'value': ein, 'page': page_num + 1})
                    
                    # ===== EXECUTIVE NAMES - VERSION AMÉLIORÉE =====
                    # DÉSACTIVÉ - Ne plus détecter les noms d'exécutifs
                    executives_found = set()
                    
                    # Liste étendue de titres exécutifs
                    executive_titles = [
                        r'Chief\s+(?:Executive|Financial|Operating|Technology|Information|Marketing|Revenue|Accounting|Legal|Compliance|Risk|Investment)\s+Officer',
                        r'CEO|CFO|CTO|COO|CIO|CMO|CRO|CAO|CLO|CCO|CRO',
                        r'President',
                        r'Vice\s+President',
                        r'VP\s+(?:of|Finance|Operations|Sales|Marketing|Engineering)',
                        r'Executive\s+Vice\s+President',
                        r'EVP',
                        r'Senior\s+Vice\s+President',
                        r'SVP',
                        r'Chairman',
                        r'Chairman\s+of\s+the\s+Board',
                        r'Vice\s+Chairman',
                        r'Secretary',
                        r'Treasurer',
                        r'Controller',
                        r'Chief\s+Controller',
                        r'Managing\s+Director',
                        r'General\s+Manager',
                        r'Director',
                        r'Executive\s+Director',
                        r'Founder',
                        r'Co-Founder',
                        r'Chief\s+of\s+Staff',
                        r'Head\s+of\s+(?:Finance|Operations|Sales|Marketing|Engineering|Legal)',
                    ]
                    
                    # Pattern 1: Signatures "/s/" ou "/s" ou "s/"
                    signature_patterns = [
                        re.compile(r'/s[/\s]+\s*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', re.IGNORECASE),
                        re.compile(r'Signature:\s*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', re.IGNORECASE),
                        re.compile(r'Signed:\s*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', re.IGNORECASE),
                    ]
                    
                    for pattern in signature_patterns:
                        for match in pattern.finditer(text):
                            name = match.group(1).strip()
                            name = re.sub(r'\s+', ' ', name)
                            if 5 <= len(name) <= 50:
                                executives_found.add(name)
                    
                    # Pattern 2: Format "Nom, Titre" (amélioré)
                    exec_title_pattern = '|'.join(executive_titles)
                    # DUPLICATE: exec_pattern = re.compile(
                        # DUPLICATE: r'\b([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[,:]\s*(' + exec_title_pattern + r')\b',
                        # DUPLICATE: re.IGNORECASE
                    # DUPLICATE: )
                    
                    for match in exec_pattern.finditer(text):
                        name = match.group(1).strip()
                        name = re.sub(r'\s+', ' ', name)
                        
                        if 5 <= len(name) <= 50:
                            name_upper = name.upper()
                            false_positives = [
                                'UNITED STATES', 'NEW YORK', 'LOS ANGELES', 'THE COMPANY',
                                'BALANCE SHEET', 'CASH FLOW', 'INCOME TAX', 'STOCK OPTION',
                                'SECURITIES AND EXCHANGE', 'COMMISSION', 'WASHINGTON'
                            ]
                            if name_upper not in false_positives:
                                executives_found.add(name)
                    
                    # Pattern 3: Format "Titre: Nom" ou "Titre Nom"
                    exec_pattern_reverse = re.compile(
                        r'\b(' + exec_title_pattern + r')\s*[:]\s*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
                        re.IGNORECASE
                    )
                    
                    for match in exec_pattern_reverse.finditer(text):
                        name = match.group(2).strip()
                        name = re.sub(r'\s+', ' ', name)
                        
                        if 5 <= len(name) <= 50:
                            name_upper = name.upper()
                            false_positives = [
                                'UNITED STATES', 'NEW YORK', 'LOS ANGELES', 'THE COMPANY',
                                'BALANCE SHEET', 'CASH FLOW', 'INCOME TAX', 'STOCK OPTION'
                            ]
                            if name_upper not in false_positives:
                                executives_found.add(name)
                    
                    # Pattern 4: Sections de signatures avec contexte étendu
                    name_context_patterns = [
                        re.compile(r'(?:By|Name|Signed\s+By|Signature\s+of|Name\s+of\s+Officer|Name\s+of\s+Signatory)[:\s]+([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', re.IGNORECASE),
                        re.compile(r'(?:Officer|Executive|Director)[:\s]+([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', re.IGNORECASE),
                    ]
                    
                    for pattern in name_context_patterns:
                        for match in pattern.finditer(text):
                            name = match.group(1).strip()
                            name = re.sub(r'\s+', ' ', name)

                            if 5 <= len(name) <= 50:
                                # Vérifier le contexte pour éviter les faux positifs
                                context_start = max(0, match.start() - 100)
                                context_end = min(len(text), match.end() + 100)
                                context = text[context_start:context_end].lower()

                                # Éviter les contextes non pertinents
                                bad_contexts = ['table of contents', 'index', 'appendix', 'reference']
                                if not any(bad in context for bad in bad_contexts):
                                    executives_found.add(name)
                    
                    # Pattern 5: Noms dans les tableaux/listes (format "Nom | Titre" ou "Nom - Titre")
                    table_patterns = [
                        re.compile(r'([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[|\-]\s*(' + exec_title_pattern + r')\b', re.IGNORECASE),
                        re.compile(r'([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(' + exec_title_pattern + r')\b', re.IGNORECASE),
                    ]
                    
                    for pattern in table_patterns:
                        for match in pattern.finditer(text):
                            name = match.group(1).strip()
                            name = re.sub(r'\s+', ' ', name)
                            
                            if 5 <= len(name) <= 50:
                                name_upper = name.upper()
                                false_positives = [
                                    'UNITED STATES', 'NEW YORK', 'LOS ANGELES', 'THE COMPANY',
                                    'BALANCE SHEET', 'CASH FLOW', 'INCOME TAX', 'STOCK OPTION'
                                ]
                                if name_upper not in false_positives:
                                    executives_found.add(name)
                    
                    # Pattern 6: Noms dans les sections "Officers" ou "Management"
                    # DUPLICATE: officers_section_pattern = re.compile(
                        # DUPLICATE: r'(?:Officers?|Management|Executive\s+Officers?|Key\s+Personnel)[\s\S]{0,500}?'
                        # DUPLICATE: r'([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[,:]\s*(' + exec_title_pattern + r')\b',
                        # DUPLICATE: re.IGNORECASE | re.MULTILINE
                    # DUPLICATE: )
                    
                    for match in officers_section_pattern.finditer(text):
                        name = match.group(1).strip()
                        name = re.sub(r'\s+', ' ', name)
                        
                        if 5 <= len(name) <= 50:
                            name_upper = name.upper()
                            false_positives = [
                                'UNITED STATES', 'NEW YORK', 'LOS ANGELES', 'THE COMPANY',
                                'BALANCE SHEET', 'CASH FLOW', 'INCOME TAX', 'STOCK OPTION'
                            ]
                            if name_upper not in false_positives:
                                executives_found.add(name)
                    
                    # Nettoyer et valider les noms trouvés avec filtres stricts
                    cleaned_executives = set()
                    
                    # Mots à exclure des noms d'executives
                    excluded_exec_words = {
                        'and', 'or', 'the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for',
                        'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be', 'been',
                        'vantiv', 'in', 'to', 'with', 'the', 'an', 'independent', 'and',
                        'secretary', 'be', 'the', 'executive', 'lead', 'check', 'mark',
                        'whether', 'purport', 'exempt', 'principal', 'traders', 'merchants',
                        'later', 'than', 'registrant', 'combined', 'filings', 'security',
                        'holdings', 'team', 'reporting', 'high', 'court', 'incremental',
                        'amendment', 'affirmative', 'vote', 'fact', 'offeree', 'company',
                        'undersigned', 'hereunto', 'title', 'officer', 'director', 'chairman',
                        'co', 'services', 'officer', 'and', 'nelson', 'f', 'greene', 'title',
                        'philip', 'jansen', 'and', 'stephanie', 'ferris'
                    }
                    
                    for exec_name in executives_found:
                        # Nettoyer les espaces multiples
                        exec_name = re.sub(r'\s+', ' ', exec_name).strip()
                        
                        # Validation: doit avoir au moins 2 mots (prénom + nom)
                        words = exec_name.split()
                        if len(words) >= 2 and len(words) <= 5:
                            # Vérifier que chaque mot fait sens (pas trop court, pas trop long)
                            if all(2 <= len(w) <= 20 for w in words):
                                # FILTRE STRICT: Exclure si contient des mots interdits
                                words_lower = [w.lower().rstrip('.,;:') for w in words]
                                
                                # Ne pas accepter si un mot est dans la liste des mots exclus
                                if any(w in excluded_exec_words for w in words_lower):
                                    continue
                                
                                # Ne pas accepter si le nom contient des mots de liaison
                                if any(w in ['and', 'or', 'the', 'of', 'in', 'to', 'with', 'an', 'a'] for w in words_lower):
                                    continue
                                
                                # Vérifier qu'il n'y a pas trop de majuscules (éviter les acronymes)
                                if sum(1 for c in exec_name if c.isupper()) <= len(exec_name) * 0.4:
                                    # Éviter les faux positifs spécifiques
                                    exec_name_upper = exec_name.upper()
                                    false_positives_exec = [
                                        'VANTIV IN', 'VANTIV TO', 'VANTIV WITH THE',
                                        'AN INDEPENDENT', 'AND SECRETARY', 'AND AMONG VANTIV',
                                        'ANY OFFEROR AND', 'ANY PERSONS ACTING', 'BE THE EXECUTIVE',
                                        'BE THE LEAD', 'CHECK MARK IF', 'CHECK MARK WHETHER',
                                        'DO NOT PURPORT', 'EXEMPT PRINCIPAL TRADERS', 'MEANS OF',
                                        'MERCHANTS OR', 'NO LATER THAN', 'OF REGISTRANT AS',
                                        'OF THE COMBINED', 'ON THE COMBINED', 'OTHER VANTIV FILINGS',
                                        'SECURITY HOLDINGS OR', 'TEAM REPORTING TO', 'THE HIGH COURT',
                                        'THE INCREMENTAL AMENDMENT', 'THE AFFIRMATIVE VOTE',
                                        'THE FACT THAT', 'THE OFFEREE COMPANY', 'THE UNDERSIGNED HEREUNTO',
                                        'CHAIRMAN AND CO', 'NELSON F. GREENE TITLE', 'OFFICER PHILIP JANSEN',
                                        'OFFICER OF', 'PHILIP JANSEN AND', 'SERVICES OFFICER AND'
                                    ]
                                    if not any(fp in exec_name_upper for fp in false_positives_exec):
                                        # Vérifier que le nom ne se termine pas par des mots suspects
                                        last_word = words_lower[-1]
                                        if last_word not in ['and', 'or', 'the', 'of', 'in', 'to', 'with', 'co', 'title', 'officer', 'director', 'chairman']:
                                            # Validation finale: le nom doit ressembler à un vrai nom
                                            if len(set(words_lower)) == len(words_lower):  # Pas de mots dupliqués
                                                cleaned_executives.add(exec_name)
                    
                    # Validation finale avec spaCy NER pour executives (OPTIONNELLE - pas obligatoire)
                    # Ne valide QUE si spaCy trouve des noms - sinon garde tous les noms détectés
                    if SPACY_AVAILABLE and SPACY_NLP and cleaned_executives:
                        validated_executives = set()

                        for exec_name in cleaned_executives:
                            # Chercher le nom dans le texte original avec contexte
                            name_pos = text.find(exec_name)
                            if name_pos != -1:
                                context_start = max(0, name_pos - 150)
                                context_end = min(len(text), name_pos + len(exec_name) + 150)
                                context_text = text[context_start:context_end]

                                # Analyser avec spaCy
                                try:
                                    doc = SPACY_NLP(context_text)

                                    # Vérifier si spaCy détecte ce nom comme une personne
                                    for ent in doc.ents:
                                        if ent.label_ == "PERSON":
                                            detected_name = ent.text.strip()
                                            detected_name = re.sub(r'\s+', ' ', detected_name)

                                            # Vérifier si notre nom correspond
                                            if exec_name.lower() in detected_name.lower() or detected_name.lower() in exec_name.lower():
                                                validated_executives.add(exec_name)
                                                break
                                except Exception:
                                    # Si spaCy échoue, accepter le nom quand même
                                    validated_executives.add(exec_name)

                        # Si spaCy a validé des noms, utiliser ceux-là
                        # Sinon, GARDER TOUS les noms détectés (pas de filtrage)
                        if validated_executives:
                            cleaned_executives = validated_executives
                        # Si rien validé par spaCy, on garde cleaned_executives tel quel

                    # RÉACTIVÉ - Ajouter les noms d'exécutifs aux résultats
                    for exec_name in cleaned_executives:
                        # === ULTRA-STRICT VALIDATION (same as person names) ===
                        exec_words = exec_name.split()
                        exec_words_lower = [w.lower().strip('.,;:') for w in exec_words]
                        exec_lower = exec_name.lower()

                        # REJECT: Gerund phrases
                        if exec_words_lower and exec_words_lower[0].endswith('ing'):
                            continue

                        # REJECT: Possessive phrases
                        if any(w in {'our', 'his', 'her', 'its', 'their', 'your', 'my'} for w in exec_words_lower):
                            continue

                        # REJECT: Job titles without names
                        if exec_lower in {'senior vice', 'vice president', 'chief executive', 'chief financial',
                                         'chief operating', 'executive chairman', 'lead director',
                                         'audit compensation', 'audit compensation nominating'}:
                            continue

                        # REJECT: Business/document terms
                        if exec_lower in {'grant date fair', 'grant date number', 'grant date threshold',
                                         'total award grant', 'stock ownership guidelines', 'severance plan',
                                         'period total less', 'name age position', 'year tra liability',
                                         'exchange act rule', 'delaware law', 'compensation decisions',
                                         'compensation plans', 'compensation program', 'compensation programs',
                                         'director compensation', 'outstanding awards under'}:
                            continue

                        # REJECT: Activity phrases
                        if exec_lower in {'financing activities', 'investing activities', 'operating activities',
                                         'entering into', 'exposing us', 'enabling us', 'converting floating',
                                         'utilizing direct sales', 'using long', 'exercising its put',
                                         'dividing net income', 'reducing our ability', 'processing electronic payment',
                                         'adding cardtronics', 'advise our corporate', 'appoints charles drucker',
                                         'parties claiming ownership', 'persons offering consumer'}:
                            continue

                        # REJECT: Company references
                        if exec_lower in {'fifth third', 'fifth third bancorp', 'fifth third bank',
                                         'advent international corporation', 'blackrock', 'jpmorgan chase',
                                         'matthew taylor group'}:
                            continue

                        # REJECT: Common verbs at start
                        if exec_words_lower and exec_words_lower[0] in {'adding', 'advise', 'appoints', 'comparing',
                                                                        'contacting', 'converting', 'discussed', 'dividing',
                                                                        'enabling', 'entering', 'exercising', 'exposing',
                                                                        'financing', 'investing', 'operating', 'processing',
                                                                        'reducing', 'reviewing', 'since', 'stockholders',
                                                                        'using', 'utilizing'}:
                            continue

                        # REJECT: Generic business phrases
                        if exec_lower in {'business segment', 'customer incentives', 'merchant category',
                                         'payment networks', 'transaction volume', 'meetings per year',
                                         'merchant acquiring entities', 'numerous laws', 'one stockholder',
                                         'two different persons', 'written consent', 'virtue hereof',
                                         'your bank', 'since november', 'discussed above', 'formal policy regarding',
                                         'general economic conditions', 'rapid technological change',
                                         'registration statement number', 'regulatory guidelines'}:
                            continue

                        # Original validation (as backup)
                        has_invalid_word = any(w in INVALID_NAME_WORDS for w in exec_words_lower)

                        # DÉSACTIVÉ - Executive name detection disabled (too many false positives)
                        # if (exec_lower not in PERSON_NAME_FALSE_POSITIVES and
                        #     exec_lower not in DOCUMENT_STRUCTURE_TERMS and
                        #     not has_invalid_word):
                        #     page_findings.append({'type': 'executive_name', 'value': exec_name, 'page': page_num + 1})
                        pass  # Executive name detection disabled
                    
                    # ===== TOUS LES NOMS DE PERSONNES (pas seulement executives) =====
                    all_person_names_found = set()

                    # ========== MÉTHODE 1 (PRINCIPALE) : spaCy NER ==========
                    # spaCy est beaucoup plus intelligent que les regex pour détecter les noms
                    # Il comprend le contexte et a été entraîné sur des millions d'exemples

                    spacy_detection_count = 0
                    if SPACY_AVAILABLE and SPACY_NLP:
                        try:
                            # Découper le texte en chunks pour éviter les problèmes de mémoire
                            max_chunk_size = 100000  # 100k characters max par chunk
                            text_chunks = []

                            if len(text) > max_chunk_size:
                                # Découper en chunks de taille raisonnable
                                for i in range(0, len(text), max_chunk_size):
                                    text_chunks.append(text[i:i + max_chunk_size])
                            else:
                                text_chunks = [text]

                            # Traiter chaque chunk avec spaCy
                            for chunk in text_chunks:
                                try:
                                    doc = SPACY_NLP(chunk)

                                    # Extraire TOUTES les entités PERSON détectées par spaCy
                                    for ent in doc.ents:
                                        if ent.label_ == "PERSON":
                                            person_name = ent.text.strip()
                                            person_name = re.sub(r'\s+', ' ', person_name)

                                            # Validation basique
                                            if 3 <= len(person_name) <= 50:
                                                words = person_name.split()
                                                # Au moins 2 mots pour un nom complet (prénom + nom)
                                                if len(words) >= 2 and len(words) <= 5:
                                                    # ACCEPT - spaCy is already accurate
                                                    all_person_names_found.add(person_name)
                                                    spacy_detection_count += 1
                                except Exception as e:
                                    # Si un chunk échoue, continuer avec le suivant
                                    logger.debug(f"spaCy chunk processing failed: {e}")
                                    continue

                            if verbose and spacy_detection_count > 0:
                                logger.info(f"   ✅ spaCy NER detected {spacy_detection_count} person names")

                        except Exception as e:
                            logger.debug(f"spaCy NER failed: {e}")
                            # Si spaCy échoue complètement, on continuera avec les regex

                    else:
                        # spaCy non disponible - informer l'utilisateur en mode verbose
                        if verbose:
                            logger.warning("   ⚠️  spaCy NER not available - using regex fallback (lower accuracy)")
                            logger.info("   💡 Install spaCy for better person name detection:")
                            logger.info("      pip install spacy")
                            logger.info("      python -m spacy download en_core_web_sm")

                    # ========== MÉTHODE 2 (COMPLÉMENTAIRE) : Regex patterns ==========
                    # Les regex capturent les cas spécifiques que spaCy pourrait rater :
                    # - Signatures (/s/ John Smith)
                    # - Listes formatées (Smith, John)
                    # - Contextes professionnels explicites (Director: John Smith)

                    # Pattern 1: Noms dans les contextes de personnes (directors, officers, employees, etc.)
                    person_context_patterns = [
                        re.compile(
                            r'(?:Director|Officer|Employee|Trustee|Beneficial\s+Owner|Shareholder|Stockholder|Member|Partner|Principal|Agent|Representative|Signatory|Authorized\s+Signatory)[:\s]+([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                            re.IGNORECASE
                        ),
                        re.compile(
                            r'(?:Name|Person|Individual|Contact)[:\s]+([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                            re.IGNORECASE
                        ),
                    ]

                    for pattern in person_context_patterns:
                        for match in pattern.finditer(text):
                            name = match.group(1).strip()
                            name = re.sub(r'\s+', ' ', name)

                            if 5 <= len(name) <= 50:
                                words = name.split()
                                if len(words) >= 2 and len(words) <= 5:
                                    all_person_names_found.add(name)
                    
                    # Pattern 2: Noms dans les listes/tableaux (format "Nom, Prénom" ou "Prénom Nom")
                    # Détecter les patterns de noms propres typiques
                    name_list_patterns = [
                        # Format "Nom, Prénom" (nom de famille en premier)
                        re.compile(
                            r'\b([A-Z][a-z]+),\s+([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)\b'
                        ),
                        # Format "Prénom Nom" (prénom en premier)
                        re.compile(
                            r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)\b'
                        ),
                    ]
                    
                    for pattern in name_list_patterns:
                        for match in pattern.finditer(text):
                            if len(match.groups()) == 2:
                                part1, part2 = match.groups()
                                # Construire le nom complet
                                if ',' in match.group(0):
                                    # Format "Nom, Prénom" -> "Prénom Nom"
                                    full_name = f"{part2} {part1}"
                                else:
                                    # Format "Prénom Nom"
                                    full_name = f"{part1} {part2}"
                                
                                full_name = re.sub(r'\s+', ' ', full_name).strip()
                                
                                # Validation
                                if 5 <= len(full_name) <= 50:
                                    words = full_name.split()
                                    if len(words) >= 2 and len(words) <= 5:
                                        # Vérifier que chaque mot commence par une majuscule
                                        if all(w[0].isupper() for w in words if len(w) > 1):
                                            # Vérifier le contexte pour éviter les faux positifs
                                            context_start = max(0, match.start() - 100)
                                            context_end = min(len(text), match.end() + 100)
                                            context = text[context_start:context_end].lower()
                                            
                                            # Éviter les contextes non pertinents
                                            bad_contexts = [
                                                'table of contents', 'index', 'appendix', 'reference',
                                                'balance sheet', 'income statement', 'cash flow',
                                                'note', 'footnote', 'exhibit', 'schedule',
                                                'form 10-k', 'form 10-q', 'form 8-k',
                                                'part i', 'part ii', 'part iii', 'part iv'
                                            ]

                                            # Chercher des indicateurs positifs (REQUIRED - not optional)
                                            good_indicators = [
                                                'director', 'officer', 'employee', 'trustee',
                                                'shareholder', 'beneficial owner', 'signatory',
                                                'authorized', 'representative', 'agent',
                                                'management', 'board', 'committee', 'team',
                                                'signed', 'by:', 'name:', '/s/'
                                            ]

                                            has_good_indicator = any(ind in context for ind in good_indicators)
                                            has_bad_context = any(bad in context for bad in bad_contexts)

                                            # Check against false positives (EXACT MATCH ONLY)
                                            full_name_lower = full_name.lower()
                                            is_false_positive = (
                                                full_name_lower in PERSON_NAME_FALSE_POSITIVES or
                                                full_name_lower in DOCUMENT_STRUCTURE_TERMS
                                                # Don't check partial matches - too aggressive
                                            )

                                            # RELAXED: Accept if (has indicator OR no bad context) AND not false positive
                                            # This allows names in signature sections even without explicit indicators
                                            if not is_false_positive and not has_bad_context:
                                                # Check that no word in the name is an invalid word
                                                words_lower = [w.lower().strip('.,;:') for w in words]
                                                has_invalid_word = any(w in INVALID_NAME_WORDS for w in words_lower)

                                                if not has_invalid_word:
                                                    # Additional validation: check capitalization pattern
                                                    # Reject all-caps or names with too many capitals
                                                    cap_ratio = sum(1 for c in full_name if c.isupper()) / len(full_name)
                                                    if cap_ratio <= 0.5:  # Max 50% capitals (allows for initials)
                                                        # If no good indicator, require at least 2 words (first + last name)
                                                        if has_good_indicator or len(words) >= 2:
                                                            all_person_names_found.add(full_name)
                    
                    # Pattern 3: Noms dans les sections de signatures et certifications
                    signature_section_patterns = [
                        re.compile(
                            r'(?:Signed|Certified|Attested|Witnessed|Notarized)[\s\S]{0,200}?([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                            re.IGNORECASE | re.MULTILINE
                        ),
                        re.compile(
                            r'(?:By|Name\s+of|Signature\s+of)[:\s]+([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                            re.IGNORECASE
                        ),
                    ]
                    
                    for pattern in signature_section_patterns:
                        for match in pattern.finditer(text):
                            name = match.group(1).strip()
                            name = re.sub(r'\s+', ' ', name)
                            
                            if 5 <= len(name) <= 50:
                                words = name.split()
                                if len(words) >= 2 and len(words) <= 5:
                                    # Vérifier que ce n'est pas déjà dans les executives
                                    if name not in cleaned_executives:
                                        all_person_names_found.add(name)
                    
                    # Pattern 4: Noms dans les tableaux de personnes (format tabulaire)
                    # Chercher des lignes qui ressemblent à des noms dans des contextes de personnes
                    # Format: "Nom | Titre | Autre info" ou "Nom - Titre"
                    table_name_patterns = [
                        re.compile(
                            r'([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[|\-]\s*[A-Z]',
                            re.MULTILINE
                        ),
                    ]
                    
                    for pattern in table_name_patterns:
                        for match in pattern.finditer(text):
                            name = match.group(1).strip()
                            name = re.sub(r'\s+', ' ', name)
                            
                            if 5 <= len(name) <= 50:
                                words = name.split()
                                if len(words) >= 2 and len(words) <= 5:
                                    # Vérifier le contexte
                                    context_start = max(0, match.start() - 150)
                                    context_end = min(len(text), match.end() + 150)
                                    context = text[context_start:context_end].lower()
                                    
                                    # Chercher des indicateurs de tableau de personnes
                                    person_table_indicators = [
                                        'director', 'officer', 'executive', 'management',
                                        'board', 'committee', 'trustee', 'beneficial owner',
                                        'shareholder', 'stockholder', 'employee', 'personnel'
                                    ]
                                    
                                    if any(ind in context for ind in person_table_indicators):
                                        if name not in cleaned_executives:
                                            all_person_names_found.add(name)
                    
                    # Pattern 5: Noms dans les emails (avant @)
                    # Les emails contiennent souvent des noms
                    # VALIDATION: Rejeter les prefixes techniques (admin, support, info, etc.)
                    # DUPLICATE: email_name_pattern = re.compile(r'\b([a-z]+\.?[a-z]+)\.([a-z]+)@', re.IGNORECASE)
                    for match in email_name_pattern.finditer(text):
                        first_part = match.group(1).capitalize()
                        second_part = match.group(2).capitalize()
                        potential_name = f"{first_part} {second_part}"

                        if 5 <= len(potential_name) <= 30:
                            # Vérifier que ça ressemble à un nom (pas un mot technique)
                            if len(first_part) >= 2 and len(second_part) >= 2:
                                # REJECT technical email prefixes
                                first_part_lower = first_part.lower()
                                second_part_lower = second_part.lower()
                                if (first_part_lower not in TECHNICAL_EMAIL_PREFIXES and
                                    second_part_lower not in TECHNICAL_EMAIL_PREFIXES):
                                    if potential_name not in cleaned_executives:
                                        all_person_names_found.add(potential_name)
                    
                    # Pattern 6: Détection générale de noms propres (prénom + nom) - VERSION TRÈS STRICTE
                    # DÉSACTIVÉ par défaut car trop de faux positifs
                    # Seulement activé si contexte très clair
                    # Format: "Prénom Nom" ou "Prénom Initial Nom"
                    # DUPLICATE: general_name_pattern = re.compile(
                        # DUPLICATE: r'\b([A-Z][a-z]{2,15})\s+([A-Z]\.?\s*)?([A-Z][a-z]{2,20})\b'
                    # DUPLICATE: )
                    
                    for match in general_name_pattern.finditer(text):
                        first_name = match.group(1)
                        middle_initial = match.group(2) if match.group(2) else ''
                        last_name = match.group(3)
                        
                        # Construire le nom complet
                        if middle_initial:
                            full_name = f"{first_name} {middle_initial.strip()} {last_name}"
                        else:
                            full_name = f"{first_name} {last_name}"
                        
                        full_name = re.sub(r'\s+', ' ', full_name).strip()
                        
                        # Validation TRÈS stricte pour éviter les faux positifs
                        if 5 <= len(full_name) <= 50:
                            words = full_name.split()
                            if len(words) >= 2 and len(words) <= 4:
                                # Vérifier le contexte pour s'assurer que c'est bien un nom de personne
                                context_start = max(0, match.start() - 200)
                                context_end = min(len(text), match.end() + 200)
                                context = text[context_start:context_end]
                                context_lower = context.lower()
                                
                                # Indicateurs positifs FORTS (contexte suggérant un nom de personne)
                                strong_positive_indicators = [
                                    'director:', 'officer:', 'executive:', 'employee:', 'trustee:',
                                    'shareholder:', 'stockholder:', 'beneficial owner:', 'owner:',
                                    'signatory:', 'authorized signatory:', 'representative:', 'agent:',
                                    'by:', 'name:', 'person:', 'individual:', 'contact:',
                                    'signed by', 'certified by', 'attested by', 'witnessed by',
                                    'notarized by', 'email:', 'phone:', 'address:', 'residence:'
                                ]
                                
                                # Indicateurs négatifs (contexte suggérant que ce n'est PAS un nom)
                                negative_indicators = [
                                    'table of contents', 'index', 'appendix', 'exhibit', 'schedule',
                                    'balance sheet', 'income statement', 'cash flow', 'statement',
                                    'note', 'footnote', 'page', 'section', 'chapter',
                                    'united states', 'new york', 'los angeles', 'washington',
                                    'commission', 'securities', 'exchange', 'filing',
                                    'the company', 'our company', 'such company', 'a company',
                                    'provides', 'entered', 'completed', 'acquired', 'merged',
                                    'income', 'taxes', 'financial', 'segment', 'revenue',
                                    'street', 'avenue', 'road', 'drive', 'boulevard', 'lane',
                                    'inc.', 'llc', 'corp', 'corporation', 'limited',
                                    'vantiv', 'and', 'or', 'the', 'of', 'in', 'to', 'with',
                                    'is', 'are', 'was', 'were', 'be', 'been', 'will', 'would'
                                ]
                                
                                has_strong_positive = any(ind in context_lower for ind in strong_positive_indicators)
                                has_negative = any(ind in context_lower for ind in negative_indicators)
                                
                                # Vérifier la position (début de ligne ou après ponctuation)
                                line_start = text.rfind('\n', 0, match.start())
                                if line_start == -1:
                                    line_start = 0
                                before_name = text[line_start:match.start()].strip()
                                is_at_line_start = len(before_name) < 5 or before_name.endswith(('.', ',', ':', ';', '-', '|'))
                                
                                # FILTRE TRÈS STRICT: Accepter SEULEMENT si:
                                # 1. Il y a un indicateur positif FORT (avec ':')
                                # 2. ET pas d'indicateur négatif
                                # 3. ET ce n'est pas déjà dans les executives
                                # 4. ET le nom ne contient pas de mots interdits
                                words_lower = [w.lower().rstrip('.,;:') for w in words]
                                excluded_words_check = {'and', 'or', 'the', 'a', 'an', 'of', 'in', 'to', 'with', 'is', 'are', 'was', 'were', 'be', 'been', 'will', 'would', 'vantiv', 'company', 'co', 'title', 'officer', 'director', 'chairman'}
                                
                                if full_name not in cleaned_executives:
                                    if has_strong_positive and not has_negative and not any(w in excluded_words_check for w in words_lower):
                                        # Validation finale: vérifier que les mots ressemblent à des noms
                                        if all(3 <= len(w) <= 15 for w in words_lower):
                                            all_person_names_found.add(full_name)
                    
                    # Nettoyer et valider tous les noms trouvés avec filtres stricts
                    cleaned_person_names = set()
                    
                    # Liste étendue de mots à exclure (mots de liaison, verbes, articles, etc.)
                    excluded_words = {
                        'and', 'or', 'the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for',
                        'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be', 'been',
                        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                        'should', 'may', 'might', 'must', 'can', 'shall', 'if', 'that', 'this',
                        'these', 'those', 'which', 'who', 'whom', 'whose', 'where', 'when',
                        'why', 'how', 'what', 'all', 'any', 'each', 'every', 'some', 'no',
                        'not', 'but', 'than', 'then', 'there', 'here', 'other', 'another',
                        'such', 'same', 'more', 'most', 'less', 'least', 'very', 'too', 'so',
                        'only', 'just', 'also', 'even', 'still', 'yet', 'already', 'again',
                        'about', 'above', 'below', 'under', 'over', 'through', 'during',
                        'before', 'after', 'since', 'until', 'while', 'because', 'although',
                        'however', 'therefore', 'thus', 'hence', 'moreover', 'furthermore',
                        'additionally', 'further', 'indeed', 'rather', 'quite', 'rather',
                        'vantiv', 'company', 'companies', 'corporation', 'inc', 'llc', 'corp',
                        'ltd', 'limited', 'incorporated', 'group', 'holdings', 'enterprises',
                        'services', 'business', 'financial', 'securities', 'exchange',
                        'commission', 'registrant', 'issuer', 'filing', 'report', 'statement',
                        'balance', 'sheet', 'income', 'cash', 'flow', 'tax', 'taxes',
                        'director', 'officer', 'executive', 'employee', 'trustee', 'shareholder',
                        'stockholder', 'beneficial', 'owner', 'signatory', 'authorized',
                        'representative', 'agent', 'management', 'board', 'committee', 'team',
                        'chairman', 'president', 'secretary', 'treasurer', 'controller',
                        'chief', 'vice', 'senior', 'junior', 'lead', 'head', 'general',
                        'additional', 'information', 'combination', 'act', 'court', 'high',
                        'mastercard', 'visa', 'stock', 'combined', 'uk', 'companies', 'worldpay'
                    }
                    
                    # Mots qui ne peuvent PAS être des noms de personnes (trop génériques)
                    invalid_name_words = {
                        'additional', 'information', 'business', 'combination', 'companies',
                        'act', 'court', 'high', 'mastercard', 'visa', 'stock', 'combined',
                        'worldpay', 'vantiv', 'services', 'executive', 'chairman', 'director',
                        'officer', 'secretary', 'treasurer', 'lead', 'title', 'and', 'co',
                        'the', 'of', 'in', 'to', 'with', 'an', 'a', 'or', 'be', 'is', 'are',
                        'was', 'were', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
                        'may', 'might', 'must', 'can', 'shall', 'if', 'that', 'this', 'these',
                        'those', 'which', 'who', 'whom', 'whose', 'where', 'when', 'why',
                        'how', 'what', 'all', 'any', 'each', 'every', 'some', 'no', 'not',
                        'but', 'than', 'then', 'there', 'here', 'other', 'another', 'such',
                        'same', 'more', 'most', 'less', 'least', 'very', 'too', 'so', 'only',
                        'just', 'also', 'even', 'still', 'yet', 'already', 'again', 'about',
                        'above', 'below', 'under', 'over', 'through', 'during', 'before',
                        'after', 'since', 'until', 'while', 'because', 'although', 'however',
                        'therefore', 'thus', 'hence', 'moreover', 'furthermore', 'additionally',
                        'further', 'indeed', 'rather', 'quite', 'means', 'check', 'mark', 'whether',
                        'purport', 'exempt', 'principal', 'traders', 'merchants', 'later',
                        'registrant', 'combined', 'filings', 'security', 'holdings', 'team',
                        'reporting', 'incremental', 'amendment', 'affirmative', 'vote', 'fact',
                        'offeree', 'undersigned', 'hereunto'
                    }
                    
                    # Termes financiers à exclure
                    financial_terms = [
                        'accounting', 'adjustment', 'amount', 'shares', 'fair', 'value',
                        'restricted', 'net', 'activity', 'attributable', 'pretax', 'tax',
                        'related', 'transactions', 'secondary', 'offering', 'purchase',
                        'plan', 'time', 'awards', 'weighted', 'merchant', 'financial',
                        'require', 'services'
                    ]
                    
                    # Phrases financières complètes à exclure
                    financial_phrases = [
                        'accounting adjustment', 'amount shares', 'fair value', 'restricted',
                        'net activity', 'attributable', 'pretax activity', 'tax',
                        'related transactions', 'secondary offering', 'purchase plan',
                        'share purchase', 'time awards', 'weighted', 'merchant services',
                        'financial', 'and/or require', 'shares amount', 'adjustment change',
                        'value restricted', 'activity attributable', 'activity tax',
                        'offering purchase', 'purchase plan', 'awards weighted'
                    ]
                    
                    # Noms d'entreprises connus à exclure
                    company_names_to_exclude = [
                        'vantiv', 'jpmorgan', 'morgan stanley', 'credit suisse',
                        'worldpay', 'tokyo-mitsubishi', 'mitsubishi ufj',
                        'fleetcor', 'broadridge', 'paymetric',
                        # Payment companies often detected as persons
                        'unionpay', 'china unionpay', 'tenpay', 'alipay', 'paypal',
                        'wechat', 'stripe', 'square', 'adyen', 'klarna',
                        # Consulting firms
                        'oliver wyman', 'mckinsey', 'bain', 'bcg', 'deloitte', 'kpmg', 'pwc',
                    ]

                    # Event/program names often detected as persons (especially in UK annual reports)
                    event_program_false_positives = [
                        'conference', 'summit', 'forum', 'symposium', 'workshop', 'seminar',
                        'rethink', 'work smart', 'willing hearts', 'brilliant basics',
                        'global retail', 'cobre bem',
                    ]

                    # Document section terms often detected as persons
                    document_section_false_positives = [
                        'nominees', 'nominations', 'nomination', 'nominees set', 'nominations subject',
                        'mitigants', 'mitigants governance', 'mitigants dedicated',
                        'regulatory compliance', 'compliance', 'governance',
                        'dedicated', 'approach', 'composition',
                    ]

                    # INTELLIGENT PATTERN: Product names (Apple, Google, Microsoft products)
                    # These often have trademark symbols or are app/store names
                    product_name_patterns = [
                        'store', 'studio', 'provider', 'networking', 'impairment',
                        'repairs', 'solution', 'returns', 'knowledge', 'confirmations',
                    ]

                    # INTELLIGENT PATTERN: Tech/Cloud product keywords
                    # Filters: "Reality Labs", "Google Cloud", "Xbox Game Pass", etc.
                    tech_product_keywords = [
                        # Cloud/Platform terms
                        ' cloud', 'cloud ', ' platform', 'platform ', ' workspace', 'workspace ',
                        ' labs', 'labs ', ' pass', ' gaming', 'gaming ',
                        # Product line indicators
                        ' quest', 'quest ', ' horizon', 'horizon ',
                        ' copilot', 'copilot ', ' automate', 'automate ',
                        # AI/Tech products
                        ' nano', ' gen', ' feed', 'feed ',
                        # Gaming products
                        'xbox ', 'game pass', 'cloud gaming',
                    ]

                    # INTELLIGENT PATTERN: Brand prefixes that indicate products, not people
                    # Filters: "Ray-Ban Meta AI", "Meta Quest", "Instagram Feed"
                    brand_product_prefixes = [
                        'ray-ban ', 'meta ', 'xbox ', 'instagram ', 'google ',
                        'microsoft ', 'power ', 'intelligent ',
                    ]

                    # INTELLIGENT PATTERN: Financial/Accounting terms as person names
                    # Filters: "Covenant Defeasance", "Retained Earnings", "Fuel Surcharges"
                    financial_false_positive_terms = [
                        'defeasance', 'earnings', 'surcharges', 'surcharge',
                        'benefit', 'benefits', 'reform', 'substantially',
                        'participant', 'participants', 'impairment', 'impairments',
                        'amortization', 'depreciation', 'accrual', 'accruals',
                        'receivable', 'receivables', 'payable', 'payables',
                        'contingent', 'contingency', 'contingencies',
                        'covenant', 'covenants', 'multiemployer',
                    ]

                    # INTELLIGENT PATTERN: Generic business/marketing phrases
                    # Filters: "Competitive Strengths", "Global Presence", "Active People"
                    generic_business_phrases = [
                        'strengths', 'presence', 'economy', 'economies',
                        'active people', 'worldwide ', ' worldwide',
                        'competitive ', ' competitive', 'global ',
                        'trustworthy', 'development', 'compose', 'demand gen',
                        'bets across', 'across alphabet', 'larger participant',
                        'reference rate', 'recognition substantially',
                    ]

                    # INTELLIGENT PATTERN: Statistical/Technical methods
                    # Filters: "Monte Carlo" (simulation method)
                    statistical_method_terms = [
                        'monte carlo', 'black scholes', 'fair value',
                    ]

                    # INTELLIGENT PATTERN: Address-like words that indicate false positives
                    address_like_patterns = [
                        'drive', 'street', 'avenue', 'boulevard', 'road', 'lane', 'way',
                        'ste', 'suite', 'floor', 'building', 'plaza', 'center', 'centre',
                        'bairro', 'vila',  # Brazilian addresses
                    ]

                    # INTELLIGENT PATTERN: Role prefixes that create partial names
                    role_prefix_patterns = [
                        'chair ', 'rm chair', 'vice ', 'senior ', 'chief ', 'director ',
                        'transformation ', 'cloud ', 'marketing ',  # "Transformation Amy E. Hood"
                    ]
                    
                    for person_name in all_person_names_found:
                        # Nettoyer les espaces multiples
                        person_name = re.sub(r'\s+', ' ', person_name).strip()

                        # === NETTOYAGE DES CHIFFRES/DATES/CARACTÈRES PARASITES (AVANT VALIDATION) ===
                        # Enlever les dates/nombres au début (ex: "2/17/2026 S. Ferris" → "S. Ferris")
                        person_name = re.sub(r'^[\d/,\s]+(?=[A-Z])', '', person_name)

                        # Enlever TOUS les nombres/dates à la fin (multiple passes si nécessaire)
                        # Ex: "Jeffrey Stieﬂer 138,750" → "Jeffrey Stieﬂer"
                        # Ex: "Charles Drucker 11,925 148,940" → "Charles Drucker"
                        # Ex: "Charles Drucker 2016" → "Charles Drucker"
                        # Pattern: retirer tous les chiffres, virgules, espaces et slashes à la fin
                        person_name = re.sub(r'[\s\d/,]+$', '', person_name)

                        # Enlever les parenthèses avec nombres à la fin (ex: "Charles Drucker(7)(8" → "Charles Drucker")
                        person_name = re.sub(r'\([^\)]*\d[^\)]*\)*$', '', person_name)
                        person_name = re.sub(r'\(\d+$', '', person_name)  # Cas "(7" sans fermeture

                        # Enlever les tirets multiples à la fin (ex: "David Karnstedt - - -" → "David Karnstedt")
                        person_name = re.sub(r'[\s\-]+$', '', person_name)

                        # Enlever les marqueurs de signature (tous les patterns)
                        # Ex: "Lars Anderson /s/", "Lisa Hook /S/", "Name (s)", "Name signed:", etc.
                        person_name = re.sub(r'\s*/[sS]/\s*', ' ', person_name, flags=re.IGNORECASE)
                        person_name = re.sub(r'\s*\([sS]\)\s*', ' ', person_name, flags=re.IGNORECASE)
                        person_name = re.sub(r'\s+signed:?\s*', ' ', person_name, flags=re.IGNORECASE)
                        person_name = re.sub(r'\s+/signed/?\s*', ' ', person_name, flags=re.IGNORECASE)

                        # Nettoyer à nouveau les espaces
                        person_name = re.sub(r'\s+', ' ', person_name).strip()

                        # Si vide après nettoyage, skip
                        if not person_name or len(person_name) < 2:
                            continue

                        # === ULTRA-STRICT VALIDATION ===
                        words = person_name.split()
                        words_lower = [w.lower().strip('.,;:') for w in words]
                        person_name_lower = person_name.lower()  # Define this early for all checks

                        # REJECT: Gerund phrases (verb-ing + words)
                        # EXCEPTION: Legitimate first names ending in "-ing" (Irving, Sterling, Fleming, etc.)
                        if words_lower and words_lower[0].endswith('ing'):
                            first_word = words_lower[0]
                            # If it's a legitimate name ending in "-ing", don't reject
                            if first_word not in LEGITIMATE_ING_NAMES:
                                continue  # Skip: "enabling us", "reducing our ability", etc.
                            # Otherwise, continue processing (it's a legitimate name)

                        # REJECT: Possessive phrases (our/his/her/its/their/your/my + words)
                        possessives = {'our', 'his', 'her', 'its', 'their', 'your', 'my'}
                        if any(w in possessives for w in words_lower):
                            continue  # Skip: "our clients", "his prior employer", etc.

                        # REJECT: Job titles without actual names
                        job_title_phrases = {
                            'senior vice', 'vice president', 'chief executive', 'chief financial',
                            'chief operating', 'executive chairman', 'lead director',
                            'audit compensation', 'audit compensation nominating'
                        }
                        if person_name_lower in job_title_phrases:
                            continue

                        # REJECT: Mots-clés qui indiquent un faux positif (vérification partielle)
                        # Si le nom contient ces mots, c'est probablement pas une personne
                        # SMART CHECK: Some keywords can be first names (e.g., "Grant Williams")
                        false_positive_keywords = [
                            # Document types
                            'accountant', 'transaction', 'addendum', 'letter', 'notice', 'agreement',
                            'award', 'repurchase', 'salary', 'severance', 'performance', 'compensation',
                            'intellectual', 'investor', 'relations', 'property', 'processing',
                            'principal', 'related', 'restated', 'offer', 'grant', 'proxy',
                            # Financial/business terms
                            'graph', 'fees', 'payments', 'schedule', 'statement', 'report',
                            'analysis', 'summary', 'overview', 'plan', 'program', 'policy',
                            # Actions/processes
                            'restatement', 'amendment', 'modification', 'termination', 'extension',
                            'acceleration', 'vesting', 'exercise', 'forfeiture', 'settlement'
                        ]

                        # SMART FILTERING: Check if keyword is first word (potential first name)
                        has_keyword_issue = False
                        for keyword in false_positive_keywords:
                            if keyword in person_name_lower:
                                # If keyword appears in name, check if it's the first word (first name)
                                if len(words_lower) >= 2 and words_lower[0] == keyword:
                                    # Check if this keyword can be a first name
                                    if keyword in KEYWORDS_AS_FIRST_NAMES:
                                        # Check second word - is it a rejection term?
                                        second_word = words_lower[1]
                                        if second_word in KEYWORDS_AS_FIRST_NAMES[keyword]:
                                            # Reject: "Grant Date", "Grant Plan"
                                            has_keyword_issue = True
                                            break
                                        # Otherwise accept: "Grant Williams", "Grant Thompson"
                                    else:
                                        # Not a known first name keyword, reject
                                        has_keyword_issue = True
                                        break
                                else:
                                    # Keyword not at start, or single word, reject
                                    has_keyword_issue = True
                                    break

                        if has_keyword_issue:
                            continue

                        # REJECT: Multi-word document/section titles (check complete phrase)
                        # Ces phrases complètes ne peuvent JAMAIS être des noms de personnes
                        document_title_phrases = {
                            'offer letter', 'performance awards', 'performance graph',
                            'principal accountant fees', 'principal accountant', 'accountant fees',
                            'related transactions', 'related party transactions',
                            'repurchase addendum', 'restated offer letter', 'restated offer',
                            'grant notice', 'award notice', 'option agreement', 'stock option',
                            'employment agreement', 'separation agreement', 'severance agreement',
                            'compensation committee', 'audit committee', 'nominating committee',
                            'board compensation', 'executive compensation', 'stock compensation',
                            'performance share', 'performance shares', 'restricted stock',
                            'stock award', 'equity award', 'cash award',
                            'market price', 'fair value', 'fair market',
                            'vesting schedule', 'payment schedule', 'exercise price',
                            'total compensation', 'base salary', 'annual bonus',
                            'change control', 'control transaction',
                            'section heading', 'table contents', 'index exhibits',
                            'financial statements', 'income statement', 'balance sheet',
                            'proxy statement', 'annual report', 'quarterly report',
                            # Department names
                            'investor relations', 'human resources', 'legal department',
                            'accounting department', 'finance department',
                            # Generic titles without names
                            'chief executive', 'chief financial', 'chief operating',
                            'vice president', 'senior vice', 'executive vice',
                            'general counsel', 'corporate secretary'
                        }
                        if person_name_lower in document_title_phrases:
                            continue

                        # REJECT: Document/business structure terms (génériques uniquement)
                        business_structure_terms = {
                            'grant date fair', 'grant date number', 'grant date threshold',
                            'total award grant', 'stock ownership guidelines', 'severance plan',
                            'period total less', 'name age position', 'year tra liability',
                            'exchange act rule', 'delaware law', 'formal policy regarding',
                            'business segment', 'payment networks', 'merchant category',
                            'customer incentives', 'transaction volume', 'general economic conditions',
                            'rapid technological change', 'numerous laws', 'written consent',
                            'virtue hereof', 'since november', 'discussed above', 'one stockholder',
                            'two different persons', 'registration statement number', 'regulatory guidelines',
                            # Document sections/headings
                            'principal accountant fees', 'related transactions', 'performance awards',
                            'performance graph', 'leadership structur', 'financial ofﬁcer',
                            'award notice', 'offer letter', 'restated offer letter', 'grant notice',
                            'repurchase addendum', 'position year salary', 'bridge lenders',
                            'stockholder outr', 'withhold allall', 'performance shar',
                            'year salary', 'severance beneﬁts', 'martin cash severance',
                            # Legal/financial terms
                            'pro forma', 'non-de minimis', 'de minimis', 'compris ed',
                            'frank act', 'sarbanes oxley', 'secur ed cr',
                            # Department/function names
                            'investor relations', 'intellectual property', 'card processing',
                            'capital research global',
                            # Broken/partial words (patterns génériques)
                            'jeffr ey', 'nelson f',
                            'nelson f. greene title', 's. ferris cash', 's. ferris vc'
                        }
                        if person_name_lower in business_structure_terms:
                            continue

                        # REJECT: Patterns suspects (références de documents)
                        # Rejeter les noms suivis directement de ".10-K" ou ".10-Q" (références de documents)
                        if re.search(r'\.\d+[KQ-]', person_name):
                            continue

                        # REJECT: Very short fragments (single words < 3 characters)
                        if len(words) == 1:
                            word = words[0].strip('.,;:')
                            word_clean = words_lower[0].strip('.,;:')

                            # Reject if < 3 chars (trop court pour être un nom)
                            if len(word_clean) < 3:
                                continue

                            # REJECT: Mots anglais très communs (utiliser logique intelligente)
                            # Liste de mots qui ne peuvent JAMAIS être des noms de personne
                            common_english_words = {
                                # Verbes communs
                                'check', 'verify', 'approve', 'confirm', 'submit', 'review', 'update',
                                'create', 'delete', 'modify', 'change', 'edit', 'save', 'cancel',
                                # Adverbes/Négations
                                'yes', 'no', 'non', 'not', 'none', 'never', 'always', 'all',
                                # Adjectifs
                                'smaller', 'larger', 'bigger', 'better', 'worse', 'new', 'old',
                                # Autres
                                'next', 'previous', 'first', 'last', 'total', 'date', 'time'
                            }
                            if word_clean in common_english_words:
                                continue

                            # REJECT: Mots tronqués courts (< 5 lettres avec terminaisons suspectes)
                            if len(word_clean) < 5:
                                # Terminaisons de troncature suspectes
                                suspicious_endings = ['er', 'ar', 'om', 'em', 'im', 'ur']
                                if any(word_clean.endswith(end) for end in suspicious_endings):
                                    # Probablement tronqué (ex: "Emer" = "Emerging" tronqué)
                                    continue

                            # REJECT: Mauvaise capitalisation pour mot unique
                            # Accepter: "Smith" (première maj, reste min) ou initiales courtes
                            # Rejeter: "SMITH" (tout maj si > 2 chars), "smith" (commence par min)
                            if not word[0].isupper():
                                continue  # Rejeter si commence par minuscule
                            if len(word) > 2 and word.isupper():
                                continue  # Rejeter si tout majuscule (sauf initiales)

                        # REJECT: Broken/truncated words (contain spaces in odd places or end with incomplete patterns)
                        # Example: "compris ed", "Performance Shar", "Leadership Structur"
                        if any(' ' in word for word in words if len(word) > 2):  # Space inside a word
                            continue
                        # Reject if ends with common truncation patterns (incomplete words)
                        if person_name_lower.endswith(('structur', ' shar', ' outr', ' ed', ' ing')):
                            continue

                        # REJECT: Document references (patterns "Mot + Numéro/Référence")
                        # Ex: "Rules 8.1", "Item 1.A", "Section II", "Part IV"
                        if len(words) >= 2:
                            last_word = words[-1].rstrip('.,;:')
                            # Détecter si le dernier mot est un numéro de référence
                            if re.match(r'^[\d]+[\.\d]*$', last_word):  # Pure numéro: 8, 8.1, 8.1.2
                                continue
                            if re.match(r'^[IVX]+$', last_word):  # Chiffres romains: I, II, III, IV
                                continue
                            if re.match(r'^[\d]+[A-Za-z]$', last_word):  # Numéro + lettre: 1a, 2B
                                continue
                            if re.match(r'^[\d]+\([a-z]\)$', last_word):  # Numéro + parenthèse: 1(a)
                                continue

                            # Mots qui indiquent des références de document
                            reference_first_words = ['rule', 'rules', 'item', 'section', 'part', 'article',
                                                    'clause', 'subsection', 'paragraph', 'exhibit', 'schedule',
                                                    'appendix', 'annex', 'attachment', 'table', 'figure']
                            if len(words) >= 2:
                                first_word_lower = words[0].lower()
                                if first_word_lower in reference_first_words:
                                    continue

                        # REJECT: Patterns de document avec numéros (ex: contient "8.1")
                        if re.search(r'\b\d+\.\d+\b', person_name):  # Contains numbered references like "8.1"
                            continue

                        # REJECT: Activity/action phrases
                        activity_phrases = {
                            'financing activities', 'investing activities', 'operating activities',
                            'financing activities during', 'entering into', 'exposing us',
                            'enabling us', 'converting floating', 'utilizing direct sales',
                            'utilizing our integrated', 'using long', 'exercising its put',
                            'dividing net income', 'reducing our ability', 'comparing our actual',
                            'contacting investor relations', 'processing electronic payment',
                            'reviewing overhang levels', 'adding cardtronics', 'advise our corporate',
                            'appoints charles drucker', 'parties claiming ownership',
                            'persons offering consumer', 'stockholders using substantially',
                            'variance between our', 'various payment networks'
                        }
                        if person_name_lower in activity_phrases:
                            continue

                        # REJECT: Compensation/awards terms
                        compensation_terms = {
                            'compensation decisions', 'compensation plans', 'compensation program',
                            'compensation program follows', 'compensation programs',
                            'director compensation', 'outstanding awards under'
                        }
                        if person_name_lower in compensation_terms:
                            continue

                        # REJECT: Company/bank references
                        company_refs = {
                            'fifth third', 'fifth third bancorp', 'fifth third bank',
                            'fifth third represents', 'advent international corporation',
                            'blackrock', 'jpmorgan chase', 'matthew taylor group'
                        }
                        if person_name_lower in company_refs:
                            continue

                        # REJECT: Waiver phrases (partial names we don't want)
                        if any(phrase in person_name_lower for phrase in ['waived his', 'waived her']):
                            continue

                        # REJECT: Names that are actually sentence fragments
                        # Check if first word is a common verb or preposition
                        common_verbs = {
                            'adding', 'advise', 'appoints', 'comparing', 'contacting',
                            'converting', 'discussed', 'dividing', 'enabling', 'entering',
                            'exercising', 'exposing', 'financing', 'investing', 'operating',
                            'parties', 'payme', 'persons', 'processing', 'reducing',
                            'registration', 'reviewing', 'since', 'stockholders', 'using',
                            'utilizing', 'variance', 'various', 'virtue'
                        }
                        if words_lower and words_lower[0] in common_verbs:
                            continue

                        # EXCLURE immédiatement si c'est un nom d'entreprise connu
                        # (person_name_lower already defined at start of validation)
                        if any(company in person_name_lower for company in company_names_to_exclude):
                            continue

                        # EXCLURE si c'est un nom d'événement/programme (common in UK annual reports)
                        if any(event in person_name_lower for event in event_program_false_positives):
                            continue

                        # EXCLURE si c'est une section de document
                        if any(section in person_name_lower for section in document_section_false_positives):
                            continue

                        # INTELLIGENT FILTER: Reject product names (Store, Studio, etc.)
                        if any(pattern in person_name_lower for pattern in product_name_patterns):
                            continue

                        # INTELLIGENT FILTER: Reject tech/cloud product keywords
                        # Filters: "Reality Labs", "Google Cloud", "Xbox Game Pass", etc.
                        if any(keyword in person_name_lower for keyword in tech_product_keywords):
                            continue

                        # INTELLIGENT FILTER: Reject brand product prefixes
                        # Filters: "Ray-Ban Meta AI", "Meta Quest", "Instagram Feed"
                        if any(person_name_lower.startswith(prefix) for prefix in brand_product_prefixes):
                            continue

                        # INTELLIGENT FILTER: Reject financial/accounting false positives
                        # Filters: "Covenant Defeasance", "Retained Earnings", "Fuel Surcharges"
                        if any(term in person_name_lower for term in financial_false_positive_terms):
                            continue

                        # INTELLIGENT FILTER: Reject generic business/marketing phrases
                        # Filters: "Competitive Strengths", "Global Presence", "Active People"
                        if any(phrase in person_name_lower for phrase in generic_business_phrases):
                            continue

                        # INTELLIGENT FILTER: Reject statistical/technical method names
                        # Filters: "Monte Carlo", "Black Scholes"
                        if any(method in person_name_lower for method in statistical_method_terms):
                            continue

                        # INTELLIGENT FILTER: Reject address-like patterns
                        if any(pattern in person_name_lower for pattern in address_like_patterns):
                            continue

                        # INTELLIGENT FILTER: Reject if starts with role prefix (creates partial names)
                        if any(person_name_lower.startswith(prefix) for prefix in role_prefix_patterns):
                            continue

                        # INTELLIGENT FILTER: Reject if contains trademark symbols (product names)
                        if '®' in person_name or '™' in person_name:
                            continue

                        # EXCLURE si contient des phrases financières
                        if any(phrase in person_name_lower for phrase in financial_phrases):
                            continue
                        
                        # Validation: doit avoir au moins 2 mots (prénom + nom)
                        words = person_name.split()
                        if len(words) >= 2 and len(words) <= 5:
                            # Vérifier que chaque mot fait sens (pas trop court, pas trop long)
                            if all(2 <= len(w) <= 20 for w in words):
                                # Vérifier que chaque mot commence par une majuscule
                                if all(w[0].isupper() for w in words if len(w) > 1):
                                    # FILTRE STRICT: Exclure si contient des mots interdits
                                    words_lower = [w.lower().rstrip('.,;:') for w in words]
                                    
                                    # Ne pas accepter si un mot est dans la liste des mots exclus
                                    if any(w in excluded_words for w in words_lower):
                                        continue
                                    
                                    # Ne pas accepter si un mot est dans la liste des mots invalides
                                    if any(w in invalid_name_words for w in words_lower):
                                        continue
                                    
                                    # EXCLURE si contient des termes financiers dans les mots
                                    if any(term in words_lower for term in financial_terms):
                                        continue
                                    
                                    # EXCLURE si le nom contient des mots collés (ex: "AdjustmentChange", "SharesAmount")
                                    # Vérifier si un mot contient une majuscule au milieu (suggère deux mots collés)
                                    # EXCEPTION: Legitimate name prefixes (McDonald, DeAngelo, O'Brien, etc.)
                                    has_collapsed_words = False
                                    for word in words:
                                        if len(word) > 8:  # Mots longs suspects
                                            # Compter les majuscules au milieu du mot (pas au début)
                                            mid_caps = sum(1 for i, c in enumerate(word[1:], 1) if c.isupper() and word[i-1].isalpha())
                                            if mid_caps > 0:
                                                # Check if it's a legitimate name prefix (Mc, Mac, De, etc.)
                                                word_lower = word.lower()
                                                is_legitimate_name = any(word_lower.startswith(prefix) for prefix in LEGITIMATE_NAME_PREFIXES)
                                                if not is_legitimate_name:
                                                    # C'est probablement deux mots collés (ex: "AdjustmentChange")
                                                    has_collapsed_words = True
                                                    break
                                                # Otherwise, continue (it's McDonald, DeAngelo, etc.)

                                    if has_collapsed_words:
                                        continue

                                    # === ADVANCED NAME STRUCTURE VALIDATION ===
                                    # HEURISTIC 1: Two-word names should look like "First Last"
                                    # Reject if both words end in common noun suffixes
                                    noun_suffix_patterns = ['ance', 'ence', 'tion', 'sion', 'ment', 'ness', 'ity', 'ing', 'ings', 'ures', 'ures']
                                    if len(words) == 2:
                                        first_lower = words_lower[0]
                                        second_lower = words_lower[1]
                                        # Reject if second word ends with common noun suffix (not a surname)
                                        if any(second_lower.endswith(suffix) for suffix in noun_suffix_patterns):
                                            # Exception: Common surnames ending in -ing (Fleming, Irving, etc.)
                                            if second_lower not in ['king', 'young', 'strong', 'sterling', 'fleming', 'irving', 'ewing', 'browning', 'cummings']:
                                                continue

                                    # HEURISTIC 2: Reject abstract concept pairs (both words are abstract nouns)
                                    abstract_nouns = {
                                        'strengths', 'presence', 'economy', 'reform', 'development',
                                        'compliance', 'governance', 'performance', 'earnings', 'revenues',
                                        'expenses', 'assets', 'liabilities', 'equity', 'deficit',
                                        'surplus', 'margin', 'ratio', 'rate', 'yield', 'return',
                                        'growth', 'decline', 'increase', 'decrease', 'change',
                                    }
                                    if len(words) == 2 and all(w in abstract_nouns for w in words_lower):
                                        continue

                                    # HEURISTIC 3: Reject if first word is an adjective commonly used with business terms
                                    business_adjectives = {
                                        'competitive', 'global', 'worldwide', 'international', 'domestic',
                                        'intelligent', 'active', 'retained', 'accumulated', 'deferred',
                                        'multiemployer', 'comprehensive', 'consolidated', 'combined',
                                    }
                                    if len(words) >= 2 and words_lower[0] in business_adjectives:
                                        continue

                                    # Ne pas accepter si le nom contient des mots de liaison communs
                                    if any(w in ['and', 'or', 'the', 'of', 'in', 'to', 'with', 'an', 'a', 'and/or'] for w in words_lower):
                                        continue
                                    
                                    # Vérifier qu'il n'y a pas trop de majuscules (éviter les acronymes)
                                    uppercase_ratio = sum(1 for c in person_name if c.isupper()) / len(person_name)
                                    if uppercase_ratio <= 0.4:
                                        # Éviter les faux positifs finaux
                                        person_name_upper = person_name.upper()
                                        final_false_positives = [
                                            'UNITED STATES', 'NEW YORK', 'LOS ANGELES',
                                            'BALANCE SHEET', 'CASH FLOW', 'INCOME TAX',
                                            'STOCK OPTION', 'SECURITIES', 'EXCHANGE',
                                            'COMMISSION', 'WASHINGTON', 'TABLE OF',
                                            'CONTENTS', 'APPENDIX', 'EXHIBIT', 'SCHEDULE',
                                            'NOTE', 'FOOTNOTE', 'PAGE', 'SECTION',
                                            'VANTIV IN', 'VANTIV TO', 'VANTIV WITH',
                                            'AN INDEPENDENT', 'AND SECRETARY', 'BE THE',
                                            'THE EXECUTIVE', 'THE LEAD', 'CHECK MARK',
                                            'NO LATER', 'OF REGISTRANT', 'THE COMBINED',
                                            'ON THE COMBINED', 'OTHER VANTIV', 'TEAM REPORTING',
                                            'THE HIGH COURT', 'THE INCREMENTAL', 'THE AFFIRMATIVE',
                                            'THE FACT', 'THE OFFEREE', 'THE UNDERSIGNED',
                                            'ADDITIONAL INFORMATION', 'BUSINESS COMBINATION',
                                            'COMPANIES ACT', 'EXECUTIVE CHAIRMAN', 'HIGH COURT',
                                            'LEAD DIRECTOR', 'MASTERCARD VISA', 'THE BUSINESS',
                                            'VANTIV STOCK', 'IS AN EMERGING', 'WILL CO',
                                            # Ajouter les faux positifs financiers
                                            'ACCOUNTING ADJUSTMENT', 'AMOUNT SHARES', 'FAIR VALUE',
                                            'RESTRICTED', 'NET ACTIVITY', 'ATTRIBUTABLE', 'PRETAX ACTIVITY',
                                            'RELATED TRANSACTIONS', 'SECONDARY OFFERING', 'PURCHASE PLAN',
                                            'SHARE PURCHASE', 'TIME AWARDS', 'WEIGHTED', 'MERCHANT SERVICES',
                                            'FINANCIAL', 'AND/OR REQUIRE', 'SHARES AMOUNT', 'ADJUSTMENT CHANGE',
                                            'VALUE RESTRICTED', 'ACTIVITY ATTRIBUTABLE', 'ACTIVITY TAX',
                                            'OFFERING PURCHASE', 'PURCHASE PLAN', 'AWARDS WEIGHTED',
                                            'ACCOUNTING ADJUSTMENTCHANGE', 'AMOUNT SHARESAMOUNT',
                                            'FAIR VALUERESTRICTED', 'MERCHANT SERVICESFINANCIAL',
                                            'NET ACTIVITYATTRIBUTABLE', 'PRETAX ACTIVITYTAX',
                                            'RELATED TRANSACTIONS', 'SECONDARY OFFERINGPURCHASE',
                                            'SHARE PURCHASE PLAN', 'SHARES AMOUNTSHARES',
                                            'TIME AWARDSWEIGHTED', 'VANTIV'
                                        ]
                                        if not any(fp in person_name_upper for fp in final_false_positives):
                                            # Vérifier que le nom ne se termine pas par des mots suspects
                                            last_word = words_lower[-1]
                                            invalid_endings = ['and', 'or', 'the', 'of', 'in', 'to', 'with', 'co', 
                                                              'title', 'officer', 'director', 'chairman', 'name',
                                                              'financial', 'services', 'plan', 'tax', 'amount',
                                                              'shares', 'awards', 'transactions', 'require']
                                            if last_word not in invalid_endings:
                                                # S'assurer que ce n'est pas déjà dans les executives
                                                if person_name not in cleaned_executives:
                                                    # Validation finale: le nom doit ressembler à un vrai nom
                                                    # (pas de mots trop courts, pas de répétitions)
                                                    if len(set(words_lower)) == len(words_lower):  # Pas de mots dupliqués
                                                        # VALIDATION CAPITALISATION: Chaque mot doit commencer par majuscule
                                                        # Format attendu: "John Smith", "M. Taylor", "Smith"
                                                        valid_capitalization = True
                                                        for word in words:
                                                            # Retirer ponctuation éventuelle
                                                            word_clean = word.rstrip('.,;:')
                                                            if len(word_clean) == 0:
                                                                valid_capitalization = False
                                                                break

                                                            # Initiales acceptées: 1-2 chars majuscules (ex: "M.", "S.", "Jr")
                                                            if len(word_clean) <= 2:
                                                                if not word_clean[0].isupper():
                                                                    valid_capitalization = False
                                                                    break
                                                            else:
                                                                # Mots normaux: première lettre majuscule, reste minuscule
                                                                if not word_clean[0].isupper():
                                                                    valid_capitalization = False
                                                                    break
                                                                # Rejeter si tout en majuscules (sauf si <= 2 chars)
                                                                if word_clean.isupper() and len(word_clean) > 2:
                                                                    valid_capitalization = False
                                                                    break

                                                        if valid_capitalization:
                                                            cleaned_person_names.add(person_name)
                    
                    # Validation finale avec spaCy NER (si disponible)
                    if SPACY_AVAILABLE and SPACY_NLP and cleaned_person_names:
                        # Utiliser spaCy pour valider les noms détectés
                        validated_person_names = set()
                        
                        # Créer un texte avec tous les noms pour analyse
                        # Analyser chaque nom individuellement avec son contexte
                        for person_name in cleaned_person_names:
                            # Chercher le nom dans le texte original avec contexte
                            name_pos = text.find(person_name)
                            if name_pos != -1:
                                # Prendre un contexte autour du nom
                                context_start = max(0, name_pos - 100)
                                context_end = min(len(text), name_pos + len(person_name) + 100)
                                context_text = text[context_start:context_end]
                                
                                # Analyser avec spaCy
                                doc = SPACY_NLP(context_text)
                                
                                # Vérifier si spaCy détecte ce nom comme une personne
                                for ent in doc.ents:
                                    if ent.label_ == "PERSON":
                                        # Normaliser le nom détecté par spaCy
                                        detected_name = ent.text.strip()
                                        detected_name = re.sub(r'\s+', ' ', detected_name)
                                        
                                        # Vérifier si notre nom correspond (exact ou partiel)
                                        if person_name.lower() in detected_name.lower() or detected_name.lower() in person_name.lower():
                                            validated_person_names.add(person_name)
                                            break
                                
                                # Si spaCy n'a pas trouvé, mais que le nom est très probable (déjà validé par nos filtres),
                                # on peut quand même l'accepter si le contexte est bon
                                if person_name not in validated_person_names:
                                    # Vérifier si le contexte contient des indicateurs positifs
                                    context_lower = context_text.lower()
                                    strong_indicators = ['director', 'officer', 'executive', 'employee', 'trustee',
                                                       'shareholder', 'by:', 'name:', 'signed', 'certified']
                                    if any(ind in context_lower for ind in strong_indicators):
                                        validated_person_names.add(person_name)
                        
                        # Utiliser les noms validés par spaCy, ou tous si spaCy n'a rien trouvé
                        if validated_person_names:
                            cleaned_person_names = validated_person_names
                    
                    # Ajouter tous les noms de personnes trouvés avec déduplication
                    # Dédupliquer les noms qui sont les mêmes mais avec différentes capitalisations
                    deduplicated_names = {}
                    
                    for person_name in cleaned_person_names:
                        # Normaliser le nom pour la comparaison (minuscules, sans espaces multiples)
                        normalized = re.sub(r'\s+', ' ', person_name.lower().strip())

                        # Enlever les initiales du milieu pour la comparaison
                        # Ex: "stephanie l. ferris" → "stephanie ferris" pour matcher avec "stephanie ferris"
                        normalized = re.sub(r'\s+[a-z]\.\s+', ' ', normalized)  # "X. " au milieu
                        normalized = re.sub(r'\s+[a-z]\s+', ' ', normalized)    # "X " au milieu (sans point)

                        # Vérifier si ce nom est contenu dans un nom existant ou vice-versa
                        # Ex: "Lisa Hook" et "Lisa Hook BOON" doivent être dédupliqués
                        matching_key = None
                        for existing_key in deduplicated_names.keys():
                            # Si le nouveau nom est un préfixe d'un nom existant
                            if existing_key.startswith(normalized + ' '):
                                matching_key = existing_key
                                break
                            # Si un nom existant est un préfixe du nouveau nom
                            elif normalized.startswith(existing_key + ' '):
                                matching_key = existing_key
                                break

                        # Si on a trouvé une correspondance partielle, utiliser la clé du nom le plus court (le plus propre)
                        if matching_key:
                            # Garder le nom le plus court (probablement le plus propre)
                            if len(normalized) < len(matching_key):
                                # Le nouveau nom est plus court, l'utiliser comme nouvelle clé
                                deduplicated_names[normalized] = person_name
                                # Supprimer l'ancienne clé plus longue
                                del deduplicated_names[matching_key]
                            else:
                                # Le nom existant est plus court, ne rien faire (garder l'existant)
                                pass
                            continue

                        # Si on a déjà vu ce nom exact (normalisé), garder la meilleure version
                        if normalized in deduplicated_names:
                            existing_name = deduplicated_names[normalized]
                            # Préférer la version avec capitalisation standard (première lettre de chaque mot en majuscule)
                            # plutôt que tout en majuscules
                            if person_name.isupper() and not existing_name.isupper():
                                # Garder la version existante (meilleure capitalisation)
                                continue
                            elif not person_name.isupper() and existing_name.isupper():
                                # Remplacer par la version avec meilleure capitalisation
                                deduplicated_names[normalized] = person_name
                            # Sinon, garder la première version trouvée
                        else:
                            # Nouveau nom, l'ajouter
                            deduplicated_names[normalized] = person_name
                    
                    # Ajouter seulement les noms dédupliqués
                    # (Le nettoyage des chiffres a déjà été fait avant la validation)
                    for person_name in deduplicated_names.values():
                        page_findings.append({'type': 'person_name', 'value': person_name, 'page': page_num + 1})
                    
                    # ===== TICKER SYMBOLS (pour documents SEC) =====
                    # Format: (NYSE: XXXX) ou (NASDAQ: XXXX)
                    ticker_pattern = re.compile(r'\((?:NYSE|NASDAQ|AMEX|OTC):\s*([A-Z]{1,5})\)', re.IGNORECASE)
                    for match in ticker_pattern.finditer(text):
                        ticker = match.group(1)
                        page_findings.append({'type': 'ticker_symbol', 'value': f"{match.group(0)}", 'page': page_num + 1})
                    
                    # ===== DATES IMPORTANTES - VERSION AMÉLIORÉE =====
                    # DÉSACTIVÉ - Ne plus détecter les dates importantes
                    # important_dates_found = set()
                    # 
                    # # Pattern 1: Dates en format texte (December 31, 2017)
                    # date_pattern1 = re.compile(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b', re.IGNORECASE)
                    # for match in date_pattern1.finditer(text):
                    #     date_str = match.group(0)
                    #     # Contexte étendu pour détecter les dates importantes
                    #     context_start = max(0, match.start() - 80)
                    #     context_end = min(len(text), match.end() + 80)
                    #     context = text[context_start:context_end].lower()
                    #     
                    #     important_keywords = [
                    #         'period ended', 'as of', 'dated', 'effective', 'fiscal year',
                    #         'quarter ended', 'year ended', 'date', 'filing date',
                    #         'report date', 'balance sheet', 'statement date', 'closing date',
                    #         'maturity date', 'expiration date', 'commencement', 'termination',
                    #         'agreement date', 'contract date', 'execution date', 'signature date'
                    #     ]
                    #     
                    #     if any(keyword in context for keyword in important_keywords):
                    #         important_dates_found.add(date_str)
                    # 
                    # # Pattern 2: Dates en format numérique (12/31/2017, 12-31-2017, 12.31.2017)
                    # date_pattern2 = re.compile(r'\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})\b')
                    # for match in date_pattern2.finditer(text):
                    #     month, day, year = match.groups()
                    #     # Validation basique (mois entre 1-12, jour entre 1-31)
                    #     if 1 <= int(month) <= 12 and 1 <= int(day) <= 31 and 1900 <= int(year) <= 2100:
                    #         date_str = f"{month}/{day}/{year}"
                    #         context_start = max(0, match.start() - 80)
                    #         context_end = min(len(text), match.end() + 80)
                    #         context = text[context_start:context_end].lower()
                    #         
                    #         important_keywords = [
                    #             'period ended', 'as of', 'dated', 'effective', 'fiscal year',
                    #             'quarter ended', 'year ended', 'date', 'filing date',
                    #             'report date', 'balance sheet', 'statement date', 'closing date',
                    #             'maturity date', 'expiration date', 'commencement', 'termination',
                    #             'agreement date', 'contract date', 'execution date', 'signature date'
                    #         ]
                    #         
                    #         if any(keyword in context for keyword in important_keywords):
                    #             important_dates_found.add(date_str)
                    # 
                    # # Pattern 3: Dates en format ISO ou autre (2017-12-31)
                    # date_pattern3 = re.compile(r'\b(\d{4})[/\-\.](\d{1,2})[/\-\.](\d{1,2})\b')
                    # for match in date_pattern3.finditer(text):
                    #     year, month, day = match.groups()
                    #     if 1900 <= int(year) <= 2100 and 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
                    #         date_str = f"{year}-{month}-{day}"
                    #         context_start = max(0, match.start() - 80)
                    #         context_end = min(len(text), match.end() + 80)
                    #         context = text[context_start:context_end].lower()
                    #         
                    #         important_keywords = [
                    #             'period ended', 'as of', 'dated', 'effective', 'fiscal year',
                    #             'quarter ended', 'year ended', 'date', 'filing date',
                    #             'report date', 'balance sheet', 'statement date', 'closing date'
                    #         ]
                    #         
                    #         if any(keyword in context for keyword in important_keywords):
                    #             important_dates_found.add(date_str)
                    # 
                    # for date_str in important_dates_found:
                    #     page_findings.append({'type': 'important_date', 'value': date_str, 'page': page_num + 1})
                    
                    # ===== COMPANY NAMES - VERSION AMÉLIORÉE =====
                    # STRATEGY: Prioritize precision over recall
                    # - Only detect companies with clear company suffixes (Inc., LLC, Corp, etc.)
                    # - OR known company names (JPMorgan, Vantiv, etc.)
                    # - Reject document sections, accounting terms, and generic words

                    company_names_found = set()
                    spacy_detected_companies = set()  # Track companies detected by spaCy (more lenient filtering)

                    # Liste étendue de suffixes d'entreprise (incluant AG, SA, etc.)
                    company_suffixes = r'(?:Inc\.?|LLC|LLP|L\.L\.C\.|L\.L\.P\.|Corporation|Corp\.?|Corp|Incorporated|Inc|Ltd\.?|Limited|LP|L\.P\.|PC|P\.C\.|PLLC|PLC|Co\.?|Company|Companies|Group|Holdings|Holdings?|Enterprises|Partners|Partnership|Bank|Banks|Trust|Capital|Securities|Financial|Services|AG|S\.A\.|SA|GmbH|BV|NV|SpA|S\.p\.A\.)'

                    # COMPREHENSIVE list of document sections/terms that spaCy incorrectly tags as ORG
                    spacy_org_false_positives = {
                        # Document sections
                        'analysis of financial condition', 'consolidated statement', 'consolidated statements',
                        'statement of equity', 'statement of income', 'statement of operations',
                        'balance sheet', 'cash flow', 'income statement', 'financial statements',
                        'table of contents', 'exhibits', 'schedules', 'financial statement schedules',
                        'management discussion', 'risk factors', 'legal proceedings',
                        # Accounting terms
                        'unaudited', 'audited', 'contingencies', 'equity unaudited', 'income unaudited',
                        'comprehensive income', 'retained earnings', 'stockholders equity',
                        'accumulated deficit', 'net income', 'gross profit',
                        # Generic words that are NOT companies
                        'company', 'state', 'customer', 'customers', 'llc', 'inc', 'corp',
                        'emer', 'interactive data file', 'documents incorporated',
                        # Form types and regulatory terms
                        '10-k', '10-q', '8-k', 'def 14a', 'form', 'sec', 'edgar',
                        'atm', 'emv', 'pin', 'pos', 'api',  # Acronyms that aren't companies
                        # Section titles
                        'principal', 'beneficial ownership', 'executive compensation',
                        'corporate governance', 'board of directors', 'audit committee',
                        # === NEW INTELLIGENT PATTERNS ===
                        # SEC document section patterns
                        'registrant', "registrant's common equity", 'common equity',
                        'independent registered public accounting firm', 'accounting firm',
                        'compensation - stock', 'stock compensation',
                        # Geographic areas (not companies)
                        'european economic area', 'economic area', 'united states',
                        # Product/Service lines (not company names)
                        'microsoft 365', 'cloud services', 'digital services',
                        'smart package', 'smart facilities', 'efficiency reimagined',
                        # Regulation/Act names
                        'digital services act', 'services act', 'companies act',
                        'standard contractual clauses', 'contractual clauses',
                        # Committee/Group terms
                        'privacy & product', 'compliance committee', 'working group',
                        'resource groups', 'payment services', 'clearing, settlement',
                        # Marketing/Report terms
                        'environmental sustainability report', 'sustainability report',
                        'class a common stock', 'class b common stock', 'common stock',
                        # Package/Service descriptors
                        'domestic package', 'international package', 'u.s. domestic',
                    }

                    # INTELLIGENT PATTERN: Product line patterns to filter from company names
                    product_line_indicators = [
                        '365 consumer', '365 copilot', '365 commercial',
                        'consumer products', 'commercial products',
                        'ai helpful', 'leverage gemini',
                    ]

                    # Known legitimate companies (will always be accepted if detected)
                    known_legitimate_companies = {
                        'vantiv', 'worldpay', 'jpmorgan', 'chase', 'morgan stanley', 'credit suisse',
                        'goldman sachs', 'bank of america', 'wells fargo', 'citigroup', 'barclays',
                        'deutsche bank', 'ubs', 'hsbc', 'bnp paribas', 'fidelity', 'blackrock',
                        'visa', 'mastercard', 'paypal', 'square', 'stripe', 'first data',
                        'fifth third', 'deloitte', 'ernst & young', 'kpmg', 'pwc', 'pricewaterhousecoopers',
                    }
                    
                    # Mots qui ne peuvent PAS être le premier mot d'un nom de compagnie (défini tôt pour être utilisé partout)
                    invalid_first_words = {
                        'amended', 'and', 'backstop', 'bridge', 'business', 'combined', 'commission',
                        'dealing', 'delaware', 'disclosure', 'executive', 'financial', 'incremental',
                        'irs', 'loan', 'london', 'offer', 'operations', 'original', 'panel', 'press',
                        'registrant', 'rule', 'scheme', 'securities', 'stock', 'u.s', 'us',
                        'a', 'an', 'is', 'will', 'be', 'are', 'was', 'were',
                        # Termes financiers/comptables
                        'accounting', 'accounts', 'accumulated', 'amount', 'average', 'based',
                        'capital', 'common', 'comprehensive', 'consolidated', 'consolidation',
                        'contents', 'controller', 'customer', 'earnings', 'equity', 'income',
                        'interest', 'internal', 'investor', 'management', 'marketing', 'merchant',
                        'net', 'non-operating', 'oci', 'office', 'parent', 'performance', 'period',
                        'principal', 'pro', 'public', 'restricted', 'retained', 'secondary',
                        'shares', 'significant', 'subsidiaries', 'tax', 'unit', 'visa',
                        # Termes génériques
                        'company', 'state', 'the', 'if', 'as', 'on', 'of', 'in', 'to', 'for',
                        'with', 'by', 'from', 'at', 'or', 'and', 'an', 'a',
                        # Comités et fonctions
                        'committee', 'committees', 'community', 'compliance', 'secretary'
                    }
                    
                    # D'abord, utiliser spaCy pour détecter les organisations (si disponible)
                    # IMPORTANT: spaCy alone produces too many false positives
                    # We ONLY accept spaCy detections if:
                    # 1. The name contains a company suffix (Inc., LLC, etc.)
                    # 2. OR it's a known legitimate company name
                    # 3. AND it's not in the false positives list
                    if SPACY_AVAILABLE and SPACY_NLP:
                        try:
                            text_to_analyze = text[:1000000] if len(text) > 1000000 else text
                            doc = SPACY_NLP(text_to_analyze)

                            for ent in doc.ents:
                                if ent.label_ == "ORG":
                                    org_name = ent.text.strip()
                                    org_name = re.sub(r'\s+', ' ', org_name)
                                    org_lower = org_name.lower()

                                    # Skip if too short or too long
                                    if not (3 <= len(org_name) <= 80):
                                        continue

                                    # FILTER 1: Reject known false positives (exact match or contains)
                                    if org_lower in spacy_org_false_positives:
                                        continue
                                    if any(fp in org_lower for fp in spacy_org_false_positives):
                                        continue

                                    # FILTER 2: Reject single words that aren't known companies
                                    words = org_name.split()
                                    if len(words) == 1:
                                        if org_lower not in known_legitimate_companies:
                                            continue

                                    # FILTER 3: Reject if starts with invalid word
                                    first_word = words[0].lower() if words else ''
                                    if first_word in invalid_first_words:
                                        continue

                                    # FILTER 4: Reject product line patterns
                                    # Filters: "Microsoft 365 Consumer", "Cloud Services Microsoft 365"
                                    if any(indicator in org_lower for indicator in product_line_indicators):
                                        continue

                                    # FILTER 5: Check if it has a company suffix OR is a known company
                                    has_suffix = bool(re.search(company_suffixes, org_name, re.IGNORECASE))
                                    is_known_company = any(kc in org_lower for kc in known_legitimate_companies)

                                    # ONLY accept if has suffix OR is known company
                                    if has_suffix or is_known_company:
                                        # Final validation: must start with uppercase
                                        if org_name[0].isupper():
                                            company_names_found.add(org_name)
                                            spacy_detected_companies.add(org_name)
                        except Exception as e:
                            if verbose:
                                logger.debug(f"spaCy NER failed on page {page_num + 1}: {e}")

                    # Méthode 0.5: Noms d'entreprises connus (WorldPay, JPMorgan, etc.) - Pattern compilé avant la boucle
                    # Ces entreprises sont toujours détectées si elles ont un contexte approprié
                    for match in known_company_names_pattern.finditer(text):
                        company_name = match.group(1).strip()

                        # Vérifier le contexte (60 caractères avant et après)
                        context_start = max(0, match.start() - 60)
                        context_end = min(len(text), match.end() + 60)
                        context = text[context_start:context_end].lower()

                        # Indicateurs de contexte d'entreprise
                        company_context_indicators = [
                            'company', 'corporation', 'registrant', 'issuer', 'entity',
                            'payment', 'transaction', 'services', 'financial', 'bank',
                            'acquired', 'merger', 'subsidiary', 'affiliate', 'partner',
                            'client', 'customer', 'vendor', 'supplier', 'underwriter',
                            'exact name', 'name of', 'provided by', 'processed by'
                        ]

                        # Accepter si contexte approprié
                        if any(indicator in context for indicator in company_context_indicators):
                            company_names_found.add(company_name)

                    # Méthode 1: Contexte "registrant" ou "company name" (amélioré)
                    context_patterns = [
                        re.compile(
                        r'(?:Exact\s+name\s+of\s+registrant|'
                            r'Name\s+of\s+(?:the\s+)?(?:registrant|issuer|company|corporation)|'
                            r'(?:Registrant|Issuer|Company|Corporation)(?:\'s)?\s+name|'
                            r'Company\s+Name|'
                            r'Entity\s+Name)'
                            r'[:\s]+([A-Z][A-Za-z0-9\s&,\.\-]+?(?:,\s*)?' + company_suffixes + r')',
                        re.IGNORECASE
                        ),
                        re.compile(
                            r'(?:Registrant|Issuer|Company)[:\s]+([A-Z][A-Za-z0-9\s&,\.\-]+?(?:,\s*)?' + company_suffixes + r')',
                            re.IGNORECASE
                        ),
                    ]
                    
                    for pattern in context_patterns:
                        for match in pattern.finditer(text):
                            company_name = match.group(1).strip()
                            company_name = re.sub(r'\s+', ' ', company_name)

                            if 5 <= len(company_name) <= 80:
                                if company_name.count(' ') <= 8:  # Max 9 mots
                                    company_names_found.add(company_name)
                    
                    # Méthode 2: Format standalone "XXX, Inc." ou "XXX AG"
                    # DISABLED: This method produces too many false positives
                    # The spaCy NER + suffix check (above) is more accurate
                    # To re-enable, set ENABLE_REGEX_COMPANY_DETECTION = True
                    ENABLE_REGEX_COMPANY_DETECTION = False

                    if ENABLE_REGEX_COMPANY_DETECTION:
                        standalone_patterns = [
                            re.compile(
                                r'(?<=[\.\n\(\s])([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,6}),?\s+' + company_suffixes + r'(?=[\.\n\)\s,])',
                            re.MULTILINE
                            ),
                            re.compile(
                                r'\b([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,6})\s+' + company_suffixes + r'\b',
                                re.MULTILINE
                            ),
                            # Pattern spécial pour "Credit Suisse Securities AG" (suffixe AG séparé)
                            re.compile(
                                r'\b([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){1,4})\s+(AG|S\.A\.|SA|GmbH|BV|NV|SpA|S\.p\.A\.)\b',
                                re.MULTILINE
                            ),
                        ]

                        for pattern_idx, pattern in enumerate(standalone_patterns):
                            for match in pattern.finditer(text):
                                # Construire le nom selon le pattern
                                if pattern_idx == 2:  # Pattern avec AG/SA/etc.
                                    company_name = f"{match.group(1)} {match.group(2)}"
                                else:
                                    company_name = match.group(0).strip()

                                company_name = re.sub(r'\s+', ' ', company_name)

                                # Vérifier qu'il n'y a pas de verbes ou mots suspects autour
                                ctx_before = text[max(0, match.start() - 100):match.start()].lower()
                                ctx_after = text[match.end():min(len(text), match.end() + 100)].lower()
                                context_full = ctx_before + ' ' + ctx_after

                                # Liste étendue de mots suspects
                                suspect_words = [
                                    'provides', 'entered', 'completed', 'acquired', 'merged',
                                    'income', 'taxes', 'financial', 'statements', 'segment',
                                    'the company', 'our company', 'such company', 'a company',
                                    'any company', 'each company', 'this company',
                                    'agreement', 'letter', 'release', 'document', 'amendment',
                                    'commitment', 'combination', 'condition', 'operation',
                                    'disclosure', 'scheme', 'rule', 'act', 'commission',
                                    'backstop', 'bridge', 'loan', 'credit', 'business',
                                    'amended', 'restated', 'original', 'incremental'
                                ]

                                # Vérifier aussi que ce n'est pas dans une phrase générique
                                if not any(word in context_full for word in suspect_words):
                                    # Vérifier que le nom commence bien par une majuscule et contient des lettres
                                    if company_name[0].isupper() and any(c.isalpha() for c in company_name):
                                        # Vérifier que le premier mot n'est pas un terme invalide
                                        first_word = company_name.split()[0].lower().rstrip('.,;:')
                                        if first_word not in INVALID_COMPANY_FIRST_WORDS:
                                            if 5 <= len(company_name) <= 80:
                                                company_names_found.add(company_name)
                    
                    # Méthode 3: Noms de compagnies dans les en-têtes ou sections spéciales
                    # DISABLED: Too many false positives - spaCy with suffix check is more accurate
                    if ENABLE_REGEX_COMPANY_DETECTION:
                        header_patterns = [
                            re.compile(
                                r'(?:^|\n)\s*([A-Z][A-Za-z0-9\s&,\.\-]+?(?:,\s*)?' + company_suffixes + r')\s*(?:\n|$)',
                                re.MULTILINE
                            ),
                        ]

                        for pattern in header_patterns:
                            for match in pattern.finditer(text):
                                company_name = match.group(1).strip()
                                company_name = re.sub(r'\s+', ' ', company_name)

                                # Vérifier que c'est bien en début de ligne ou après un saut de ligne
                                line_start = text.rfind('\n', 0, match.start())
                                if line_start == -1:
                                    line_start = 0
                                line_text = text[line_start:match.end()].strip()

                                # Si la ligne est courte (probablement un en-tête), c'est probablement un nom de compagnie
                                if len(line_text) < 100 and 5 <= len(company_name) <= 80:
                                    company_names_found.add(company_name)

                    # Méthode 4: Détecter les noms de compagnies SANS suffixe (comme JPMorgan, WorldPay, Credit Suisse)
                    # DISABLED: Pattern 3 especially is too broad and causes many false positives
                    if ENABLE_REGEX_COMPANY_DETECTION:
                        company_name_patterns_no_suffix = [
                            # Pattern 1: Noms composés avec mots-clés d'entreprise (Bank, Trust, Capital, Securities, etc.)
                            re.compile(
                                r'\b([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){1,4})\s+(Bank|Trust|Capital|Securities|Financial|Services|Group|Holdings|Partners)\b',
                                re.MULTILINE
                            ),
                            # Pattern 2: "The" + nom d'entreprise (The Bank of..., The Company...)
                            re.compile(
                                r'\bThe\s+([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){1,5})\s+(?:of\s+)?([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,4})?\s*(?:Bank|Trust|Capital|Securities|Financial|Services|Group|Holdings|Company|Corporation)?\b',
                                re.MULTILINE
                            ),
                            # Pattern 3: Noms composés connus (Credit Suisse, Morgan Stanley, etc.)
                            re.compile(
                                r'\b([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){1,3})\b'
                            ),
                        ]

                    # Acronymes d'entreprises connus (détection intelligente)
                    # DISABLED: Too many false positives (ATM, EMV, PIN, etc. detected as companies)
                    if ENABLE_REGEX_COMPANY_DETECTION:
                        acronym_pattern = re.compile(
                            r'\b([A-Z]{3,6})\b'
                        )
                    
                    # Mots-clés qui suggèrent qu'un acronyme est une entreprise
                    company_acronym_indicators = [
                        'bank', 'trust', 'capital', 'securities', 'financial', 'services',
                        'group', 'holdings', 'funding', 'lender', 'creditor', 'underwriter',
                        'company', 'corporation', 'inc', 'llc', 'corp', 'ltd'
                    ]

                    # The following regex-based methods are DISABLED due to high false positive rates
                    # They are kept for reference but skipped unless ENABLE_REGEX_COMPANY_DETECTION is True
                    if ENABLE_REGEX_COMPANY_DETECTION:
                      for pattern_idx, pattern in enumerate(company_name_patterns_no_suffix):
                        for match in pattern.finditer(text):
                            # Construire le nom de l'entreprise selon le pattern
                            if pattern_idx == 1:  # Pattern "The ..."
                                if match.group(2):  # Si "of" est présent
                                    potential_company = f"The {match.group(1)} of {match.group(2)}"
                                else:
                                    potential_company = f"The {match.group(1)}"
                            else:
                                potential_company = match.group(0).strip()
                            
                            potential_company = re.sub(r'\s+', ' ', potential_company)
                            
                            # Vérifier le contexte
                            match_start = match.start()
                            match_end = match.end()
                            context_start = max(0, match_start - 250)
                            context_end = min(len(text), match_end + 250)
                            context = text[context_start:context_end].lower()
                            
                            # Indicateurs positifs (suggèrent que c'est une entreprise)
                            positive_indicators = [
                                'company', 'corporation', 'bank', 'trust', 'capital', 'securities',
                                'financial', 'services', 'group', 'holdings', 'partners',
                                'name of registrant', 'name of issuer', 'name of company',
                                'registrant\'s name', 'issuer\'s name', 'company\'s name',
                                'exact name', 'entity name', 'underwriter', 'lender',
                                'creditor', 'debtor', 'party', 'counterparty', 'funding',
                                'credit suisse', 'morgan stanley', 'jpmorgan', 'worldpay',
                                'vantiv', 'tokyo-mitsubishi', 'mitsubishi ufj'
                            ]
                            
                            # Indicateurs négatifs (exclure)
                            negative_indicators = [
                                'agreement', 'letter', 'release', 'document', 'amendment',
                                'commitment', 'combination', 'condition', 'operation',
                                'disclosure', 'scheme', 'rule', 'act', 'commission',
                                'file number', 'employer identification', 'delaware',
                                'london stock exchange', 'securities exchange act',
                                'press release', 'annual meeting', 'stockholder',
                                'the business combination', 'the original loan',
                                'amended and restated', 'backstop commitment letter',
                                'bridge commitment letter', 'loan agreement',
                                'financial condition', 'operations', 'panel',
                                'registrant', 'executive', 'the disclosure table'
                            ]
                            
                            has_positive = any(ind in context for ind in positive_indicators)
                            has_negative = any(ind in context for ind in negative_indicators)
                            
                            # Validation: doit avoir au moins 1 mot (ou 2 pour certains patterns)
                            words = potential_company.split()
                            
                            # Noms d'entreprises connus (même avec 1-2 mots)
                            known_companies = ['credit suisse', 'morgan stanley', 'jpmorgan', 'worldpay',
                                              'vantiv', 'tokyo-mitsubishi', 'mitsubishi', 'ufj']
                            
                            is_known_company = any(known in potential_company.lower() for known in known_companies)
                            
                            if len(words) >= 1 and len(words) <= 8:
                                # Vérifier que tous les mots commencent par majuscule (nom propre) ou sont "The", "of"
                                valid_words = [w for w in words if w.lower() not in ['the', 'of', 'and', 'or']]
                                if all(w[0].isupper() for w in valid_words if len(w) > 1):
                                    # Vérifier que ce n'est pas déjà détecté
                                    if potential_company not in company_names_found:
                                        # Accepter si:
                                        # 1. Pattern 1 (avec Bank/Trust/etc.) - toujours accepter
                                        # 2. Pattern 2 (The...) - accepter si contexte positif
                                        # 3. Pattern 3 - accepter si connu OU contexte positif
                                        # 4. Noms connus - toujours accepter
                                        if 'Bank' in potential_company or 'Trust' in potential_company or \
                                           'Capital' in potential_company or 'Securities' in potential_company or \
                                           'Financial' in potential_company or 'Services' in potential_company or \
                                           'Group' in potential_company or 'Holdings' in potential_company or \
                                           'Partners' in potential_company:
                                            # Toujours accepter les noms avec ces mots-clés
                                            if not has_negative:
                                                company_names_found.add(potential_company)
                                        elif pattern_idx == 1:  # Pattern "The ..."
                                            # Pour "The Bank of...", accepter si contexte positif
                                            if has_positive and not has_negative:
                                                company_names_found.add(potential_company)
                                        elif is_known_company:
                                            # Toujours accepter les entreprises connues
                                            if not has_negative:
                                                company_names_found.add(potential_company)
                                        elif has_positive and not has_negative:
                                            # Pour les autres, être plus strict
                                            # Vérifier que le nom ne contient pas de mots interdits
                                            words_lower = [w.lower() for w in words]
                                            invalid_words = ['a', 'an', 'and', 'or', 'in', 'to', 'for', 'with', 'by']
                                            if not any(w in invalid_words for w in words_lower):
                                                # Vérifier que ce n'est pas un faux positif spécifique
                                                potential_lower = potential_company.lower()
                                                excluded = ['combined company', 'business combination', 'executive', 'operations', 'panel', 'registrant']
                                                if not any(ex in potential_lower for ex in excluded):
                                                    company_names_found.add(potential_company)
                    
                      # Méthode 5: Détecter les acronymes d'entreprises (MSSF, etc.)
                      # DISABLED: Also wrapped in ENABLE_REGEX_COMPANY_DETECTION
                      for match in acronym_pattern.finditer(text):
                          acronym = match.group(1)

                          # Vérifier le contexte
                          match_start = match.start()
                          match_end = match.end()
                          context_start = max(0, match_start - 150)
                          context_end = min(len(text), match_end + 150)
                          context = text[context_start:context_end].lower()

                          # Vérifier si le contexte suggère que c'est une entreprise
                          has_company_indicator = any(ind in context for ind in company_acronym_indicators)

                          # Vérifier si l'acronyme est suivi ou précédé d'un nom d'entreprise connu
                          context_upper = text[context_start:context_end].upper()
                          known_company_acronyms = ['MSSF', 'JPM', 'CS', 'MS', 'BOT', 'UFJ']

                          if has_company_indicator or acronym in known_company_acronyms:
                              # Vérifier que ce n'est pas dans un contexte négatif
                              negative_context = [
                                  'agreement', 'letter', 'release', 'document', 'amendment',
                                  'file number', 'employer identification', 'rule', 'act'
                              ]
                              if not any(neg in context for neg in negative_context):
                                  # Construire le nom complet si possible
                                  # Chercher le nom complet avant ou après l'acronyme
                                  before_text = text[max(0, match_start - 100):match_start].strip()
                                  after_text = text[match_end:min(len(text), match_end + 100)].strip()

                                  # Si on trouve un nom d'entreprise connu, utiliser celui-ci
                                  # Sinon, utiliser l'acronyme seul
                                  full_name = None
                                  for known in known_companies:
                                      if known in before_text.lower() or known in after_text.lower():
                                          # Extraire le nom complet
                                          name_match = re.search(r'\b([A-Z][A-Za-z\s-]+' + known.replace('-', r'[\s-]') + r'[A-Za-z\s-]*)\b',
                                                                 before_text + ' ' + after_text, re.IGNORECASE)
                                          if name_match:
                                              full_name = name_match.group(1).strip()
                                              break

                                  if full_name:
                                      company_names_found.add(full_name)
                                  else:
                                      # Pour les acronymes connus, les ajouter tels quels
                                      if acronym in known_company_acronyms:
                                          company_names_found.add(acronym)

                    # Nettoyer et valider les noms de compagnies avec filtres ULTRA stricts
                    cleaned_companies = set()
                    
                    # Liste massive de termes à exclure (titres de documents, termes génériques, etc.)
                    excluded_company_terms = {
                        # Articles et verbes
                        'is', 'an', 'a', 'the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by',
                        'from', 'as', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
                        'did', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall', 'will',
                        # Titres de documents et termes légaux
                        'agreement', 'letter', 'release', 'document', 'disclosure', 'disclosures', 'scheme',
                        'amendment', 'amendments', 'commitment', 'commitments', 'combination', 'combinations',
                        'condition', 'conditions', 'operation', 'operations', 'executive', 'executives',
                        'registrant', 'registrants', 'issuer', 'issuers', 'panel', 'panels', 'rule', 'rules',
                        'act', 'acts', 'commission', 'commissions', 'exchange', 'exchanges', 'securities',
                        'stockholder', 'stockholders', 'meeting', 'meetings', 'annual', 'stock',
                        # Termes génériques
                        'combined', 'original', 'amended', 'restated', 'backstop', 'bridge', 'loan', 'credit',
                        'business', 'financial', 'disclosure', 'dealing', 'offer', 'period', 'table',
                        'press', 'fee', 'lenders', 'documents', 'lender', 'incremental',
                        # Termes spécifiques à exclure
                        'emerging', 'growth', 'co', 'file', 'number', 'employer', 'identification',
                        'no', 'delaware', 'london', 'stock', 'u.s', 'us', 'usa'
                    }
                    
                    # Phrases complètes à exclure (faux positifs communs)
                    excluded_phrases = [
                        'amended and restated', 'backstop commitment', 'backstop fee', 'backstop credit',
                        'bridge commitment', 'bridge documents', 'bridge lenders', 'business combination',
                        'combined company', 'commission file', 'dealing disclosures', 'disclosure table',
                        'executive', 'financial condition', 'incremental amendment', 'irs employer',
                        'loan agreement', 'london stock', 'offer period', 'original loan',
                        'press release', 'rule 8.3', 'scheme', 'securities exchange', 'the business',
                        'the disclosure', 'the incremental', 'the london', 'the offer', 'the original',
                        'the securities', 'the u.s', 'the us', 'the u.s. securities',
                        'the backstop', 'the bridge', 'the business combination',
                        'the "business', 'the "original',
                        # INTELLIGENT PATTERN: Courts and legal entities
                        'district court', 'circuit court', 'court of', 'superior court', 'supreme court',
                        'federal court', 'state court', 'appeals court', 'bankruptcy court',
                        # INTELLIGENT PATTERN: Generic roles/terms
                        'general counsel', 'registrant', 'payment services', 'our group', 'working group',
                        'supplier trust', 'accountant fees', 'back-office services',
                        # INTELLIGENT PATTERN: Cloud/Services descriptions (not company names)
                        'cloud services', 'clearing, settlement', 'sponsorship services',
                        # Comités et fonctions
                        'committee going', 'committee how', 'committee separately', 'committee the board',
                        'committeegroup', 'committeeremuneration', 'committee the', 'committees',
                        'committees (audit', 'committees link', 'community', 'community diversity',
                        'company secretary', 'company stock',
                        'compliance functions', 'group risk committee', 'remuneration committee',
                        'nomination committee', 'audit committee', 'board of directors',
                        'compensation committee', 'compensation discussion', 'compensation-stock compensation',
                        'corporate governance', 'corporate services', 'corporate services officer',
                        'competition merchant services', 'death or disability',
                        # Termes financiers/comptables
                        'accounting adjustment', 'accounting standards', 'accounts receivable',
                        'accumulated common stock', 'amount capital', 'amount shares', 'average price',
                        'based compensation', 'capital stock', 'common stock', 'comprehensive income',
                        'consolidated statement', 'consolidated statements', 'consolidation',
                        'contents bank', 'contents item', 'contents merchant', 'contents net',
                        'contents part', 'contents sales', 'contents segment', 'contents the',
                        'contents tra', 'contents we', 'customer incentives', 'earnings income',
                        'equity incentive plan', 'equity shares', 'income tax', 'income taxes',
                        'interest coverage', 'interest rate', 'internal control', 'internal revenue',
                        'investor relations', 'management\'s report', 'marketing sales',
                        'merchant services total', 'merchant services year', 'merchant servicesfinancial',
                        'net income per share', 'non-operating income', 'oci component',
                        'office services', 'parent company', 'performance share', 'period leverage',
                        'principal agent', 'pro forma adjustments', 'public company accounting',
                        'restricted stock', 'retained comprehensive', 'secondary offering',
                        'shares amount', 'significant accounting', 'subsidiaries report',
                        'tax receivable', 'unit incentive plan', 'visa debit processing',
                        # Sections de documents
                        'consolidated statement of equity', 'consolidated statements of comprehensive',
                        'consolidated statements of financial', 'consolidated statements of income',
                        'contingencies', 'mine safety disclosures', 'net income per share',
                        # === NEW INTELLIGENT PATTERNS ===
                        # UPS/Logistics specific false positives
                        'smart package', 'smart facilities', 'smart facility',
                        'efficiency reimagined', 'domestic package', 'international package',
                        'package international', 'u.s. domestic package',
                        # Government/Regulatory bodies (not companies)
                        'pipeline and hazardous', 'hazardous materials safety', 'safety administration',
                        'federal trade commission', 'trade commission',
                        # Tech product/feature names (not companies)
                        'whatsapp channels', 'facebook page', 'facebook, instagram',
                        'instagram feed', 'meta resource', 'channels', 'pages',
                        # Microsoft product lines
                        'microsoft 365 consumer', 'microsoft 365 copilot', 'microsoft 365 commercial',
                        '365 consumer', '365 copilot', '365 commercial',
                        # Google/Alphabet product names
                        'google services', 'alphabet and google', "alphabet inc.'s",
                        "alphabet' s", 'ai helpful', 'leverage gemini',
                        # Generic report/marketing terms
                        'annual better business', 'better business conference',
                        'marketsbusiness model', 'business model',
                        # Address-related false positives
                        'address of principal', 'principal executive offices',
                    ]
                    
                    # NOTE: invalid_first_words est maintenant défini plus tôt (ligne ~5165) pour être utilisé partout
                    
                    # Mots qui ne peuvent PAS être dans un nom de compagnie (sauf si c'est vraiment une compagnie)
                    invalid_company_words = {
                        'agreement', 'letter', 'release', 'document', 'disclosure', 'scheme', 'amendment',
                        'commitment', 'combination', 'condition', 'operation', 'executive', 'registrant',
                        'issuer', 'panel', 'rule', 'act', 'commission', 'exchange', 'securities', 'stockholder',
                        'meeting', 'annual', 'stock', 'combined', 'original', 'amended', 'restated', 'backstop',
                        'bridge', 'loan', 'credit', 'business', 'financial', 'disclosure', 'dealing', 'offer',
                        'period', 'table', 'press', 'fee', 'lenders', 'documents', 'lender', 'incremental',
                        'file', 'number', 'employer', 'identification', 'no', 'delaware', 'london', 'u.s', 'us'
                    }
                    
                    for company in company_names_found:
                        # Nettoyer les espaces multiples
                        company = re.sub(r'\s+', ' ', company).strip()
                        
                        # Validation: doit avoir au moins 3 caractères et un suffixe valide
                        if len(company) >= 3 and len(company) <= 80:
                            # Vérifier qu'il contient un suffixe d'entreprise
                            if re.search(company_suffixes, company, re.IGNORECASE):
                                # FILTRE ULTRA STRICT: Validation en plusieurs étapes
                                words = company.split()
                                words_lower = [w.lower().rstrip('.,;:') for w in words]
                                company_lower = company.lower()
                                company_upper = company.upper()

                                # ========== INTELLIGENT FILTERING FOR SPACY-DETECTED COMPANIES ==========
                                # If detected by spaCy (ML-based), trust it more but apply smart sanity checks
                                if company in spacy_detected_companies:
                                    # Apply INTELLIGENT sanity checks for spaCy companies

                                    # FILTER 1: Reject obvious document sections
                                    obvious_document_sections = [
                                        'consolidated statement', 'consolidated statements',
                                        'table of contents', 'mine safety disclosures',
                                        'management\'s discussion and analysis'
                                    ]
                                    if any(section in company_lower for section in obvious_document_sections):
                                        continue

                                    # FILTER 2: Reject if starts with "Committee" (unless has clear company suffix)
                                    if company_lower.startswith('committee') and not any(suffix in company_lower for suffix in [' inc', ' llc', ' corp', ' ltd', ' limited']):
                                        continue

                                    # FILTER 3: Reject generic/accounting words when they appear ALONE
                                    generic_single_words = {
                                        'company', 'corporate', 'consolidated', 'consolidation',
                                        'community', 'computer', 'compliance', 'composition',
                                        'control', 'conducted', 'conclusion', 'continuation',
                                        'contracts', 'customers', 'definition', 'digital'
                                    }
                                    # Check if it's a single generic word (e.g., "Company Inc.")
                                    first_word = words_lower[0] if words_lower else ''
                                    if len(words) <= 2 and first_word in generic_single_words:
                                        # Reject unless it's clearly a well-known company
                                        continue

                                    # FILTER 4: Reject phrases that are TOO LONG (>6 words = probably a sentence)
                                    if len(words) > 6:
                                        continue

                                    # FILTER 5: Reject phrases containing verbs or role indicators
                                    verb_indicators = {
                                        'joined', 'based', 'chair', 'member', 'officer',
                                        'director', 'support', 'approach', 'composition'
                                    }
                                    if any(verb in words_lower for verb in verb_indicators):
                                        continue

                                    # FILTER 6: Reject if starts with prepositions/articles (indicates a phrase)
                                    phrase_starts = {'of', 'the', 'a', 'an', 'in', 'at', 'on', 'for', 'with'}
                                    if first_word in phrase_starts:
                                        continue

                                    # ACCEPT - spaCy detected it and passed all intelligent filters
                                    cleaned_companies.add(company)
                                    continue  # Skip ultra-strict validation below

                                # ========== ULTRA STRICT FILTERING FOR REGEX-DETECTED COMPANIES ==========
                                # Only apply strict filters to companies detected by regex patterns

                                # ÉTAPE 1: Exclure si contient des phrases interdites
                                if any(phrase in company_lower for phrase in excluded_phrases):
                                    continue
                                
                                # ÉTAPE 1.5: Exclure les sections de documents
                                document_section_indicators = [
                                    'consolidated statement', 'consolidated statements', 'contents',
                                    'mine safety', 'management\'s report', 'subsidiaries report',
                                    'independent registered', 'public accounting', 'accounting firm',
                                    # Comités et fonctions
                                    'committee going', 'committee how', 'committee separately',
                                    'committee the board', 'committee the', 'committees (audit',
                                    'committees link', 'community diversity', 'company secretary',
                                    'compliance functions', 'group risk committee', 'remuneration committee',
                                    'nomination committee', 'audit committee'
                                ]
                                if any(ind in company_lower for ind in document_section_indicators):
                                    continue
                                
                                # ÉTAPE 1.5.5: Exclure les termes commençant par "Committee" (sauf si vraiment une compagnie)
                                if company_lower.startswith('committee') and not any(suffix in company_lower for suffix in ['inc', 'llc', 'corp', 'ltd', 'limited', 'company']):
                                    continue
                                
                                # ÉTAPE 1.5.6: Exclure "Community" seul ou avec descriptions
                                if company_lower.strip() == 'community' or company_lower.startswith('community '):
                                    continue
                                
                                # ÉTAPE 1.5.7: Exclure "Company Secretary" et variations
                                if 'company secretary' in company_lower:
                                    continue
                                
                                # ÉTAPE 1.5.8: Exclure "Compliance Functions"
                                if 'compliance functions' in company_lower:
                                    continue
                                
                                # ÉTAPE 1.6: Exclure les phrases mal formées (mots collés, répétitions)
                                has_collapsed_words = False
                                for word in words:
                                    if len(word) > 10:
                                        mid_caps = sum(1 for i, c in enumerate(word[1:], 1) if c.isupper() and word[i-1].isalpha())
                                        if mid_caps > 1:  # Plus d'une majuscule au milieu = mots collés
                                            has_collapsed_words = True
                                            break
                                if has_collapsed_words:
                                    continue
                                
                                # ÉTAPE 1.6.5: Exclure les patterns avec "Committee" collé (ex: "CommitteeGroup", "CommitteeRemuneration")
                                if re.search(r'committeegroup|committeeremuneration|committeethe', company_lower):
                                    continue
                                
                                # Vérifier les répétitions de mots
                                if len(words_lower) != len(set(words_lower)):  # Mots dupliqués
                                    continue
                                
                                # ÉTAPE 1.7: Exclure les patterns suspects
                                suspicious_patterns = [
                                    r'sharesamount', r'amountshares', r'amount\s+shares\s+amount',
                                    r'equity\s+shares\s+amount', r'shares\s+amount\s+shares',
                                    r'amount\s+capital\s+earnings', r'earnings\s+income',
                                    r'comprehensive\s+controlling', r'retained\s+comprehensive'
                                ]
                                if any(re.search(pattern, company_lower) for pattern in suspicious_patterns):
                                    continue
                                
                                # ÉTAPE 1.8: Exclure les termes génériques seuls
                                generic_terms = ['company', 'controller', 'state', 'the', 'principal', 'public company']
                                if company_lower.strip() in generic_terms:
                                    continue

                                # ÉTAPE 1.9: Exclure les titres de sections de documents
                                section_keywords = ['discussion', 'analysis', 'overview', 'summary', 'report',
                                                   'statement', 'compensation', 'governance', 'directors']
                                if any(keyword in company_lower for keyword in section_keywords):
                                    # Si contient un keyword de section ET pas de suffixe clair d'entreprise
                                    has_clear_suffix = any(suf in company_lower for suf in [' inc', ' llc', ' corp', ' ltd', ' limited'])
                                    if not has_clear_suffix:
                                        # Vérifier si c'est vraiment un titre de section
                                        # Patterns suspects: "Discussion and Analysis", "Board of Directors", etc.
                                        section_patterns = [
                                            r'discussion\s+and\s+analysis', r'board\s+of\s+directors',
                                            r'compensation\s+discussion', r'compensation\s+committee',
                                            r'corporate\s+governance', r'corporate\s+services',
                                            r'compensation-stock', r'competition\s+merchant',
                                            r'death\s+or\s+disability'
                                        ]
                                        if any(re.search(p, company_lower) for p in section_patterns):
                                            continue

                                # ÉTAPE 1.10: Exclure les noms se terminant par des pronoms
                                if len(words) > 0:
                                    last_word = words[-1].lower().rstrip('.,;:')
                                    invalid_endings = ['our', 'their', 'his', 'her', 'its', 'your', 'my']
                                    if last_word in invalid_endings:
                                        continue

                                # ÉTAPE 1.11: Détecter les patterns "Committee/Board + Nom de personne"
                                # Si commence par "Committee" ou "Board" et contient 3+ mots, vérifier si le dernier mot est un nom propre seul
                                if len(words) >= 3:
                                    first_word_lower = words[0].lower()
                                    if first_word_lower in ['committee', 'board', 'compensation', 'corporate']:
                                        # Si les 2 derniers mots sont des noms propres (majuscules), c'est probablement "Committee + Nom Personne"
                                        if len(words) >= 2:
                                            last_two = words[-2:]
                                            if all(w[0].isupper() and w.lower() not in ['inc', 'llc', 'corp', 'ltd', 'limited', 'company', 'group', 'holdings'] for w in last_two):
                                                # Probablement "Compensation Committee Gary Lauer" ou similaire
                                                continue

                                # ÉTAPE 1.12: Renforcer la validation des premiers mots - termes de sections
                                invalid_first_terms = ['board', 'compensation', 'corporate', 'competition', 'company',
                                                      'consolidated', 'combined', 'executive', 'governance', 'discussion',
                                                      'analysis', 'overview', 'summary', 'statement', 'report']
                                if len(words) > 0:
                                    first_word_check = words[0].lower().rstrip('.,;:')
                                    if first_word_check in invalid_first_terms:
                                        # Accepter uniquement si a un suffixe clair d'entreprise
                                        has_clear_suffix = any(suf in company_lower for suf in [' inc.', ' inc', ' llc', ' corp.', ' corp', ' ltd.', ' ltd', ' limited'])
                                        if not has_clear_suffix:
                                            continue

                                # ÉTAPE 1.13: Détecter les mots tronqués/incomplets dans des PATTERNS DE 2 MOTS
                                # Ex: "Performance Shar" (Share tronqué), "Equity Aw" (Award tronqué)
                                # IMPORTANT: Ne s'applique QUE si c'est un pattern de 2 mots générique
                                # Ne rejette PAS les noms d'entreprise légitimes comme "Lyft", "Zoom", "Uber"
                                if len(words) == 2:  # Seulement pour les patterns de 2 mots
                                    first_word_lower = words[0].lower()
                                    last_word = words[-1].lower().rstrip('.,;:')

                                    # Mots génériques de premier mot (contexte de compensation/document)
                                    generic_context_words = ['performance', 'equity', 'stock', 'compensation', 'restricted',
                                                            'incentive', 'executive', 'employee', 'annual', 'quarterly']

                                    # Si le premier mot est générique, vérifier si le second est tronqué
                                    if first_word_lower in generic_context_words:
                                        # Patterns spécifiques de troncature évidents (mots incomplets connus)
                                        # Ces patterns sont clairement des mots tronqués, pas des noms d'entreprise
                                        truncated_patterns = ['shar', 'aw', 'awa', 'opt', 'compen', 'incent', 'restr']

                                        if any(last_word == pattern for pattern in truncated_patterns):
                                            # Clairement tronqué dans un contexte de compensation
                                            continue

                                # ÉTAPE 1.14: Détecter les patterns de compensation/documents génériques
                                # Ex: "Performance Awards", "Offer Letter", "Equity Plan", "Stock Options"
                                if len(words) == 2:  # Exactement 2 mots
                                    first_word_lower = words[0].lower()
                                    second_word_lower = words[1].lower().rstrip('.,;:')

                                    # Listes de termes génériques
                                    generic_first_words = ['performance', 'offer', 'equity', 'stock', 'compensation',
                                                          'incentive', 'restricted', 'employee', 'executive', 'annual']
                                    generic_second_words = ['awards', 'award', 'letter', 'plan', 'options', 'option',
                                                           'graph', 'chart', 'table', 'report', 'shares', 'share',
                                                           'bonus', 'compensation', 'program', 'schedule']

                                    # Si les 2 mots sont génériques ET pas de suffixe d'entreprise
                                    if first_word_lower in generic_first_words and second_word_lower in generic_second_words:
                                        has_clear_suffix = any(suf in company_lower for suf in [' inc', ' llc', ' corp', ' ltd', ' limited'])
                                        if not has_clear_suffix:
                                            continue

                                # ÉTAPE 1.15: Nettoyer les chiffres à la fin du nom AVANT validation
                                # Ex: "Paymetric 423,113" → "Paymetric"
                                # Ceci gère les cas où les chiffres ne sont pas détectés au début
                                company_cleaned = re.sub(r'[\s\d,]+$', '', company).strip()
                                if company_cleaned != company:
                                    # Le nom contenait des chiffres - utiliser la version nettoyée
                                    company = company_cleaned
                                    # Revérifier la longueur minimale après nettoyage
                                    if len(company) < 3:
                                        continue
                                    # Mettre à jour les variables
                                    words = company.split()
                                    words_lower = [w.lower().rstrip('.,;:') for w in words]
                                    company_lower = company.lower()
                                    company_upper = company.upper()

                                # ÉTAPE 1.16: Détecter les patterns "Mot + Numéro/Référence"
                                # Ex: "Rules 8.1", "Item 1.A", "Section 2.3", "Part II"
                                if len(words) >= 2:
                                    last_word = words[-1].rstrip('.,;:')
                                    # Détecter si le dernier mot est un numéro de référence
                                    # Patterns: "8.1", "1.A", "II", "2a", "1(a)", etc.
                                    if re.match(r'^[\d]+[\.\d]*$', last_word):  # Pure numéro: 8, 8.1, 8.1.2
                                        continue
                                    if re.match(r'^[IVX]+$', last_word):  # Chiffres romains: I, II, III, IV
                                        continue
                                    if re.match(r'^[\d]+[A-Za-z]$', last_word):  # Numéro + lettre: 1a, 2B
                                        continue
                                    if re.match(r'^[\d]+\([a-z]\)$', last_word):  # Numéro + parenthèse: 1(a), 2(b)
                                        continue
                                    # Mots qui indiquent des références de document
                                    reference_first_words = ['rule', 'rules', 'item', 'section', 'part', 'article',
                                                            'clause', 'subsection', 'paragraph', 'exhibit', 'schedule',
                                                            'appendix', 'annex', 'attachment', 'table', 'figure']
                                    if len(words) >= 2:
                                        first_word_lower = words[0].lower()
                                        if first_word_lower in reference_first_words:
                                            continue

                                # ÉTAPE 1.17: Détecter les mots anglais très communs (verbes, adverbes, adjectifs)
                                # Ex: "Check", "Non", "Smaller", "Larger", "Better", "Faster", etc.
                                if len(words) == 1:  # Un seul mot
                                    word_lower = words[0].lower().rstrip('.,;:')
                                    # Liste de mots anglais très communs qui ne sont JAMAIS des noms d'entreprise
                                    common_words = {
                                        # Verbes communs
                                        'check', 'verify', 'approve', 'confirm', 'submit', 'review', 'update',
                                        'create', 'delete', 'modify', 'change', 'edit', 'save', 'cancel',
                                        'continue', 'proceed', 'accept', 'reject', 'decline',
                                        # Adverbes/Négations
                                        'yes', 'no', 'non', 'not', 'none', 'never', 'always', 'often', 'sometimes',
                                        # Adjectifs comparatifs/superlatifs
                                        'smaller', 'larger', 'bigger', 'better', 'worse', 'faster', 'slower',
                                        'higher', 'lower', 'greater', 'lesser', 'older', 'newer',
                                        'smallest', 'largest', 'biggest', 'best', 'worst', 'fastest', 'slowest',
                                        # Mots de direction
                                        'next', 'previous', 'first', 'last', 'back', 'forward',
                                        # Autres mots très génériques
                                        'total', 'amount', 'number', 'date', 'time', 'name', 'title',
                                        'description', 'status', 'type', 'category', 'notes', 'comments'
                                    }
                                    if word_lower in common_words:
                                        continue

                                # ÉTAPE 1.18: Détecter les mots tronqués très courts (< 5 lettres)
                                # Ex: "Emer" (probablement "Emerging" tronqué), "Comp" (probablement "Company")
                                if len(words) == 1:  # Un seul mot
                                    word_lower = words[0].lower().rstrip('.,;:')
                                    # Exceptions: abréviations légitimes et suffixes d'entreprise
                                    legitimate_short = {'inc', 'llc', 'corp', 'ltd', 'plc', 'sa', 'ag', 'gmbh',
                                                       'usa', 'uk', 'eu', 'asia', 'nasa', 'fbi', 'cia', 'ibm'}
                                    if len(word_lower) < 5 and word_lower not in legitimate_short:
                                        # Vérifier si c'est un mot complet ou tronqué
                                        # Un mot de < 5 lettres est suspect s'il ne se termine pas par une terminaison valide
                                        suspicious_endings = ['er', 'ar', 'om', 'em', 'im', 'ur']  # Terminaisons de troncature
                                        if any(word_lower.endswith(end) for end in suspicious_endings):
                                            # Probablement tronqué
                                            continue

                                # ÉTAPE 2: Exclure si le premier mot est invalide
                                if len(words_lower) > 0:
                                    first_word = words_lower[0]
                                    if first_word in invalid_first_words:
                                        continue
                                
                                # ÉTAPE 3: Exclure si contient trop de mots interdits
                                invalid_word_count = sum(1 for w in words_lower if w in invalid_company_words)
                                if invalid_word_count > 0 and len(words_lower) <= 3:
                                    # Si c'est un nom court avec des mots interdits, c'est probablement un faux positif
                                    continue
                                
                                # ÉTAPE 4: Exclure les faux positifs spécifiques
                                false_positives = [
                                    'SECURITIES AND EXCHANGE COMMISSION', 'COMMISSION FILE',
                                    'UNITED STATES', 'NEW YORK', 'LOS ANGELES',
                                    'IS AN EMERGING GROWTH CO', 'WILL CO', 'THE CO',
                                    'AN EMERGING', 'GROWTH CO', 'IS AN',
                                    'AMENDED AND RESTATED', 'BACKSTOP COMMITMENT', 'BACKSTOP FEE',
                                    'BRIDGE COMMITMENT', 'BRIDGE DOCUMENTS', 'BRIDGE LENDERS',
                                    'BUSINESS COMBINATION', 'COMBINED COMPANY', 'COMMISSION FILE NUMBER',
                                    'DEALING DISCLOSURES', 'DISCLOSURE TABLE', 'EXECUTIVE',
                                    'FINANCIAL CONDITION', 'INCREMENTAL AMENDMENT', 'IRS EMPLOYER',
                                    'LOAN AGREEMENT', 'LONDON STOCK', 'OFFER PERIOD', 'ORIGINAL LOAN',
                                    'PRESS RELEASE', 'RULE 8.3', 'SCHEME', 'SECURITIES EXCHANGE',
                                    'THE BUSINESS', 'THE DISCLOSURE', 'THE INCREMENTAL', 'THE LONDON',
                                    'THE OFFER', 'THE ORIGINAL', 'THE SECURITIES', 'THE U.S',
                                    'THE US', 'THE U.S. SECURITIES',
                                    'THE BACKSTOP', 'THE BRIDGE', 'THE BUSINESS COMBINATION',
                                    'THE "BUSINESS', 'THE "ORIGINAL', 'OPERATIONS', 'PANEL',
                                    'REGISTRANT', 'EXECUTIVE', 'FINANCIAL CONDITION',
                                    # Ajouter les faux positifs de comités et fonctions
                                    'COMMITTEE GOING', 'COMMITTEE HOW', 'COMMITTEE SEPARATELY',
                                    'COMMITTEE THE BOARD', 'COMMITTEEGROUP', 'COMMITTEEREMUNERATION',
                                    'COMMITTEE THE', 'COMMITTEES', 'COMMITTEES (AUDIT', 'COMMITTEES LINK',
                                    'COMMUNITY', 'COMMUNITY DIVERSITY', 'COMPANY SECRETARY', 'COMPANY STOCK',
                                    'COMPLIANCE FUNCTIONS', 'GROUP RISK COMMITTEE', 'REMUNERATION COMMITTEE',
                                    'NOMINATION COMMITTEE', 'AUDIT COMMITTEE', 'BOARD OF DIRECTORS',
                                    'COMPENSATION COMMITTEE', 'COMPENSATION DISCUSSION', 'COMPENSATION-STOCK COMPENSATION',
                                    'CORPORATE GOVERNANCE', 'CORPORATE SERVICES', 'CORPORATE SERVICES OFFICER',
                                    'COMPETITION MERCHANT SERVICES', 'DEATH OR DISABILITY',
                                    # Ajouter les faux positifs financiers
                                    'ACCOUNTING ADJUSTMENT', 'ACCOUNTING STANDARDS', 'ACCOUNTS RECEIVABLE',
                                    'AMOUNT CAPITAL', 'AMOUNT SHARES', 'AVERAGE PRICE', 'BASED COMPENSATION',
                                    'CAPITAL STOCK', 'COMMON STOCK', 'COMPREHENSIVE INCOME', 'CONSOLIDATED STATEMENT',
                                    'CONSOLIDATED STATEMENTS', 'CONSOLIDATION', 'CONTENTS BANK', 'CONTENTS ITEM',
                                    'CONTENTS MERCHANT', 'CONTENTS NET', 'CONTENTS PART', 'CONTENTS SALES',
                                    'CONTENTS SEGMENT', 'CONTENTS THE', 'CONTENTS TRA', 'CONTENTS WE',
                                    'CUSTOMER INCENTIVES', 'EARNINGS INCOME', 'EQUITY INCENTIVE PLAN',
                                    'EQUITY SHARES', 'INCOME TAX', 'INCOME TAXES', 'INTEREST COVERAGE',
                                    'INTEREST RATE', 'INTERNAL CONTROL', 'INTERNAL REVENUE', 'INVESTOR RELATIONS',
                                    'MANAGEMENT\'S REPORT', 'MARKETING SALES', 'MERCHANT SERVICES TOTAL',
                                    'MERCHANT SERVICES YEAR', 'MERCHANT SERVICESFINANCIAL', 'NET INCOME PER SHARE',
                                    'NON-OPERATING INCOME', 'OCI COMPONENT', 'OFFICE SERVICES', 'PARENT COMPANY',
                                    'PERFORMANCE SHARE', 'PERIOD LEVERAGE', 'PRINCIPAL AGENT', 'PRO FORMA ADJUSTMENTS',
                                    'PUBLIC COMPANY ACCOUNTING', 'RESTRICTED STOCK', 'RETAINED COMPREHENSIVE',
                                    'SECONDARY OFFERING', 'SHARES AMOUNT', 'SIGNIFICANT ACCOUNTING',
                                    'SUBSIDIARIES REPORT', 'TAX RECEIVABLE', 'UNIT INCENTIVE PLAN',
                                    'VISA DEBIT PROCESSING', 'MINE SAFETY DISCLOSURES', 'CONTROLLER', 'STATE',
                                    'COMPANY', 'PRINCIPAL'
                                ]
                                if any(fp in company_upper for fp in false_positives):
                                    continue
                                
                                # ÉTAPE 5: Vérifier que le nom ne commence pas par "the" suivi d'un terme générique
                                # MAIS autoriser "The Bank of...", "The Company...", etc.
                                if len(words_lower) >= 2 and words_lower[0] == 'the':
                                    second_word = words_lower[1]
                                    # Termes génériques à exclure
                                    invalid_after_the = ['business', 'combined', 'disclosure', 'incremental',
                                                         'london', 'offer', 'original', 'securities', 'u.s', 'us',
                                                         'backstop', 'bridge', 'backstop commitment', 'bridge commitment',
                                                         'executive', 'operations', 'panel', 'registrant']
                                    # Termes valides après "The" (noms d'entreprises)
                                    valid_after_the = ['bank', 'company', 'corporation', 'trust', 'capital',
                                                      'securities', 'financial', 'services', 'group', 'holdings']
                                    
                                    if second_word in invalid_after_the:
                                        continue
                                    # Si c'est un terme valide (Bank, Company, etc.), continuer la validation
                                
                                # ÉTAPE 6: Extraire les mots avant le suffixe et valider
                                words_before_suffix = []
                                for word in words:
                                    word_lower = word.lower().rstrip('.,;:')
                                    if word_lower not in ['inc', 'llc', 'llp', 'corp', 'corporation', 'ltd', 'limited', 
                                                          'co', 'company', 'companies', 'group', 'holdings', 'enterprises',
                                                          'partners', 'partnership', 'incorporated']:
                                        words_before_suffix.append(word)
                                
                                if len(words_before_suffix) >= 1:
                                    # Vérifier que le premier mot réel n'est pas invalide
                                    first_real_word = words_before_suffix[0].lower().rstrip('.,;:')
                                    
                                    # Exclure si le premier mot est un terme invalide
                                    if first_real_word in invalid_first_words:
                                        continue
                                    
                                    # Exclure si le premier mot est un article/verbe suivi d'un terme générique
                                    if first_real_word in ['the', 'a', 'an'] and len(words_before_suffix) > 1:
                                        second_real_word = words_before_suffix[1].lower().rstrip('.,;:')
                                        if second_real_word in invalid_company_words:
                                            continue
                                    
                                    # ÉTAPE 7: Validation contextuelle - vérifier le contexte dans le texte
                                    company_pos = text.find(company)
                                    if company_pos != -1:
                                        context_start = max(0, company_pos - 200)
                                        context_end = min(len(text), company_pos + len(company) + 200)
                                        context = text[context_start:context_end].lower()
                                        
                                        # Indicateurs négatifs (suggèrent que ce n'est PAS un nom de compagnie)
                                        negative_context_indicators = [
                                            'agreement', 'letter', 'release', 'document', 'amendment',
                                            'commitment', 'combination', 'condition', 'operation',
                                            'disclosure', 'scheme', 'rule', 'act', 'commission',
                                            'file number', 'employer identification', 'delaware',
                                            'london stock exchange', 'securities exchange act',
                                            'press release', 'annual meeting', 'stockholder',
                                            'the business combination', 'the original loan',
                                            'the backstop commitment', 'the bridge commitment',
                                            'the disclosure table', 'the offer period',
                                            'the incremental amendment', 'the securities exchange',
                                            'amended and restated', 'backstop commitment letter',
                                            'bridge commitment letter', 'loan agreement',
                                            'financial condition', 'operations'
                                        ]
                                        
                                        # Si le contexte contient des indicateurs négatifs, exclure
                                        if any(ind in context for ind in negative_context_indicators):
                                            # Sauf si c'est clairement dans un contexte de nom de compagnie
                                            positive_context_indicators = [
                                                'name of registrant', 'name of issuer', 'name of company',
                                                'company name', 'registrant name', 'issuer name',
                                                'exact name', 'entity name'
                                            ]
                                            if not any(pos_ind in context for pos_ind in positive_context_indicators):
                                                continue
                                    
                                    # ÉTAPE 8: Validation finale - le nom doit ressembler à un vrai nom de compagnie
                                    # Un vrai nom de compagnie devrait avoir au moins un mot substantif (nom propre)
                                    # qui n'est pas dans la liste des mots interdits
                                    valid_substantive_words = [w for w in words_before_suffix 
                                                              if w.lower().rstrip('.,;:') not in excluded_company_terms 
                                                              and len(w) >= 2]
                                    
                                    if len(valid_substantive_words) >= 1:
                                        # Vérifier que le premier mot substantif commence par une majuscule
                                        if valid_substantive_words[0][0].isupper():
                                            cleaned_companies.add(company)
                    
                    # Validation finale avec spaCy NER pour company names (si disponible)
                    if SPACY_AVAILABLE and SPACY_NLP and cleaned_companies:
                        validated_companies = set()
                        
                        for company in cleaned_companies:
                            # Chercher le nom dans le texte original avec contexte
                            company_pos = text.find(company)
                            if company_pos != -1:
                                context_start = max(0, company_pos - 200)
                                context_end = min(len(text), company_pos + len(company) + 200)
                                context_text = text[context_start:context_end]
                                context_lower = context_text.lower()
                                
                                # Vérifier d'abord le contexte pour éviter les faux positifs
                                negative_context = [
                                    'agreement', 'letter', 'release', 'document', 'amendment',
                                    'commitment', 'combination', 'condition', 'operation',
                                    'disclosure', 'scheme', 'rule', 'act', 'commission',
                                    'file number', 'employer identification', 'delaware',
                                    'london stock exchange', 'securities exchange act',
                                    'press release', 'annual meeting', 'stockholder',
                                    'the business combination', 'the original loan',
                                    'the backstop commitment', 'the bridge commitment'
                                ]
                                
                                # Si le contexte est négatif, exclure même si spaCy le détecte
                                if any(neg in context_lower for neg in negative_context):
                                    # Sauf si c'est clairement dans un contexte de nom de compagnie
                                    positive_context = [
                                        'name of registrant', 'name of issuer', 'name of company',
                                        'company name', 'registrant name', 'issuer name',
                                        'exact name', 'entity name'
                                    ]
                                    if not any(pos in context_lower for pos in positive_context):
                                        continue
                                
                                # Analyser avec spaCy
                                doc = SPACY_NLP(context_text)
                                
                                # Vérifier si spaCy détecte ce nom comme une organisation
                                found_in_spacy = False
                                for ent in doc.ents:
                                    if ent.label_ == "ORG":
                                        detected_org = ent.text.strip()
                                        detected_org = re.sub(r'\s+', ' ', detected_org)
                                        
                                        # Vérifier si notre nom correspond
                                        if company.lower() in detected_org.lower() or detected_org.lower() in company.lower():
                                            # Validation supplémentaire: vérifier que spaCy n'a pas détecté un faux positif
                                            detected_lower = detected_org.lower()
                                            if not any(phrase in detected_lower for phrase in excluded_phrases):
                                                if detected_org[0].isupper():  # Doit commencer par majuscule
                                                    found_in_spacy = True
                                                    validated_companies.add(company)
                                                    break
                                
                                # Si spaCy ne l'a pas trouvé mais que le contexte est très positif, on peut quand même l'accepter
                                if not found_in_spacy:
                                    # Vérifier le contexte pour des indicateurs très positifs
                                    very_positive_context = [
                                        'exact name of registrant', 'name of the registrant',
                                        'name of the issuer', 'name of the company',
                                        'registrant\'s name', 'issuer\'s name', 'company\'s name'
                                    ]
                                    if any(pos in context_lower for pos in very_positive_context):
                                        # Vérifier que le nom ne contient pas de termes interdits
                                        company_lower = company.lower()
                                        company_words = company.split()
                                        company_words_lower = [w.lower().rstrip('.,;:') for w in company_words]
                                        if not any(phrase in company_lower for phrase in excluded_phrases):
                                            if len(company_words_lower) > 0 and company_words_lower[0] not in invalid_first_words:
                                                validated_companies.add(company)
                        
                        # Utiliser les companies validées par spaCy, ou garder celles qui ont passé les filtres
                        if validated_companies:
                            # Ajouter les companies validées par spaCy
                            cleaned_companies.update(validated_companies)
                        # Note: On garde aussi les companies qui ont passé les filtres stricts précédents
                        # car elles peuvent être valides même si spaCy ne les a pas détectées

                    # ========== FINAL INTELLIGENT FILTER FOR ALL COMPANIES ==========
                    # Apply smart final checks to eliminate remaining false positives
                    final_filtered_companies = set()

                    for company in cleaned_companies:
                        company_lower = company.lower().strip()
                        words = company.split()
                        words_lower = [w.lower().rstrip('.,;:') for w in words]
                        first_word = words_lower[0] if words_lower else ''

                        # ULTRA-STRICT: Reject exact matches of standalone generic words
                        standalone_generic = {
                            'company', 'corporate', 'consolidated', 'community',
                            'computer', 'compliance', 'composition', 'control',
                            'conducted', 'conclusion', 'contracts', 'customers',
                            'group', 'digital', 'definition', 'companies'
                        }
                        if company_lower in standalone_generic:
                            continue  # Reject standalone "Company", "Group", etc.

                        # Reject exact matches of generic two-word combinations
                        two_word_generic = {
                            'group company', 'company group', 'corporate group',
                            'group corporate', 'best companies', 'best company',
                            'company inc', 'corporate inc', 'group inc'
                        }
                        if company_lower in two_word_generic:
                            continue  # Reject "Group Company", "Company Group", etc.

                        # Reject if it's JUST a generic word (even without suffix)
                        single_generic_words = {
                            'company', 'corporate', 'consolidated', 'community',
                            'computer', 'compliance', 'composition', 'control',
                            'conducted', 'conclusion', 'contracts', 'customers',
                            'group', 'digital', 'definition'
                        }
                        # Reject single word OR if first word is generic and <=2 words
                        if first_word in single_generic_words and len(words) <= 2:
                            # Exception: if second word is a real company indicator
                            if len(words) == 2:
                                real_company_indicators = {'bank', 'securities', 'financial', 'services', 'holdings', 'capital'}
                                if words_lower[1] not in real_company_indicators:
                                    continue  # Reject "Company Inc.", "Corporate Ltd.", etc.
                            else:
                                continue  # Reject single word like "Company"

                        # Reject if starts with generic word even if longer (e.g., "Corporate.118 Worldpay...")
                        if first_word in {'corporate', 'consolidated', 'company'} and len(words) <= 5:
                            # Exception: if contains a known company suffix in the middle, keep it
                            if not any(word in ['worldpay', 'jpmorgan', 'vantiv', 'bank', 'securities'] for word in words_lower[1:]):
                                continue

                        # Reject if ALL words are generic (e.g., "Group Company")
                        all_generic_words = {'company', 'corporate', 'group', 'consolidated', 'community'}
                        if all(w in all_generic_words for w in words_lower if w not in ['.', ',', 'inc', 'llc', 'ltd']):
                            continue  # Reject "Group Company", "Corporate Group", etc.

                        # Reject phrases with verbs (indicates it's a sentence, not a company name)
                        verb_phrases = {'joined', 'based', 'approach', 'support'}
                        if any(verb in words_lower for verb in verb_phrases):
                            continue  # Reject "Chief Operating Officer Joined Worldpay Group"

                        # Reject overly generic multi-word phrases
                        generic_phrases = {
                            'corporate responsibility council',
                            'group company',
                            'best company index',
                            'derek woodward group company'
                        }
                        if company_lower in generic_phrases:
                            continue

                        # ACCEPT - passed all final filters
                        final_filtered_companies.add(company)

                    # Add final filtered companies to results
                    for company in final_filtered_companies:
                        page_findings.append({'type': 'company_name', 'value': company, 'page': page_num + 1})
                    
                    # ===== CIK NUMBERS (SEC Central Index Key) =====
                    # Format: 7-10 chiffres (ex: 1065280)
                    # Chercher dans un contexte spécifique pour éviter faux positifs
                    # REMOVED (duplicate): cik_context_pattern = re.compile(
                    # REMOVED (duplicate): r'(?:CIK|Central\s+Index\s+Key|File\s+Number)[:\s]+(\d{7,10})',
                    # REMOVED (duplicate): re.IGNORECASE
                    # REMOVED (duplicate): )
                    cik_found = False
                    for match in cik_context_pattern.finditer(text):
                        cik = match.group(1)
                        page_findings.append({'type': 'cik_number', 'value': cik, 'page': page_num + 1})
                        cik_found = True
                    
                    # Si pas de contexte, chercher les nombres de 7-10 chiffres près de "Commission"
                    if not cik_found:
                        cik_generic_pattern = re.compile(r'\b(\d{7,10})\b')
                        for match in cik_generic_pattern.finditer(text):
                            context = text[max(0, match.start() - 100):match.end() + 100]
                            if 'Commission' in context or 'SEC' in context or 'File' in context:
                                cik = match.group(1)
                                page_findings.append({'type': 'cik_number', 'value': cik, 'page': page_num + 1})
                                break  # Prendre seulement le premier
                    
                    # ===== CUSIP/ISIN CODES =====
                    # CUSIP: 9 caractères alphanumériques (ex: 64110LAH9)
                    # ISIN: 2 lettres + 9 alphanumériques + 1 chiffre (ex: US64110LAH96)
                    cusip_pattern = re.compile(r'\b([0-9A-Z]{6,9}[A-Z0-9]{2}[0-9])\b')
                    isin_pattern = re.compile(r'\b(US[0-9A-Z]{9}[0-9])\b')
                    
                    for match in cusip_pattern.finditer(text):
                        cusip = match.group(1)
                        # Vérifier que c'est bien un code financier (contexte)
                        context = text[max(0, match.start() - 50):match.end() + 50]
                        if any(kw in context.upper() for kw in ['CUSIP', 'SECURITY', 'BOND', 'NOTE', 'DEBT']):
                            page_findings.append({'type': 'cusip_code', 'value': cusip, 'page': page_num + 1})
                    
                    for match in isin_pattern.finditer(text):
                        isin = match.group(1)
                        page_findings.append({'type': 'isin_code', 'value': isin, 'page': page_num + 1})

                    # ===== ISIN CODES - EXPANDED (All Countries) =====
                    # Format: 2-letter country code + 9 alphanumeric + 1 check digit
                    # Ex: GB0002374006 (UK), DE0005140008 (Germany), FR0000120271 (France)
                    isin_all_pattern = re.compile(r'\b([A-Z]{2}[A-Z0-9]{9}[0-9])\b')

                    for match in isin_all_pattern.finditer(text):
                        isin = match.group(1)
                        # Skip if already captured as US ISIN
                        if isin.startswith('US'):
                            continue
                        # Context validation - must appear near ISIN-related keywords
                        context = text[max(0, match.start() - 60):match.end() + 60]
                        if any(kw in context.upper() for kw in ['ISIN', 'INTERNATIONAL SECURITIES', 'SECURITY IDENTIFIER']):
                            page_findings.append({'type': 'isin_code', 'value': isin, 'page': page_num + 1})

                    # ===== SEDOL CODES (UK Securities) =====
                    # Format: 7 characters (alphanumeric, excluding vowels)
                    # Ex: 2046251, B0WNLY7
                    sedol_pattern = re.compile(r'\b([0-9BCDFGHJKLMNPQRSTVWXYZ]{7})\b')

                    for match in sedol_pattern.finditer(text):
                        sedol = match.group(1)
                        # Context validation - must appear near SEDOL keyword
                        context = text[max(0, match.start() - 60):match.end() + 60]
                        if any(kw in context.upper() for kw in ['SEDOL', 'UK SECURITY', 'LONDON STOCK']):
                            page_findings.append({'type': 'sedol_code', 'value': sedol, 'page': page_num + 1})

                    # ===== FIGI CODES (Bloomberg Identifiers) =====
                    # Format: BBG + 9 alphanumeric characters (base 36)
                    # Ex: BBG000BLNQ16 (Apple Inc.)
                    figi_pattern = re.compile(r'\b(BBG[0-9A-Z]{9})\b')

                    for match in figi_pattern.finditer(text):
                        figi = match.group(1)
                        # FIGI format is strict - BBG prefix is mandatory
                        # No additional context needed as format is unique
                        page_findings.append({'type': 'figi_code', 'value': figi, 'page': page_num + 1})

                    # ===== LEI CODES (Legal Entity Identifiers) =====
                    # Format: 20 alphanumeric characters
                    # Ex: 549300VGEJKB7SVUZR78
                    # Structure: 4-char LOU ID + 2 reserved + 12-char entity ID + 2-char checksum
                    lei_pattern = re.compile(r'\b([A-Z0-9]{20})\b')

                    for match in lei_pattern.finditer(text):
                        lei = match.group(1)
                        # Very strict context validation required (20 random chars = high false positive risk)
                        context = text[max(0, match.start() - 80):match.end() + 80]
                        context_upper = context.upper()

                        # Must appear near LEI-specific keywords
                        lei_keywords = ['LEI', 'LEGAL ENTITY IDENTIFIER', 'ENTITY IDENTIFIER CODE']
                        if any(kw in context_upper for kw in lei_keywords):
                            # Additional validation: check for all uppercase (LEIs are always uppercase)
                            if lei.isupper() and lei.isalnum():
                                page_findings.append({'type': 'lei_code', 'value': lei, 'page': page_num + 1})

                    # ===== PATENT NUMBERS (US Patents) =====
                    # Format: US + 7-8 digits + optional letter + optional digit
                    # Ex: US1234567, US12345678A, US7654321B2
                    patent_pattern = re.compile(r'\b(US\d{7,8}[A-Z]?\d?)\b')

                    for match in patent_pattern.finditer(text):
                        patent = match.group(1)
                        # Context validation - must appear near patent-related keywords
                        context = text[max(0, match.start() - 80):match.end() + 80]
                        context_upper = context.upper()

                        patent_keywords = ['PATENT', 'PATENT NO', 'PATENT NUMBER', 'U.S. PATENT',
                                          'ISSUED', 'INTELLECTUAL PROPERTY', 'IP PORTFOLIO']
                        if any(kw in context_upper for kw in patent_keywords):
                            page_findings.append({'type': 'patent_number', 'value': patent, 'page': page_num + 1})

                    # ===== SEC.GOV URLs =====
                    # Format: https://www.sec.gov/* or http://sec.gov/*
                    # Ex: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001018724
                    sec_url_pattern = re.compile(
                        r'(https?://(?:www\.)?sec\.gov/[^\s<>"\')]+)',
                        re.IGNORECASE
                    )

                    for match in sec_url_pattern.finditer(text):
                        url = match.group(1)
                        # Clean up trailing punctuation that might be captured
                        url = url.rstrip('.,;:!?')
                        # SEC URLs are always sensitive (contain CIK, file references, etc.)
                        page_findings.append({'type': 'sec_url', 'value': url, 'page': page_num + 1})

                    # ===== CITY NAMES - SUPPRESSION COMPLÈTE =====
                    # NE PAS détecter les villes seules - trop de faux positifs
                    # Les villes sont capturées dans les adresses complètes seulement
                    
                    # ===== PARTIAL ADDRESSES - SEULEMENT si pas dans adresse complète =====
                    
                    partial_addresses_found = set()
                    
                    # Pattern strict: "Ville, État ZIP" seulement
                    city_state_zip_pattern = re.compile(
                        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}),\s+([A-Z]{2})\s+(\d{5}(?:-\d{4})?)\b'
                    )
                    
                    for match in city_state_zip_pattern.finditer(text):
                        city = match.group(1)
                        state = match.group(2)
                        zip_code = match.group(3)
                        
                        partial = f"{city}, {state} {zip_code}"
                        
                        # Vérifier que ce n'est pas déjà dans une adresse complète
                        already_in_full = any(partial in addr for addr in addresses_found)

                        if not already_in_full and state in valid_states_abbr:
                            # Vérifier qu'il n'y a pas un numéro de rue juste avant
                            ctx_before = text[max(0, match.start() - 50):match.start()]
                            has_street_number = bool(re.search(r'\b\d{1,5}\s+[A-Za-z]+\s+(Street|Avenue|Drive|Road|Lane|Boulevard)\s*$', ctx_before, re.IGNORECASE))
                            
                            if not has_street_number:
                                partial_addresses_found.add(partial)
                    
                    for partial in partial_addresses_found:
                        page_findings.append({'type': 'partial_address', 'value': partial, 'page': page_num + 1})
                    
                    # ===== PROFESSIONAL FIRMS - VERSION ULTRA STRICTE =====
                    
                    firms_found = set()
                    
                    # Pattern: Chercher SEULEMENT les noms propres se terminant par LLP/LLC/etc.
                    # ET qui sont précédés/suivis de ponctuation ou début/fin de phrase
                    firm_pattern = re.compile(
                        r'(?:^|[.\n\(])\s*([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,4})[,\s]+(LLP|LLC|L\.L\.P\.|L\.L\.C\.|PLLC)\b',
                        re.MULTILINE
                    )
                    
                    for match in firm_pattern.finditer(text):
                        firm_name = f"{match.group(1)} {match.group(2)}"
                        firm_name = re.sub(r'\s+', ' ', firm_name).strip()
                        
                        # Validation stricte
                        if 10 <= len(firm_name) <= 60:
                            # Vérifier que c'est bien un nom propre (tous les mots commencent par majuscule)
                            words = firm_name.replace(',', '').split()
                            if all(w[0].isupper() for w in words if len(w) > 2):
                                # Vérifier le contexte (50 caractères avant/après)
                                ctx_start = max(0, match.start() - 50)
                                ctx_end = min(len(text), match.end() + 50)
                                context = text[ctx_start:ctx_end].upper()
                                
                                # Déterminer le type
                                firm_type = 'professional_firm'
                                
                                if any(kw in context for kw in ['AUDIT', 'ACCOUNTANT', 'KPMG', 'ERNST', 'DELOITTE', 'PWC', 'PRICEWATERHOUSE']):
                                    firm_type = 'auditor'
                                elif any(kw in context for kw in ['UNDERWRITER', 'UNDERWRITING', 'BOOK-RUNNING', 'LEAD MANAGER']):
                                    firm_type = 'underwriter'
                                elif any(kw in context for kw in ['COUNSEL', 'ATTORNEY', 'LAW FIRM', 'LEGAL']):
                                    firm_type = 'law_firm'
                                elif any(kw in context for kw in ['BANK', 'TRUST', 'TRUSTEE', 'PAYING AGENT']):
                                    firm_type = 'financial_institution'
                                
                                # Filtrer les faux positifs
                                false_positives = ['Vantiv LLC', 'Vantiv Holding LLC', 'Mercury Payment Systems LLC']
                                if firm_name not in false_positives:
                                    if firm_name not in firms_found:
                                        firms_found.add(firm_name)
                                        page_findings.append({'type': firm_type, 'value': firm_name, 'page': page_num + 1})
                    
                    # ===== SHOW/PRODUCT TITLES - DÉSACTIVÉ =====
                    # DÉSACTIVÉ - Trop de faux positifs
                    # show_pattern = re.compile(r'[""]([A-Z][A-Za-z\s]+(?:of|is|the|and)[A-Za-z\s]+)[""]')
                    # for match in show_pattern.finditer(text):
                    #     title = match.group(1).strip()
                    #     if 10 <= len(title) <= 50:
                    #         page_findings.append({'type': 'quoted_title', 'value': title, 'page': page_num + 1})
                    
                    # ===== ANCIENNE VALIDATION SPACY - PARTIELLEMENT DÉSACTIVÉE =====
                    # PERSON detection est désactivée (faux positifs) - nouvelle implémentation utilisée (lignes 1060-1100)
                    # ORG detection reste ACTIVE - détection complémentaire pour les entreprises
                    if SPACY_AVAILABLE and SPACY_NLP:
                        try:
                            # Analyser le texte complet de la page avec spaCy
                            # Limiter à 1M de caractères pour éviter les problèmes de mémoire
                            text_to_analyze = text[:1000000] if len(text) > 1000000 else text
                            doc = SPACY_NLP(text_to_analyze)

                            # Collecter les entités détectées par spaCy
                            spacy_persons = set()  # DÉSACTIVÉ - not used
                            spacy_orgs = set()

                            for ent in doc.ents:
                                if False and ent.label_ == "PERSON":  # DISABLED - PERSON detection moved to lines 1060-1100
                                    person_name = ent.text.strip()
                                    person_name = re.sub(r'\s+', ' ', person_name)
                                    # Validation basique
                                    words = person_name.split()
                                    if len(words) >= 2 and len(words) <= 5:
                                        # Vérifier que ce n'est pas déjà détecté
                                        already_found = any(
                                            person_name.lower() in f.get('value', '').lower() or 
                                            f.get('value', '').lower() in person_name.lower()
                                            for f in page_findings if f.get('type') in ['person_name']
                                        )
                                        if not already_found:
                                            # Vérifier le contexte pour éviter les faux positifs
                                            start_char = ent.start_char
                                            end_char = ent.end_char
                                            context_start = max(0, start_char - 100)
                                            context_end = min(len(text_to_analyze), end_char + 100)
                                            context = text_to_analyze[context_start:context_end].lower()
                                            
                                            # Indicateurs positifs (MANDATORY)
                                            positive_indicators = [
                                                'director', 'officer', 'executive', 'employee',
                                                'trustee', 'shareholder', 'by:', 'name:', 'signed',
                                                'beneficial owner', 'signatory', 'authorized',
                                                'representative', 'agent', '/s/'
                                            ]
                                            # Indicateurs négatifs (expanded)
                                            negative_indicators = [
                                                'table of contents', 'balance sheet', 'income statement',
                                                'cash flow', 'note', 'footnote', 'page', 'section',
                                                'form 10-k', 'form 10-q', 'form 8-k',
                                                'part i', 'part ii', 'part iii', 'part iv',
                                                'exhibit', 'schedule', 'appendix', 'index',
                                                'consolidated', 'financial statements', 'statement of operations'
                                            ]

                                            has_positive = any(ind in context for ind in positive_indicators)
                                            has_negative = any(ind in context for ind in negative_indicators)

                                            # Check against false positive lists (EXACT MATCH ONLY)
                                            person_name_lower = person_name.lower()
                                            is_false_positive = (
                                                person_name_lower in PERSON_NAME_FALSE_POSITIVES or
                                                person_name_lower in DOCUMENT_STRUCTURE_TERMS or
                                                person_name_lower in GENERIC_BUSINESS_TERMS
                                                # Don't check partial matches - too aggressive
                                            )

                                            # Validate capitalization (reject all-caps or excessive capitals)
                                            cap_ratio = sum(1 for c in person_name if c.isupper()) / len(person_name) if person_name else 0
                                            valid_capitalization = cap_ratio <= 0.5

                                            # Check that no word in the name is an invalid word
                                            words = person_name.split()
                                            words_lower = [w.lower().strip('.,;:') for w in words]
                                            has_invalid_word = any(w in INVALID_NAME_WORDS for w in words_lower)

                                            # RELAXED: Accept if no negative AND not false positive AND valid capitalization AND no invalid words
                                            # Positive indicator is helpful but not mandatory for spaCy-detected persons
                                            if not has_negative and not is_false_positive and valid_capitalization and not has_invalid_word:
                                                spacy_persons.add(person_name)
                                
                                elif ent.label_ == "ORG":
                                    org_name = ent.text.strip()
                                    org_name = re.sub(r'\s+', ' ', org_name)
                                    # Validation basique
                                    if 5 <= len(org_name) <= 80:
                                        # Vérifier que ce n'est pas déjà détecté
                                        already_found = any(
                                            org_name.lower() in f.get('value', '').lower() or 
                                            f.get('value', '').lower() in org_name.lower()
                                            for f in page_findings if f.get('type') == 'company_name'
                                        )
                                        if not already_found:
                                            # Vérifier que c'est une organisation valide (contient des mots substantifs)
                                            words = org_name.split()
                                            if len(words) >= 1:
                                                # Vérifier le contexte
                                                start_char = ent.start_char
                                                end_char = ent.end_char
                                                context_start = max(0, start_char - 100)
                                                context_end = min(len(text_to_analyze), end_char + 100)
                                                context = text_to_analyze[context_start:context_end].lower()
                                                
                                                # Check against false positive lists FIRST (EXACT MATCH ONLY)
                                                org_name_lower = org_name.lower()
                                                is_false_positive = (
                                                    org_name_lower in DOCUMENT_STRUCTURE_TERMS or
                                                    org_name_lower in GENERIC_BUSINESS_TERMS
                                                    # Don't check partial matches - too aggressive
                                                )

                                                # Check if first word is invalid
                                                first_word = org_name.split()[0].lower().rstrip('.,;:') if org_name.split() else ''
                                                has_invalid_first_word = first_word in INVALID_COMPANY_FIRST_WORDS

                                                # Only proceed if not a false positive and valid first word
                                                if not is_false_positive and not has_invalid_first_word:
                                                    # Indicateurs négatifs (expanded)
                                                    negative_indicators = [
                                                        'table of contents', 'balance sheet', 'income statement',
                                                        'cash flow', 'note', 'footnote', 'form 10-k', 'form 10-q',
                                                        'exhibit', 'schedule', 'appendix', 'part i', 'part ii'
                                                    ]

                                                    has_negative = any(ind in context for ind in negative_indicators)

                                                    # RELAXED: Accept if no negative context
                                                    # Don't require positive indicators - just filter out bad contexts
                                                    if not has_negative:
                                                        spacy_orgs.add(org_name)
                            
                            # PERSON detection DISABLED - using new implementation at lines 1060-1100
                            # for person_name in spacy_persons:
                            #     page_findings.append({'type': 'person_name', 'value': person_name, 'page': page_num + 1})

                            # Filtrer les organisations détectées par spaCy avec les mêmes règles strictes
                            for org_name in spacy_orgs:
                                org_lower = org_name.lower()
                                org_upper = org_name.upper()

                                # Check against comprehensive false positive lists (EXACT MATCH ONLY)
                                is_false_positive = (
                                    org_lower in DOCUMENT_STRUCTURE_TERMS or
                                    org_lower in GENERIC_BUSINESS_TERMS
                                    # Don't check partial matches - filters out legitimate companies
                                )

                                if is_false_positive:
                                    continue

                                # Additional specific false positives (highly specific terms)
                                specific_false_positives = [
                                    'SECURITIES AND EXCHANGE COMMISSION', 'COMMISSION FILE',
                                    'UNITED STATES', 'NEW YORK', 'LOS ANGELES',
                                    'IS AN EMERGING GROWTH CO', 'WILL CO', 'THE CO',
                                    'AN EMERGING', 'GROWTH CO', 'IS AN',
                                    'AMENDED AND RESTATED', 'BACKSTOP COMMITMENT', 'BACKSTOP FEE',
                                    'BRIDGE COMMITMENT', 'BRIDGE DOCUMENTS', 'BRIDGE LENDERS',
                                    'BUSINESS COMBINATION', 'COMBINED COMPANY', 'COMMISSION FILE NUMBER',
                                    'DEALING DISCLOSURES', 'DISCLOSURE TABLE',
                                    'INCREMENTAL AMENDMENT', 'IRS EMPLOYER',
                                    'LOAN AGREEMENT', 'LONDON STOCK', 'OFFER PERIOD', 'ORIGINAL LOAN',
                                    'PRESS RELEASE', 'RULE 8.3', 'SCHEME', 'SECURITIES EXCHANGE',
                                    'THE DISCLOSURE', 'THE INCREMENTAL', 'THE LONDON',
                                    'THE OFFER', 'THE ORIGINAL', 'THE SECURITIES', 'THE U.S',
                                    'THE US', 'THE U.S. SECURITIES',
                                    'THE BACKSTOP', 'THE BRIDGE', 'THE BUSINESS COMBINATION',
                                    'THE "BUSINESS', 'THE "ORIGINAL'
                                ]
                                if any(fp in org_upper for fp in specific_false_positives):
                                    continue

                                # Vérifier que le nom commence par une majuscule
                                if not org_name or not org_name[0].isupper():
                                    continue

                                # Vérifier que le premier mot n'est pas invalide
                                org_words = org_name.split()
                                if len(org_words) > 0:
                                    first_word = org_words[0].lower().rstrip('.,;:')
                                    if first_word in INVALID_COMPANY_FIRST_WORDS:
                                        continue

                                # Vérifier qu'il contient un suffixe d'entreprise ou est dans un contexte TRÈS positif
                                # Common company suffixes pattern
                                company_suffixes = r'\b(Inc|LLC|Corp|Corporation|Company|Co|Ltd|Limited|LP|LLP|PLLC|PC)\b'
                                has_suffix = bool(re.search(company_suffixes, org_name, re.IGNORECASE))

                                if not has_suffix:
                                    # Sans suffixe, être TRÈS strict - REQUIRE explicit registrant/issuer context
                                    org_pos = text_to_analyze.find(org_name)
                                    if org_pos != -1:
                                        context_start = max(0, org_pos - 200)
                                        context_end = min(len(text_to_analyze), org_pos + len(org_name) + 200)
                                        context_lower = text_to_analyze[context_start:context_end].lower()

                                        # VERY strict - only accept if explicitly identified as registrant/issuer
                                        very_positive = [
                                            'exact name of registrant', 'name of the registrant',
                                            'name of the issuer', 'name of the company',
                                            'registrant\'s name', 'issuer\'s name',
                                            'registrant as specified', 'issuer as specified'
                                        ]
                                        if not any(pos in context_lower for pos in very_positive):
                                            continue

                                # FINAL CHECK: Reject standalone generic words and generic combinations
                                org_name_lower = org_name.lower().strip()
                                standalone_generic = {
                                    'company', 'corporate', 'consolidated', 'community',
                                    'computer', 'compliance', 'composition', 'control',
                                    'conducted', 'conclusion', 'contracts', 'customers',
                                    'group', 'digital', 'definition', 'companies'
                                }
                                if org_name_lower in standalone_generic:
                                    continue  # Reject standalone "Company", "Group", etc.

                                # Reject generic two-word combinations
                                two_word_generic = {
                                    'group company', 'company group', 'corporate group',
                                    'group corporate', 'best companies', 'best company',
                                    'company inc', 'corporate inc', 'group inc'
                                }
                                if org_name_lower in two_word_generic:
                                    continue  # Reject "Group Company", etc.

                                page_findings.append({'type': 'company_name', 'value': org_name, 'page': page_num + 1})
                                
                        except Exception as e:
                            # Si spaCy échoue, continuer sans cette validation
                            if verbose:
                                logger.debug(f"spaCy NER failed on page {page_num + 1}: {e}")
                    
                    if page_findings:
                        sensitive_info_by_page[page_num + 1] = page_findings
                    
                    # Progress indicator (every 10 pages or last page)
                    if verbose and total_pages > 10 and ((page_num + 1) % 10 == 0 or page_num + 1 == total_pages):
                        progress = (page_num + 1) / total_pages * 100
                        print(f"\r   📄 Analyzing {total_pages} pages... {page_num + 1}/{total_pages} ({progress:.1f}%)", end='', flush=True)
                        
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num + 1}: {e}")
                    if verbose and total_pages > 10:
                        progress = (page_num + 1) / total_pages * 100
                        print(f"\r   📄 Analyzing {total_pages} pages... {page_num + 1}/{total_pages} ({progress:.1f}%) [error]", end='', flush=True)
                    continue
            
            # Complete progress indicator (seulement en mode verbose)
            if verbose and total_pages > 10:
                print(f"\r   📄 Analyzing {total_pages} pages... {total_pages}/{total_pages} (100%) ✓", flush=True)
                    
    except Exception as e:
        logger.error(f"Error during sensitive information detection: {e}")
    
    return sensitive_info_by_page

