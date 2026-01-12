#!/usr/bin/env python3
"""
Script de test pour vérifier les 6 nouvelles détections ajoutées
"""

import sys
import tempfile
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

from src.analysis.sensitive_info_detector import detect_sensitive_information

# Import pour créer des PDFs de test
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️  reportlab not available - installing...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "reportlab"], check=True)
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    REPORTLAB_AVAILABLE = True

def create_test_pdf(text: str) -> Path:
    """
    Crée un PDF temporaire avec le texte de test
    """
    # Créer un fichier temporaire
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False)
    temp_path = Path(temp_file.name)
    temp_file.close()

    # Créer le PDF
    c = canvas.Canvas(str(temp_path), pagesize=letter)

    # Écrire le texte (gérer les lignes longues)
    y_position = 750
    words = text.split()
    current_line = ""

    for word in words:
        test_line = current_line + " " + word if current_line else word
        if len(test_line) > 80:  # Ligne trop longue
            c.drawString(50, y_position, current_line)
            y_position -= 15
            current_line = word
        else:
            current_line = test_line

    # Écrire la dernière ligne
    if current_line:
        c.drawString(50, y_position, current_line)

    c.save()
    return temp_path

def test_detection(test_name, text, expected_type, expected_value=None, should_detect=True):
    """
    Teste une détection spécifique
    """
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")
    print(f"Text: {text[:100]}...")

    # Créer un PDF temporaire avec le texte
    pdf_path = create_test_pdf(text)

    try:
        # Détecter
        findings_by_page = detect_sensitive_information(pdf_path, verbose=False)

        # Convertir en liste plate
        findings = []
        for page_findings in findings_by_page.values():
            findings.extend(page_findings)

        # Filtrer par type
        type_findings = [f for f in findings if f['type'] == expected_type]
    finally:
        # Nettoyer le PDF temporaire
        pdf_path.unlink(missing_ok=True)

    if should_detect:
        if type_findings:
            print(f"✅ PASS - Détecté {len(type_findings)} occurrence(s) de type '{expected_type}':")
            for f in type_findings:
                print(f"   - {f['value']}")
                if expected_value and f['value'] != expected_value:
                    print(f"   ⚠️  WARNING: Expected '{expected_value}', got '{f['value']}'")
            return True
        else:
            print(f"❌ FAIL - Aucune détection de type '{expected_type}'")
            print(f"   Détections trouvées: {[f['type'] for f in findings]}")
            return False
    else:
        if type_findings:
            print(f"❌ FAIL - Ne devrait PAS détecter, mais a trouvé:")
            for f in type_findings:
                print(f"   - {f['value']}")
            return False
        else:
            print(f"✅ PASS - Correctement ignoré (pas de faux positif)")
            return True

def main():
    print("\n" + "="*80)
    print(" " * 20 + "🧪 TEST DES NOUVELLES DÉTECTIONS")
    print("="*80)

    results = []

    # ===== TEST 1: SEC.GOV URLs =====
    results.append(test_detection(
        "SEC.gov URL - Valid EDGAR Link",
        "Visit https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001018724 for more info.",
        "sec_url",
        "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001018724"
    ))

    results.append(test_detection(
        "SEC.gov URL - Archives Link",
        "Document available at http://sec.gov/Archives/edgar/data/1018724/000119312517065791/d293630d10k.htm.",
        "sec_url"
    ))

    results.append(test_detection(
        "SEC.gov URL - Should NOT detect fake domain",
        "Visit http://www.example.com/sec.gov/fake for info.",
        "sec_url",
        should_detect=False
    ))

    # ===== TEST 2: SEDOL CODES =====
    results.append(test_detection(
        "SEDOL Code - With Context",
        "The UK security has SEDOL: 2046251 assigned to it.",
        "sedol_code",
        "2046251"
    ))

    results.append(test_detection(
        "SEDOL Code - Alphanumeric with Context",
        "London Stock Exchange identifier SEDOL B0WNLY7 is used for trading.",
        "sedol_code",
        "B0WNLY7"
    ))

    results.append(test_detection(
        "SEDOL Code - Should NOT detect without context",
        "The number 2046251 appears in the document.",
        "sedol_code",
        should_detect=False
    ))

    results.append(test_detection(
        "SEDOL Code - Should NOT detect with vowels",
        "SEDOL: ABCDEFG is invalid because it contains vowels.",
        "sedol_code",
        should_detect=False
    ))

    # ===== TEST 3: FIGI CODES =====
    results.append(test_detection(
        "FIGI Code - Apple Inc.",
        "The Bloomberg identifier BBG000BLNQ16 represents Apple Inc.",
        "figi_code",
        "BBG000BLNQ16"
    ))

    results.append(test_detection(
        "FIGI Code - Alphabet Inc.",
        "Google parent company has FIGI BBG000BPH459 in the system.",
        "figi_code",
        "BBG000BPH459"
    ))

    results.append(test_detection(
        "FIGI Code - Should NOT detect if too short",
        "The code BBG123 is too short to be valid.",
        "figi_code",
        should_detect=False
    ))

    # ===== TEST 4: LEI CODES =====
    results.append(test_detection(
        "LEI Code - With Context",
        "The Legal Entity Identifier 549300VGEJKB7SVUZR78 is assigned to this entity.",
        "lei_code",
        "549300VGEJKB7SVUZR78"
    ))

    results.append(test_detection(
        "LEI Code - With LEI keyword",
        "LEI: 213800WAVVOPS85N2205 for this organization.",
        "lei_code",
        "213800WAVVOPS85N2205"
    ))

    results.append(test_detection(
        "LEI Code - Should NOT detect without context",
        "The random code 12345678901234567890 appears here.",
        "lei_code",
        should_detect=False
    ))

    results.append(test_detection(
        "LEI Code - Should NOT detect lowercase",
        "LEI: 549300vgejkb7svuzr78 is invalid (lowercase).",
        "lei_code",
        should_detect=False
    ))

    # ===== TEST 5: ISIN EXPANDED (Non-US) =====
    results.append(test_detection(
        "ISIN - UK (with context)",
        "The ISIN GB0002374006 represents Vodafone Group plc.",
        "isin_code",
        "GB0002374006"
    ))

    results.append(test_detection(
        "ISIN - Germany (with context)",
        "ISIN DE0005140008 is assigned to Deutsche Bank AG.",
        "isin_code",
        "DE0005140008"
    ))

    results.append(test_detection(
        "ISIN - France (with context)",
        "International Securities Identifier ISIN FR0000120271 for Total SE.",
        "isin_code",
        "FR0000120271"
    ))

    results.append(test_detection(
        "ISIN - US (should still work, no context needed)",
        "Apple Inc. US ISIN is US0378331005 in the market.",
        "isin_code",
        "US0378331005"
    ))

    results.append(test_detection(
        "ISIN - Non-US should NOT detect without context",
        "The code GB0002374006 appears randomly in text.",
        "isin_code",
        should_detect=False
    ))

    # ===== TEST 6: PATENT NUMBERS =====
    results.append(test_detection(
        "Patent Number - Basic format",
        "This invention is protected by U.S. Patent US1234567.",
        "patent_number",
        "US1234567"
    ))

    results.append(test_detection(
        "Patent Number - With type letter",
        "Patent No. US12345678A was issued last year.",
        "patent_number",
        "US12345678A"
    ))

    results.append(test_detection(
        "Patent Number - With revision",
        "Our intellectual property includes Patent US7654321B2.",
        "patent_number",
        "US7654321B2"
    ))

    results.append(test_detection(
        "Patent Number - Should NOT detect without context",
        "The code US1234567 appears in the document.",
        "patent_number",
        should_detect=False
    ))

    results.append(test_detection(
        "Patent Number - Should NOT detect if too short",
        "Patent US123 is invalid (too short).",
        "patent_number",
        should_detect=False
    ))

    # ===== RÉSUMÉ =====
    print("\n" + "="*80)
    print(" " * 30 + "📊 RÉSUMÉ DES TESTS")
    print("="*80)

    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0

    print(f"\n✅ Tests réussis: {passed}/{total} ({percentage:.1f}%)")
    print(f"❌ Tests échoués: {total - passed}/{total}")

    if passed == total:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS ! Les nouvelles détections fonctionnent correctement.")
        return 0
    else:
        print("\n⚠️  CERTAINS TESTS ONT ÉCHOUÉ ! Vérifier l'implémentation.")
        return 1

if __name__ == "__main__":
    exit(main())
