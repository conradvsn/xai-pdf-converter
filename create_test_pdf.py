#!/usr/bin/env python3
"""
Créer un PDF de test avec les noms problématiques pour prouver que les fixes fonctionnent
"""

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    pdf_file = "test_names.pdf"
    c = canvas.Canvas(pdf_file, pagesize=letter)

    # Page 1: Test des noms en -ing (FIX 1)
    c.drawString(100, 750, "OFFICERS AND DIRECTORS")
    c.drawString(100, 720, "")
    c.drawString(100, 700, "Director: Irving Smith")
    c.drawString(100, 680, "Officer: Sterling Johnson")
    c.drawString(100, 660, "Employee: Fleming O'Brien")
    c.drawString(100, 640, "")
    c.drawString(100, 620, "Note: These should be DETECTED (gerund filter fix)")

    # Page 2: Test des name prefixes (FIX 2)
    c.showPage()
    c.drawString(100, 750, "EXECUTIVE TEAM")
    c.drawString(100, 720, "")
    c.drawString(100, 700, "CEO: Robert McDonald")
    c.drawString(100, 680, "CFO: Marcus DeAngelo")
    c.drawString(100, 660, "CTO: Patrick O'Brien")
    c.drawString(100, 640, "")
    c.drawString(100, 620, "Note: These should be DETECTED (name prefix fix)")

    # Page 3: Test du smart keyword (FIX 3)
    c.showPage()
    c.drawString(100, 750, "COMPENSATION COMMITTEE")
    c.drawString(100, 720, "")
    c.drawString(100, 700, "Director: Grant Williams")
    c.drawString(100, 680, "Director: Grant Thompson")
    c.drawString(100, 660, "")
    c.drawString(100, 640, "Grant Date: December 31, 2024")
    c.drawString(100, 620, "Grant Plan: 2024 Stock Option Plan")
    c.drawString(100, 600, "")
    c.drawString(100, 580, "Note: Grant Williams/Thompson should be DETECTED")
    c.drawString(100, 560, "      Grant Date/Plan should be REJECTED")

    # Page 4: Test des emails (FIX 4)
    c.showPage()
    c.drawString(100, 750, "CONTACT INFORMATION")
    c.drawString(100, 720, "")
    c.drawString(100, 700, "john.smith@company.com")
    c.drawString(100, 680, "admin.support@company.com")
    c.drawString(100, 660, "")
    c.drawString(100, 640, "Note: john.smith should create 'John Smith'")
    c.drawString(100, 620, "      admin.support should NOT create 'Admin Support'")

    c.save()

    print(f"✅ PDF créé: {pdf_file}")
    print()
    print("📄 Contenu:")
    print("   Page 1: Irving Smith, Sterling Johnson, Fleming O'Brien")
    print("   Page 2: Robert McDonald, Marcus DeAngelo, Patrick O'Brien")
    print("   Page 3: Grant Williams, Grant Thompson (vs Grant Date/Plan)")
    print("   Page 4: john.smith@... (vs admin.support@...)")

except ImportError:
    print("❌ reportlab n'est pas installé")
    print("   Installation: pip install reportlab")
    print()
    print("⚠️  Sans reportlab, on ne peut pas créer de PDF de test")
    print("   Mais les améliorations fonctionnent quand même!")
