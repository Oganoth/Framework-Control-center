using System;
using System.Diagnostics;
using System.Collections.Generic;
using System.Runtime.Versioning;
using System.Management;
using Microsoft.Win32;

namespace FrameworkControl.Models
{
    [SupportedOSPlatform("windows")]
    public class WindowsPerformanceMonitor : IDisposable
    {
        private readonly Logger _logger;
        private PerformanceCounter? _cpuCounter;
        private PerformanceCounter? _ramCounter;
        private readonly List<PerformanceCounter> _cpuCoreCounters = new();
        private ManagementObjectSearcher? _temperatureSearcher;
        private ManagementObjectSearcher? _gpuSearcher;
        private bool _isDisposed;
        private DateTime _lastUpdate = DateTime.MinValue;
        private float _lastTemperature;
        private DateTime _lastGpuUpdate = DateTime.MinValue;
        private (float Usage, float Memory) _lastGpuInfo;
        private int _updateInterval = 1000; // Par défaut 1 seconde
        private bool _isAdmin;

        public WindowsPerformanceMonitor()
        {
            _logger = new Logger("WindowsPerfMon");

            try
            {
                // Vérifier les permissions administrateur
                _isAdmin = IsAdministrator();
                if (!_isAdmin)
                {
                    _logger.LogError("Application must be run as administrator for performance monitoring");
                    return;
                }

                // Activer les compteurs de performance avec les droits admin
                var process = new Process
                {
                    StartInfo = new ProcessStartInfo
                    {
                        FileName = "lodctr",
                        Arguments = "/r",
                        UseShellExecute = true,
                        Verb = "runas",
                        CreateNoWindow = true,
                        WindowStyle = ProcessWindowStyle.Hidden
                    }
                };
                process.Start();
                process.WaitForExit();

                // CPU Total Load
                _cpuCounter = new PerformanceCounter("Processor", "% Processor Time", "_Total", true);
                
                // RAM Usage
                _ramCounter = new PerformanceCounter("Memory", "% Committed Bytes In Use", null, true);

                // CPU Core Loads
                var processorCount = Environment.ProcessorCount;
                for (int i = 0; i < processorCount; i++)
                {
                    var coreCounter = new PerformanceCounter("Processor", "% Processor Time", i.ToString(), true);
                    _cpuCoreCounters.Add(coreCounter);
                }

                // WMI Queries pour la température et le GPU
                _temperatureSearcher = new ManagementObjectSearcher(@"root\WMI", 
                    "SELECT * FROM MSAcpi_ThermalZoneTemperature");
                
                // Nouvelle requête WMI spécifique pour les GPU Intel
                _gpuSearcher = new ManagementObjectSearcher(@"root\CIMV2", 
                    "SELECT * FROM Win32_VideoController WHERE Name LIKE '%Intel%'");

                _logger.Log("Windows Performance Monitor initialized successfully with admin rights");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error initializing Windows Performance Monitor: {ex.Message}");
                throw;
            }
        }

        private bool IsAdministrator()
        {
            var identity = System.Security.Principal.WindowsIdentity.GetCurrent();
            var principal = new System.Security.Principal.WindowsPrincipal(identity);
            return principal.IsInRole(System.Security.Principal.WindowsBuiltInRole.Administrator);
        }

        public void SetUpdateInterval(int milliseconds)
        {
            _updateInterval = milliseconds;
            _logger.Log($"Update interval set to {milliseconds}ms");
        }

        public float GetCpuUsage()
        {
            try
            {
                if (_cpuCounter == null)
                {
                    _logger.LogWarning("CPU counter not initialized");
                    return 0;
                }

                var usage = _cpuCounter.NextValue();
                _logger.Log($"CPU Usage (Windows): {usage}%");
                return usage;
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error getting CPU usage: {ex.Message}");
                return 0;
            }
        }

        public List<float> GetCpuCoreUsages()
        {
            try
            {
                var usages = new List<float>();
                foreach (var counter in _cpuCoreCounters)
                {
                    usages.Add(counter.NextValue());
                }
                return usages;
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error getting CPU core usages: {ex.Message}");
                return new List<float>();
            }
        }

        public float GetCpuTemperature()
        {
            try
            {
                // Vérifier si nous devons mettre à jour la température
                var now = DateTime.Now;
                if ((now - _lastUpdate).TotalMilliseconds < _updateInterval)
                {
                    return _lastTemperature;
                }

                // Utiliser les compteurs de performance Windows pour la température
                using var tempCounter = new PerformanceCounter("Thermal Zone Information", 
                    "Temperature", 
                    @"\_TZ.TZ00", // Zone thermique principale du CPU
                    true);

                try
                {
                    var tempKelvin = tempCounter.NextValue();
                    var tempCelsius = tempKelvin - 273.15f;

                    // Vérifier si la température est dans une plage réaliste
                    if (tempCelsius >= 0 && tempCelsius <= 100)
                    {
                        _lastUpdate = now;
                        _lastTemperature = tempCelsius;
                        _logger.Log($"CPU Temperature (Performance Counter): {tempCelsius:F2}°C");
                        return tempCelsius;
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogWarning($"Error reading temperature from performance counter: {ex.Message}");
                }

                // Si le compteur de performance échoue, essayer via WMI
                using var searcher = new ManagementObjectSearcher(@"root\WMI",
                    "SELECT * FROM MSAcpi_ThermalZoneTemperature WHERE Active='1'");

                float maxTemp = 0;
                bool tempFound = false;

                foreach (ManagementObject obj in searcher.Get())
                {
                    try
                    {
                        var temp = Convert.ToInt32(obj["CurrentTemperature"]);
                        var tempC = (temp / 10.0f) - 273.15f;

                        if (tempC >= 0 && tempC <= 100)
                        {
                            maxTemp = Math.Max(maxTemp, tempC);
                            tempFound = true;
                            _logger.Log($"Found temperature sensor: {tempC:F2}°C");
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogWarning($"Error reading temperature sensor: {ex.Message}");
                    }
                }

                if (tempFound)
                {
                    _lastUpdate = now;
                    _lastTemperature = maxTemp;
                    _logger.Log($"CPU Temperature (WMI): {maxTemp:F2}°C");
                    return maxTemp;
                }

                _logger.LogWarning("No valid temperature sensors found");
                return _lastTemperature;
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error getting CPU temperature: {ex.Message}");
                return _lastTemperature;
            }
        }

        public (float Usage, float Memory) GetIntelGpuInfo()
        {
            try
            {
                // Vérifier si nous devons mettre à jour les informations GPU
                var now = DateTime.Now;
                if ((now - _lastGpuUpdate).TotalMilliseconds < _updateInterval)
                {
                    return _lastGpuInfo;
                }

                if (_gpuSearcher == null)
                {
                    _logger.LogWarning("GPU searcher not initialized");
                    return (0, 0);
                }

                foreach (ManagementObject obj in _gpuSearcher.Get())
                {
                    try
                    {
                        // Obtenir la mémoire dédiée en Mo
                        var memoryString = obj["AdapterRAM"]?.ToString();
                        float dedicatedMemory = 0;
                        if (!string.IsNullOrEmpty(memoryString) && long.TryParse(memoryString, out long memoryBytes))
                        {
                            dedicatedMemory = memoryBytes / (1024f * 1024f); // Conversion en Mo
                        }

                        // Obtenir l'utilisation via le registre
                        using var key = Registry.LocalMachine.OpenSubKey(@"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0000");
                        if (key != null)
                        {
                            var loadValue = key.GetValue("LoadPercentage");
                            if (loadValue != null && int.TryParse(loadValue.ToString(), out int usage))
                            {
                                _lastGpuUpdate = now;
                                _lastGpuInfo = (usage, dedicatedMemory);
                                _logger.Log($"Intel GPU - Usage: {usage}%, Memory: {dedicatedMemory:F0}MB");
                                return (usage, dedicatedMemory);
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogWarning($"Error reading GPU info: {ex.Message}");
                    }
                }

                _lastGpuUpdate = now;
                _lastGpuInfo = (0, 0);
                return (0, 0);
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error getting Intel GPU info: {ex.Message}");
                return _lastGpuInfo; // Retourner les dernières valeurs connues en cas d'erreur
            }
        }

        public (float Used, float Total) GetRamInfo()
        {
            try
            {
                if (_ramCounter == null)
                {
                    _logger.LogWarning("RAM counter not initialized");
                    return (0, 0);
                }

                var usagePercent = _ramCounter.NextValue();
                
                // Obtenir la RAM totale via WMI
                using var searcher = new ManagementObjectSearcher("SELECT TotalVisibleMemorySize FROM Win32_OperatingSystem");
                foreach (ManagementObject obj in searcher.Get())
                {
                    var totalKB = Convert.ToInt64(obj["TotalVisibleMemorySize"]);
                    var totalGB = totalKB / (1024f * 1024f);
                    var usedGB = (totalGB * usagePercent) / 100f;

                    _logger.Log($"RAM Usage: {usagePercent}%, Used: {usedGB:F1}GB, Total: {totalGB:F1}GB");
                    return (usedGB, totalGB);
                }

                return (0, 0);
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error getting RAM info: {ex.Message}");
                return (0, 0);
            }
        }

        public void Dispose()
        {
            if (!_isDisposed)
            {
                try
                {
                    _cpuCounter?.Dispose();
                    _ramCounter?.Dispose();
                    foreach (var counter in _cpuCoreCounters)
                    {
                        counter.Dispose();
                    }
                    _cpuCoreCounters.Clear();
                    _temperatureSearcher?.Dispose();
                    _gpuSearcher?.Dispose();
                }
                catch (Exception ex)
                {
                    _logger.LogError($"Error disposing performance monitor: {ex.Message}");
                }
                finally
                {
                    _isDisposed = true;
                }
            }
            GC.SuppressFinalize(this);
        }
    }
} 