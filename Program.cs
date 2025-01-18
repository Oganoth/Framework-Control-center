using Avalonia;
using System;
using System.IO;
using System.Runtime.Versioning;

namespace FrameworkControl
{
    [SupportedOSPlatform("windows")]
    internal class Program
    {
        [STAThread]
        public static void Main(string[] args)
        {
            try
            {
                // Create logs directory if it doesn't exist
                var logsDirectory = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "logs");
                if (!Directory.Exists(logsDirectory))
                {
                    Directory.CreateDirectory(logsDirectory);
                }

                // Enable logging to file
                var logPath = Path.Combine(logsDirectory, "app_log.txt");
                File.WriteAllText(logPath, $"Application starting at {DateTime.Now}\n");

                // Log environment info
                File.AppendAllText(logPath, $"Current directory: {Environment.CurrentDirectory}\n");
                File.AppendAllText(logPath, $"Base directory: {AppDomain.CurrentDomain.BaseDirectory}\n");
                
                // Check if running as admin
                var identity = System.Security.Principal.WindowsIdentity.GetCurrent();
                var principal = new System.Security.Principal.WindowsPrincipal(identity);
                var isAdmin = principal.IsInRole(System.Security.Principal.WindowsBuiltInRole.Administrator);
                File.AppendAllText(logPath, $"Running as admin: {isAdmin}\n");

                // Check if required DLLs exist
                var requiredDlls = new[] { 
                    "LibreHardwareMonitorLib.dll",
                    "WinRing0x64.dll",
                    "inpoutx64.dll"
                };
                
                foreach (var dll in requiredDlls)
                {
                    var exists = File.Exists(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, dll));
                    File.AppendAllText(logPath, $"DLL {dll} exists: {exists}\n");
                }

                File.AppendAllText(logPath, "Starting Avalonia app...\n");

                // Export available sensors
                try
                {
                    File.AppendAllText(logPath, "Starting sensor export...\n");
                    using (var monitor = new Models.HardwareMonitor())
                    {
                        File.AppendAllText(logPath, "HardwareMonitor instance created\n");
                        monitor.ExportAvailableSensors();
                        File.AppendAllText(logPath, "Sensor export completed\n");
                    }
                }
                catch (Exception ex)
                {
                    File.AppendAllText(logPath, $"Error during sensor export: {ex.GetType().Name}: {ex.Message}\n{ex.StackTrace}\n");
                }

                BuildAvaloniaApp().StartWithClassicDesktopLifetime(args);
            }
            catch (Exception ex)
            {
                var logsDirectory = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "logs");
                if (!Directory.Exists(logsDirectory))
                {
                    Directory.CreateDirectory(logsDirectory);
                }
                var logPath = Path.Combine(logsDirectory, "app_error.txt");
                File.WriteAllText(logPath, $"Fatal error at {DateTime.Now}:\n{ex.GetType().Name}: {ex.Message}\n{ex.StackTrace}");
                throw;
            }
        }

        public static AppBuilder BuildAvaloniaApp()
            => AppBuilder.Configure<App>()
                .UsePlatformDetect()
                .LogToTrace();
    }
}