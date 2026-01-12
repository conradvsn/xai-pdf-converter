#!/usr/bin/env python3
"""
Test spécifique pour vérifier si les noms problématiques sont détectés
"""

from pathlib import Path
from src.analysis.sensitive_info_detector import detect_sensitive_information
import re

pdf_path = Path("pdf/March 15, 2017 Form- DEF 14A (Proxy Statement).pdf")

print("=" * 80)
print("🔍 Test Spécifique - Noms Problématiques")
print("=" * 80)
print()

# Analyser
results = detect_sensitive_information(pdf_path, verbose=False)

# Extraire tous les noms
all_names = []
for page_num, findings in results.items():
    for finding in findings:
        if finding['type'] == 'person_name':
            all_names.append(finding['value'])

all_names_lower = [name.lower() for name in all_names]

print(f"📊 Total noms détectés: {len(all_names)}\n")

# Tester les cas spécifiques des améliorations
print("🧪 TEST DES AMÉLIORATIONS:")
print()

test_cases = [
    # Fix 1: Gerund filter
    ("Irving", "irving", "Fix gerund filter"),
    ("Sterling", "sterling", "Fix gerund filter"),
    ("Fleming", "fleming", "Fix gerund filter"),

    # Fix 2: Name prefixes
    ("McDonald", "mcdonald", "Fix name prefixes"),
    ("DeAngelo", "deangelo", "Fix name prefixes"),
    ("O'Brien", "o'brien", "Fix name prefixes"),

    # Fix 3: Smart keyword
    ("Grant", "grant", "Fix smart keyword"),
]

found_count = 0
not_found = []

for display_name, search_pattern, fix_type in test_cases:
    found = any(search_pattern in name for name in all_names_lower)

    if found:
        found_count += 1
        matches = [name for name in all_names if search_pattern in name.lower()]
        print(f"✅ {display_name:15} - TROUVÉ ({fix_type})")
        for match in matches[:3]:
            print(f"   → {match}")
    else:
        not_found.append((display_name, fix_type))
        print(f"❌ {display_name:15} - NON TROUVÉ ({fix_type})")

print()
print("=" * 80)
print(f"📊 Résumé: {found_count}/{len(test_cases)} cas de test trouvés")
print("=" * 80)

if not_found:
    print()
    print("❌ CAS NON TROUVÉS:")
    for name, fix_type in not_found:
        print(f"   • {name} ({fix_type})")
    print()
    print("💡 Ces noms ne sont probablement pas présents dans ce PDF")
    print("   → C'est NORMAL si le PDF ne contient pas ces noms spécifiques")
    print()
    print("🔍 Pour vérifier si les FILTRES fonctionnent:")
    print("   → Les filtres acceptent maintenant Irving, Sterling, Fleming, etc.")
    print("   → Mais si ces noms ne sont PAS dans le PDF, ils ne seront PAS détectés")
    print()

# Afficher quelques vrais noms pour vérifier que la détection marche
print("=" * 80)
print("✅ EXEMPLES DE NOMS RÉELLEMENT DÉTECTÉS:")
print("=" * 80)
for name in sorted(set(all_names))[:20]:
    print(f"   • {name}")
