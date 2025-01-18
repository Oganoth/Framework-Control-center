using System;
using System.Runtime.Versioning;
using System.Text.RegularExpressions;
using System.Collections.Generic;
using LibreHardwareMonitor.Hardware;
using Avalonia.Logging;

namespace FrameworkControl.Models
{
    [SupportedOSPlatform("windows")]
    public class CpuModelDetector
    {
        private readonly HardwareMonitor _hardwareMonitor;
        private readonly Logger _logger;

        public CpuModelDetector(HardwareMonitor hardwareMonitor)
        {
            _hardwareMonitor = hardwareMonitor;
            _logger = new Logger("CpuDetector");
        }

        public CpuInfo? DetectCpuModel()
        {
            try
            {
                var cpuName = _hardwareMonitor.GetCpuName();
                _logger.Log($"Detected CPU: {cpuName}");

                // Check if it's an AMD CPU
                if (cpuName.Contains("AMD", StringComparison.OrdinalIgnoreCase) && 
                    cpuName.Contains("Ryzen", StringComparison.OrdinalIgnoreCase))
                {
                    return DetectAmdModel(cpuName);
                }
                
                // Check if it's a supported Intel CPU
                if (cpuName.Contains("Intel", StringComparison.OrdinalIgnoreCase))
                {
                    return DetectIntelModel(cpuName);
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
                _logger.LogError($"Error detecting CPU model: {ex.Message}");
                return null;
            }
        }

        private CpuInfo DetectAmdModel(string cpuName)
        {
            // Extract CPU model for AMD
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

        private CpuInfo DetectIntelModel(string cpuName)
        {
            string? model = null;
            
            // Check Framework 13" Intel Models
            if (cpuName.Contains("1340P")) model = "1340P";
            else if (cpuName.Contains("1360P")) model = "1360P";
            else if (cpuName.Contains("1370P")) model = "1370P";
            // Core Ultra models
            else if (cpuName.Contains("Core Ultra 7 165H")) model = "165H";
            else if (cpuName.Contains("Core Ultra 7 155H")) model = "155H";
            else if (cpuName.Contains("Core Ultra 5 125H")) model = "125H";

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
    }

    public class CpuInfo
    {
        public required string FullName { get; init; }
        public required string Model { get; init; }
        public required string ProfileKey { get; init; }
        public required bool IsAmd { get; init; }
    }
}
