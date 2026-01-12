#!/usr/bin/env python3
"""
Tests de logique pour les améliorations de détection
Author: Conrad Vaslin - xAI Finance Tutor

Tests que les constantes et la logique des filtres fonctionnent correctement.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConstants(unittest.TestCase):
    """Tests que toutes les nouvelles constantes sont définies"""

    def test_legitimate_ing_names_defined(self):
        """Test: LEGITIMATE_ING_NAMES est défini"""
        from src.analysis.sensitive_info_detector import LEGITIMATE_ING_NAMES
        self.assertIsNotNone(LEGITIMATE_ING_NAMES)
        self.assertGreater(len(LEGITIMATE_ING_NAMES), 0)
        self.assertIn('irving', LEGITIMATE_ING_NAMES)
        self.assertIn('sterling', LEGITIMATE_ING_NAMES)
        self.assertIn('fleming', LEGITIMATE_ING_NAMES)

    def test_legitimate_name_prefixes_defined(self):
        """Test: LEGITIMATE_NAME_PREFIXES est défini"""
        from src.analysis.sensitive_info_detector import LEGITIMATE_NAME_PREFIXES
        self.assertIsNotNone(LEGITIMATE_NAME_PREFIXES)
        self.assertIn('mc', LEGITIMATE_NAME_PREFIXES)
        self.assertIn('mac', LEGITIMATE_NAME_PREFIXES)
        self.assertIn('de', LEGITIMATE_NAME_PREFIXES)
        self.assertIn("o'", LEGITIMATE_NAME_PREFIXES)

    def test_keywords_as_first_names_defined(self):
        """Test: KEYWORDS_AS_FIRST_NAMES est défini"""
        from src.analysis.sensitive_info_detector import KEYWORDS_AS_FIRST_NAMES
        self.assertIsNotNone(KEYWORDS_AS_FIRST_NAMES)
        self.assertIn('grant', KEYWORDS_AS_FIRST_NAMES)
        # Grant Date devrait être dans la liste de rejet
        self.assertIn('date', KEYWORDS_AS_FIRST_NAMES['grant'])
        self.assertIn('plan', KEYWORDS_AS_FIRST_NAMES['grant'])

    def test_technical_email_prefixes_defined(self):
        """Test: TECHNICAL_EMAIL_PREFIXES est défini"""
        from src.analysis.sensitive_info_detector import TECHNICAL_EMAIL_PREFIXES
        self.assertIsNotNone(TECHNICAL_EMAIL_PREFIXES)
        self.assertIn('admin', TECHNICAL_EMAIL_PREFIXES)
        self.assertIn('support', TECHNICAL_EMAIL_PREFIXES)
        self.assertIn('info', TECHNICAL_EMAIL_PREFIXES)


class TestGerundFilterLogic(unittest.TestCase):
    """Tests de la logique du filtre gerund"""

    def setUp(self):
        from src.analysis.sensitive_info_detector import LEGITIMATE_ING_NAMES
        self.legitimate_names = LEGITIMATE_ING_NAMES

    def test_legitimate_ing_names_accepted(self):
        """Test: Prénoms légitimes en -ing sont dans la liste"""
        test_cases = [
            ('irving', True),    # Devrait être accepté
            ('sterling', True),  # Devrait être accepté
            ('fleming', True),   # Devrait être accepté
            ('enabling', False), # Devrait être rejeté
            ('processing', False), # Devrait être rejeté
        ]

        for name, should_be_legitimate in test_cases:
            is_legitimate = name in self.legitimate_names
            self.assertEqual(is_legitimate, should_be_legitimate,
                           f"{name} - attendu: {should_be_legitimate}, obtenu: {is_legitimate}")


class TestKeywordSmartCheckLogic(unittest.TestCase):
    """Tests de la logique du smart check pour keywords"""

    def setUp(self):
        from src.analysis.sensitive_info_detector import KEYWORDS_AS_FIRST_NAMES
        self.keywords_config = KEYWORDS_AS_FIRST_NAMES

    def test_grant_williams_logic(self):
        """Test: 'Grant Williams' devrait être accepté"""
        first_word = 'grant'
        second_word = 'williams'

        # Logique: si 'grant' est un keyword connu ET 'williams' n'est pas dans la liste de rejet
        if first_word in self.keywords_config:
            is_rejection_term = second_word in self.keywords_config[first_word]
            should_accept = not is_rejection_term
        else:
            should_accept = False

        self.assertTrue(should_accept, "Grant Williams devrait être accepté")

    def test_grant_date_logic(self):
        """Test: 'Grant Date' devrait être rejeté"""
        first_word = 'grant'
        second_word = 'date'

        if first_word in self.keywords_config:
            is_rejection_term = second_word in self.keywords_config[first_word]
            should_accept = not is_rejection_term
        else:
            should_accept = False

        self.assertFalse(should_accept, "Grant Date devrait être rejeté")

    def test_grant_plan_logic(self):
        """Test: 'Grant Plan' devrait être rejeté"""
        first_word = 'grant'
        second_word = 'plan'

        if first_word in self.keywords_config:
            is_rejection_term = second_word in self.keywords_config[first_word]
            should_accept = not is_rejection_term
        else:
            should_accept = False

        self.assertFalse(should_accept, "Grant Plan devrait être rejeté")


class TestNamePrefixLogic(unittest.TestCase):
    """Tests de la logique des préfixes de noms"""

    def setUp(self):
        from src.analysis.sensitive_info_detector import LEGITIMATE_NAME_PREFIXES
        self.prefixes = LEGITIMATE_NAME_PREFIXES

    def test_mcdonald_has_prefix(self):
        """Test: 'mcdonald' a un préfixe légitime"""
        word = 'mcdonald'
        has_prefix = any(word.startswith(prefix) for prefix in self.prefixes)
        self.assertTrue(has_prefix, "mcdonald devrait avoir un préfixe légitime (mc)")

    def test_deangelo_has_prefix(self):
        """Test: 'deangelo' a un préfixe légitime"""
        word = 'deangelo'
        has_prefix = any(word.startswith(prefix) for prefix in self.prefixes)
        self.assertTrue(has_prefix, "deangelo devrait avoir un préfixe légitime (de)")

    def test_obrien_has_prefix(self):
        """Test: 'o'brien' a un préfixe légitime"""
        word = "o'brien"
        has_prefix = any(word.startswith(prefix) for prefix in self.prefixes)
        self.assertTrue(has_prefix, "o'brien devrait avoir un préfixe légitime (o')")

    def test_adjustment_no_prefix(self):
        """Test: 'adjustment' n'a pas de préfixe légitime"""
        word = 'adjustment'
        has_prefix = any(word.startswith(prefix) for prefix in self.prefixes)
        self.assertFalse(has_prefix, "adjustment ne devrait pas avoir de préfixe légitime")


class TestEmailPrefixLogic(unittest.TestCase):
    """Tests de la logique des préfixes d'email techniques"""

    def setUp(self):
        from src.analysis.sensitive_info_detector import TECHNICAL_EMAIL_PREFIXES
        self.technical_prefixes = TECHNICAL_EMAIL_PREFIXES

    def test_admin_support_rejected(self):
        """Test: 'admin.support' devrait être rejeté"""
        first = 'admin'
        second = 'support'
        is_technical = (first in self.technical_prefixes or
                       second in self.technical_prefixes)
        self.assertTrue(is_technical, "admin.support devrait être technique")

    def test_john_smith_accepted(self):
        """Test: 'john.smith' devrait être accepté"""
        first = 'john'
        second = 'smith'
        is_technical = (first in self.technical_prefixes or
                       second in self.technical_prefixes)
        self.assertFalse(is_technical, "john.smith ne devrait pas être technique")


class TestModuleImports(unittest.TestCase):
    """Tests que le module peut être importé"""

    def test_module_imports(self):
        """Test: Le module peut être importé sans erreurs"""
        try:
            from src.analysis.sensitive_info_detector import detect_sensitive_information
            self.assertIsNotNone(detect_sensitive_information)
        except ImportError as e:
            self.fail(f"Impossible d'importer le module: {e}")

    def test_function_signature(self):
        """Test: La fonction a la bonne signature"""
        from src.analysis.sensitive_info_detector import detect_sensitive_information
        import inspect

        sig = inspect.signature(detect_sensitive_information)
        params = list(sig.parameters.keys())

        self.assertIn('pdf_path', params)
        self.assertIn('verbose', params)


def run_all_tests():
    """Exécute tous les tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Ajouter tous les tests
    suite.addTests(loader.loadTestsFromTestCase(TestConstants))
    suite.addTests(loader.loadTestsFromTestCase(TestGerundFilterLogic))
    suite.addTests(loader.loadTestsFromTestCase(TestKeywordSmartCheckLogic))
    suite.addTests(loader.loadTestsFromTestCase(TestNamePrefixLogic))
    suite.addTests(loader.loadTestsFromTestCase(TestEmailPrefixLogic))
    suite.addTests(loader.loadTestsFromTestCase(TestModuleImports))

    # Exécuter les tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == "__main__":
    print("=" * 80)
    print("🧪 Tests de Logique - Améliorations de Détection")
    print("=" * 80)
    print()

    result = run_all_tests()

    print()
    print("=" * 80)
    print("📊 Résumé:")
    print(f"   Tests exécutés: {result.testsRun}")
    print(f"   ✅ Succès: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   ❌ Échecs: {len(result.failures)}")
    print(f"   🔥 Erreurs: {len(result.errors)}")
    print("=" * 80)

    # Exit code
    sys.exit(0 if result.wasSuccessful() else 1)
