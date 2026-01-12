#!/usr/bin/env python3
"""
Analyse approfondie du PDF WorldPay pour comprendre le problème de détection
"""

from pathlib import Path
from src.analysis.sensitive_info_detector import detect_sensitive_information
import PyPDF2

pdf_path = Path("pdf/worldpay-ar16.pdf")

print("=" * 80)
print("🔍 Analyse Détaillée - WorldPay PDF")
print("=" * 80)
print()

# Analyser avec notre détecteur
print("📊 Analyse avec notre détecteur...")
results = detect_sensitive_information(pdf_path, verbose=False)

# Extraire tous les person names ET company names
person_names = []
company_names = []

for page_num, findings in results.items():
    for finding in findings:
        if finding['type'] == 'person_name':
            person_names.append({
                'name': finding['value'],
                'page': finding['page']
            })
        elif finding['type'] == 'company_name':
            company_names.append({
                'name': finding['value'],
                'page': finding['page']
            })

print(f"   Total détecté: {len(person_names)} person names")
print(f"   Total détecté: {len(company_names)} company names")
print()

# Analyser les résultats
print("📋 PERSON NAMES DÉTECTÉS:")
print()
for item in person_names:
    print(f"   Page {item['page']:3d}: {item['name']}")

print()
print("=" * 80)
print("🔍 ANALYSE DES PROBLÈMES")
print("=" * 80)
print()

# Catégoriser
problems = {
    'companies': [],  # Entreprises détectées comme personnes
    'roles': [],      # Rôles/titres sans noms
    'fragments': [],  # Fragments de texte
    'ok': []         # Vrais noms
}

known_companies = ['tenpay', 'unionpay', 'virtuoz', 'hackerank', 'benefit', 'trust']
roles = ['member', 'chair', 'governance', 'code']

for item in person_names:
    name_lower = item['name'].lower()

    # Check si c'est une entreprise
    if any(company in name_lower for company in known_companies):
        problems['companies'].append(item['name'])
    # Check si c'est un rôle
    elif any(role in name_lower for role in roles):
        problems['roles'].append(item['name'])
    # Check si c'est un fragment (mots collés, bizarre)
    elif len(name_lower.split()) == 1 or 'this' in name_lower.lower():
        problems['fragments'].append(item['name'])
    else:
        problems['ok'].append(item['name'])

print("❌ FAUX POSITIFS - Entreprises:")
for name in problems['companies']:
    print(f"   • {name}")
print()

print("❌ FAUX POSITIFS - Rôles/Titres:")
for name in problems['roles']:
    print(f"   • {name}")
print()

print("❌ FAUX POSITIFS - Fragments:")
for name in problems['fragments']:
    print(f"   • {name}")
print()

print("✅ VRAIS NOMS:")
for name in set(problems['ok']):
    count = problems['ok'].count(name)
    print(f"   • {name} ({count}x)")
print()

# Afficher les company names
print("=" * 80)
print("🏢 COMPANY NAMES DÉTECTÉS")
print("=" * 80)
print()

if company_names:
    # Compter les occurrences
    unique_companies = {}
    for item in company_names:
        name = item['name']
        if name not in unique_companies:
            unique_companies[name] = []
        unique_companies[name].append(item['page'])

    print(f"Total: {len(company_names)} détections ({len(unique_companies)} uniques)")
    print()

    # Afficher par ordre alphabétique
    for company in sorted(unique_companies.keys()):
        pages = unique_companies[company]
        print(f"   • {company}")
        print(f"     Pages: {', '.join(map(str, sorted(set(pages))))} ({len(pages)} occurrences)")
    print()
else:
    print("   Aucun company name détecté")
    print()

# Maintenant extraire du texte brut pour voir ce qu'on manque
print("=" * 80)
print("🔍 EXTRACTION BRUTE - Chercher les noms manqués")
print("=" * 80)
print()

try:
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)

        # Chercher dans les premières pages (directeurs, etc.)
        print("📄 Pages 1-20 (section des directeurs/executives):")
        print()

        for page_num in range(min(20, len(pdf_reader.pages))):
            text = pdf_reader.pages[page_num].extract_text()

            # Chercher des patterns de noms
            # Patterns communs: "Name Surname" avec contextes comme "Director", "CEO", etc.
            import re

            # Pattern 1: "Director: Name"
            director_pattern = r'(?:Director|CEO|CFO|Chairman|Officer|Executive|Member)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})'
            matches = re.findall(director_pattern, text, re.MULTILINE)

            if matches:
                print(f"   Page {page_num + 1}:")
                for match in matches[:10]:  # Limite à 10 par page
                    print(f"      • {match}")

        print()

except Exception as e:
    print(f"❌ Erreur lors de l'extraction: {e}")

print()
print("=" * 80)
print("💡 DIAGNOSTIC")
print("=" * 80)
print()
print(f"Détections actuelles: {len(person_names)}")
print(f"   ✅ Vrais noms: {len(set(problems['ok']))}")
print(f"   ❌ Faux positifs: {len(problems['companies']) + len(problems['roles']) + len(problems['fragments'])}")
print()
print("⚠️  PROBLÈME: Trop de faux positifs et probablement beaucoup de vrais noms manqués")
print()
print("Causes possibles:")
print("   1. Filtres trop permissifs pour certains cas")
print("   2. Entreprises détectées comme personnes (TenPay Europe, China UnionPay)")
print("   3. Rôles/titres détectés comme personnes (RM Member, RM Chair)")
print("   4. Fragments bizarres (Governance CodeThis)")
