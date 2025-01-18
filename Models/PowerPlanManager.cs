using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text.Json;
using System.Runtime.Versioning;
using System.Management;
using System.Linq;

namespace FrameworkControl.Models
{
    [SupportedOSPlatform("windows")]
    public class PowerPlanManager
    {
        private readonly Logger _logger;
        private readonly string _powerPlansPath;
        private Dictionary<string, PowerPlan> _powerPlans = new();
        private readonly RyzenAdjManager? _ryzenAdjManager;
        private readonly IntelCpuManager? _intelCpuManager;
        private string? _activePowerPlan;
        private const string BALANCED_SCHEME_GUID = "381b4222-f694-41f0-9685-ff5bb260df2e";  // GUID du plan Balanced Windows par défaut

        // AMD Dynamic Graphics Mode values
        private static readonly int[] AMD_DYNAMIC_GRAPHICS_VALUES = {
            0x00000000, // Force power-saving graphics
            0x00000001, // Optimize power savings
            0x00000002, // Optimize performance
            0x00000003  // Maximize performance
        };

        // Advanced Color Quality Bias values
        private static readonly int[] ADVANCED_COLOR_QUALITY_VALUES = {
            0x00000000, // Advanced Color power saving bias
            0x00000001  // Advanced Color visual quality bias
        };

        public PowerPlanManager()
        {
            _logger = new Logger("PowerPlan");
            _powerPlansPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "powerplans", "powerplans.json");
            
            // Initialiser les managers CPU-spécifiques
            try
            {
                _intelCpuManager = new IntelCpuManager();
                _ryzenAdjManager = new RyzenAdjManager();
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error initializing CPU-specific managers: {ex.Message}");
            }

            LoadPowerPlans();
            InitializePowerPlans();
        }

        private void LoadPowerPlans()
        {
            try
            {
                if (!File.Exists(_powerPlansPath))
                {
                    _logger.LogError($"Power plans file not found: {_powerPlansPath}");
                    return;
                }

                var json = File.ReadAllText(_powerPlansPath);
                var options = new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                };
                var root = JsonSerializer.Deserialize<Dictionary<string, Dictionary<string, PowerPlan>>>(json, options);
                if (root == null || !root.ContainsKey("power_plans"))
                {
                    _logger.LogError("Invalid power plans file format");
                    return;
                }
                _powerPlans = root["power_plans"];
                _logger.Log($"Loaded {_powerPlans.Count} power plans");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error loading power plans: {ex.Message}");
                throw;
            }
        }

        public void InitializePowerPlans()
        {
            try
            {
                // 1. Supprimer tous les plans Framework existants
                CleanupExistingPowerPlans();

                // 2. Créer nos plans personnalisés
                foreach (var plan in _powerPlans)
                {
                    var originalName = plan.Value.Name;
                    if (!originalName.StartsWith("Framework-"))
                    {
                        plan.Value.Name = $"Framework-{originalName}";
                    }
                    
                    CreatePowerPlan(plan.Value);
                }
                _logger.Log("Power plans initialized successfully");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error initializing power plans: {ex.Message}");
            }
        }

        private void CleanupExistingPowerPlans()
        {
            try
            {
                // 1. Obtenir la liste de tous les plans
                var startInfo = new ProcessStartInfo
                {
                    FileName = "powercfg",
                    Arguments = "/list",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    CreateNoWindow = true
                };

                using var process = Process.Start(startInfo);
                if (process == null)
                {
                    _logger.LogError("Failed to list power plans");
                    return;
                }

                var output = process.StandardOutput.ReadToEnd();
                process.WaitForExit();

                // 2. Supprimer tous les plans sauf le Balanced original
                foreach (var line in output.Split('\n'))
                {
                    if (string.IsNullOrWhiteSpace(line)) continue;
                    
                    try
                    {
                        // Format attendu: Power Scheme GUID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx  (name)
                        var parts = line.Split(new[] { "GUID:", "(", ")" }, StringSplitOptions.RemoveEmptyEntries);
                        if (parts.Length < 3) continue;

                        var guid = parts[1].Trim();
                        var name = parts[2].Trim();

                        // Ne pas supprimer le plan Balanced original
                        if (guid == BALANCED_SCHEME_GUID || name == "Balanced")
                        {
                            continue;
                        }

                        // Supprimer tous les autres plans
                        DeletePowerPlan(guid);
                        _logger.Log($"Deleted power plan: {name} with GUID: {guid}");
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError($"Error processing power plan line: {line}. Error: {ex.Message}");
                        continue;
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error cleaning up power plans: {ex.Message}");
            }
        }

        private void CreatePowerPlan(PowerPlan plan)
        {
            try
            {
                // 1. Dupliquer le plan Balanced
                var startInfo = new ProcessStartInfo
                {
                    FileName = "powercfg",
                    Arguments = $"/duplicatescheme {BALANCED_SCHEME_GUID}",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    CreateNoWindow = true,
                    StandardOutputEncoding = System.Text.Encoding.UTF8
                };

                string newGuid = string.Empty;
                using (var process = Process.Start(startInfo))
                {
                    if (process == null)
                    {
                        _logger.LogError($"Failed to start process for creating power plan {plan.Name}");
                        return;
                    }
                    var output = process.StandardOutput.ReadToEnd();
                    process.WaitForExit();
                    if (process.ExitCode != 0)
                    {
                        _logger.LogError($"Failed to create power plan {plan.Name}. Exit code: {process.ExitCode}");
                        return;
                    }
                    
                    // Format attendu: Power Scheme GUID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
                    var guidMatch = output.Split(new[] { "GUID:" }, StringSplitOptions.RemoveEmptyEntries);
                    if (guidMatch.Length < 2)
                    {
                        _logger.LogError($"Failed to extract GUID from output: {output}");
                        return;
                    }
                    newGuid = guidMatch[1].Trim().Split(' ')[0]; // Prendre seulement le GUID, pas le reste
                }

                // 2. Mettre à jour le GUID du plan
                plan.Guid = newGuid;

                // 3. Renommer le plan en utilisant la syntaxe correcte de powercfg
                startInfo = new ProcessStartInfo
                {
                    FileName = "powercfg",
                    Arguments = $"-changename {newGuid} \"{plan.Name}\"",  // Utiliser - au lieu de / et des guillemets
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                    StandardOutputEncoding = System.Text.Encoding.UTF8,
                    StandardErrorEncoding = System.Text.Encoding.UTF8
                };

                using (var process = Process.Start(startInfo))
                {
                    if (process == null)
                    {
                        _logger.LogError($"Failed to start process for renaming power plan {plan.Name}");
                        return;
                    }
                    var output = process.StandardOutput.ReadToEnd();
                    var error = process.StandardError.ReadToEnd();
                    process.WaitForExit();
                    
                    if (process.ExitCode != 0)
                    {
                        _logger.LogError($"Failed to rename power plan {plan.Name}. Exit code: {process.ExitCode}");
                        _logger.LogError($"Error output: {error}");
                        _logger.LogError($"Standard output: {output}");
                        return;
                    }
                }

                // 4. Appliquer les paramètres
                ApplyPowerPlanSettings(plan);

                // 5. Vérifier que le plan a bien été créé avec le bon nom
                startInfo = new ProcessStartInfo
                {
                    FileName = "powercfg",
                    Arguments = "-list",  // Utiliser - au lieu de /
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    CreateNoWindow = true,
                    StandardOutputEncoding = System.Text.Encoding.UTF8
                };

                using (var process = Process.Start(startInfo))
                {
                    if (process != null)
                    {
                        var output = process.StandardOutput.ReadToEnd();
                        process.WaitForExit();

                        if (output.Contains(plan.Name))
                        {
                            _logger.Log($"Successfully created and renamed power plan: {plan.Name} with GUID: {newGuid}");
                        }
                        else
                        {
                            _logger.LogError($"Power plan {plan.Name} was not found in the system after creation");
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error creating power plan {plan.Name}: {ex.Message}");
            }
        }

        private void DeletePowerPlan(string guid)
        {
            try
            {
                // 1. Vérifier si c'est le plan actif
                var startInfo = new ProcessStartInfo
                {
                    FileName = "powercfg",
                    Arguments = "/getactivescheme",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    CreateNoWindow = true
                };

                using (var process = Process.Start(startInfo))
                {
                    if (process == null)
                    {
                        _logger.LogError($"Failed to check active power plan");
                        return;
                    }

                    var output = process.StandardOutput.ReadToEnd();
                    process.WaitForExit();

                    // Si c'est le plan actif, passer au plan Balanced
                    if (output.Contains(guid, StringComparison.OrdinalIgnoreCase))
                    {
                        startInfo.Arguments = $"/setactive {BALANCED_SCHEME_GUID}";
                        using var setProcess = Process.Start(startInfo);
                        setProcess?.WaitForExit();
                    }
                }

                // 2. Supprimer le plan
                startInfo.Arguments = $"/delete {guid}";
                using (var process = Process.Start(startInfo))
                {
                    if (process == null)
                    {
                        _logger.LogError($"Failed to delete power plan with GUID: {guid}");
                        return;
                    }
                    process.WaitForExit();
                    if (process.ExitCode == 0)
                    {
                        _logger.Log($"Deleted power plan with GUID: {guid}");
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error deleting power plan: {ex.Message}");
            }
        }

        private void ApplyPowerPlanSettings(PowerPlan plan)
        {
            try
            {
                var startInfo = new ProcessStartInfo
                {
                    FileName = "powercfg",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                    StandardOutputEncoding = System.Text.Encoding.UTF8,
                    StandardErrorEncoding = System.Text.Encoding.UTF8
                };

                _logger.Log($"Applying AC settings for {plan.Name}");

                // Processor minimum state (AC)
                startInfo.Arguments = $"/setacvalueindex {plan.Guid} SUB_PROCESSOR PROCTHROTTLEMIN {plan.AcSettings.ProcessorMinimumState}";
                ExecutePowerCfgCommand(startInfo, "processor minimum state (AC)");

                // Processor maximum state (AC)
                startInfo.Arguments = $"/setacvalueindex {plan.Guid} SUB_PROCESSOR PROCTHROTTLEMAX {plan.AcSettings.ProcessorMaximumState}";
                ExecutePowerCfgCommand(startInfo, "processor maximum state (AC)");

                // System cooling policy (AC)
                startInfo.Arguments = $"/setacvalueindex {plan.Guid} SUB_PROCESSOR SYSCOOLPOL {plan.AcSettings.SystemCoolingPolicy}";
                ExecutePowerCfgCommand(startInfo, "system cooling policy (AC)");

                // Processor performance boost mode (AC)
                startInfo.Arguments = $"/setacvalueindex {plan.Guid} SUB_PROCESSOR PERFBOOSTMODE {plan.AcSettings.ProcessorPerformanceBoostMode}";
                ExecutePowerCfgCommand(startInfo, "processor boost mode (AC)");

                // Processor boost policy (AC)
                startInfo.Arguments = $"/setacvalueindex {plan.Guid} SUB_PROCESSOR PERFBOOSTPOL {plan.AcSettings.ProcessorPerformanceBoostPolicy}";
                ExecutePowerCfgCommand(startInfo, "processor boost policy (AC)");

                // Hard disk idle timeout (AC)
                startInfo.Arguments = $"/setacvalueindex {plan.Guid} 0012ee47-9041-4b5d-9b77-535fba8b1442 6738e2c4-e8a5-4a42-b16a-e040e769756e {plan.AcSettings.DiskIdleTimeout}";
                ExecutePowerCfgCommand(startInfo, "disk idle timeout (AC)");

                // USB Hub Suspend Timeout (AC)
                startInfo.Arguments = $"/setacvalueindex {plan.Guid} 2a737441-1930-4402-8d77-b2bebba308a3 0853a681-27c8-4100-a2fd-82013e970683 {plan.AcSettings.UsbHubTimeout}";
                ExecutePowerCfgCommand(startInfo, "USB hub suspend timeout (AC)");

                // USB Selective Suspend (AC)
                startInfo.Arguments = $"/setacvalueindex {plan.Guid} 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 {(plan.AcSettings.UsbSuspend ? 1 : 0)}";
                ExecutePowerCfgCommand(startInfo, "USB selective suspend (AC)");

                // USB IOC Setting (AC)
                startInfo.Arguments = $"/setacvalueindex {plan.Guid} 2a737441-1930-4402-8d77-b2bebba308a3 498c044a-201b-4631-a522-5c744ed4e678 {(plan.AcSettings.UsbIoc ? 1 : 0)}";
                ExecutePowerCfgCommand(startInfo, "USB IOC setting (AC)");

                // USB 3 Link Power Management (AC)
                startInfo.Arguments = $"/setacvalueindex {plan.Guid} 2a737441-1930-4402-8d77-b2bebba308a3 d4e98f31-5ffe-4ce1-be31-1b38b384c009 {plan.AcSettings.UsbLinkPower}";
                ExecutePowerCfgCommand(startInfo, "USB 3 link power management (AC)");

                // Apply processor boost time window
                startInfo.Arguments = $"/setacvalueindex {plan.Guid} SUB_PROCESSOR PERFBOOSTPERCENT {plan.AcSettings.ProcessorBoostTimeWindow}";
                ExecutePowerCfgCommand(startInfo, "processor boost time window (AC)");

                // Apply processor performance increase policy
                startInfo.Arguments = $"/setacvalueindex {plan.Guid} 54533251-82be-4824-96c1-47b60b740d00 465e1f50-b610-473a-ab58-00d1077dc418 {plan.AcSettings.ProcessorPerformanceIncreasePolicy}";
                ExecutePowerCfgCommand(startInfo, "processor performance increase policy (AC)");

                // Appliquer les paramètres DC
                _logger.Log($"Applying DC settings for {plan.Name}");
                
                // AMD Dynamic Graphics (DC)
                if (_intelCpuManager?.IsSupported() == true)
                {
                    var graphicsMode = plan.DcSettings.DynamicGraphicsMode;
                    if (graphicsMode >= 0 && graphicsMode < AMD_DYNAMIC_GRAPHICS_VALUES.Length)
                    {
                        startInfo.Arguments = $"/setdcvalueindex {plan.Guid} e276e160-7cb0-43c6-b20b-73f5dce39954 a1662ab2-9d34-4e53-ba8b-2639b9e20857 {AMD_DYNAMIC_GRAPHICS_VALUES[graphicsMode]:X8}";
                        ExecutePowerCfgCommand(startInfo, "AMD dynamic graphics mode (DC)");
                    }
                }

                // Processor minimum state (DC)
                startInfo.Arguments = $"/setdcvalueindex {plan.Guid} SUB_PROCESSOR PROCTHROTTLEMIN {plan.DcSettings.ProcessorMinimumState}";
                ExecutePowerCfgCommand(startInfo, "processor minimum state (DC)");

                // Processor maximum state (DC)
                startInfo.Arguments = $"/setdcvalueindex {plan.Guid} SUB_PROCESSOR PROCTHROTTLEMAX {plan.DcSettings.ProcessorMaximumState}";
                ExecutePowerCfgCommand(startInfo, "processor maximum state (DC)");

                // System cooling policy (DC)
                startInfo.Arguments = $"/setdcvalueindex {plan.Guid} SUB_PROCESSOR SYSCOOLPOL {plan.DcSettings.SystemCoolingPolicy}";
                ExecutePowerCfgCommand(startInfo, "system cooling policy (DC)");

                // Processor performance boost mode (DC)
                startInfo.Arguments = $"/setdcvalueindex {plan.Guid} SUB_PROCESSOR PERFBOOSTMODE {plan.DcSettings.ProcessorPerformanceBoostMode}";
                ExecutePowerCfgCommand(startInfo, "processor boost mode (DC)");

                // Processor boost policy (DC)
                startInfo.Arguments = $"/setdcvalueindex {plan.Guid} SUB_PROCESSOR PERFBOOSTPOL {plan.DcSettings.ProcessorPerformanceBoostPolicy}";
                ExecutePowerCfgCommand(startInfo, "processor boost policy (DC)");

                // Hard disk idle timeout (DC)
                startInfo.Arguments = $"/setdcvalueindex {plan.Guid} 0012ee47-9041-4b5d-9b77-535fba8b1442 6738e2c4-e8a5-4a42-b16a-e040e769756e {plan.DcSettings.DiskIdleTimeout}";
                ExecutePowerCfgCommand(startInfo, "disk idle timeout (DC)");

                // USB Hub Suspend Timeout (DC)
                startInfo.Arguments = $"/setdcvalueindex {plan.Guid} 2a737441-1930-4402-8d77-b2bebba308a3 0853a681-27c8-4100-a2fd-82013e970683 {plan.DcSettings.UsbHubTimeout}";
                ExecutePowerCfgCommand(startInfo, "USB hub suspend timeout (DC)");

                // USB Selective Suspend (DC)
                startInfo.Arguments = $"/setdcvalueindex {plan.Guid} 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 {(plan.DcSettings.UsbSuspend ? 1 : 0)}";
                ExecutePowerCfgCommand(startInfo, "USB selective suspend (DC)");

                // USB IOC Setting (DC)
                startInfo.Arguments = $"/setdcvalueindex {plan.Guid} 2a737441-1930-4402-8d77-b2bebba308a3 498c044a-201b-4631-a522-5c744ed4e678 {(plan.DcSettings.UsbIoc ? 1 : 0)}";
                ExecutePowerCfgCommand(startInfo, "USB IOC setting (DC)");

                // USB 3 Link Power Management (DC)
                startInfo.Arguments = $"/setdcvalueindex {plan.Guid} 2a737441-1930-4402-8d77-b2bebba308a3 d4e98f31-5ffe-4ce1-be31-1b38b384c009 {plan.DcSettings.UsbLinkPower}";
                ExecutePowerCfgCommand(startInfo, "USB 3 link power management (DC)");

                // Apply processor boost time window
                startInfo.Arguments = $"/setdcvalueindex {plan.Guid} SUB_PROCESSOR PERFBOOSTPERCENT {plan.DcSettings.ProcessorBoostTimeWindow}";
                ExecutePowerCfgCommand(startInfo, "processor boost time window (DC)");

                // Apply processor performance increase policy
                startInfo.Arguments = $"/setdcvalueindex {plan.Guid} 54533251-82be-4824-96c1-47b60b740d00 465e1f50-b610-473a-ab58-00d1077dc418 {plan.DcSettings.ProcessorPerformanceIncreasePolicy}";
                ExecutePowerCfgCommand(startInfo, "processor performance increase policy (DC)");

                // Appliquer les changements
                startInfo.Arguments = $"/setactive {plan.Guid}";
                ExecutePowerCfgCommand(startInfo, "activating plan");
                
                // Revenir au plan précédent si nécessaire
                if (_activePowerPlan != null)
                {
                    var currentPlan = _powerPlans[_activePowerPlan];
                    startInfo.Arguments = $"/setactive {currentPlan.Guid}";
                    ExecutePowerCfgCommand(startInfo, "restoring previous active plan");
                }

                _logger.Log($"Successfully applied all settings for power plan: {plan.Name}");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error applying settings for power plan {plan.Name}: {ex.Message}");
            }
        }

        private void ExecutePowerCfgCommand(ProcessStartInfo startInfo, string operation)
        {
            using var process = Process.Start(startInfo);
            if (process == null)
            {
                _logger.LogError($"Failed to start process for {operation}");
                return;
            }
            
            var output = process.StandardOutput.ReadToEnd();
            var error = process.StandardError.ReadToEnd();
            process.WaitForExit();
            
            if (process.ExitCode != 0)
            {
                _logger.LogError($"Failed to apply {operation}. Exit code: {process.ExitCode}");
                if (!string.IsNullOrEmpty(error))
                {
                    _logger.LogError($"Error output: {error}");
                }
                if (!string.IsNullOrEmpty(output))
                {
                    _logger.LogError($"Standard output: {output}");
                }
            }
            else
            {
                _logger.Log($"Successfully applied {operation}");
            }
        }

        public void SetActivePowerPlan(string planType)
        {
            try
            {
                if (!_powerPlans.ContainsKey(planType))
                {
                    _logger.LogError($"Power plan type not found: {planType}");
                    return;
                }

                var plan = _powerPlans[planType];
                var frameworkPlanName = plan.Name;

                // Obtenir le GUID du plan
                var guid = GetPowerPlanGuid(frameworkPlanName);
                if (string.IsNullOrEmpty(guid))
                {
                    _logger.LogError($"Power plan {frameworkPlanName} not found in system");
                    return;
                }

                // Activer le plan
                var startInfo = new ProcessStartInfo
                {
                    FileName = "powercfg",
                    Arguments = $"-setactive {guid}",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                    StandardOutputEncoding = System.Text.Encoding.UTF8,
                    StandardErrorEncoding = System.Text.Encoding.UTF8
                };

                using (var process = Process.Start(startInfo))
                {
                    if (process == null)
                    {
                        _logger.LogError($"Failed to start process for setting active power plan {frameworkPlanName}");
                        return;
                    }
                    var output = process.StandardOutput.ReadToEnd();
                    var error = process.StandardError.ReadToEnd();
                    process.WaitForExit();
                    
                    if (process.ExitCode != 0)
                    {
                        _logger.LogError($"Failed to set active power plan {frameworkPlanName}. Exit code: {process.ExitCode}");
                        _logger.LogError($"Error output: {error}");
                        _logger.LogError($"Standard output: {output}");
                        return;
                    }
                }

                _activePowerPlan = planType;  // Mettre à jour directement le cache
                _logger.Log($"Set active power plan to: {frameworkPlanName}");

                // Appliquer les profils CPU-spécifiques
                if (_intelCpuManager?.IsSupported() == true)
                {
                    _intelCpuManager.ApplyProfile(planType);
                }
                else if (_ryzenAdjManager?.GetCurrentCpuModel() != null)
                {
                    _ryzenAdjManager.ApplyProfile(planType);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error setting active power plan: {ex.Message}");
            }
        }

        public string GetActivePowerPlanType()
        {
            // Si on a déjà un plan actif en mémoire, le retourner
            if (!string.IsNullOrEmpty(_activePowerPlan))
            {
                return _activePowerPlan;
            }

            try
            {
                var startInfo = new ProcessStartInfo
                {
                    FileName = "powercfg",
                    Arguments = "/getactivescheme",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    CreateNoWindow = true,
                    StandardOutputEncoding = System.Text.Encoding.UTF8
                };

                using var process = Process.Start(startInfo);
                if (process == null)
                {
                    _logger.LogError("Failed to start process for getting active power plan");
                    return "balanced";
                }

                var output = process.StandardOutput.ReadToEnd();
                process.WaitForExit();

                // Extraire le GUID du plan actif
                var activeGuid = output.Split(' ').FirstOrDefault(part => part.Contains('-'))?.Trim();
                if (string.IsNullOrEmpty(activeGuid))
                {
                    _logger.LogWarning("Could not extract active power plan GUID");
                    return "balanced";
                }

                // Si c'est le plan Balanced par défaut, retourner "balanced"
                if (activeGuid.Equals(BALANCED_SCHEME_GUID, StringComparison.OrdinalIgnoreCase))
                {
                    _activePowerPlan = "balanced";
                    return "balanced";
                }

                // Chercher le plan correspondant par GUID
                foreach (var plan in _powerPlans)
                {
                    if (plan.Value.Guid.Equals(activeGuid, StringComparison.OrdinalIgnoreCase))
                    {
                        _activePowerPlan = plan.Key;
                        return plan.Key;
                    }
                }

                _logger.LogWarning($"Active power plan with GUID {activeGuid} not found in known Framework plans");
                _activePowerPlan = "balanced";
                return "balanced";
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error getting active power plan: {ex.Message}");
                return "balanced";
            }
        }

        // Méthode pour forcer la mise à jour du plan actif
        public void RefreshActivePowerPlan()
        {
            _activePowerPlan = null;  // Reset le cache
            GetActivePowerPlanType(); // Force une nouvelle détection
        }

        private string? GetPowerPlanGuid(string planName)
        {
            try
            {
                var startInfo = new ProcessStartInfo
                {
                    FileName = "powercfg",
                    Arguments = "/list",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    CreateNoWindow = true
                };

                using var process = Process.Start(startInfo);
                if (process == null)
                {
                    _logger.LogError($"Failed to start process for getting power plan GUID: {planName}");
                    return null;
                }

                var output = process.StandardOutput.ReadToEnd();
                process.WaitForExit();

                foreach (var line in output.Split('\n'))
                {
                    if (string.IsNullOrWhiteSpace(line)) continue;

                    try
                    {
                        // Format attendu: Power Scheme GUID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx  (name)
                        var parts = line.Split(new[] { "GUID:", "(", ")" }, StringSplitOptions.RemoveEmptyEntries);
                        if (parts.Length < 3) continue;

                        var guid = parts[1].Trim();
                        var name = parts[2].Trim();

                        if (name.Equals(planName, StringComparison.OrdinalIgnoreCase))
                        {
                            return guid;
                        }
                    }
                    catch
                    {
                        continue;
                    }
                }

                return null;
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error getting power plan GUID: {ex.Message}");
                return null;
            }
        }

        public bool IsSupported()
        {
            return _intelCpuManager?.IsSupported() == true || _ryzenAdjManager?.GetCurrentCpuModel() != null;
        }

        public (int? Pl1, int? Pl2)? GetCurrentPowerLimits()
        {
            if (_intelCpuManager?.IsSupported() == true)
            {
                var profile = _intelCpuManager.GetProfile(_activePowerPlan ?? "balanced");
                if (profile != null)
                {
                    return (profile.Pl1, profile.Pl2);
                }
            }
            return null;
        }

        public PowerPlan? GetProfile(string profileType)
        {
            try
            {
                if (_powerPlans.TryGetValue(profileType, out var profile))
                {
                    return profile;
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

        public void SaveProfile(string profileType, PowerPlan profile)
        {
            try
            {
                // 1. Mettre à jour le dictionnaire des plans
                _powerPlans[profileType] = profile;

                // 2. Sauvegarder dans le fichier JSON
                var root = new Dictionary<string, Dictionary<string, PowerPlan>>
                {
                    { "power_plans", _powerPlans }
                };

                var options = new JsonSerializerOptions
                {
                    WriteIndented = true,
                    PropertyNamingPolicy = JsonNamingPolicy.CamelCase
                };

                var json = JsonSerializer.Serialize(root, options);
                var directory = Path.GetDirectoryName(_powerPlansPath);
                if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }
                File.WriteAllText(_powerPlansPath, json);

                // 3. Mettre à jour le plan Windows existant
                var startInfo = new ProcessStartInfo
                {
                    FileName = "powercfg",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                    StandardOutputEncoding = System.Text.Encoding.UTF8,
                    StandardErrorEncoding = System.Text.Encoding.UTF8
                };

                // Vérifier si le plan existe déjà
                var existingGuid = GetPowerPlanGuid(profile.Name);
                if (!string.IsNullOrEmpty(existingGuid))
                {
                    // Mettre à jour le GUID dans le profil
                    profile.Guid = existingGuid;

                    // Appliquer les paramètres au plan existant
                    ApplyPowerPlanSettings(profile);
                    _logger.Log($"Updated existing power plan: {profile.Name}");
                    
                    // Forcer une mise à jour du plan actif après la modification
                    RefreshActivePowerPlan();
                }
                else
                {
                    // Créer un nouveau plan si nécessaire
                    CreatePowerPlan(profile);
                    // Forcer une mise à jour du plan actif après la création
                    RefreshActivePowerPlan();
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error saving profile {profileType}: {ex.Message}");
                throw;
            }
        }

        public void UpdatePowerPlanSettings()
        {
            try
            {
                // Recharger les paramètres depuis le fichier JSON
                LoadPowerPlans();

                // Mettre à jour chaque plan existant
                foreach (var plan in _powerPlans)
                {
                    var frameworkPlanName = plan.Value.Name;  // Le nom contient déjà "Framework-"
                    var guid = GetPowerPlanGuid(frameworkPlanName);

                    if (string.IsNullOrEmpty(guid))
                    {
                        _logger.LogError($"Could not find GUID for power plan {frameworkPlanName}");
                        continue;
                    }

                    _logger.Log($"Updating settings for power plan {frameworkPlanName}");
                    ApplyPowerPlanSettings(plan.Value);
                }

                _logger.Log("Power plan settings updated successfully");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error updating power plan settings: {ex.Message}");
            }
        }
    }
}
