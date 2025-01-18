using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Runtime.Versioning;
using Avalonia.Logging;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Linq;
using LibreHardwareMonitor.Hardware;

namespace FrameworkControl.Models
{
    public class RyzenProfile
    {
        [JsonPropertyName("name")]
        public required string Name { get; set; }

        [JsonPropertyName("tctl_temp")]
        public int TctlTemp { get; set; }

        [JsonPropertyName("chtc_temp")]
        public int? ChtcTemp { get; set; }

        [JsonPropertyName("apu_skin_temp")]
        public int? ApuSkinTemp { get; set; }

        [JsonPropertyName("stapm_limit")]
        public int StapmLimit { get; set; }

        [JsonPropertyName("fast_limit")]
        public int FastLimit { get; set; }

        [JsonPropertyName("slow_limit")]
        public int SlowLimit { get; set; }

        [JsonPropertyName("vrm_current")]
        public int VrmCurrent { get; set; }

        [JsonPropertyName("vrmmax_current")]
        public int VrmMaxCurrent { get; set; }

        [JsonPropertyName("vrmsoc_current")]
        public int VrmSocCurrent { get; set; }

        [JsonPropertyName("vrmsocmax_current")]
        public int VrmSocMaxCurrent { get; set; }

        [JsonPropertyName("win_power")]
        public int? WinPower { get; set; }
    }

    [SupportedOSPlatform("windows")]
    public class RyzenAdjManager
    {
        private readonly string _ryzenAdjPath;
        private readonly string _profilesPath;
        private Dictionary<string, Dictionary<string, RyzenProfile>> _profiles = new();
        private string? _currentCpuModel;
        private readonly HardwareMonitor _hardwareMonitor;
        private readonly CpuModelDetector _cpuModelDetector;
        private readonly Logger _logger;

        // Paramètres minimums pour éviter le throttling
        private const int MIN_STAPM_LIMIT = 45000;  // 45W minimum
        private const int MIN_FAST_LIMIT = 45000;   // 45W minimum
        private const int MIN_SLOW_LIMIT = 45000;   // 45W minimum
        private const int MIN_VRM_CURRENT = 60000;  // 60A minimum

        public RyzenAdjManager()
        {
            _logger = new Logger("RyzenADJ");
            _ryzenAdjPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "ryzenadj", "ryzenadj.exe");
            _profilesPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "ryzenadj", "amd_profiles.json");
            _hardwareMonitor = new HardwareMonitor();
            _cpuModelDetector = new CpuModelDetector(_hardwareMonitor);
            LoadProfiles();
            DetectCpuModel();
        }

        private void LoadProfiles()
        {
            try
            {
                if (!File.Exists(_profilesPath))
                {
                    throw new FileNotFoundException($"Profile file not found: {_profilesPath}");
                }

                var json = File.ReadAllText(_profilesPath);
                var options = new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                };
                var root = JsonSerializer.Deserialize<Dictionary<string, Dictionary<string, Dictionary<string, RyzenProfile>>>>(json, options);
                if (root == null || !root.ContainsKey("amd_profiles"))
                {
                    throw new InvalidOperationException("Invalid profile file format");
                }
                _profiles = root["amd_profiles"].ToDictionary(
                    cpu => cpu.Key,
                    cpu => cpu.Value.ToDictionary(
                        profile => profile.Key,
                        profile => profile.Value
                    )
                );
                _logger.Log($"Loaded {_profiles.Count} CPU profiles");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error loading profiles: {ex.Message}");
                throw;
            }
        }

        public RyzenProfile? GetProfile(string cpuKey, string profileType)
        {
            if (_profiles.TryGetValue(cpuKey, out var cpuProfiles) &&
                cpuProfiles.TryGetValue(profileType, out var profile))
            {
                return profile;
            }
            return null;
        }

        private void DetectCpuModel()
        {
            try
            {
                var cpuInfo = _cpuModelDetector.DetectCpuModel();
                if (cpuInfo == null)
                {
                    _logger.LogWarning("Failed to detect CPU model");
                    _currentCpuModel = null;
                    return;
                }
                
                _logger.Log($"Detected CPU: {cpuInfo.FullName}");

                // Si ce n'est pas un CPU AMD, on ne cherche pas de profil
                if (!cpuInfo.IsAmd)
                {
                    _logger.Log($"Non-AMD CPU detected, RyzenADJ will be disabled");
                    _currentCpuModel = null;
                    return;
                }

                if (!_profiles.ContainsKey(cpuInfo.ProfileKey))
                {
                    _logger.LogWarning($"No profile found for CPU model: {cpuInfo.ProfileKey}");
                    _currentCpuModel = null;
                    return;
                }

                _currentCpuModel = cpuInfo.ProfileKey;
                _logger.Log($"Using profile: {_currentCpuModel}");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error detecting CPU model: {ex.Message}");
                _currentCpuModel = null;
            }
        }

        private void ExecuteRyzenAdj(string arguments)
        {
            try
            {
                var startInfo = new ProcessStartInfo
                {
                    FileName = _ryzenAdjPath,
                    Arguments = arguments,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    WindowStyle = ProcessWindowStyle.Hidden
                };

                // Masquer complètement la fenêtre
                startInfo.LoadUserProfile = false;
                startInfo.ErrorDialog = false;
                startInfo.RedirectStandardInput = true;

                _logger.Log($"Executing command:");
                _logger.Log($"Command: {_ryzenAdjPath} {arguments}");

                using var process = Process.Start(startInfo);
                if (process == null)
                {
                    throw new Exception("Failed to start RyzenAdj process");
                }

                string output = process.StandardOutput.ReadToEnd();
                string error = process.StandardError.ReadToEnd();
                process.WaitForExit();

                _logger.Log($"Output:\n{output}");
                if (!string.IsNullOrEmpty(error))
                    _logger.Log($"Error:\n{error}");
                _logger.Log($"Exit code: {process.ExitCode}");
                _logger.Log($"--------------------------------------------------------------------------------");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error executing RyzenAdj: {ex.Message}");
                throw;
            }
        }

        public void ApplyProfile(string profileType)
        {
            try
            {
                if (string.IsNullOrEmpty(_currentCpuModel) || !_profiles.ContainsKey(_currentCpuModel))
                {
                    throw new Exception("No valid CPU model detected");
                }

                if (!_profiles[_currentCpuModel].ContainsKey(profileType))
                {
                    throw new Exception($"Profile {profileType} not found for CPU model {_currentCpuModel}");
                }

                var cpuTemp = _hardwareMonitor.GetCpuTemperature();
                var cpuUsage = _hardwareMonitor.GetCpuUsage();
                
                _logger.Log($"Current CPU Temperature: {cpuTemp}°C, Usage: {cpuUsage}%");
                
                // Ajuster le profil en fonction de la température et de l'utilisation
                if (cpuTemp > 85 && profileType == "boost")
                {
                    _logger.Log($"CPU temperature too high ({cpuTemp}°C), switching to balanced profile");
                    profileType = "balanced";
                }

                // Charger d'abord le profil personnalisé s'il existe
                var settings = AppSettings.Load();
                var profile = settings.GetSavedProfile(_currentCpuModel, profileType) ?? _profiles[_currentCpuModel][profileType];
                
                _logger.Log($"Applying {(settings.GetSavedProfile(_currentCpuModel, profileType) != null ? "custom" : "default")} {profileType} profile for CPU model {_currentCpuModel}");

                var args = new List<string>
                {
                    $"--tctl-temp={Math.Max(profile.TctlTemp, 85)}",  // Température minimum de 85°C
                    $"--stapm-limit={Math.Max(profile.StapmLimit, MIN_STAPM_LIMIT)}",
                    $"--fast-limit={Math.Max(profile.FastLimit, MIN_FAST_LIMIT)}",
                    $"--slow-limit={Math.Max(profile.SlowLimit, MIN_SLOW_LIMIT)}",
                    $"--vrm-current={Math.Max(profile.VrmCurrent, MIN_VRM_CURRENT)}",
                    $"--vrmmax-current={Math.Max(profile.VrmMaxCurrent, MIN_VRM_CURRENT)}",
                    $"--vrmsoc-current={profile.VrmSocCurrent}",
                    $"--vrmsocmax-current={profile.VrmSocMaxCurrent}",
                    profileType == "eco" ? "--power-saving" : "--max-performance"  // Mode économie d'énergie uniquement pour le profil eco
                };

                ExecuteRyzenAdj(string.Join(" ", args));
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error applying profile: {ex.Message}");
                throw;
            }
        }

        public string? GetCurrentCpuModel() => _currentCpuModel;

        public bool IsSupported() => !string.IsNullOrEmpty(_currentCpuModel) && _profiles.ContainsKey(_currentCpuModel);
    }
}
