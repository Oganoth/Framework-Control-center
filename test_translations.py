import unittest
from translations import TRANSLATIONS

class TestTranslations(unittest.TestCase):
    def test_all_languages_have_same_keys(self):
        """Test that all languages have the same translation keys"""
        reference_keys = set(TRANSLATIONS["en"].keys())
        for lang, translations in TRANSLATIONS.items():
            if lang != "en":
                current_keys = set(translations.keys())
                missing_keys = reference_keys - current_keys
                extra_keys = current_keys - reference_keys
                self.assertEqual(missing_keys, set(), f"Language {lang} is missing keys: {missing_keys}")
                self.assertEqual(extra_keys, set(), f"Language {lang} has extra keys: {extra_keys}")
                
    def test_no_empty_translations(self):
        """Test that no translation is empty"""
        for lang, translations in TRANSLATIONS.items():
            for key, value in translations.items():
                self.assertNotEqual(value, "", f"Empty translation for key '{key}' in language {lang}")
                self.assertIsNotNone(value, f"None translation for key '{key}' in language {lang}")
                
    def test_no_missing_translations(self):
        """Test that no translation is missing"""
        for lang, translations in TRANSLATIONS.items():
            for key, value in translations.items():
                self.assertIn(key, TRANSLATIONS["en"], f"Key '{key}' in language {lang} not found in English translations")
                
    def test_language_codes(self):
        """Test that all required language codes are present"""
        required_languages = {"en", "fr", "de", "it", "es", "zh"}
        self.assertEqual(set(TRANSLATIONS.keys()), required_languages)
        
    def test_translation_format(self):
        """Test that all translations are strings"""
        for lang, translations in TRANSLATIONS.items():
            for key, value in translations.items():
                self.assertIsInstance(value, str, f"Translation for key '{key}' in language {lang} is not a string")
                
if __name__ == "__main__":
    unittest.main() 