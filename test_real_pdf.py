#!/usr/bin/env python3
"""
Test de détection sur un PDF réel
"""

from pathlib import Path
from src.analysis.sensitive_info_detector import detect_sensitive_information

print("=" * 80)
print("🔍 Test de Détection sur PDF Réel")
print("=" * 80)
print()

# Utiliser le Proxy Statement qui contient beaucoup de noms
pdf_path = Path("pdf/March 15, 2017 Form- DEF 14A (Proxy Statement).pdf")

if not pdf_path.exists():
    print(f"❌ PDF non trouvé: {pdf_path}")
    exit(1)

print(f"📄 PDF: {pdf_path.name}")
print()

# Analyser le PDF (mode verbose pour voir les détails)
print("Analyse en cours...")
results = detect_sensitive_information(pdf_path, verbose=True)

print()
print("=" * 80)
print("📊 Résultats")
print("=" * 80)
print()

# Compter les types d'informations trouvées
total_findings = sum(len(findings) for findings in results.values())
person_names = []
company_names = []
emails = []
phones = []
addresses = []

for page_num, findings in results.items():
    for finding in findings:
        if finding['type'] == 'person_name':
            person_names.append(finding['value'])
        elif finding['type'] == 'company_name':
            company_names.append(finding['value'])
        elif finding['type'] == 'email':
            emails.append(finding['value'])
        elif finding['type'] == 'phone':
            phones.append(finding['value'])
        elif finding['type'] == 'address':
            addresses.append(finding['value'])

print(f"📊 Total de résultats trouvés: {total_findings}")
print()
print(f"👤 Noms de personnes: {len(person_names)}")
if person_names:
    print("   Exemples:")
    for name in sorted(set(person_names))[:10]:
        print(f"      • {name}")
print()

print(f"🏢 Noms d'entreprises: {len(company_names)}")
if company_names:
    print("   Exemples:")
    for name in sorted(set(company_names))[:10]:
        print(f"      • {name}")
print()

print(f"📧 Emails: {len(emails)}")
if emails:
    print("   Exemples:")
    for email in sorted(set(emails))[:5]:
        print(f"      • {email}")
print()

print(f"📞 Téléphones: {len(phones)}")
print(f"🏠 Adresses: {len(addresses)}")
print()

# Vérifier si nos cas de test spécifiques sont détectés
print("=" * 80)
print("🧪 Vérification des Améliorations")
print("=" * 80)
print()

test_cases = {
    'Grant': False,  # Nom qui contient "grant"
    'Irving': False,  # Nom en -ing
    'Sterling': False,  # Nom en -ing
    'McDonald': False,  # Nom avec Mc
    'DeAngelo': False,  # Nom avec De
}

for name in person_names:
    name_lower = name.lower()
    if 'grant' in name_lower:
        test_cases['Grant'] = True
    if 'irving' in name_lower:
        test_cases['Irving'] = True
    if 'sterling' in name_lower:
        test_cases['Sterling'] = True
    if 'mcdonald' in name_lower:
        test_cases['McDonald'] = True
    if 'deangelo' in name_lower or 'de angelo' in name_lower:
        test_cases['DeAngelo'] = True

for test_name, found in test_cases.items():
    status = "✅ TROUVÉ" if found else "⚠️  NON TROUVÉ"
    print(f"{status}: {test_name}")

print()
print("=" * 80)
print("✅ Test terminé!")
print("=" * 80)
