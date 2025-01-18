using Microsoft.Win32;
using System;
using System.Runtime.Versioning;
using System.Threading;
using System.Threading.Tasks;

namespace FrameworkControl.Helpers
{
    [SupportedOSPlatform("windows")]
    public class ThemeWatcher : IDisposable
    {
        private const string DWMKeyPath = @"Software\Microsoft\Windows\DWM";
        private const string ColorPrevalenceKey = "ColorPrevalence";
        private const string AccentColorKey = "AccentColor";
        private readonly Models.Logger _logger;
        private readonly CancellationTokenSource _cancellationTokenSource;
        private Task? _watcherTask;
        private bool _disposed;
        
        public event EventHandler? ThemeColorChanged;

        public ThemeWatcher()
        {
            _logger = new Models.Logger("ThemeWatcher");
            _cancellationTokenSource = new CancellationTokenSource();
            StartWatching();
        }

        private void StartWatching()
        {
            try
            {
                _watcherTask = Task.Run(async () =>
                {
                    uint? lastAccentColor = null;
                    int? lastColorPrevalence = null;

                    while (!_cancellationTokenSource.Token.IsCancellationRequested)
                    {
                        try
                        {
                            using var key = Registry.CurrentUser.OpenSubKey(DWMKeyPath);
                            if (key != null)
                            {
                                var currentAccentColor = key.GetValue(AccentColorKey) as uint?;
                                var currentColorPrevalence = key.GetValue(ColorPrevalenceKey) as int?;
                                var colorPrevalenceChanged = currentColorPrevalence != (lastColorPrevalence ?? -1);
                                var accentColorChanged = currentAccentColor != (lastAccentColor ?? 0);

                                if (colorPrevalenceChanged || accentColorChanged)
                                {
                                    lastAccentColor = currentAccentColor;
                                    lastColorPrevalence = currentColorPrevalence;
                                    ThemeColorChanged?.Invoke(this, EventArgs.Empty);
                                }
                            }
                        }
                        catch (Exception ex)
                        {
                            _logger.LogError($"Error checking registry values: {ex.Message}");
                        }

                        try
                        {
                            await Task.Delay(500, _cancellationTokenSource.Token);
                        }
                        catch (OperationCanceledException)
                        {
                            break;
                        }
                    }
                }, _cancellationTokenSource.Token);
            }
            catch (Exception ex)
            {
                _logger.LogError($"Failed to start theme watcher: {ex.Message}");
            }
        }

        public void Dispose()
        {
            if (!_disposed)
            {
                try
                {
                    _cancellationTokenSource.Cancel();
                    _watcherTask?.Wait(1000);
                    _cancellationTokenSource.Dispose();
                }
                catch (Exception ex)
                {
                    _logger.LogError($"Error during disposal: {ex.Message}");
                }
                finally
                {
                    _disposed = true;
                }
            }
        }
    }
}
