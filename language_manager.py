from translations import translations

class LanguageManager:
    def __init__(self, settings):
        self.settings = settings
        self.current_language = self.settings.get_setting("language", "en")
        
    def get_text(self, key):
        """Get translated text for a given key"""
        try:
            return translations[self.current_language][key]
        except KeyError:
            # Fallback to English if translation is missing
            try:
                return translations["en"][key]
            except KeyError:
                return key
    
    def set_language(self, language_code):
        """Change the current language"""
        if language_code in translations:
            self.current_language = language_code
            self.settings.set_setting("language", language_code)
            return True
        return False
    
    def get_available_languages(self):
        """Get list of available languages"""
        return list(translations.keys())
    
    def get_language_name(self, language_code):
        """Get the native name of a language"""
        language_names = {
            "en": "English",
            "fr": "Français",
            "es": "Español",
            "de": "Deutsch"
        }
        return language_names.get(language_code, language_code) 