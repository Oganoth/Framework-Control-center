using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using System.Security.Principal;
using System.Runtime.Versioning;
using System.Diagnostics.CodeAnalysis;
using LibreHardwareMonitor.Hardware;
using System.Threading;
using System.Text.RegularExpressions;

namespace FrameworkControl.Models
{
    [SupportedOSPlatform("windows")]
    public class HardwareMonitor : IDisposable
    {
        private Computer? computer;
        private readonly Logger _logger;
        private bool _isDisposed;
        private readonly object _lock = new object();
        private bool _isMonitoring = true;
        private WindowsPerformanceMonitor? _windowsPerfMon;
        private bool _isIntelCpu;
        private int _updateInterval = 1000;

        public HardwareMonitor()
        {
            _logger = new Logger("Hardware");
            Initialize();
        }

        public void SetUpdateInterval(int milliseconds)
        {
            _updateInterval = milliseconds;
            if (_isIntelCpu && _windowsPerfMon != null)
            {
                _windowsPerfMon.SetUpdateInterval(milliseconds);
            }
        }

        private void Initialize()
        {
            try
            {
                lock (_lock)
                {
                    _logger.Log("Initializing HardwareMonitor");
                    
                    // Check if we're running with admin privileges
                    _logger.Log("Checking administrative privileges");
                    if (!IsAdministrator())
                    {
                        _logger.LogError("Application must be run as administrator");
                        return;
                    }

                    // Check if required DLLs exist
                    _logger.Log("Checking required DLLs");
                    if (!CheckRequiredDlls())
                    {
                        _logger.LogError("Required DLLs not found");
                        return;
                    }

                    // Initialize computer instance
                    _logger.Log("Opening computer");
                    computer = new Computer
                    {
                        IsCpuEnabled = true,
                        IsGpuEnabled = true,
                        IsMemoryEnabled = true,
                        IsMotherboardEnabled = true,
                        IsBatteryEnabled = true,
                        IsControllerEnabled = true,
                        IsNetworkEnabled = false,
                        IsStorageEnabled = false
                    };

                    computer.Open();
                    computer.Accept(new UpdateVisitor());

                    // Détection du CPU Intel
                    var cpu = computer.Hardware.FirstOrDefault(h => h.HardwareType == HardwareType.Cpu);
                    _isIntelCpu = cpu?.Name.Contains("Intel", StringComparison.OrdinalIgnoreCase) == true;

                    // Si c'est un CPU Intel, initialiser le Windows Performance Monitor
                    if (_isIntelCpu)
                    {
                        _logger.Log("Intel CPU detected, initializing Windows Performance Monitor");
                        _windowsPerfMon = new WindowsPerformanceMonitor();
                        _windowsPerfMon.SetUpdateInterval(_updateInterval);
                    }

                    // Log des capteurs disponibles
                    ExportAvailableSensors();
                    _logger.Log("\nHardwareMonitor initialized successfully");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error initializing hardware monitor: {ex.Message}");
                computer = null;
            }
        }

        public void Reset()
        {
            try
            {
                lock (_lock)
                {
                    if (computer != null)
                    {
                        computer.Close();
                        computer = null;
                    }
                    Initialize();
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error resetting hardware monitor: {ex.Message}");
            }
        }

        public void StartMonitoring()
        {
            _isMonitoring = true;
        }

        public void StopMonitoring()
        {
            _isMonitoring = false;
            // Reset all values to 0 when monitoring is stopped
            // CpuTemp = 0;
            // CpuPower = 0;
            // GpuTemp = 0;
            // GpuPower = 0;
            // FanSpeed = 0;
        }

        public void Update()
        {
            if (!_isMonitoring) return;

            try
            {
                lock (_lock)
                {
                    if (computer == null)
                    {
                        Reset();
                        return;
                    }

                    try
                    {
                        foreach (var hardware in computer.Hardware)
                        {
                            hardware.Update();
                            foreach (var subHardware in hardware.SubHardware)
                            {
                                subHardware.Update();
                            }
                        }
                    }
                    catch (Exception)
                    {
                        // Si une erreur se produit pendant la mise à jour, on réinitialise
                        Reset();
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error updating: {ex.Message}");
            }
        }

        private bool IsAdministrator()
        {
            var identity = WindowsIdentity.GetCurrent();
            if (identity == null) return false;
            var principal = new WindowsPrincipal(identity);
            return principal.IsInRole(WindowsBuiltInRole.Administrator);
        }

        private bool CheckRequiredDlls()
        {
            var baseDir = AppDomain.CurrentDomain.BaseDirectory;
            var requiredDlls = new[] { "WinRing0x64.dll", "inpoutx64.dll" };
            var missingDlls = new List<string>();

            _logger.Log("Checking required DLLs");
            foreach (var dll in requiredDlls)
            {
                if (!File.Exists(Path.Combine(baseDir, dll)))
                {
                    missingDlls.Add(dll);
                    _logger.LogWarning($"Missing DLL: {dll}");
                }
            }

            if (missingDlls.Any())
            {
                var error = $"Missing required DLLs for hardware monitoring: {string.Join(", ", missingDlls)}. " +
                           "Please ensure these DLLs are present in the application directory.";
                _logger.LogError(error);
                throw new FileNotFoundException(error);
            }

            return true;
        }

        public float GetCpuTemperature()
        {
            try
            {
                // Pour les CPU Intel, utiliser Windows Performance Monitor
                if (_isIntelCpu && _windowsPerfMon != null)
                {
                    return _windowsPerfMon.GetCpuTemperature();
                }

                // Pour les autres CPU, utiliser LibreHardwareMonitor
                if (computer?.Hardware == null)
                {
                    _logger.LogWarning("Computer or hardware is null");
                    return 0;
                }

                var cpu = computer.Hardware.FirstOrDefault(h => h.HardwareType == HardwareType.Cpu);
                if (cpu == null)
                {
                    _logger.LogWarning("No CPU hardware found");
                    return 0;
                }

                cpu.Update();
                var tempSensors = cpu.Sensors
                    .Where(s => s.SensorType == SensorType.Temperature)
                    .ToList();

                if (tempSensors.Any())
                {
                    var maxTemp = tempSensors
                        .Where(s => s.Value.HasValue)
                        .Select(s => s.Value!.Value)
                        .DefaultIfEmpty(0)
                        .Max();

                    _logger.Log($"CPU Temperature (LibreHardware): {maxTemp}°C");
                    return maxTemp;
                }

                _logger.LogWarning("No CPU temperature sensors found");
                return 0;
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error getting CPU temperature: {ex.Message}");
                return 0;
            }
        }

        public float GetCpuUsage()
        {
            try
            {
                // Pour les CPU Intel, utiliser Windows Performance Monitor
                if (_isIntelCpu && _windowsPerfMon != null)
                {
                    return _windowsPerfMon.GetCpuUsage();
                }

                // Pour les autres CPU, utiliser LibreHardwareMonitor
                if (computer?.Hardware == null)
                {
                    _logger.LogWarning("Computer or hardware is null");
                    return 0;
                }

                var cpu = computer.Hardware.FirstOrDefault(h => h.HardwareType == HardwareType.Cpu);
                if (cpu == null)
                {
                    _logger.LogWarning("No CPU hardware found");
                    return 0;
                }

                cpu.Update();
                var totalSensor = cpu.Sensors.FirstOrDefault(s => s.SensorType == SensorType.Load && s.Name == "CPU Total");
                if (totalSensor?.Value != null)
                {
                    var usage = totalSensor.Value.Value;
                    _logger.Log($"CPU Usage (LibreHardware): {usage}%");
                    return usage;
                }

                _logger.LogWarning("CPU Total sensor not found");
                return 0;
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error getting CPU usage: {ex.Message}");
                return 0;
            }
        }

        public string GetCpuName()
        {
            try
            {
                if (computer?.Hardware == null)
                {
                    _logger.LogWarning("Computer or hardware is null");
                    return string.Empty;
                }

                var cpu = computer.Hardware.FirstOrDefault(h => h.HardwareType == HardwareType.Cpu);
                if (cpu == null)
                {
                    _logger.LogWarning("No CPU hardware found");
                    return string.Empty;
                }

                _logger.Log($"CPU Name: {cpu.Name}");
                return cpu.Name;
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error getting CPU name: {ex.Message}");
                return string.Empty;
            }
        }

        public (float Usage, float Temperature) GetIntegratedGpuInfo()
        {
            try
            {
                // Pour les GPU Intel, utiliser Windows Performance Monitor
                if (_isIntelCpu && _windowsPerfMon != null)
                {
                    var (usage, memory) = _windowsPerfMon.GetIntelGpuInfo();
                    return (usage, 0); // La température n'est pas disponible via les compteurs Windows
                }

                // Pour les autres GPU, utiliser LibreHardwareMonitor
                if (computer?.Hardware == null)
                {
                    _logger.LogWarning("Computer or hardware is null");
                    return (0, 0);
                }

                var igpu = computer.Hardware.FirstOrDefault(h => h.HardwareType == HardwareType.GpuAmd && 
                    (h.Name.Contains("780M") || h.Name.Contains("760M")));
                if (igpu != null)
                {
                    igpu.Update();
                    var usage = igpu.Sensors.FirstOrDefault(s => s.SensorType == SensorType.Load && s.Name == "D3D 3D")?.Value ?? 0;
                    var temp = igpu.Sensors.FirstOrDefault(s => s.SensorType == SensorType.Temperature && s.Name == "GPU VR SoC")?.Value ?? 0;
                    _logger.Log($"AMD iGPU - Usage: {usage}%, Temperature: {temp}°C");
                    return (usage, temp);
                }

                _logger.LogWarning("No integrated GPU found");
                return (0, 0);
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error getting iGPU info: {ex.Message}");
                return (0, 0);
            }
        }

        public (float Usage, float Temperature) GetDiscreteGpuInfo()
        {
            try
            {
                if (computer?.Hardware == null)
                {
                    _logger.LogWarning("Computer or hardware is null");
                    return (0, 0);
                }

                var dgpu = computer.Hardware.FirstOrDefault(h => h.HardwareType == HardwareType.GpuAmd && 
                    (h.Name.Contains("RX 7700", StringComparison.OrdinalIgnoreCase) || 
                     h.Name.Contains("Radeon RX", StringComparison.OrdinalIgnoreCase)) &&
                    !h.Name.Contains("Radeon(TM) Graphics", StringComparison.OrdinalIgnoreCase));
                if (dgpu != null)
                {
                    dgpu.Update();
                    var usage = dgpu.Sensors.FirstOrDefault(s => s.SensorType == SensorType.Load && s.Name == "GPU Core")?.Value ?? 0;
                    var temp = dgpu.Sensors.FirstOrDefault(s => s.SensorType == SensorType.Temperature && s.Name == "GPU Core")?.Value ?? 0;
                    _logger.Log($"dGPU Usage: {usage}%, Temperature: {temp}°C");
                    return (usage, temp);
                }
                _logger.LogWarning("Discrete GPU not found");
                return (0, 0);
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error getting dGPU info: {ex.Message}");
                return (0, 0);
            }
        }

        public (float UsagePercentage, float UsedGB, float AvailableGB) GetMemoryInfo()
        {
            try
            {
                if (computer?.Hardware == null)
                {
                    _logger.LogWarning("Computer or hardware is null");
                    return (0, 0, 0);
                }

                var ram = computer.Hardware.FirstOrDefault(h => h.HardwareType == HardwareType.Memory);
                if (ram != null)
                {
                    ram.Update();
                    var usage = ram.Sensors.FirstOrDefault(s => s.SensorType == SensorType.Load && s.Name == "Memory")?.Value ?? 0;
                    var used = ram.Sensors.FirstOrDefault(s => s.SensorType == SensorType.Data && s.Name == "Memory Used")?.Value ?? 0;
                    var available = ram.Sensors.FirstOrDefault(s => s.SensorType == SensorType.Data && s.Name == "Memory Available")?.Value ?? 0;
                    _logger.Log($"RAM Usage: {usage}%, Used: {used:F1}GB, Available: {available:F1}GB");
                    return (usage, used, available);
                }
                _logger.LogWarning("Memory info not found");
                return (0, 0, 0);
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error getting memory info: {ex.Message}");
                return (0, 0, 0);
            }
        }

        public void ExportAvailableSensors()
        {
            try
            {
                if (computer?.Hardware == null)
                {
                    _logger.LogWarning("Computer or hardware is null");
                    return;
                }

                _logger.Log("Starting sensor export...");
                var logsDirectory = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "logs");
                if (!Directory.Exists(logsDirectory))
                {
                    Directory.CreateDirectory(logsDirectory);
                }
                var sensorsPath = Path.Combine(logsDirectory, "available_sensors.txt");
                using (StreamWriter writer = new StreamWriter(sensorsPath))
                {
                    writer.WriteLine($"Available Sensors Export - {DateTime.Now:yyyy-MM-dd HH:mm:ss}");
                    writer.WriteLine("================================================");

                    _logger.Log($"Number of hardware components: {computer.Hardware.Count}");
                    foreach (var hardware in computer.Hardware)
                    {
                        _logger.Log($"Processing hardware: {hardware.Name} ({hardware.HardwareType})");
                        writer.WriteLine($"\nHardware: {hardware.Name} ({hardware.HardwareType})");
                        writer.WriteLine("------------------------");

                        hardware.Update();  // Update before accessing sensors
                        _logger.Log($"Number of sensors for {hardware.Name}: {hardware.Sensors.Count()}");

                        foreach (var sensor in hardware.Sensors)
                        {
                            writer.WriteLine($"Sensor: {sensor.Name}");
                            writer.WriteLine($"  Type: {sensor.SensorType}");
                            writer.WriteLine($"  Value: {sensor.Value}");
                            writer.WriteLine($"  Min: {sensor.Min}");
                            writer.WriteLine($"  Max: {sensor.Max}");
                            writer.WriteLine($"  Index: {sensor.Index}");
                            writer.WriteLine("------------------------");
                        }

                        if (hardware.SubHardware.Count() > 0)
                        {
                            _logger.Log($"Number of sub-hardware components for {hardware.Name}: {hardware.SubHardware.Count()}");
                            foreach (var subHardware in hardware.SubHardware)
                            {
                                writer.WriteLine($"\nSubHardware: {subHardware.Name} ({subHardware.HardwareType})");
                                writer.WriteLine("------------------------");

                                subHardware.Update();  // Update before accessing sensors
                                _logger.Log($"Number of sensors for sub-hardware {subHardware.Name}: {subHardware.Sensors.Count()}");

                                foreach (var sensor in subHardware.Sensors)
                                {
                                    writer.WriteLine($"Sensor: {sensor.Name}");
                                    writer.WriteLine($"  Type: {sensor.SensorType}");
                                    writer.WriteLine($"  Value: {sensor.Value}");
                                    writer.WriteLine($"  Min: {sensor.Min}");
                                    writer.WriteLine($"  Max: {sensor.Max}");
                                    writer.WriteLine($"  Index: {sensor.Index}");
                                    writer.WriteLine("------------------------");
                                }
                            }
                        }
                    }
                }
                _logger.Log("Sensors export completed successfully");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error exporting sensors: {ex.GetType().Name}: {ex.Message}\n{ex.StackTrace}");
                throw;
            }
        }

        public bool HasDiscreteGpu()
        {
            try
            {
                if (computer?.Hardware == null)
                {
                    return false;
                }

                return computer.Hardware.Any(h => h.HardwareType == HardwareType.GpuNvidia || 
                                                h.HardwareType == HardwareType.GpuAmd);
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error checking discrete GPU presence: {ex.Message}");
                return false;
            }
        }

        public void Dispose()
        {
            if (!_isDisposed)
            {
                try
                {
                    lock (_lock)
                    {
                        if (computer != null)
                        {
                            computer.Close();
                            computer = null;
                        }
                        _windowsPerfMon?.Dispose();
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogError($"Error disposing hardware monitor: {ex.Message}");
                }
                finally
                {
                    _isDisposed = true;
                }
            }
            GC.SuppressFinalize(this);
        }

        public CpuInfo? GetCpuInfo()
        {
            try
            {
                var cpuName = GetCpuName();
                if (string.IsNullOrEmpty(cpuName))
                {
                    _logger.LogWarning("Could not get CPU name");
                    return null;
                }

                // Check if it's an AMD CPU
                if (cpuName.Contains("AMD", StringComparison.OrdinalIgnoreCase) && 
                    cpuName.Contains("Ryzen", StringComparison.OrdinalIgnoreCase))
                {
                    var match = Regex.Match(cpuName, @"Ryzen (?:\d+)? ?(\d{4}[A-Z]+\d*[A-Z]*)", RegexOptions.IgnoreCase);
                    if (!match.Success)
                    {
                        _logger.LogWarning($"Could not extract model from AMD CPU name: {cpuName}");
                        return new CpuInfo
                        {
                            FullName = cpuName,
                            Model = "Unknown",
                            ProfileKey = "UNKNOWN",
                            IsAmd = true
                        };
                    }

                    var model = match.Groups[1].Value;
                    _logger.Log($"Extracted AMD model: {model}");

                    return new CpuInfo
                    {
                        FullName = cpuName,
                        Model = model,
                        ProfileKey = $"{model}_AMD",
                        IsAmd = true
                    };
                }

                // Check if it's a supported Intel CPU
                if (cpuName.Contains("Intel", StringComparison.OrdinalIgnoreCase))
                {
                    string? model = null;
                    
                    // Check Framework 13" Intel Models
                    if (cpuName.Contains("1340P")) model = "1340P";
                    else if (cpuName.Contains("1360P")) model = "1360P";
                    else if (cpuName.Contains("1370P")) model = "1370P";
                    // Core Ultra models
                    else if (cpuName.Contains("Ultra") && cpuName.Contains("165H")) model = "165H";
                    else if (cpuName.Contains("Ultra") && cpuName.Contains("155H")) model = "155H";
                    else if (cpuName.Contains("Ultra") && cpuName.Contains("125H")) model = "125H";

                    if (model != null)
                    {
                        _logger.Log($"Detected supported Intel model: {model}");
                        return new CpuInfo
                        {
                            FullName = cpuName,
                            Model = model,
                            ProfileKey = $"{model}_INTEL",
                            IsAmd = false
                        };
                    }

                    _logger.LogWarning($"Unsupported Intel CPU model: {cpuName}");
                    return new CpuInfo
                    {
                        FullName = cpuName,
                        Model = "Unknown",
                        ProfileKey = "UNKNOWN",
                        IsAmd = false
                    };
                }

                _logger.Log($"Unknown CPU manufacturer: {cpuName}");
                return new CpuInfo
                {
                    FullName = cpuName,
                    Model = "Unknown",
                    ProfileKey = "UNKNOWN",
                    IsAmd = false
                };
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error getting CPU info: {ex.Message}");
                return null;
            }
        }
    }

    public class UpdateVisitor : IVisitor
    {
        public void VisitComputer(IComputer computer)
        {
            computer.Traverse(this);
        }

        public void VisitHardware(IHardware hardware)
        {
            hardware.Update();
            foreach (IHardware subHardware in hardware.SubHardware) subHardware.Accept(this);
        }

        public void VisitSensor(ISensor sensor) { }
        public void VisitParameter(IParameter parameter) { }
    }
}