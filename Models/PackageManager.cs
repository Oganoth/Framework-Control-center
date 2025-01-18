using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Threading.Tasks;

namespace FrameworkControl.Models
{
    public class PackageManager
    {
        private readonly Logger _logger;

        public PackageManager()
        {
            _logger = new Logger("PackageManager");
        }

        private bool IsWingetAvailable()
        {
            var paths = Environment.GetEnvironmentVariable("PATH")?.Split(Path.PathSeparator);
            if (paths == null) return false;

            var extensions = Environment.GetEnvironmentVariable("PATHEXT")?.Split(Path.PathSeparator) 
                ?? new[] { ".EXE", ".CMD", ".BAT" };

            return paths.Any(path =>
                extensions.Any(ext =>
                    File.Exists(Path.Combine(path, "winget" + ext))));
        }

        public async Task<IEnumerable<PackageUpdate>> CheckForUpdatesAsync(PackageManagerType type)
        {
            if (type != PackageManagerType.Winget)
                throw new ArgumentException("Only Winget package manager is supported");

            try
            {
                if (!IsWingetAvailable())
                {
                    _logger.LogWarning("Winget is not installed or not found in PATH");
                    return Array.Empty<PackageUpdate>();
                }

                return await CheckWingetUpdatesAsync();
            }
            catch (Exception ex)
            {
                _logger.Error($"Error checking for updates with Winget: {ex.Message}");
                return Array.Empty<PackageUpdate>();
            }
        }

        private async Task<IEnumerable<PackageUpdate>> CheckWingetUpdatesAsync()
        {
            var updates = new List<PackageUpdate>();
            var output = await RunCommandAsync("winget", "upgrade");

            // Parse winget output
            var lines = output.Split('\n');
            var startParsing = false;
            var idIndex = -1;
            var nameIndex = -1;
            var versionIndex = -1;
            var availableIndex = -1;

            foreach (var line in lines)
            {
                if (line.Contains("Name") && line.Contains("Id") && line.Contains("Version") && line.Contains("Available"))
                {
                    startParsing = true;
                    // Find column indexes from header
                    var headerParts = line.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                    for (int i = 0; i < headerParts.Length; i++)
                    {
                        switch (headerParts[i].ToLower())
                        {
                            case "name": nameIndex = i; break;
                            case "id": idIndex = i; break;
                            case "version": versionIndex = i; break;
                            case "available": availableIndex = i; break;
                        }
                    }
                    continue;
                }

                if (startParsing && !string.IsNullOrWhiteSpace(line) && !line.Contains("--"))
                {
                    var parts = line.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                    if (parts.Length >= 4 && idIndex >= 0 && nameIndex >= 0 && versionIndex >= 0 && availableIndex >= 0)
                    {
                        updates.Add(new PackageUpdate
                        {
                            Name = parts[nameIndex],
                            Id = parts[idIndex],
                            CurrentVersion = parts[versionIndex],
                            NewVersion = parts[availableIndex],
                            PackageManager = PackageManagerType.Winget
                        });
                    }
                }
            }

            return updates;
        }

        private async Task<string> RunCommandAsync(string command, string arguments)
        {
            try
            {
                if (!IsWingetAvailable())
                {
                    throw new FileNotFoundException("Winget is not installed or not found in PATH");
                }

                var startInfo = new ProcessStartInfo
                {
                    FileName = command,
                    Arguments = arguments,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    WorkingDirectory = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile)
                };

                using var process = new Process { StartInfo = startInfo };
                process.Start();

                var output = await process.StandardOutput.ReadToEndAsync();
                var error = await process.StandardError.ReadToEndAsync();
                await process.WaitForExitAsync();

                _logger.LogCommand(command, arguments, output, error, process.ExitCode);

                if (process.ExitCode != 0)
                {
                    throw new Exception($"Command failed with exit code {process.ExitCode}: {error}");
                }

                return output;
            }
            catch (Exception ex)
            {
                _logger.Error($"Error running command '{command} {arguments}': {ex.Message}");
                throw;
            }
        }

        public async Task UpdatePackageAsync(PackageUpdate package)
        {
            if (package.PackageManager != PackageManagerType.Winget)
                throw new ArgumentException("Only Winget packages can be updated");

            try
            {
                if (!IsWingetAvailable())
                {
                    throw new FileNotFoundException("Winget is not installed or not found in PATH");
                }

                await RunCommandAsync("winget", $"upgrade {package.Id} --source winget --force --accept-source-agreements");
            }
            catch (Exception ex)
            {
                _logger.Error($"Error updating package {package.Name}: {ex.Message}");
                throw;
            }
        }
    }
} 