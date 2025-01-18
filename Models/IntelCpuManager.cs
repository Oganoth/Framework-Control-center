using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Runtime.Versioning;

namespace FrameworkControl.Models
{
    public class IntelProfile
    {
        public string Name { get; set; } = string.Empty;
        public int Pl1 { get; set; }
        public int Pl2 { get; set; }
        public int TurboTime { get; set; }
        public int Temperature { get; set; }
    }

    [SupportedOSPlatform("windows")]
    public class IntelCpuManager
    {
        private readonly Logger _logger;
        private readonly string _profilesPath;
        private Dictionary<string, Dictionary<string, IntelProfile>> _profiles = new();
        private string _cpuModel = "Unknown_INTEL";

        public IntelCpuManager()
        {
            _logger = new Logger("IntelCPU");
            _profilesPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "intel", "profiles.json");
            LoadProfiles();
        }

        private void LoadProfiles()
        {
            try
            {
                if (!File.Exists(_profilesPath))
                {
                    _logger.Log($"Creating default profiles at: {_profilesPath}");
                    CreateDefaultProfiles();
                }

                var json = File.ReadAllText(_profilesPath);
                var options = new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                };

                var root = JsonSerializer.Deserialize<Dictionary<string, Dictionary<string, Dictionary<string, IntelProfile>>>>(json, options);
                if (root == null || !root.ContainsKey("intel_profiles"))
                {
                    _logger.LogError("Invalid profiles file format, creating default profiles");
                    CreateDefaultProfiles();
                    return;
                }

                _profiles = root["intel_profiles"];
                _logger.Log($"Loaded {_profiles.Count} CPU profiles");

                // Ne pas réinitialiser _cpuModel si on l'a déjà détecté correctement
                if (_cpuModel == "Unknown_INTEL")
                {
                    DetectCpuModel();
                }
                else
                {
                    _logger.Log($"Using existing CPU model: {_cpuModel}");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error loading profiles: {ex.Message}");
                CreateDefaultProfiles();
            }
        }

        private void CreateDefaultProfiles()
        {
            try
            {
                // Créer le dossier intel s'il n'existe pas
                var intelDirectory = Path.GetDirectoryName(_profilesPath);
                if (!string.IsNullOrEmpty(intelDirectory) && !Directory.Exists(intelDirectory))
                {
                    Directory.CreateDirectory(intelDirectory);
                    _logger.Log($"Created directory: {intelDirectory}");
                }

                // Détecter le modèle de CPU si nécessaire
                if (_cpuModel == "Unknown_INTEL")
                {
                    DetectCpuModel();
                }

                // Créer les profils par défaut
                _profiles = new Dictionary<string, Dictionary<string, IntelProfile>>
                {
                    {
                        _cpuModel,
                        new Dictionary<string, IntelProfile>
                        {
                            {
                                "eco",
                                new IntelProfile
                                {
                                    Name = "eco",
                                    Pl1 = 28,
                                    Pl2 = 45,
                                    TurboTime = 28,
                                    Temperature = 95
                                }
                            },
                            {
                                "balanced",
                                new IntelProfile
                                {
                                    Name = "balanced",
                                    Pl1 = 35,
                                    Pl2 = 55,
                                    TurboTime = 28,
                                    Temperature = 95
                                }
                            },
                            {
                                "boost",
                                new IntelProfile
                                {
                                    Name = "boost",
                                    Pl1 = 45,
                                    Pl2 = 65,
                                    TurboTime = 28,
                                    Temperature = 95
                                }
                            }
                        }
                    }
                };

                // Sauvegarder les profils par défaut
                var root = new Dictionary<string, Dictionary<string, Dictionary<string, IntelProfile>>>
                {
                    { "intel_profiles", _profiles }
                };

                var options = new JsonSerializerOptions
                {
                    WriteIndented = true
                };

                var json = JsonSerializer.Serialize(root, options);
                File.WriteAllText(_profilesPath, json);
                _logger.Log("Created default profiles");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error creating default profiles: {ex.Message}");
            }
        }

        private void DetectCpuModel()
        {
            try
            {
                var hardwareMonitor = new HardwareMonitor();
                var cpuDetector = new CpuModelDetector(hardwareMonitor);
                var cpuInfo = cpuDetector.DetectCpuModel();
                
                if (cpuInfo != null && cpuInfo.FullName.Contains("Core Ultra"))
                {
                    var parts = cpuInfo.FullName.Split(' ');
                    if (parts.Length >= 4)
                    {
                        var model = parts[parts.Length - 1];
                        if (model.EndsWith("H", StringComparison.OrdinalIgnoreCase))
                        {
                            _cpuModel = model + "_INTEL";
                            _logger.Log($"Detected Intel CPU model: {_cpuModel}");
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error detecting CPU model: {ex.Message}");
            }
        }

        public bool IsSupported()
        {
            try
            {
                _logger.Log("Intel CPU support check:");
                _logger.Log($"  - CPU Model: {_cpuModel}");

                var hasProfile = _profiles.ContainsKey(_cpuModel);
                _logger.Log($"  - Has profile: {hasProfile}");

                var result = hasProfile;
                _logger.Log($"  - Final result: {result}");

                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error checking CPU support: {ex.Message}");
                return false;
            }
        }

        public void ApplyProfile(string profileType)
        {
            try
            {
                // Recharger les profils avant d'appliquer pour avoir les dernières valeurs
                LoadProfiles();
                
                var profile = GetProfile(profileType);
                if (profile == null)
                {
                    _logger.LogError($"Profile not found: {profileType}");
                    return;
                }

                _logger.Log($"Applying profile '{profileType}' with values:");
                _logger.Log($"  PL1: {profile.Pl1}W");
                _logger.Log($"  PL2: {profile.Pl2}W");
                _logger.Log($"  Turbo Time: {profile.TurboTime}s");
                _logger.Log($"  Temperature: {profile.Temperature}°C");

                bool anySuccess = false;

                // Apply PL1
                uint pl1Value = (uint)(profile.Pl1 * 8);
                bool pl1Success = Ring0.WriteMsr(0x610, pl1Value);
                if (!pl1Success)
                {
                    _logger.LogError("Failed to write PL1");
                }
                anySuccess |= pl1Success;

                // Apply PL2
                uint pl2Value = (uint)(profile.Pl2 * 8);
                bool pl2Success = Ring0.WriteMsr(0x611, pl2Value);
                if (!pl2Success)
                {
                    _logger.LogWarning("Failed to write PL2 - This is expected on some Intel CPUs where PL2 is locked");
                }
                anySuccess |= pl2Success;

                // Apply Turbo Time
                uint turboValue = (uint)profile.TurboTime;
                bool turboSuccess = Ring0.WriteMsr(0x612, turboValue);
                if (!turboSuccess)
                {
                    _logger.LogWarning("Failed to write Turbo Time - This is expected on some Intel CPUs where Turbo Time is locked");
                }
                anySuccess |= turboSuccess;

                // Apply Temperature Limit
                uint tempValue = (uint)profile.Temperature;
                bool tempSuccess = Ring0.WriteMsr(0x613, tempValue);
                if (!tempSuccess)
                {
                    _logger.LogWarning("Failed to write Temperature Limit - This is expected on some Intel CPUs where Temperature Limit is locked");
                }
                anySuccess |= tempSuccess;

                if (anySuccess)
                {
                    var appliedSettings = new System.Text.StringBuilder("Applied profile settings: ");
                    if (pl1Success) appliedSettings.Append($"PL1={profile.Pl1}W ");
                    if (pl2Success) appliedSettings.Append($"PL2={profile.Pl2}W ");
                    if (turboSuccess) appliedSettings.Append($"Turbo={profile.TurboTime}s ");
                    if (tempSuccess) appliedSettings.Append($"Temp={profile.Temperature}°C ");
                    
                    _logger.Log(appliedSettings.ToString().Trim());
                    _logger.Log($"Profile '{profileType}' partially applied - Some settings may be locked by BIOS");
                }
                else
                {
                    _logger.LogError("Failed to apply any profile settings - All MSR writes failed");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error applying profile: {ex.Message}");
            }
        }

        public IntelProfile? GetProfile(string profileType)
        {
            try
            {
                if (_profiles.ContainsKey(_cpuModel) && 
                    _profiles[_cpuModel].ContainsKey(profileType))
                {
                    return _profiles[_cpuModel][profileType];
                }

                _logger.LogWarning($"Profile not found: {profileType}");
                return null;
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error getting profile {profileType}: {ex.Message}");
                return null;
            }
        }

        public void SaveProfile(string profileType, IntelProfile profile)
        {
            try
            {
                _logger.Log($"Saving Intel CPU profile '{profileType}' for model {_cpuModel}");

                // Vérifier que le CPU est supporté
                if (!IsSupported())
                {
                    _logger.LogError("Cannot save profile: CPU not supported");
                    return;
                }

                // Créer le dossier intel s'il n'existe pas
                var intelDirectory = Path.GetDirectoryName(_profilesPath);
                if (!string.IsNullOrEmpty(intelDirectory) && !Directory.Exists(intelDirectory))
                {
                    Directory.CreateDirectory(intelDirectory);
                    _logger.Log($"Created directory: {intelDirectory}");
                }

                // Sauvegarder une copie des profils actuels
                var currentProfiles = new Dictionary<string, Dictionary<string, IntelProfile>>(_profiles);

                if (!_profiles.ContainsKey(_cpuModel))
                {
                    _profiles[_cpuModel] = new Dictionary<string, IntelProfile>();
                }

                _profiles[_cpuModel][profileType] = profile;

                var root = new Dictionary<string, Dictionary<string, Dictionary<string, IntelProfile>>>
                {
                    { "intel_profiles", _profiles }
                };

                var options = new JsonSerializerOptions
                {
                    WriteIndented = true
                };

                // Sauvegarder dans un fichier temporaire d'abord
                var tempPath = _profilesPath + ".tmp";
                var json = JsonSerializer.Serialize(root, options);
                File.WriteAllText(tempPath, json);

                // Vérifier que le fichier temporaire est valide
                try
                {
                    var testJson = File.ReadAllText(tempPath);
                    var testRoot = JsonSerializer.Deserialize<Dictionary<string, Dictionary<string, Dictionary<string, IntelProfile>>>>(testJson, options);
                    if (testRoot == null || !testRoot.ContainsKey("intel_profiles"))
                    {
                        throw new Exception("Invalid JSON format in temporary file");
                    }
                }
                catch
                {
                    // Restaurer les profils précédents en cas d'erreur
                    _profiles = currentProfiles;
                    if (File.Exists(tempPath))
                    {
                        File.Delete(tempPath);
                    }
                    throw;
                }

                // Remplacer le fichier original par le fichier temporaire
                if (File.Exists(_profilesPath))
                {
                    File.Delete(_profilesPath);
                }
                File.Move(tempPath, _profilesPath);

                _logger.Log($"Successfully saved profile '{profileType}' with PL1={profile.Pl1}W");

                // Recharger les profils pour s'assurer que les changements sont pris en compte
                LoadProfiles();

                // Appliquer immédiatement le profil modifié
                ApplyProfile(profileType);
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error saving profile {profileType}: {ex.Message}");
                throw;
            }
        }
    }
} 