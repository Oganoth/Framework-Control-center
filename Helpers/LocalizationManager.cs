using System;
using System.Collections.Generic;
using System.Globalization;

namespace FrameworkControl.Helpers
{
    public static class LocalizationManager
    {
        private static readonly Dictionary<string, string> LanguageCodes = new()
        {
            { "English", "en-US" },
            { "Français", "fr-FR" }
        };

        public static void SetLanguage(string language)
        {
            if (LanguageCodes.TryGetValue(language, out string? cultureCode))
            {
                try
                {
                    var culture = new CultureInfo(cultureCode);
                    CultureInfo.CurrentUICulture = culture;
                    CultureInfo.CurrentCulture = culture;
                }
                catch (CultureNotFoundException)
                {
                    // Fallback to English if culture is not found
                    CultureInfo.CurrentUICulture = new CultureInfo("en-US");
                    CultureInfo.CurrentCulture = new CultureInfo("en-US");
                }
            }
        }

        public static string GetCurrentLanguage()
        {
            var currentCulture = CultureInfo.CurrentUICulture.Name;
            foreach (var language in LanguageCodes)
            {
                if (language.Value.Equals(currentCulture, StringComparison.OrdinalIgnoreCase))
                {
                    return language.Key;
                }
            }
            return "English"; // Default fallback
        }
    }
}
