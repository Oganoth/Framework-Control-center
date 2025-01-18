using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Primitives;
using Avalonia.Media;
using System;
using System.Timers;
using FrameworkControl.Models;
using System.IO;
using System.Runtime.Versioning;
using Avalonia.Interactivity;
using Avalonia.Threading;
using ReactiveUI;
using Avalonia.Input;
using System.Runtime.InteropServices;
using FrameworkControl.Views;
using System.Threading.Tasks;
using System.Diagnostics;

namespace FrameworkControl
{
    [SupportedOSPlatform("windows")]
    public partial class MainWindow : Window
    {
        private readonly HardwareMonitor _hardwareMonitor;
        private readonly BrightnessController _brightnessController;
        private readonly BatteryMonitor _batteryMonitor;
        private readonly DisplayRefreshRate _displayRefreshRate;
        private readonly PowerPlanManager _powerPlanManager;
        private readonly DispatcherTimer _timer;
        private readonly Logger _logger;
        private bool _autoRefreshRateEnabled = true;
        private Grid? _dgpuGrid;
        private bool _isCompatibleCpu = false;
        private bool _hasDgpu = false;
        private string _toggleWindowHotkey = "F12";
        private GlobalHotkey? _globalHotkey;
        private int? _currentHotkeyId;
        private double _lastWidth;
        private double _lastHeight;
        private Popup? _autoProfilePopup;
        private bool _isInitializing = true;
        private bool _isManualProfileSelected = false;
        private StackPanel? _profileSelectionPanel;

        public MainWindow()
        {
            InitializeComponent();

            // Initialize logger
            _logger = new Logger("MainWindow");

            // Initialize debug settings
            var debugSettings = DebugSettings.Load();
            
            // Initialize hardware monitoring
            _hardwareMonitor = new HardwareMonitor();
            _hasDgpu = _hardwareMonitor.HasDiscreteGpu();

            if (this.FindControl<Border>("DgpuBorder") is Border dgpuBorder)
            {
                dgpuBorder.IsVisible = _hasDgpu && debugSettings.ShowDgpuControls;
            }

            if (!debugSettings.IsMonitoringEnabled)
            {
                _hardwareMonitor.StopMonitoring();
            }
            else
            {
                _hardwareMonitor.StartMonitoring();
            }

            _brightnessController = new BrightnessController();
            _batteryMonitor = new BatteryMonitor();
            _displayRefreshRate = new DisplayRefreshRate();
            _powerPlanManager = new PowerPlanManager();

            _dgpuGrid = this.FindControl<Grid>("DgpuGrid");
            CheckCpuCompatibility();

            var settings = AppSettings.Load();
            _timer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(settings.GuiUpdateInterval) };
            _timer.Tick += UpdateHardwareInfo;
            _timer.Start();

            // Initialize auto profile popup
            _autoProfilePopup = this.FindControl<Popup>("AutoProfilePopup");
            _profileSelectionPanel = this.FindControl<StackPanel>("ProfileSelectionPanel");
            
            // Load saved auto profile settings
            if (this.FindControl<ComboBox>("AcProfileSelector") is ComboBox acSelector)
            {
                acSelector.SelectedIndex = GetProfileIndex(settings.AcProfile);
            }
            if (this.FindControl<ComboBox>("DcProfileSelector") is ComboBox dcSelector)
            {
                dcSelector.SelectedIndex = GetProfileIndex(settings.DcProfile);
            }
            if (this.FindControl<CheckBox>("AutoSwitchEnabled") is CheckBox autoSwitch)
            {
                autoSwitch.IsChecked = settings.AutoSwitchEnabled;
                _isManualProfileSelected = !settings.AutoSwitchEnabled;
                if (_profileSelectionPanel != null)
                {
                    _profileSelectionPanel.IsEnabled = settings.AutoSwitchEnabled;
                }
            }
            _isInitializing = false;

            // Subscribe to battery status changes
            _batteryMonitor.ChargingStatusChanged += OnChargingStatusChanged;

            // Appliquer le profil de démarrage en fonction de l'état de l'auto-switch
            if (settings.AutoSwitchEnabled)
            {
                // Si auto-switch est activé, appliquer le profil en fonction de l'état de la batterie
                var profile = _batteryMonitor.IsCharging ? settings.AcProfile : settings.DcProfile;
                ApplyStartupProfile(profile);
            }
            else
            {
                // Si auto-switch est désactivé, appliquer le profil de démarrage défini dans les paramètres
                ApplyStartupProfile(settings.StartupProfile);
            }

            // Initialiser le slider avec la luminosité actuelle
            InitializeBrightnessSlider();

            // S'abonner à l'événement de changement d'état de la fenêtre
            PropertyChanged += (s, e) =>
            {
                if (e.Property == Window.WindowStateProperty)
                {
                    if (WindowState == WindowState.Minimized)
                    {
                        _timer.Stop();
                        Topmost = false;
                        Log("Monitoring paused - Window minimized");
                    }
                    else if (WindowState == WindowState.Normal || WindowState == WindowState.Maximized)
                    {
                        _timer.Start();
                        Topmost = true;
                        Log("Monitoring resumed - Window restored");
                    }
                }
            };

            // Set up keyboard button
            if (this.FindControl<Button>("KeyboardButton") is Button keyboardButton)
            {
                keyboardButton.Click += (s, e) =>
                {
                    var psi = new System.Diagnostics.ProcessStartInfo
                    {
                        FileName = "https://keyboard.frame.work/",
                        UseShellExecute = true
                    };
                    System.Diagnostics.Process.Start(psi);
                };
            }

            // Set up settings button
            if (this.FindControl<Button>("SettingsButton") is Button settingsButton)
            {
                settingsButton.Click += SettingsButton_Click;
            }

            // Set up updates manager button
            if (this.FindControl<Button>("UpdatesButton") is Button updatesButton)
            {
                updatesButton.Click += UpdatesButton_Click;
            }

            // Set up refresh rate radio buttons
            if (this.FindControl<RadioButton>("AutoRefreshRate") is RadioButton autoRate)
                autoRate.IsCheckedChanged += (s, e) => 
                {
                    if (autoRate.IsChecked == true)
                    {
                        _autoRefreshRateEnabled = true;
                        _logger.Log($"Switching to Auto refresh rate mode (Charging: {_batteryMonitor.IsCharging})");
                        _displayRefreshRate.SetAutoRefreshRate(_batteryMonitor.IsCharging);
                    }
                };

            if (this.FindControl<RadioButton>("Rate60Hz") is RadioButton rate60)
                rate60.IsCheckedChanged += (s, e) => 
                {
                    if (rate60.IsChecked == true)
                    {
                        _autoRefreshRateEnabled = false;
                        _logger.Log("Manually setting refresh rate to 60Hz");
                        _displayRefreshRate.SetRefreshRate(60);
                    }
                };

            if (this.FindControl<RadioButton>("RateMaxHz") is RadioButton rateMax)
            {
                // Update the max refresh rate text
                if (this.FindControl<TextBlock>("MaxRefreshRateText") is TextBlock maxRefreshText)
                {
                    int maxRate = _displayRefreshRate.GetMaxRefreshRate();
                    maxRefreshText.Text = $"{maxRate}Hz";
                    _logger.Log($"Initialized max refresh rate button with {maxRate}Hz");
                }

                rateMax.IsCheckedChanged += (s, e) => 
                {
                    if (rateMax.IsChecked == true)
                    {
                        _autoRefreshRateEnabled = false;
                        int maxRate = _displayRefreshRate.GetMaxRefreshRate();
                        _logger.Log($"Manually setting refresh rate to maximum ({maxRate}Hz)");
                        _displayRefreshRate.SetRefreshRate(maxRate);
                    }
                };
            }

            // Initial update
            UpdateHardwareInfo(this, EventArgs.Empty);

            _toggleWindowHotkey = settings.ToggleWindowHotkey;
            InitializeGlobalHotkey();

            // Set up minimize and close buttons
            if (this.FindControl<Button>("MinimizeButton") is Button minimizeButton)
            {
                minimizeButton.Click += MinimizeButton_Click;
            }

            if (this.FindControl<Button>("CloseButton") is Button closeButton)
            {
                closeButton.Click += CloseButton_Click;
            }
        }

        private void CheckCpuCompatibility()
        {
            _isCompatibleCpu = _powerPlanManager.IsSupported();

            // Disable power profile buttons if power management is not supported
            if (!_isCompatibleCpu)
            {
                if (this.FindControl<Button>("EcoButton") is Button ecoButton)
                    ecoButton.IsEnabled = false;
                if (this.FindControl<Button>("BalancedButton") is Button balancedButton)
                    balancedButton.IsEnabled = false;
                if (this.FindControl<Button>("BoostButton") is Button boostButton)
                    boostButton.IsEnabled = false;
            }
        }

        private void UpdateHardwareInfo(object? sender, EventArgs e)
        {
            if (!Dispatcher.UIThread.CheckAccess())
            {
                Dispatcher.UIThread.InvokeAsync(() => UpdateHardwareInfo(sender, e));
                return;
            }

            _batteryMonitor.UpdateBatteryInfo();

            try
            {
                // Mettre à jour toutes les valeurs hardware en une fois
                _hardwareMonitor.Update();

                var cpuUsage = _hardwareMonitor.GetCpuUsage();
                var cpuTemp = _hardwareMonitor.GetCpuTemperature();
                var (ramUsage, ramUsed, ramAvailable) = _hardwareMonitor.GetMemoryInfo();
                var (igpuUsage, igpuTemp) = _hardwareMonitor.GetIntegratedGpuInfo();
                var (dgpuUsage, dgpuTemp) = _hardwareMonitor.GetDiscreteGpuInfo();

                // Update power plan buttons
                var activePlan = _powerPlanManager.GetActivePowerPlanType();
                if (this.FindControl<Button>("EcoButton") is Button ecoButton)
                {
                    if (activePlan == "eco")
                        ecoButton.Classes.Add("active");
                    else
                        ecoButton.Classes.Remove("active");
                }
                if (this.FindControl<Button>("BalancedButton") is Button balancedButton)
                {
                    if (activePlan == "balanced")
                        balancedButton.Classes.Add("active");
                    else
                        balancedButton.Classes.Remove("active");
                }
                if (this.FindControl<Button>("BoostButton") is Button boostButton)
                {
                    if (activePlan == "boost")
                        boostButton.Classes.Add("active");
                    else
                        boostButton.Classes.Remove("active");
                }

                // Update battery text and level
                if (this.FindControl<TextBlock>("BatteryStatusText") is TextBlock batteryText)
                    batteryText.Text = _batteryMonitor.GetStatusText();
                
                if (this.FindControl<Border>("BatteryLevel") is Border batteryLevel)
                {
                    batteryLevel.Width = 28 * (_batteryMonitor.BatteryPercentage / 100.0);
                    if (_batteryMonitor.BatteryPercentage <= 20)
                    {
                        batteryLevel.Background = new SolidColorBrush(Colors.Red);
                    }
                    else
                    {
                        batteryLevel.Classes.Set("batteryFill", true);
                    }
                }

                // Mettre à jour les labels
                if (this.FindControl<ProgressBar>("cpuUsageBar") is ProgressBar cpuUsageBar)
                    cpuUsageBar.Value = cpuUsage;

                if (this.FindControl<TextBlock>("cpuUsageText") is TextBlock cpuUsageText)
                    cpuUsageText.Text = $"CPU: {cpuUsage:F1}%";

                if (this.FindControl<TextBlock>("cpuTempText") is TextBlock cpuTempText)
                    cpuTempText.Text = $"{cpuTemp:F1}°C";

                if (this.FindControl<ProgressBar>("ramUsageBar") is ProgressBar ramUsageBar)
                    ramUsageBar.Value = ramUsage;

                if (this.FindControl<TextBlock>("ramUsageText") is TextBlock ramUsageText)
                    ramUsageText.Text = $"RAM: {ramUsage:F1}% ({ramUsed:F1} GB/{ramUsed + ramAvailable:F1} GB)";

                if (this.FindControl<ProgressBar>("igpuUsageBar") is ProgressBar igpuUsageBar)
                    igpuUsageBar.Value = igpuUsage;

                if (this.FindControl<TextBlock>("igpuUsageText") is TextBlock igpuUsageText)
                    igpuUsageText.Text = $"iGPU: {igpuUsage:F1}%";

                if (this.FindControl<TextBlock>("igpuTempText") is TextBlock igpuTempText)
                    igpuTempText.Text = $"{igpuTemp:F1}°C";

                if (_isCompatibleCpu)
                {
                    if (this.FindControl<ProgressBar>("dgpuUsageBar") is ProgressBar dgpuUsageBar)
                        dgpuUsageBar.Value = dgpuUsage;

                    if (this.FindControl<TextBlock>("dgpuUsageText") is TextBlock dgpuUsageText)
                        dgpuUsageText.Text = $"dGPU: {dgpuUsage:F1}%";

                    if (this.FindControl<TextBlock>("dgpuTempText") is TextBlock dgpuTempText)
                        dgpuTempText.Text = $"{dgpuTemp:F1}°C";
                }

                // Update brightness slider position
                UpdateBrightnessSliderPosition();
            }
            catch (Exception ex)
            {
                Log($"Error updating hardware info: {ex.Message}");
            }
        }

        private void UpdateBrightnessSliderPosition()
        {
            try
            {
                var currentBrightness = _brightnessController.GetCurrentBrightness();
                var slider = this.FindControl<Slider>("BrightnessSlider");
                var valueText = this.FindControl<TextBlock>("BrightnessValue");
                
                if (slider != null && Math.Abs(slider.Value - currentBrightness) > 1)
                {
                    slider.Value = currentBrightness;
                }
                
                if (valueText != null)
                {
                    valueText.Text = $"{currentBrightness}%";
                }
            }
            catch (Exception ex)
            {
                Log($"Error updating brightness slider: {ex.Message}");
            }
        }

        private void InitializeBrightnessSlider()
        {
            try
            {
                var currentBrightness = _brightnessController.GetCurrentBrightness();
                var slider = this.FindControl<Slider>("BrightnessSlider");
                if (slider != null)
                {
                    slider.Value = currentBrightness;
                    slider.PropertyChanged += (s, e) =>
                    {
                        if (e.Property == Slider.ValueProperty)
                        {
                            _brightnessController.SetBrightness((int)slider.Value);
                        }
                    };
                }
            }
            catch (Exception ex)
            {
                Log($"Error initializing brightness slider: {ex.Message}");
            }
        }

        private void Log(string message)
        {
            try
            {
                var logsDirectory = Path.Combine(
                    Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location) ?? "",
                    "logs"
                );
                
                // Ensure logs directory exists
                if (!Directory.Exists(logsDirectory))
                {
                    Directory.CreateDirectory(logsDirectory);
                }
                
                var logPath = Path.Combine(logsDirectory, "app_log.txt");
                File.AppendAllText(logPath, $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] {message}\n");
            }
            catch
            {
                // Ignore logging errors
            }
        }

        private void LogPowerPlanChange(string profileType)
        {
            try
            {
                var cpuInfo = _hardwareMonitor.GetCpuInfo();
                if (cpuInfo == null)
                {
                    _logger.LogWarning("Could not get CPU info for logging power plan change");
                    return;
                }

                var powerLimits = _powerPlanManager.GetCurrentPowerLimits();
                var logMessage = $"Switching to {profileType} profile for {cpuInfo.FullName}";
                
                if (powerLimits.HasValue)
                {
                    var (pl1, pl2) = powerLimits.Value;
                    if (pl1.HasValue && pl2.HasValue)
                    {
                        logMessage += $" (PL1: {pl1}W, PL2: {pl2}W)";
                    }
                }

                _logger.Log(logMessage);
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error logging power plan change: {ex.Message}");
            }
        }

        private void EcoButton_Click(object sender, RoutedEventArgs e)
        {
            if (this.FindControl<CheckBox>("AutoSwitchEnabled") is CheckBox autoSwitch)
            {
                autoSwitch.IsChecked = false;
                var settings = AppSettings.Load();
                settings.AutoSwitchEnabled = false;
                settings.Save();
            }
            _powerPlanManager.SetActivePowerPlan("eco");
            UpdateButtonStates();
            LogPowerPlanChange("eco");
        }

        private void BalancedButton_Click(object sender, RoutedEventArgs e)
        {
            if (this.FindControl<CheckBox>("AutoSwitchEnabled") is CheckBox autoSwitch)
            {
                autoSwitch.IsChecked = false;
                var settings = AppSettings.Load();
                settings.AutoSwitchEnabled = false;
                settings.Save();
            }
            _powerPlanManager.SetActivePowerPlan("balanced");
            UpdateButtonStates();
            LogPowerPlanChange("balanced");
        }

        private void BoostButton_Click(object sender, RoutedEventArgs e)
        {
            if (this.FindControl<CheckBox>("AutoSwitchEnabled") is CheckBox autoSwitch)
            {
                autoSwitch.IsChecked = false;
                var settings = AppSettings.Load();
                settings.AutoSwitchEnabled = false;
                settings.Save();
            }
            _powerPlanManager.SetActivePowerPlan("boost");
            UpdateButtonStates();
            LogPowerPlanChange("boost");
        }

        private void MinimizeButton_Click(object? sender, RoutedEventArgs e)
        {
            // Simuler l'appui sur la touche de raccourci
            if (Application.Current is App app)
            {
                app.ToggleWindowCommand.Execute(null);
            }
        }

        private void CloseButton_Click(object? sender, RoutedEventArgs e)
        {
            Close();
        }

        private void SettingsButton_Click(object? sender, RoutedEventArgs e)
        {
            ShowSettings();
        }

        private void OnSettingsChanged(object? sender, AppSettings settings)
        {
            try
            {
                _timer.Interval = TimeSpan.FromMilliseconds(settings.GuiUpdateInterval);
                if (_toggleWindowHotkey != settings.ToggleWindowHotkey)
                {
                    _toggleWindowHotkey = settings.ToggleWindowHotkey;
                    InitializeGlobalHotkey();
                }
            }
            catch (Exception ex)
            {
                Log($"Error applying settings changes: {ex.Message}");
            }
        }

        private void UpdatesButton_Click(object? sender, RoutedEventArgs e)
        {
            var updatesWindow = new UpdatesWindow();
            updatesWindow.Show();
        }

        private void OnChargingStatusChanged(object? sender, bool isCharging)
        {
            try
            {
                var settings = AppSettings.Load();
                if (!settings.AutoSwitchEnabled)
                {
                    _logger.Log("Auto-switch disabled, skipping automatic profile switch");
                    return;
                }

                var profile = isCharging ? settings.AcProfile : settings.DcProfile;
                
                _logger.Log($"Power source changed. Charging: {isCharging}, Applying profile: {profile}");
                ApplyStartupProfile(profile);

                if (_autoRefreshRateEnabled)
                {
                    _displayRefreshRate.SetAutoRefreshRate(isCharging);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error in charging status change handler: {ex.Message}");
            }
        }

        private void ApplyStartupProfile(string profile)
        {
            _isManualProfileSelected = false;
            switch (profile.ToLower())
            {
                case "eco":
                    _powerPlanManager.SetActivePowerPlan("eco");
                    LogPowerPlanChange("eco");
                    break;
                case "balanced":
                    _powerPlanManager.SetActivePowerPlan("balanced");
                    LogPowerPlanChange("balanced");
                    break;
                case "boost":
                    _powerPlanManager.SetActivePowerPlan("boost");
                    LogPowerPlanChange("boost");
                    break;
            }
            UpdateButtonStates();
        }

        private void InitializeGlobalHotkey()
        {
            try
            {
                if (_globalHotkey == null)
                {
                    var handle = Win32Helper.GetWindowHandle(this);
                    _globalHotkey = new GlobalHotkey(handle);
                    
                    // Enregistrer le gestionnaire de messages Windows
                    if (handle != IntPtr.Zero)
                    {
                        WindowsMessageHelper.RegisterMessageHandler(handle, _globalHotkey);
                    }
                }

                // Désinscrire l'ancien raccourci s'il existe
                if (_currentHotkeyId.HasValue)
                {
                    _globalHotkey.UnregisterHotkey(_currentHotkeyId.Value);
                    _currentHotkeyId = null;
                }

                // Convertir la chaîne de caractères en Key
                if (Enum.TryParse<Key>(_toggleWindowHotkey, out var key))
                {
                    _currentHotkeyId = _globalHotkey.RegisterHotkey(key, () =>
                    {
                        Dispatcher.UIThread.Post(() =>
                        {
                            if (WindowState == WindowState.Minimized)
                            {
                                WindowState = WindowState.Normal;
                                Activate();
                            }
                            else
                            {
                                WindowState = WindowState.Minimized;
                            }
                        });
                    });
                }
            }
            catch (Exception ex)
            {
                Log($"Error initializing global hotkey: {ex.Message}");
            }
        }

        protected override void OnClosed(EventArgs e)
        {
            try
            {
                WindowsMessageHelper.UnregisterMessageHandler();
                _globalHotkey?.Dispose();
                _globalHotkey = null;
            }
            catch (Exception ex)
            {
                Log($"Error cleaning up hotkey resources: {ex.Message}");
            }
            finally
            {
                base.OnClosed(e);
            }
        }

        private void ToggleWindow()
        {
            if (this == null) return;

            if (IsVisible)
            {
                // Sauvegarder l'état normal avant de cacher
                if (WindowState == WindowState.Normal)
                {
                    _lastWidth = Width;
                    _lastHeight = Height;
                }
                WindowState = WindowState.Minimized;
                Hide();
            }
            else
            {
                Show();
                Activate();
                // Restaurer les dimensions si elles ont été sauvegardées
                if (_lastWidth > 0 && _lastHeight > 0)
                {
                    Width = _lastWidth;
                    Height = _lastHeight;
                }
                WindowState = WindowState.Normal;
            }
        }

        private void ShowSettings()
        {
            var settingsWindow = new SettingsWindow();
            settingsWindow.SettingsChanged += OnSettingsChanged;
            settingsWindow.DebugSettingsChanged += OnDebugSettingsChanged;
            settingsWindow.Show();
        }

        private void OnDebugSettingsChanged(object? sender, DebugSettingsChangedEventArgs e)
        {
            if (this.FindControl<Border>("DgpuBorder") is Border dgpuBorder)
            {
                dgpuBorder.IsVisible = _hasDgpu && e.Settings.ShowDgpuControls;
            }

            if (!e.Settings.IsMonitoringEnabled)
            {
                _hardwareMonitor?.StopMonitoring();
                _timer?.Stop();
            }
            else
            {
                _hardwareMonitor?.StartMonitoring();
                _timer?.Start();
            }
        }

        private void UpdateButtonStates()
        {
            try
            {
                var activePlanType = _powerPlanManager.GetActivePowerPlanType();
                var settings = AppSettings.Load();
                
                if (this.FindControl<Button>("EcoButton") is Button ecoButton)
                {
                    ecoButton.Classes.Set("active", !settings.AutoSwitchEnabled && activePlanType == "eco");
                }
                
                if (this.FindControl<Button>("BalancedButton") is Button balancedButton)
                {
                    balancedButton.Classes.Set("active", !settings.AutoSwitchEnabled && activePlanType == "balanced");
                }
                
                if (this.FindControl<Button>("BoostButton") is Button boostButton)
                {
                    boostButton.Classes.Set("active", !settings.AutoSwitchEnabled && activePlanType == "boost");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error updating button states: {ex.Message}");
            }
        }

        private void AutoProfileButton_Click(object? sender, RoutedEventArgs e)
        {
            if (_autoProfilePopup != null)
            {
                _autoProfilePopup.IsOpen = !_autoProfilePopup.IsOpen;
            }
        }

        private void AcProfileSelector_SelectionChanged(object? sender, SelectionChangedEventArgs e)
        {
            if (_isInitializing) return;
            
            if (sender is ComboBox comboBox && comboBox.SelectedItem is ComboBoxItem selectedItem)
            {
                var profile = selectedItem.Content?.ToString()?.ToLower() ?? "balanced";
                var settings = AppSettings.Load();
                settings.AcProfile = profile;
                settings.Save();

                // Apply immediately if currently charging and no manual selection
                if (_batteryMonitor.IsCharging && !_isManualProfileSelected)
                {
                    ApplyStartupProfile(profile);
                }
            }
        }

        private void DcProfileSelector_SelectionChanged(object? sender, SelectionChangedEventArgs e)
        {
            if (_isInitializing) return;
            
            if (sender is ComboBox comboBox && comboBox.SelectedItem is ComboBoxItem selectedItem)
            {
                var profile = selectedItem.Content?.ToString()?.ToLower() ?? "eco";
                var settings = AppSettings.Load();
                settings.DcProfile = profile;
                settings.Save();

                // Apply immediately if currently on battery and no manual selection
                if (!_batteryMonitor.IsCharging && !_isManualProfileSelected)
                {
                    ApplyStartupProfile(profile);
                }
            }
        }

        private int GetProfileIndex(string profile)
        {
            return profile.ToLower() switch
            {
                "eco" => 0,
                "balanced" => 1,
                "boost" => 2,
                _ => 1 // Default to balanced
            };
        }

        private void AutoSwitchEnabled_CheckedChanged(object? sender, RoutedEventArgs e)
        {
            if (_isInitializing) return;

            if (sender is CheckBox checkBox)
            {
                var settings = AppSettings.Load();
                settings.AutoSwitchEnabled = checkBox.IsChecked ?? false;
                settings.Save();

                _isManualProfileSelected = !settings.AutoSwitchEnabled;
                
                if (_profileSelectionPanel != null)
                {
                    _profileSelectionPanel.IsEnabled = settings.AutoSwitchEnabled;
                }

                // Mettre à jour l'état des boutons
                UpdateButtonStates();

                if (settings.AutoSwitchEnabled)
                {
                    // Appliquer immédiatement le profil correspondant à l'état actuel
                    var profile = _batteryMonitor.IsCharging ? settings.AcProfile : settings.DcProfile;
                    ApplyStartupProfile(profile);
                }

                _logger.Log($"Auto-switch {(settings.AutoSwitchEnabled ? "enabled" : "disabled")}");
            }
        }
    }
}