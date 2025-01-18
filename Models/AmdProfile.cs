using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace FrameworkControl.Models
{
    public class AmdProfiles
    {
        [JsonPropertyName("amd_profiles")]
        public Dictionary<string, CpuProfiles> Profiles { get; set; } = new Dictionary<string, CpuProfiles>();
        private static readonly string _filePath = Path.Combine(AppContext.BaseDirectory, "amd_profiles.json");

        public static AmdProfiles Load()
        {
            if (!File.Exists(_filePath))
            {
                var defaultProfiles = new AmdProfiles();
                defaultProfiles.CreateDefaultProfiles();
                defaultProfiles.Save();
                return defaultProfiles;
            }

            try
            {
                var json = File.ReadAllText(_filePath);
                return JsonSerializer.Deserialize<AmdProfiles>(json) ?? new AmdProfiles();
            }
            catch (Exception)
            {
                return new AmdProfiles();
            }
        }

        public void Save()
        {
            var json = JsonSerializer.Serialize(this, new JsonSerializerOptions { WriteIndented = true });
            File.WriteAllText(_filePath, json);
        }

        public void ResetToDefault()
        {
            CreateDefaultProfiles();
            Save();
        }

        private void CreateDefaultProfiles()
        {
            Profiles.Clear();
            
            // Default profile for AMD Ryzen 7 7840U
            Profiles["AMD Ryzen 7 7840U"] = new CpuProfiles
            {
                Eco = new ProfileSettings
                {
                    TctlTemp = 75,
                    ApuSkinTemp = 50,
                    StapmLimit = 15000,
                    FastLimit = 20000,
                    SlowLimit = 15000
                },
                Balanced = new ProfileSettings
                {
                    TctlTemp = 85,
                    ApuSkinTemp = 60,
                    StapmLimit = 25000,
                    FastLimit = 30000,
                    SlowLimit = 25000
                },
                Boost = new ProfileSettings
                {
                    TctlTemp = 95,
                    ApuSkinTemp = 70,
                    StapmLimit = 35000,
                    FastLimit = 40000,
                    SlowLimit = 35000
                }
            };
        }
    }

    public class CpuProfiles
    {
        [JsonPropertyName("eco")]
        public ProfileSettings Eco { get; set; } = new ProfileSettings();
        [JsonPropertyName("balanced")]
        public ProfileSettings Balanced { get; set; } = new ProfileSettings();
        [JsonPropertyName("boost")]
        public ProfileSettings Boost { get; set; } = new ProfileSettings();
    }

    public class ProfileSettings
    {
        [JsonPropertyName("tctl_temp")]
        public int TctlTemp { get; set; }
        [JsonPropertyName("apu_skin_temp")]
        public int ApuSkinTemp { get; set; }
        [JsonPropertyName("stapm_limit")]
        public int StapmLimit { get; set; }
        [JsonPropertyName("fast_limit")]
        public int FastLimit { get; set; }
        [JsonPropertyName("slow_limit")]
        public int SlowLimit { get; set; }
    }
}
