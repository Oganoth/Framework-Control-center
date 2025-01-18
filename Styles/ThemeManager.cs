using Avalonia;
using Avalonia.Media;
using Avalonia.Styling;
using System;
using System.Runtime.InteropServices;
using Microsoft.Win32;
using Avalonia.Themes.Fluent;
using System.Runtime.Versioning;

namespace FrameworkControl.Styles
{
    [SupportedOSPlatform("windows")]
    public class ThemeManager
    {
        private const string PersonalizeKeyPath = @"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize";
        private const string DWMKeyPath = @"Software\Microsoft\Windows\DWM";

        public static Color GetAccentColor()
        {
            try
            {
                using var dwmKey = Registry.CurrentUser.OpenSubKey(DWMKeyPath);
                if (dwmKey?.GetValue("ColorizationColor") is int colorValue)
                {
                    byte a = (byte)((colorValue >> 24) & 0xFF);
                    byte r = (byte)((colorValue >> 16) & 0xFF);
                    byte g = (byte)((colorValue >> 8) & 0xFF);
                    byte b = (byte)(colorValue & 0xFF);
                    return new Color(a, r, g, b);
                }
            }
            catch (Exception)
            {
                // Fallback to default accent color if registry access fails
            }
            return Colors.DodgerBlue;
        }

        public static void ApplyTheme(Application app)
        {
            var accentColor = GetAccentColor();
            
            if (app.Styles[0] is FluentTheme fluentTheme)
            {
                // Set dark theme
                var themeVariant = ThemeVariant.Dark;
                app.RequestedThemeVariant = themeVariant;
                
                var resources = app.Resources;
                resources["SystemAccentColor"] = accentColor;
                resources["SystemAccentColorLight1"] = LightenColor(accentColor, 0.2);
                resources["SystemAccentColorLight2"] = LightenColor(accentColor, 0.4);
                resources["SystemAccentColorDark1"] = DarkenColor(accentColor, 0.2);
                resources["SystemAccentColorDark2"] = DarkenColor(accentColor, 0.4);
                
                // Background colors
                resources["ApplicationBackgroundColor"] = Color.FromRgb(32, 32, 32);
                resources["SystemControlBackgroundAltHigh"] = Color.FromRgb(39, 39, 39);
                resources["SystemControlBackgroundAltMedium"] = Color.FromRgb(45, 45, 45);
                
                // Text colors
                resources["SystemBaseHighColor"] = Colors.White;
                resources["SystemBaseMediumColor"] = Color.FromRgb(215, 215, 215);
                resources["SystemBaseLowColor"] = Color.FromRgb(127, 127, 127);
            }
        }

        private static Color LightenColor(Color color, double factor)
        {
            return Color.FromArgb(
                color.A,
                (byte)Math.Min(255, color.R + (255 - color.R) * factor),
                (byte)Math.Min(255, color.G + (255 - color.G) * factor),
                (byte)Math.Min(255, color.B + (255 - color.B) * factor)
            );
        }

        private static Color DarkenColor(Color color, double factor)
        {
            return Color.FromArgb(
                color.A,
                (byte)(color.R * (1 - factor)),
                (byte)(color.G * (1 - factor)),
                (byte)(color.B * (1 - factor))
            );
        }
    }
}
