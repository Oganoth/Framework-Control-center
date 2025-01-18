using System;
using System.Runtime.InteropServices;
using System.Runtime.Versioning;
using Avalonia.Logging;
using System.IO;

namespace FrameworkControl.Models
{
    [SupportedOSPlatform("windows")]
    public static class Ring0
    {
        private static readonly Logger _logger = new Logger("Ring0");
        private static bool _initialized = false;

        // Status codes
        private const uint OLS_DLL_NO_ERROR = 0;
        private const uint OLS_DLL_UNSUPPORTED_PLATFORM = 1;
        private const uint OLS_DLL_DRIVER_NOT_LOADED = 2;
        private const uint OLS_DLL_DRIVER_NOT_FOUND = 3;
        private const uint OLS_DLL_DRIVER_UNLOADED = 4;
        private const uint OLS_DLL_DRIVER_NOT_LOADED_ON_NETWORK = 5;
        private const uint OLS_DLL_UNKNOWN_ERROR = 9;

        [DllImport("WinRing0x64.dll")]
        private static extern byte InitializeOls();

        [DllImport("WinRing0x64.dll")]
        private static extern void DeinitializeOls();

        [DllImport("WinRing0x64.dll")]
        private static extern byte Rdmsr(uint Index, ref uint EAX, ref uint EDX);

        [DllImport("WinRing0x64.dll")]
        private static extern byte Wrmsr(uint Index, uint EAX, uint EDX);

        [DllImport("WinRing0x64.dll")]
        private static extern uint GetDllStatus();

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        private static extern IntPtr LoadLibrary(string dllToLoad);

        static Ring0()
        {
            try
            {
                // 1. Vérifier que tous les fichiers nécessaires sont présents
                var baseDir = AppDomain.CurrentDomain.BaseDirectory;
                var dllPath = Path.Combine(baseDir, "WinRing0x64.dll");
                var sysPath = Path.Combine(baseDir, "WinRing0x64.sys");

                if (!File.Exists(dllPath))
                {
                    _logger.LogError($"WinRing0x64.dll not found at: {dllPath}");
                    return;
                }

                if (!File.Exists(sysPath))
                {
                    _logger.LogError($"WinRing0x64.sys not found at: {sysPath}");
                    _logger.Log($"Please copy WinRing0x64.sys to: {sysPath}");
                    return;
                }

                // 2. Charger la DLL
                _logger.Log($"Loading WinRing0x64.dll from: {dllPath}");
                var hModule = LoadLibrary(dllPath);
                if (hModule == IntPtr.Zero)
                {
                    var error = Marshal.GetLastWin32Error();
                    _logger.LogError($"Failed to load WinRing0x64.dll. Error code: {error}");
                    return;
                }
                _logger.Log($"Successfully loaded WinRing0x64.dll");

                // 3. Initialiser WinRing0
                _logger.Log("Attempting to initialize WinRing0...");
                var result = InitializeOls();
                _logger.Log($"InitializeOls returned: {result}");

                // 4. Vérifier le statut
                var status = GetDllStatus();
                _logger.Log($"WinRing0 Driver status: {GetStatusMessage(status)}");

                if (result == 1)
                {
                    if (status == OLS_DLL_NO_ERROR)
                    {
                        _initialized = true;
                        _logger.Log("WinRing0 initialized successfully");
                    }
                    else if (status == OLS_DLL_DRIVER_NOT_FOUND)
                    {
                        _logger.LogError("WinRing0 driver not found. Please ensure WinRing0x64.sys is in the same directory as the executable.");
                    }
                    else if (status == OLS_DLL_DRIVER_NOT_LOADED)
                    {
                        _logger.LogError("WinRing0 driver could not be loaded. Please run the application as administrator.");
                    }
                }
                else
                {
                    _logger.LogError($"Failed to initialize WinRing0. Status: {GetStatusMessage(status)}");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error initializing WinRing0: {ex.Message}");
            }
        }

        private static string GetStatusMessage(uint status)
        {
            return status switch
            {
                OLS_DLL_NO_ERROR => "No error",
                OLS_DLL_UNSUPPORTED_PLATFORM => "Unsupported platform",
                OLS_DLL_DRIVER_NOT_LOADED => "Driver not loaded",
                OLS_DLL_DRIVER_NOT_FOUND => "Driver not found",
                OLS_DLL_DRIVER_UNLOADED => "Driver unloaded",
                OLS_DLL_DRIVER_NOT_LOADED_ON_NETWORK => "Driver not loaded on network",
                OLS_DLL_UNKNOWN_ERROR => "Unknown error",
                _ => $"Undefined error: {status}"
            };
        }

        public static bool WriteMsr(uint register, uint value)
        {
            if (!_initialized)
            {
                _logger.LogError("WinRing0 not initialized");
                return false;
            }

            try
            {
                if (Wrmsr(register, value, 0) == 1)
                {
                    _logger.Log($"Successfully wrote value {value} to MSR register 0x{register:X}");
                    return true;
                }
                
                _logger.LogError($"Failed to write to MSR register 0x{register:X}");
                return false;
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error writing to MSR: {ex.Message}");
                return false;
            }
        }

        public static bool ReadMsr(uint register, out uint value)
        {
            value = 0;
            if (!_initialized)
            {
                _logger.LogError("WinRing0 not initialized");
                return false;
            }

            try
            {
                uint eax = 0, edx = 0;
                if (Rdmsr(register, ref eax, ref edx) == 1)
                {
                    value = eax;
                    _logger.Log($"Successfully read value {value} from MSR register 0x{register:X}");
                    return true;
                }
                
                _logger.LogError($"Failed to read from MSR register 0x{register:X}");
                return false;
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error reading from MSR: {ex.Message}");
                return false;
            }
        }

        public static void Cleanup()
        {
            if (_initialized)
            {
                try
                {
                    DeinitializeOls();
                    _logger.Log("WinRing0 deinitialized");
                }
                catch (Exception ex)
                {
                    _logger.LogError($"Error deinitializing WinRing0: {ex.Message}");
                }
            }
        }
    }
} 