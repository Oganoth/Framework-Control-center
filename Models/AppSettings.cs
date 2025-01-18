using System;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Collections.Generic;

namespace FrameworkControl.Models
{
    public class AppSettings
    {
        private static readonly string SettingsPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "app_settings.json");
        private static readonly JsonSerializerOptions JsonOptions = new() { WriteIndented = true };

        [JsonPropertyName("start_minimized")]
        public bool StartMinimized { get; set; } = false;

        [JsonPropertyName("startup_profile")]
        public string StartupProfile { get; set; } = "balanced";

        [JsonPropertyName("gui_update_interval")]
        public int GuiUpdateInterval { get; set; } = 1000; // Default to 1 second

        [JsonPropertyName("toggle_window_hotkey")]
        public string ToggleWindowHotkey { get; set; } = "F12";

        [JsonPropertyName("saved_profiles")]
        public Dictionary<string, Dictionary<string, RyzenProfile>> SavedProfiles { get; set; } = new();

        [JsonPropertyName("start_with_windows")]
        public bool StartWithWindows { get; set; } = false;

        [JsonPropertyName("ac_profile")]
        public string AcProfile { get; set; } = "balanced";

        [JsonPropertyName("dc_profile")]
        public string DcProfile { get; set; } = "eco";

        [JsonPropertyName("auto_switch_enabled")]
        public bool AutoSwitchEnabled { get; set; } = true;

        public RyzenProfile? GetSavedProfile(string cpuKey, string profileType)
        {
            if (SavedProfiles.TryGetValue(cpuKey, out var cpuProfiles) &&
                cpuProfiles.TryGetValue(profileType, out var profile))
            {
                return profile;
            }
            return null;
        }

        public void SaveProfile(string cpuKey, string profileType, RyzenProfile profile)
        {
            if (!SavedProfiles.ContainsKey(cpuKey))
            {
                SavedProfiles[cpuKey] = new Dictionary<string, RyzenProfile>();
            }
            SavedProfiles[cpuKey][profileType] = profile;
            Save();
        }

        public static AppSettings Load()
        {
            if (!File.Exists(SettingsPath))
            {
                var defaultSettings = new AppSettings();
                defaultSettings.Save();
                return defaultSettings;
            }

            try
            {
                var json = File.ReadAllText(SettingsPath);
                return JsonSerializer.Deserialize<AppSettings>(json) ?? new AppSettings();
            }
            catch
            {
                return new AppSettings();
            }
        }

        public void Save()
        {
            var json = JsonSerializer.Serialize(this, JsonOptions);
            File.WriteAllText(SettingsPath, json);
        }
    }
}
