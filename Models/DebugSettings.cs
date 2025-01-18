using System;
using System.Text.Json;
using System.IO;

namespace FrameworkControl.Models
{
    public class DebugSettings
    {
        private static readonly string SettingsPath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "FrameworkControl",
            "debug_settings.json"
        );

        public bool IsMonitoringEnabled { get; set; } = true;
        public bool ShowDgpuControls { get; set; } = true;

        public static DebugSettings Load()
        {
            try
            {
                if (File.Exists(SettingsPath))
                {
                    var json = File.ReadAllText(SettingsPath);
                    return JsonSerializer.Deserialize<DebugSettings>(json) ?? new DebugSettings();
                }
            }
            catch
            {
                // Ignore errors and return default settings
            }
            return new DebugSettings();
        }

        public void Save()
        {
            try
            {
                var directory = Path.GetDirectoryName(SettingsPath);
                if (directory != null && !Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                var json = JsonSerializer.Serialize(this);
                File.WriteAllText(SettingsPath, json);
            }
            catch
            {
                // Ignore save errors
            }
        }

        public static void Reset()
        {
            try
            {
                if (File.Exists(SettingsPath))
                {
                    File.Delete(SettingsPath);
                }
            }
            catch
            {
                // Ignore deletion errors
            }
        }
    }
}
