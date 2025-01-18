using Avalonia;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Markup.Xaml;
using Avalonia.Themes.Fluent;
using System.Linq;
using System.Runtime.Versioning;
using System.Windows.Input;
using System;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Threading;
using System.Threading.Tasks;
using System.Runtime.InteropServices;
using FrameworkControl.Models;
using System.Threading;
using FrameworkControl.Styles;
using FrameworkControl.Helpers;

namespace FrameworkControl
{
    [SupportedOSPlatform("windows")]
    public partial class App : Application
    {
        private Window? _mainWindow;
        public ICommand ToggleWindowCommand { get; }
        public ICommand ExitApplicationCommand { get; }
        private const int WH_KEYBOARD_LL = 13;
        private const int WM_KEYDOWN = 0x0100;
        private IntPtr _hookHandle = IntPtr.Zero;
        private Win32.LowLevelKeyboardProc? _hookProc;
        private AppSettings _settings;
        private ThemeWatcher? _themeWatcher;
        private readonly Models.Logger _logger;

        public App()
        {
            _logger = new Models.Logger("App");
            ToggleWindowCommand = new RelayCommand(ToggleWindow);
            ExitApplicationCommand = new RelayCommand(ExitApplication);
            _settings = AppSettings.Load();
            
            try
            {
                // Initialiser le ThemeWatcher
                _themeWatcher = new ThemeWatcher();
                _themeWatcher.ThemeColorChanged += OnThemeColorChanged;
            }
            catch (Exception ex)
            {
                _logger.LogError($"Failed to initialize ThemeWatcher: {ex.Message}");
            }
        }

        private void OnThemeColorChanged(object? sender, EventArgs e)
        {
            try
            {
                // S'assurer que la mise à jour du thème se fait sur le thread UI
                Dispatcher.UIThread.Post(() => 
                {
                    try
                    {
                        ThemeManager.ApplyTheme(this);
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError($"Failed to apply theme: {ex.Message}");
                    }
                });
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error in OnThemeColorChanged: {ex.Message}");
            }
        }

        public override void Initialize()
        {
            try
            {
                AvaloniaXamlLoader.Load(this);
            }
            catch (Exception ex)
            {
                _logger.LogError($"Failed to initialize Avalonia: {ex.Message}");
                throw;
            }
        }

        public override void OnFrameworkInitializationCompleted()
        {
            try
            {
                if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
                {
                    desktop.MainWindow = new MainWindow();
                    _mainWindow = desktop.MainWindow;

                    // Position window after it's opened
                    _mainWindow.Opened += (s, e) => PositionWindow();
                    
                    try
                    {
                        ThemeManager.ApplyTheme(this);
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError($"Failed to apply initial theme: {ex.Message}");
                    }
                    
                    _mainWindow.Closed += (sender, args) => 
                    {
                        if (Application.Current?.ApplicationLifetime is IClassicDesktopStyleApplicationLifetime lifetime)
                        {
                            lifetime.Shutdown();
                        }
                    };

                    _mainWindow.Show();
                    
                    if (_settings.StartMinimized)
                    {
                        Dispatcher.UIThread.Post(() => ToggleWindow(), DispatcherPriority.Background);
                    }
                    
                    DataContext = this;

                    try
                    {
                        InstallHook();
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError($"Failed to install keyboard hook: {ex.Message}");
                    }

                    desktop.Exit += OnExit;
                }

                base.OnFrameworkInitializationCompleted();
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error in OnFrameworkInitializationCompleted: {ex.Message}");
                throw;
            }
        }

        private void PositionWindow()
        {
            if (_mainWindow == null) return;

            var screen = TopLevel.GetTopLevel(_mainWindow)?.Screens?.Primary;
            if (screen == null) return;

            var workArea = screen.WorkingArea;
            var bounds = _mainWindow.Bounds;
            var scaling = screen.Scaling;

            // Force window width to be exactly 320 (as defined in XAML)
            bounds = bounds.WithWidth(320);
            _mainWindow.Width = 320;

            // Position the window exactly 3 pixels from the right edge
            const int rightMargin = 3;

            // Calculate horizontal position with scaling compensation
            var scaledScreenWidth = workArea.Width;
            var scaledWindowWidth = bounds.Width * scaling;
            var scaledMargin = rightMargin * scaling;
            var xPosition = (scaledScreenWidth - scaledWindowWidth - scaledMargin) / scaling;

            // Adjust horizontal position based on scaling percentage
            if (scaling > 1.0)
            {
                // Calculate scaling percentage above 100%
                var scalingPercentageAbove100 = (scaling - 1.0) * 100;
                // Add that same percentage to xPosition
                xPosition *= (1 + scalingPercentageAbove100 / 100);
            }

            // Keep the original working vertical position that was correct
            var yPosition = workArea.Height - bounds.Height;
            yPosition /= scaling;

            // Force the position update
            _mainWindow.WindowStartupLocation = WindowStartupLocation.Manual;
            _mainWindow.Position = new PixelPoint(
                (int)Math.Round(workArea.X / scaling + xPosition),
                (int)Math.Round(workArea.Y / scaling + yPosition)
            );

            // Log position details
            Console.WriteLine($"Screen Width: {workArea.Width}, Window Width: {bounds.Width}, Scaling: {scaling}, X Position: {xPosition}");

            // Ensure window is visible and active
            _mainWindow.Show();
            _mainWindow.Activate();
        }

        private void OnExit(object? sender, ControlledApplicationLifetimeExitEventArgs e)
        {
            try
            {
                UninstallHook();
                _themeWatcher?.Dispose();
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error during application exit: {ex.Message}");
            }
        }

        private void InstallHook()
        {
            _hookProc = HookCallback;
            using var process = System.Diagnostics.Process.GetCurrentProcess();
            using var module = process.MainModule;
            if (module != null)
            {
                try
                {
                    _hookHandle = Win32.SetWindowsHookEx(
                        WH_KEYBOARD_LL,
                        _hookProc,
                        Win32.GetModuleHandle(module.ModuleName),
                        0);
                }
                catch (Exception ex)
                {
                    _logger.LogError($"Failed to install keyboard hook: {ex.Message}");
                }
            }
        }

        private void UninstallHook()
        {
            if (_hookHandle != IntPtr.Zero)
            {
                try
                {
                    Win32.UnhookWindowsHookEx(_hookHandle);
                }
                catch (Exception ex)
                {
                    _logger.LogError($"Failed to uninstall keyboard hook: {ex.Message}");
                }
                _hookHandle = IntPtr.Zero;
            }
        }

        private IntPtr HookCallback(int nCode, IntPtr wParam, IntPtr lParam)
        {
            if (nCode >= 0 && wParam == (IntPtr)WM_KEYDOWN)
            {
                var vkCode = Marshal.ReadInt32(lParam);
                
                // Convertir le raccourci configuré en code virtuel
                if (Enum.TryParse<Key>(_settings.ToggleWindowHotkey, out var configuredKey))
                {
                    // Conversion spécifique pour les touches de fonction
                    int configuredVkCode = configuredKey switch
                    {
                        Key.F1 => 0x70,
                        Key.F2 => 0x71,
                        Key.F3 => 0x72,
                        Key.F4 => 0x73,
                        Key.F5 => 0x74,
                        Key.F6 => 0x75,
                        Key.F7 => 0x76,
                        Key.F8 => 0x77,
                        Key.F9 => 0x78,
                        Key.F10 => 0x79,
                        Key.F11 => 0x7A,
                        Key.F12 => 0x7B,
                        _ => (int)configuredKey
                    };

                    if (vkCode == configuredVkCode)
                    {
                        Dispatcher.UIThread.Post(ToggleWindow);
                        return (IntPtr)1;
                    }
                }
            }
            return Win32.CallNextHookEx(_hookHandle, nCode, wParam, lParam);
        }

        private void ToggleWindow()
        {
            if (_mainWindow == null) return;

            if (_mainWindow.IsVisible)
            {
                _mainWindow.Hide();
            }
            else
            {
                _mainWindow.Show();
                _mainWindow.Activate();
                _mainWindow.WindowState = WindowState.Normal;
            }
        }

        private void ExitApplication()
        {
            try
            {
                UninstallHook();
                if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
                {
                    desktop.Shutdown();
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error during application exit: {ex.Message}");
            }
        }

        public void SetTheme(string theme)
        {
            if (Current?.Styles == null) return;

            var currentTheme = Current.Styles.OfType<FluentTheme>().FirstOrDefault();
            if (currentTheme != null)
            {
                Current.Styles.Remove(currentTheme);
            }

            var newTheme = new FluentTheme();
            Current.RequestedThemeVariant = theme.ToLower() switch
            {
                "dark" => Avalonia.Styling.ThemeVariant.Dark,
                "light" => Avalonia.Styling.ThemeVariant.Light,
                _ => Avalonia.Styling.ThemeVariant.Dark // Default to dark
            };

            Current.Styles.Insert(0, newTheme);
        }

        public class RelayCommand : ICommand
        {
            private readonly Action _execute;
            private readonly Func<bool>? _canExecute;

            public RelayCommand(Action execute, Func<bool>? canExecute = null)
            {
                _execute = execute ?? throw new ArgumentNullException(nameof(execute));
                _canExecute = canExecute;
            }

            public bool CanExecute(object? parameter)
            {
                return _canExecute?.Invoke() ?? true;
            }

            public void Execute(object? parameter)
            {
                _execute();
            }

            // This event is required by ICommand but we don't use it
            // Suppress the warning since this is by design
#pragma warning disable CS0067
            public event EventHandler? CanExecuteChanged;
#pragma warning restore CS0067
        }

        internal static class Win32
        {
            public delegate IntPtr LowLevelKeyboardProc(int nCode, IntPtr wParam, IntPtr lParam);

            [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
            public static extern IntPtr SetWindowsHookEx(int idHook, LowLevelKeyboardProc lpfn, IntPtr hMod, uint dwThreadId);

            [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
            [return: MarshalAs(UnmanagedType.Bool)]
            public static extern bool UnhookWindowsHookEx(IntPtr hhk);

            [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
            public static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);

            [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
            public static extern IntPtr GetModuleHandle(string? lpModuleName);
        }

        public void RefreshSettings()
        {
            try
            {
                _settings = AppSettings.Load();
            }
            catch (Exception ex)
            {
                _logger.LogError($"Failed to refresh settings: {ex.Message}");
            }
        }
    }
}