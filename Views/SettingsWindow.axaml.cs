using Avalonia;
using Avalonia.Controls;
using Avalonia.Interactivity;
using FrameworkControl.Models;
using FrameworkControl.Helpers;
using System;
using System.Runtime.Versioning;
using Avalonia.Controls.Primitives;
using Avalonia.Input;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Threading;

namespace FrameworkControl.Views
{
    [SupportedOSPlatform("windows")]
    public partial class SettingsWindow : Window
    {
        private readonly AppSettings _settings;
        private readonly Models.Logger _logger;
        private readonly CpuModelDetector _cpuDetector;
        private readonly HardwareMonitor _hardwareMonitor;
        private readonly RyzenAdjManager _ryzenAdjManager;
        private readonly PowerPlanManager _powerPlanManager;
        private readonly IntelCpuManager _intelCpuManager;
        private CpuInfo _cpuInfo = new()
        {
            FullName = "Unknown CPU",
            Model = "Unknown",
            ProfileKey = "unknown",
            IsAmd = false
        };
        private bool _isCapturingHotkey = false;
        private Button? _hotkeyButton;
        private int _aboutClickCount = 0;
        private readonly DebugSettings _debugSettings;
        private bool _isUpdating = false;

        public event EventHandler<AppSettings>? SettingsChanged;
        public event EventHandler<DebugSettingsChangedEventArgs>? DebugSettingsChanged;

        public SettingsWindow()
        {
            InitializeComponent();

            // Enable hardware composition
            UseLayoutRounding = true;
            
            _settings = AppSettings.Load();
            _logger = new Models.Logger("Settings");
            _hardwareMonitor = new HardwareMonitor();
            _cpuDetector = new CpuModelDetector(_hardwareMonitor);
            _ryzenAdjManager = new RyzenAdjManager();
            _powerPlanManager = new PowerPlanManager();
            _intelCpuManager = new IntelCpuManager();
            _debugSettings = DebugSettings.Load();
            
            try
            {
                var detectedCpu = _cpuDetector.DetectCpuModel();
                if (detectedCpu != null)
                {
                    _cpuInfo = detectedCpu;
                }

                // Ensure smooth initial render
                Dispatcher.UIThread.Post(() =>
                {
                    InitializeControls();
                    AttachEventHandlers();
                }, DispatcherPriority.Loaded);
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error initializing settings window: {ex.Message}");
            }
        }

        private void UpdateControlValue<T>(T? value, Action<T> updateAction)
        {
            if (_isUpdating) return;
            _isUpdating = true;
            try
            {
                if (value != null)
                {
                    Dispatcher.UIThread.Post(() => updateAction(value), DispatcherPriority.Background);
                }
            }
            finally
            {
                _isUpdating = false;
            }
        }

        private void InitializeControls()
        {
            if (this.FindControl<CheckBox>("StartWithWindowsCheck") is CheckBox startWithWindows)
            {
                UpdateControlValue(StartupManager.IsStartupEnabled(), enabled => startWithWindows.IsChecked = enabled);
            }

            if (this.FindControl<CheckBox>("StartMinimizedCheck") is CheckBox startMinimized)
            {
                UpdateControlValue(_settings.StartMinimized, minimized => startMinimized.IsChecked = minimized);
            }

            if (this.FindControl<NumericUpDown>("UpdateIntervalUpDown") is NumericUpDown updateInterval)
            {
                UpdateControlValue(_settings.GuiUpdateInterval, interval => updateInterval.Value = interval);
            }

            if (this.FindControl<ComboBox>("StartupProfileSelector") is ComboBox startupProfile)
            {
                UpdateControlValue(_settings.StartupProfile, profile =>
                {
                    startupProfile.SelectedIndex = profile switch
                {
                    "eco" => 0,
                    "balanced" => 1,
                    "boost" => 2,
                    _ => 0
                };
                });
            }

            _hotkeyButton = this.FindControl<Button>("HotkeyButton");
            if (_hotkeyButton != null)
            {
                _hotkeyButton.Content = $"Click to set key (Current: {_settings.ToggleWindowHotkey})";
                _hotkeyButton.Click += HotkeyButton_Click;
            }

            // Mettre à jour le titre de l'onglet RyzenADJ avec le modèle de CPU
            if (_cpuInfo.IsAmd && this.FindControl<TextBlock>("RyzenADJTitle") is TextBlock titleBlock)
            {
                titleBlock.Text = $"RyzenADJ Profiles - {_cpuInfo.Model}";

                // Charger le profil par défaut (eco)
                if (this.FindControl<ComboBox>("ProfileSelector") is ComboBox profileSelector)
                {
                    profileSelector.SelectedIndex = 0;
                    LoadSavedValues("eco");
                }
            }

            // Initialize PowerCFG tab with default values
            if (this.FindControl<ComboBox>("PowerProfileSelector") is ComboBox powerProfileSelector)
            {
                powerProfileSelector.SelectedIndex = 0;
                LoadPowerPlanValues("eco");
            }

            if (this.FindControl<CheckBox>("MonitoringCheckBox") is CheckBox monitoringCheckBox)
            {
                monitoringCheckBox.IsChecked = _debugSettings.IsMonitoringEnabled;
            }
            
            if (this.FindControl<CheckBox>("DgpuCheckBox") is CheckBox dgpuCheckBox)
            {
                dgpuCheckBox.IsChecked = _debugSettings.ShowDgpuControls;
            }

            // Initialize Intel CPU controls
            if (this.FindControl<TabItem>("IntelCpuTab") is TabItem intelCpuTab)
            {
                intelCpuTab.IsVisible = _intelCpuManager.IsSupported();
            }

            if (this.FindControl<ComboBox>("IntelCpuProfileSelector") is ComboBox intelCpuSelector)
            {
                intelCpuSelector.SelectedIndex = 1; // Default to Balanced
                LoadIntelCpuValues("balanced");
            }
        }

        private void AttachEventHandlers()
        {
            if (this.FindControl<Button>("SaveButton") is Button saveButton)
            {
                saveButton.Click += SaveButton_Click;
            }

            if (this.FindControl<Button>("CloseButton") is Button closeButton)
            {
                closeButton.Click += (s, e) => Close();
            }

            if (this.FindControl<ComboBox>("ProfileSelector") is ComboBox profileSelector)
            {
                profileSelector.SelectionChanged += ProfileSelector_SelectionChanged;
            }

            if (this.FindControl<ComboBox>("PowerProfileSelector") is ComboBox powerProfileSelector)
            {
                powerProfileSelector.SelectionChanged += PowerProfileSelector_SelectionChanged;
            }

            if (this.FindControl<Button>("PatreonButton") is Button patreonButton)
            {
                patreonButton.Click += (s, e) =>
                {
                    var psi = new System.Diagnostics.ProcessStartInfo
                    {
                        FileName = "https://patreon.com/Oganoth",
                        UseShellExecute = true
                    };
                    System.Diagnostics.Process.Start(psi);
                };
            }

            if (this.FindControl<Button>("GithubButton") is Button githubButton)
            {
                githubButton.Click += (s, e) =>
                {
                    var psi = new System.Diagnostics.ProcessStartInfo
                    {
                        FileName = "https://github.com/Oganoth",
                        UseShellExecute = true
                    };
                    System.Diagnostics.Process.Start(psi);
                };
            }

            if (this.FindControl<TextBlock>("AboutTitle") is TextBlock aboutTitle)
            {
                aboutTitle.PointerPressed += AboutTitle_PointerPressed;
            }

            if (this.FindControl<CheckBox>("MonitoringCheckBox") is CheckBox monitoringCheckBox)
            {
                monitoringCheckBox.IsCheckedChanged += MonitoringCheckBox_CheckedChanged;
            }

            if (this.FindControl<CheckBox>("DgpuCheckBox") is CheckBox dgpuCheckBox)
            {
                dgpuCheckBox.IsCheckedChanged += DgpuCheckBox_CheckedChanged;
            }

            // Intel CPU event handlers
            if (this.FindControl<ComboBox>("IntelCpuProfileSelector") is ComboBox intelCpuSelector)
            {
                intelCpuSelector.SelectionChanged += IntelCpuProfileSelector_SelectionChanged;
            }
        }

        private void SaveButton_Click(object? sender, RoutedEventArgs e)
        {
            try
            {
                // Save Intel CPU values if we're on the Intel CPU tab
                if (IntelCpuTab?.IsSelected == true)
                {
                    SaveIntelCpuValues();
                }

                _logger.Log("Saving settings...");

                // Save startup settings
                if (this.FindControl<CheckBox>("StartWithWindowsCheck") is CheckBox startWithWindows)
                {
                    var startWithWindowsEnabled = startWithWindows.IsChecked ?? false;
                    _logger.Log($"Setting 'Start with Windows' to: {startWithWindowsEnabled}");
                    StartupManager.SetStartupState(startWithWindowsEnabled);
                }

                // Save start minimized setting
                if (this.FindControl<CheckBox>("StartMinimizedCheck") is CheckBox startMinimized)
                {
                    _settings.StartMinimized = startMinimized.IsChecked ?? false;
                    _logger.Log($"Setting 'Start Minimized' to: {_settings.StartMinimized}");
                }

                // Save GUI update interval
                if (this.FindControl<NumericUpDown>("UpdateIntervalUpDown") is NumericUpDown updateInterval)
                {
                    _settings.GuiUpdateInterval = (int)(updateInterval.Value ?? _settings.GuiUpdateInterval);
                    _logger.Log($"Setting GUI update interval to: {_settings.GuiUpdateInterval}ms");
                }

                // Save startup profile
                if (this.FindControl<ComboBox>("StartupProfileSelector") is ComboBox startupProfile)
                {
                    _settings.StartupProfile = startupProfile.SelectedIndex switch
                    {
                        0 => "eco",
                        1 => "balanced",
                        2 => "boost",
                        _ => "eco"
                    };
                    _logger.Log($"Setting startup profile to: {_settings.StartupProfile}");
                }

                // Save RyzenADJ profile settings if a profile is selected
                if (_cpuInfo.IsAmd && this.FindControl<ComboBox>("ProfileSelector") is ComboBox profileSelector &&
                    profileSelector.SelectedIndex >= 0)
                {
                    string profileType = profileSelector.SelectedIndex switch
                    {
                        0 => "eco",
                        1 => "balanced",
                        2 => "boost",
                        _ => "eco"
                    };

                    var profile = new RyzenProfile
                    {
                        Name = profileType,
                        TctlTemp = (int)(this.FindControl<NumericUpDown>("TctlTemp")?.Value ?? 95),
                        ChtcTemp = (int)(this.FindControl<NumericUpDown>("ChtcTemp")?.Value ?? 95),
                        ApuSkinTemp = (int)(this.FindControl<NumericUpDown>("ApuSkinTemp")?.Value ?? 50),
                        StapmLimit = (int)((this.FindControl<NumericUpDown>("StapmLimit")?.Value ?? 45) * 1000),
                        FastLimit = (int)((this.FindControl<NumericUpDown>("FastLimit")?.Value ?? 45) * 1000),
                        SlowLimit = (int)((this.FindControl<NumericUpDown>("SlowLimit")?.Value ?? 45) * 1000),
                        VrmCurrent = (int)((this.FindControl<NumericUpDown>("VrmCurrent")?.Value ?? 60) * 1000),
                        VrmSocCurrent = (int)((this.FindControl<NumericUpDown>("VrmSocCurrent")?.Value ?? 60) * 1000),
                        VrmMaxCurrent = _ryzenAdjManager.GetProfile(_cpuInfo.ProfileKey, profileType)?.VrmMaxCurrent ?? 180000,
                        VrmSocMaxCurrent = _ryzenAdjManager.GetProfile(_cpuInfo.ProfileKey, profileType)?.VrmSocMaxCurrent ?? 180000
                    };

                    _settings.SaveProfile(_cpuInfo.ProfileKey, profileType, profile);
                }

                // Save PowerCFG profile settings if a profile is selected
                if (this.FindControl<ComboBox>("PowerProfileSelector") is ComboBox powerProfileSelector &&
                    powerProfileSelector.SelectedIndex >= 0)
                {
                    string profileType = powerProfileSelector.SelectedIndex switch
                    {
                        0 => "eco",
                        1 => "balanced",
                        2 => "boost",
                        _ => "eco"
                    };

                    var powerProfile = new PowerPlan
                    {
                        Name = GetPowerPlanName(profileType),
                        Description = $"Power-saving profile for Framework laptops",
                        AcSettings = new PowerPlanSettings
                        {
                            ProcessorMinimumState = (int)(this.FindControl<NumericUpDown>("AcProcessorMinimumState")?.Value ?? 0),
                            ProcessorMaximumState = (int)(this.FindControl<NumericUpDown>("AcProcessorMaximumState")?.Value ?? 100),
                            SystemCoolingPolicy = this.FindControl<ComboBox>("AcSystemCoolingPolicy")?.SelectedIndex ?? 0,
                            ProcessorPerformanceBoostMode = this.FindControl<ComboBox>("AcProcessorBoostMode")?.SelectedIndex ?? 0,
                            ProcessorPerformanceBoostPolicy = (int)(this.FindControl<NumericUpDown>("AcProcessorBoostPolicy")?.Value ?? 100),
                            ProcessorBoostTimeWindow = (int)(this.FindControl<NumericUpDown>("AcProcessorBoostTimeWindow")?.Value ?? 45),
                            ProcessorPerformanceIncreasePolicy = this.FindControl<ComboBox>("AcProcessorPerformanceIncreasePolicy")?.SelectedIndex ?? 0,
                            DynamicGraphicsMode = this.FindControl<ComboBox>("AcDynamicGraphicsMode")?.SelectedIndex ?? 1,
                            AdaptiveBrightness = this.FindControl<ComboBox>("AcAdaptiveBrightness")?.SelectedIndex ?? 0,
                            AdvancedColorQualityBias = this.FindControl<ComboBox>("AcAdvancedColorQualityBias")?.SelectedIndex ?? 1,
                            DiskIdleTimeout = (int)(this.FindControl<NumericUpDown>("AcDiskIdleTimeout")?.Value ?? 1200),
                            UsbHubTimeout = (int)(this.FindControl<NumericUpDown>("AcUsbHubTimeout")?.Value ?? 50),
                            UsbSuspend = (this.FindControl<ComboBox>("AcUsbSuspend")?.SelectedIndex ?? 1) == 1,
                            UsbIoc = (this.FindControl<ComboBox>("AcUsbIoc")?.SelectedIndex ?? 1) == 1,
                            UsbLinkPower = this.FindControl<ComboBox>("AcUsbLinkPower")?.SelectedIndex ?? 2
                        },
                        DcSettings = new PowerPlanSettings
                        {
                            ProcessorMinimumState = (int)(this.FindControl<NumericUpDown>("DcProcessorMinimumState")?.Value ?? 0),
                            ProcessorMaximumState = (int)(this.FindControl<NumericUpDown>("DcProcessorMaximumState")?.Value ?? 100),
                            SystemCoolingPolicy = this.FindControl<ComboBox>("DcSystemCoolingPolicy")?.SelectedIndex ?? 0,
                            ProcessorPerformanceBoostMode = this.FindControl<ComboBox>("DcProcessorBoostMode")?.SelectedIndex ?? 0,
                            ProcessorPerformanceBoostPolicy = (int)(this.FindControl<NumericUpDown>("DcProcessorBoostPolicy")?.Value ?? 100),
                            ProcessorBoostTimeWindow = (int)(this.FindControl<NumericUpDown>("DcProcessorBoostTimeWindow")?.Value ?? 45),
                            ProcessorPerformanceIncreasePolicy = this.FindControl<ComboBox>("DcProcessorPerformanceIncreasePolicy")?.SelectedIndex ?? 0,
                            DynamicGraphicsMode = this.FindControl<ComboBox>("DcDynamicGraphicsMode")?.SelectedIndex ?? 1,
                            AdaptiveBrightness = this.FindControl<ComboBox>("DcAdaptiveBrightness")?.SelectedIndex ?? 0,
                            AdvancedColorQualityBias = this.FindControl<ComboBox>("DcAdvancedColorQualityBias")?.SelectedIndex ?? 1,
                            DiskIdleTimeout = (int)(this.FindControl<NumericUpDown>("DcDiskIdleTimeout")?.Value ?? 600),
                            UsbHubTimeout = (int)(this.FindControl<NumericUpDown>("DcUsbHubTimeout")?.Value ?? 20),
                            UsbSuspend = (this.FindControl<ComboBox>("DcUsbSuspend")?.SelectedIndex ?? 1) == 1,
                            UsbIoc = (this.FindControl<ComboBox>("DcUsbIoc")?.SelectedIndex ?? 1) == 1,
                            UsbLinkPower = this.FindControl<ComboBox>("DcUsbLinkPower")?.SelectedIndex ?? 1
                        }
                    };

                    // Récupérer le GUID existant du plan
                    var existingPlan = _powerPlanManager.GetProfile(profileType);
                    if (existingPlan != null && !string.IsNullOrEmpty(existingPlan.Guid))
                    {
                        powerProfile.Guid = existingPlan.Guid;
                    }

                    // Générer les commandes PowerCFG pour les nouveaux paramètres
                    powerProfile.GenerateCommands();

                    _powerPlanManager.SaveProfile(profileType, powerProfile);
                    _logger.Log($"Saved power plan profile: {powerProfile.Name}");

                    // Appliquer immédiatement les changements
                    _powerPlanManager.UpdatePowerPlanSettings();
                    _logger.Log("Applied power plan settings");
                }

                // Mettre à jour les paramètres des plans d'alimentation
                _powerPlanManager.UpdatePowerPlanSettings();
                _logger.Log("Updated power plan settings");

                // Save settings to file
                _settings.Save();
                _logger.Log("Settings saved successfully");

                // Notify subscribers that settings have changed
                SettingsChanged?.Invoke(this, _settings);

                Close();
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error saving settings: {ex.Message}");
                if (ex.InnerException != null)
                {
                    _logger.LogError($"Inner exception: {ex.InnerException.Message}");
                }
            }
        }

        private void ProfileSelector_SelectionChanged(object? sender, SelectionChangedEventArgs e)
        {
            if (sender is ComboBox comboBox)
            {
                string profileType = comboBox.SelectedIndex switch
                {
                    0 => "eco",
                    1 => "balanced",
                    2 => "boost",
                    _ => "eco"
                };

                try
                {
                    LoadSavedValues(profileType);
                }
                catch (Exception ex)
                {
                    _logger.LogError($"Error loading profile: {ex.Message}");
                }
            }
        }

        private void LoadSavedValues(string profileType)
        {
            try
            {
                var savedProfile = _settings.GetSavedProfile(_cpuInfo.ProfileKey, profileType);
                var defaultProfile = _ryzenAdjManager.GetProfile(_cpuInfo.ProfileKey, profileType);

                if (savedProfile != null)
                {
                    // Mettre à jour les valeurs sauvegardées (afficher en orange)
                    if (this.FindControl<TextBlock>("TctlTempSaved") is TextBlock tctlSaved)
                        tctlSaved.Text = $"(Saved: {savedProfile.TctlTemp}°C)";

                    if (this.FindControl<TextBlock>("ChtcTempSaved") is TextBlock chtcSaved)
                        chtcSaved.Text = $"(Saved: {savedProfile.ChtcTemp}°C)";

                    if (this.FindControl<TextBlock>("ApuSkinTempSaved") is TextBlock apuSkinSaved)
                        apuSkinSaved.Text = $"(Saved: {savedProfile.ApuSkinTemp}°C)";

                    if (this.FindControl<TextBlock>("StapmLimitSaved") is TextBlock stapmSaved)
                        stapmSaved.Text = $"(Saved: {savedProfile.StapmLimit / 1000}W)";

                    if (this.FindControl<TextBlock>("FastLimitSaved") is TextBlock fastSaved)
                        fastSaved.Text = $"(Saved: {savedProfile.FastLimit / 1000}W)";

                    if (this.FindControl<TextBlock>("SlowLimitSaved") is TextBlock slowSaved)
                        slowSaved.Text = $"(Saved: {savedProfile.SlowLimit / 1000}W)";

                    if (this.FindControl<TextBlock>("VrmCurrentSaved") is TextBlock vrmSaved)
                        vrmSaved.Text = $"(Saved: {savedProfile.VrmCurrent / 1000}A)";

                    if (this.FindControl<TextBlock>("VrmMaxCurrentSaved") is TextBlock vrmMaxSaved)
                        vrmMaxSaved.Text = $"(Saved: {savedProfile.VrmMaxCurrent / 1000}A)";

                    if (this.FindControl<TextBlock>("VrmSocCurrentSaved") is TextBlock vrmSocSaved)
                        vrmSocSaved.Text = $"(Saved: {savedProfile.VrmSocCurrent / 1000}A)";

                    if (this.FindControl<TextBlock>("VrmSocMaxCurrentSaved") is TextBlock vrmSocMaxSaved)
                        vrmSocMaxSaved.Text = $"(Saved: {savedProfile.VrmSocMaxCurrent / 1000}A)";

                    // Mettre à jour les valeurs des NumericUpDown avec les valeurs sauvegardées
                    if (this.FindControl<NumericUpDown>("TctlTemp") is NumericUpDown tctlTemp)
                        tctlTemp.Value = savedProfile.TctlTemp;

                    if (this.FindControl<NumericUpDown>("ChtcTemp") is NumericUpDown chtcTemp)
                        chtcTemp.Value = savedProfile.ChtcTemp ?? savedProfile.TctlTemp;

                    if (this.FindControl<NumericUpDown>("ApuSkinTemp") is NumericUpDown apuSkinTemp)
                        apuSkinTemp.Value = savedProfile.ApuSkinTemp ?? 50;

                    if (this.FindControl<NumericUpDown>("StapmLimit") is NumericUpDown stapmLimit)
                        stapmLimit.Value = savedProfile.StapmLimit / 1000;

                    if (this.FindControl<NumericUpDown>("FastLimit") is NumericUpDown fastLimit)
                        fastLimit.Value = savedProfile.FastLimit / 1000;

                    if (this.FindControl<NumericUpDown>("SlowLimit") is NumericUpDown slowLimit)
                        slowLimit.Value = savedProfile.SlowLimit / 1000;

                    if (this.FindControl<NumericUpDown>("VrmCurrent") is NumericUpDown vrmCurrent)
                        vrmCurrent.Value = savedProfile.VrmCurrent / 1000;

                    if (this.FindControl<NumericUpDown>("VrmMaxCurrent") is NumericUpDown vrmMaxCurrent)
                        vrmMaxCurrent.Value = savedProfile.VrmMaxCurrent / 1000;

                    if (this.FindControl<NumericUpDown>("VrmSocCurrent") is NumericUpDown vrmSocCurrent)
                        vrmSocCurrent.Value = savedProfile.VrmSocCurrent / 1000;

                    if (this.FindControl<NumericUpDown>("VrmSocMaxCurrent") is NumericUpDown vrmSocMaxCurrent)
                        vrmSocMaxCurrent.Value = savedProfile.VrmSocMaxCurrent / 1000;
                }
                else if (defaultProfile != null)
                {
                    // Si pas de valeurs sauvegardées, utiliser les valeurs par défaut
                    if (this.FindControl<NumericUpDown>("TctlTemp") is NumericUpDown tctlTemp)
                        tctlTemp.Value = defaultProfile.TctlTemp;

                    if (this.FindControl<NumericUpDown>("ChtcTemp") is NumericUpDown chtcTemp)
                        chtcTemp.Value = defaultProfile.ChtcTemp ?? defaultProfile.TctlTemp;

                    if (this.FindControl<NumericUpDown>("ApuSkinTemp") is NumericUpDown apuSkinTemp)
                        apuSkinTemp.Value = defaultProfile.ApuSkinTemp ?? 50;

                    if (this.FindControl<NumericUpDown>("StapmLimit") is NumericUpDown stapmLimit)
                        stapmLimit.Value = defaultProfile.StapmLimit / 1000;

                    if (this.FindControl<NumericUpDown>("FastLimit") is NumericUpDown fastLimit)
                        fastLimit.Value = defaultProfile.FastLimit / 1000;

                    if (this.FindControl<NumericUpDown>("SlowLimit") is NumericUpDown slowLimit)
                        slowLimit.Value = defaultProfile.SlowLimit / 1000;

                    if (this.FindControl<NumericUpDown>("VrmCurrent") is NumericUpDown vrmCurrent)
                        vrmCurrent.Value = defaultProfile.VrmCurrent / 1000;

                    if (this.FindControl<NumericUpDown>("VrmMaxCurrent") is NumericUpDown vrmMaxCurrent)
                        vrmMaxCurrent.Value = defaultProfile.VrmMaxCurrent / 1000;

                    if (this.FindControl<NumericUpDown>("VrmSocCurrent") is NumericUpDown vrmSocCurrent)
                        vrmSocCurrent.Value = defaultProfile.VrmSocCurrent / 1000;

                    if (this.FindControl<NumericUpDown>("VrmSocMaxCurrent") is NumericUpDown vrmSocMaxCurrent)
                        vrmSocMaxCurrent.Value = defaultProfile.VrmSocMaxCurrent / 1000;

                    // Effacer les valeurs sauvegardées
                    ClearSavedValues();
                }

                // Toujours afficher les valeurs par défaut (en gris)
                if (defaultProfile != null)
                {
                    if (this.FindControl<TextBlock>("TctlTempDefault") is TextBlock tctlDefault)
                        tctlDefault.Text = $"(Default: {defaultProfile.TctlTemp}°C)";

                    if (this.FindControl<TextBlock>("ChtcTempDefault") is TextBlock chtcDefault)
                        chtcDefault.Text = $"(Default: {defaultProfile.ChtcTemp ?? defaultProfile.TctlTemp}°C)";

                    if (this.FindControl<TextBlock>("ApuSkinTempDefault") is TextBlock apuSkinDefault)
                        apuSkinDefault.Text = $"(Default: {defaultProfile.ApuSkinTemp ?? 50}°C)";

                    if (this.FindControl<TextBlock>("StapmLimitDefault") is TextBlock stapmDefault)
                        stapmDefault.Text = $"(Default: {defaultProfile.StapmLimit / 1000}W)";

                    if (this.FindControl<TextBlock>("FastLimitDefault") is TextBlock fastDefault)
                        fastDefault.Text = $"(Default: {defaultProfile.FastLimit / 1000}W)";

                    if (this.FindControl<TextBlock>("SlowLimitDefault") is TextBlock slowDefault)
                        slowDefault.Text = $"(Default: {defaultProfile.SlowLimit / 1000}W)";

                    if (this.FindControl<TextBlock>("VrmCurrentDefault") is TextBlock vrmDefault)
                        vrmDefault.Text = $"(Default: {defaultProfile.VrmCurrent / 1000}A)";

                    if (this.FindControl<TextBlock>("VrmMaxCurrentDefault") is TextBlock vrmMaxDefault)
                        vrmMaxDefault.Text = $"(Default: {defaultProfile.VrmMaxCurrent / 1000}A)";

                    if (this.FindControl<TextBlock>("VrmSocCurrentDefault") is TextBlock vrmSocDefault)
                        vrmSocDefault.Text = $"(Default: {defaultProfile.VrmSocCurrent / 1000}A)";

                    if (this.FindControl<TextBlock>("VrmSocMaxCurrentDefault") is TextBlock vrmSocMaxDefault)
                        vrmSocMaxDefault.Text = $"(Default: {defaultProfile.VrmSocMaxCurrent / 1000}A)";
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error loading saved values: {ex.Message}");
            }
        }

        private void ClearSavedValues()
        {
            var savedLabels = new[]
            {
                "TctlTempSaved", "ChtcTempSaved", "ApuSkinTempSaved",
                "StapmLimitSaved", "FastLimitSaved", "SlowLimitSaved",
                "VrmCurrentSaved", "VrmMaxCurrentSaved", "VrmSocCurrentSaved",
                "VrmSocMaxCurrentSaved"
            };

            foreach (var label in savedLabels)
            {
                if (this.FindControl<TextBlock>(label) is TextBlock textBlock)
                {
                    textBlock.Text = string.Empty;
                }
            }
        }

        private void HotkeyButton_Click(object? sender, RoutedEventArgs e)
        {
            if (!_isCapturingHotkey)
            {
                _isCapturingHotkey = true;
                if (_hotkeyButton != null)
                {
                    _hotkeyButton.Content = "Press any key...";
                    _hotkeyButton.Focus();
                }
            }
        }

        protected override void OnKeyDown(KeyEventArgs e)
        {
            base.OnKeyDown(e);

            if (_isCapturingHotkey)
            {
                e.Handled = true;
                var key = e.Key;

                // Ignorer certaines touches qui ne devraient pas être utilisées comme raccourci
                if (key == Key.LeftAlt || key == Key.RightAlt || 
                    key == Key.LeftCtrl || key == Key.RightCtrl || 
                    key == Key.LeftShift || key == Key.RightShift ||
                    key == Key.Escape)
                {
                    return;
                }

                _settings.ToggleWindowHotkey = key.ToString();
                if (_hotkeyButton != null)
                {
                    _hotkeyButton.Content = $"Click to set key (Current: {key})";
                }
                _isCapturingHotkey = false;
            }
        }

        protected override void OnClosed(EventArgs e)
        {
            base.OnClosed(e);
            
            // Nettoyer les gestionnaires d'événements
            if (_hotkeyButton != null)
            {
                _hotkeyButton.Click -= HotkeyButton_Click;
            }

            // Nettoyer les autres ressources si nécessaire
            _hardwareMonitor.Dispose();
        }

        private void AboutTitle_PointerPressed(object? sender, PointerPressedEventArgs e)
        {
            _aboutClickCount++;
            if (_aboutClickCount >= 7)
            {
                if (this.FindControl<TabItem>("DebugTab") is TabItem debugTab)
                {
                    if (debugTab.IsVisible)
                    {
                        // Hide debug tab and reset settings
                        debugTab.IsVisible = false;
                        _aboutClickCount = 0;
                        DebugSettings.Reset();
                        DebugSettingsChanged?.Invoke(this, new DebugSettingsChangedEventArgs(new DebugSettings()));
                    }
                    else
                    {
                        // Show debug tab
                        debugTab.IsVisible = true;
                        _aboutClickCount = 0;
                    }
                }
            }
        }

        private void MonitoringCheckBox_CheckedChanged(object? sender, RoutedEventArgs e)
        {
            if (sender is CheckBox checkBox)
            {
                _debugSettings.IsMonitoringEnabled = checkBox.IsChecked ?? true;
                _debugSettings.Save();
                DebugSettingsChanged?.Invoke(this, new DebugSettingsChangedEventArgs(_debugSettings));
            }
        }

        private void DgpuCheckBox_CheckedChanged(object? sender, RoutedEventArgs e)
        {
            if (sender is CheckBox checkBox)
            {
                _debugSettings.ShowDgpuControls = checkBox.IsChecked ?? true;
                _debugSettings.Save();
                DebugSettingsChanged?.Invoke(this, new DebugSettingsChangedEventArgs(_debugSettings));
            }
        }

        private void PowerProfileSelector_SelectionChanged(object? sender, SelectionChangedEventArgs e)
        {
            if (sender is ComboBox comboBox)
            {
                string profileType = comboBox.SelectedIndex switch
                {
                    0 => "eco",
                    1 => "balanced",
                    2 => "boost",
                    _ => "eco"
                };

                LoadPowerPlanValues(profileType);
            }
        }

        private void LoadPowerPlanValues(string profileType)
        {
            try
            {
                var profile = _powerPlanManager.GetProfile(profileType);
                if (profile == null)
                {
                    _logger.LogWarning($"Profile not found: {profileType}");
                    return;
                }

                // AC Power
                if (this.FindControl<NumericUpDown>("AcProcessorMinimumState") is NumericUpDown acProcessorMinimumState)
                {
                    acProcessorMinimumState.Value = profile.AcSettings.ProcessorMinimumState;
                }

                if (this.FindControl<NumericUpDown>("AcProcessorMaximumState") is NumericUpDown acProcessorMaximumState)
                {
                    acProcessorMaximumState.Value = profile.AcSettings.ProcessorMaximumState;
                }

                if (this.FindControl<NumericUpDown>("AcProcessorBoostPolicy") is NumericUpDown acProcessorBoostPolicy)
                {
                    acProcessorBoostPolicy.Value = profile.AcSettings.ProcessorPerformanceBoostPolicy;
                }

                if (this.FindControl<ComboBox>("AcProcessorBoostMode") is ComboBox acProcessorBoostMode)
                {
                    acProcessorBoostMode.SelectedIndex = profile.AcSettings.ProcessorPerformanceBoostMode;
                }

                if (this.FindControl<ComboBox>("AcProcessorPerformanceIncreasePolicy") is ComboBox acProcessorPerformanceIncreasePolicy)
                {
                    acProcessorPerformanceIncreasePolicy.SelectedIndex = profile.AcSettings.ProcessorPerformanceIncreasePolicy;
                }

                if (this.FindControl<ComboBox>("AcSystemCoolingPolicy") is ComboBox acSystemCoolingPolicy)
                {
                    acSystemCoolingPolicy.SelectedIndex = profile.AcSettings.SystemCoolingPolicy;
                }

                if (this.FindControl<ComboBox>("AcDynamicGraphicsMode") is ComboBox acDynamicGraphicsMode)
                {
                    acDynamicGraphicsMode.SelectedIndex = profile.AcSettings.DynamicGraphicsMode;
                }

                if (this.FindControl<ComboBox>("AcAdaptiveBrightness") is ComboBox acAdaptiveBrightness)
                {
                    acAdaptiveBrightness.SelectedIndex = profile.AcSettings.AdaptiveBrightness;
                }

                if (this.FindControl<ComboBox>("AcAdvancedColorQualityBias") is ComboBox acAdvancedColorQualityBias)
                {
                    acAdvancedColorQualityBias.SelectedIndex = profile.AcSettings.AdvancedColorQualityBias;
                }

                if (this.FindControl<NumericUpDown>("AcDiskIdleTimeout") is NumericUpDown acDiskIdleTimeout)
                {
                    acDiskIdleTimeout.Value = profile.AcSettings.DiskIdleTimeout;
                }

                if (this.FindControl<NumericUpDown>("AcUsbHubTimeout") is NumericUpDown acUsbHubTimeout)
                {
                    acUsbHubTimeout.Value = profile.AcSettings.UsbHubTimeout;
                }

                if (this.FindControl<ComboBox>("AcUsbSuspend") is ComboBox acUsbSuspend)
                {
                    acUsbSuspend.SelectedIndex = profile.AcSettings.UsbSuspend ? 1 : 0;
                }

                if (this.FindControl<ComboBox>("AcUsbIoc") is ComboBox acUsbIoc)
                {
                    acUsbIoc.SelectedIndex = profile.AcSettings.UsbIoc ? 1 : 0;
                }

                if (this.FindControl<ComboBox>("AcUsbLinkPower") is ComboBox acUsbLinkPower)
                {
                    acUsbLinkPower.SelectedIndex = profile.AcSettings.UsbLinkPower;
                }

                // DC Power
                if (this.FindControl<NumericUpDown>("DcProcessorMinimumState") is NumericUpDown dcProcessorMinimumState)
                {
                    dcProcessorMinimumState.Value = profile.DcSettings.ProcessorMinimumState;
                }

                if (this.FindControl<NumericUpDown>("DcProcessorMaximumState") is NumericUpDown dcProcessorMaximumState)
                {
                    dcProcessorMaximumState.Value = profile.DcSettings.ProcessorMaximumState;
                }

                if (this.FindControl<NumericUpDown>("DcProcessorBoostPolicy") is NumericUpDown dcProcessorBoostPolicy)
                {
                    dcProcessorBoostPolicy.Value = profile.DcSettings.ProcessorPerformanceBoostPolicy;
                }

                if (this.FindControl<ComboBox>("DcProcessorBoostMode") is ComboBox dcProcessorBoostMode)
                {
                    dcProcessorBoostMode.SelectedIndex = profile.DcSettings.ProcessorPerformanceBoostMode;
                }

                if (this.FindControl<ComboBox>("DcProcessorPerformanceIncreasePolicy") is ComboBox dcProcessorPerformanceIncreasePolicy)
                {
                    dcProcessorPerformanceIncreasePolicy.SelectedIndex = profile.DcSettings.ProcessorPerformanceIncreasePolicy;
                }

                if (this.FindControl<ComboBox>("DcSystemCoolingPolicy") is ComboBox dcSystemCoolingPolicy)
                {
                    dcSystemCoolingPolicy.SelectedIndex = profile.DcSettings.SystemCoolingPolicy;
                }

                if (this.FindControl<ComboBox>("DcDynamicGraphicsMode") is ComboBox dcDynamicGraphicsMode)
                {
                    dcDynamicGraphicsMode.SelectedIndex = profile.DcSettings.DynamicGraphicsMode;
                }

                if (this.FindControl<ComboBox>("DcAdaptiveBrightness") is ComboBox dcAdaptiveBrightness)
                {
                    dcAdaptiveBrightness.SelectedIndex = profile.DcSettings.AdaptiveBrightness;
                }

                if (this.FindControl<ComboBox>("DcAdvancedColorQualityBias") is ComboBox dcAdvancedColorQualityBias)
                {
                    dcAdvancedColorQualityBias.SelectedIndex = profile.DcSettings.AdvancedColorQualityBias;
                }

                if (this.FindControl<NumericUpDown>("DcDiskIdleTimeout") is NumericUpDown dcDiskIdleTimeout)
                {
                    dcDiskIdleTimeout.Value = profile.DcSettings.DiskIdleTimeout;
                }

                if (this.FindControl<NumericUpDown>("DcUsbHubTimeout") is NumericUpDown dcUsbHubTimeout)
                {
                    dcUsbHubTimeout.Value = profile.DcSettings.UsbHubTimeout;
                }

                if (this.FindControl<ComboBox>("DcUsbSuspend") is ComboBox dcUsbSuspend)
                {
                    dcUsbSuspend.SelectedIndex = profile.DcSettings.UsbSuspend ? 1 : 0;
                }

                if (this.FindControl<ComboBox>("DcUsbIoc") is ComboBox dcUsbIoc)
                {
                    dcUsbIoc.SelectedIndex = profile.DcSettings.UsbIoc ? 1 : 0;
                }

                if (this.FindControl<ComboBox>("DcUsbLinkPower") is ComboBox dcUsbLinkPower)
                {
                    dcUsbLinkPower.SelectedIndex = profile.DcSettings.UsbLinkPower;
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error loading power plan values: {ex.Message}");
            }
        }

        private string GetPowerPlanName(string profileType)
        {
            // Standardiser la casse des noms de plans
            string capitalizedType = char.ToUpper(profileType[0]) + profileType.Substring(1).ToLower();
            return $"Framework-{capitalizedType}";
        }

        private void SavePowerPlanValues()
        {
            try
            {
                var settings = AppSettings.Load();
                var powerPlan = _powerPlanManager.GetProfile(settings.StartupProfile);
                if (powerPlan == null) return;

                powerPlan.AcSettings = new PowerPlanSettings
                {
                    ProcessorMinimumState = (int)(this.FindControl<NumericUpDown>("AcProcessorMinimumState")?.Value ?? 0),
                    ProcessorMaximumState = (int)(this.FindControl<NumericUpDown>("AcProcessorMaximumState")?.Value ?? 100),
                    SystemCoolingPolicy = this.FindControl<ComboBox>("AcSystemCoolingPolicy")?.SelectedIndex ?? 0,
                    ProcessorPerformanceBoostMode = this.FindControl<ComboBox>("AcProcessorBoostMode")?.SelectedIndex ?? 0,
                    ProcessorPerformanceBoostPolicy = (int)(this.FindControl<NumericUpDown>("AcProcessorBoostPolicy")?.Value ?? 100),
                    ProcessorBoostTimeWindow = (int)(this.FindControl<NumericUpDown>("AcProcessorBoostTimeWindow")?.Value ?? 45),
                    ProcessorPerformanceIncreasePolicy = this.FindControl<ComboBox>("AcProcessorPerformanceIncreasePolicy")?.SelectedIndex ?? 0,
                    DynamicGraphicsMode = this.FindControl<ComboBox>("AcDynamicGraphicsMode")?.SelectedIndex ?? 1,
                    AdaptiveBrightness = this.FindControl<ComboBox>("AcAdaptiveBrightness")?.SelectedIndex ?? 0,
                    AdvancedColorQualityBias = this.FindControl<ComboBox>("AcAdvancedColorQualityBias")?.SelectedIndex ?? 1,
                    DiskIdleTimeout = (int)(this.FindControl<NumericUpDown>("AcDiskIdleTimeout")?.Value ?? 1200),
                    UsbHubTimeout = (int)(this.FindControl<NumericUpDown>("AcUsbHubTimeout")?.Value ?? 50),
                    UsbSuspend = (this.FindControl<ComboBox>("AcUsbSuspend")?.SelectedIndex ?? 1) == 1,
                    UsbIoc = (this.FindControl<ComboBox>("AcUsbIoc")?.SelectedIndex ?? 1) == 1,
                    UsbLinkPower = this.FindControl<ComboBox>("AcUsbLinkPower")?.SelectedIndex ?? 2
                };

                powerPlan.DcSettings = new PowerPlanSettings
                {
                    ProcessorMinimumState = (int)(this.FindControl<NumericUpDown>("DcProcessorMinimumState")?.Value ?? 0),
                    ProcessorMaximumState = (int)(this.FindControl<NumericUpDown>("DcProcessorMaximumState")?.Value ?? 100),
                    SystemCoolingPolicy = this.FindControl<ComboBox>("DcSystemCoolingPolicy")?.SelectedIndex ?? 0,
                    ProcessorPerformanceBoostMode = this.FindControl<ComboBox>("DcProcessorBoostMode")?.SelectedIndex ?? 0,
                    ProcessorPerformanceBoostPolicy = (int)(this.FindControl<NumericUpDown>("DcProcessorBoostPolicy")?.Value ?? 100),
                    ProcessorBoostTimeWindow = (int)(this.FindControl<NumericUpDown>("DcProcessorBoostTimeWindow")?.Value ?? 45),
                    ProcessorPerformanceIncreasePolicy = this.FindControl<ComboBox>("DcProcessorPerformanceIncreasePolicy")?.SelectedIndex ?? 0,
                    DynamicGraphicsMode = this.FindControl<ComboBox>("DcDynamicGraphicsMode")?.SelectedIndex ?? 1,
                    AdaptiveBrightness = this.FindControl<ComboBox>("DcAdaptiveBrightness")?.SelectedIndex ?? 0,
                    AdvancedColorQualityBias = this.FindControl<ComboBox>("DcAdvancedColorQualityBias")?.SelectedIndex ?? 1,
                    DiskIdleTimeout = (int)(this.FindControl<NumericUpDown>("DcDiskIdleTimeout")?.Value ?? 600),
                    UsbHubTimeout = (int)(this.FindControl<NumericUpDown>("DcUsbHubTimeout")?.Value ?? 20),
                    UsbSuspend = (this.FindControl<ComboBox>("DcUsbSuspend")?.SelectedIndex ?? 1) == 1,
                    UsbIoc = (this.FindControl<ComboBox>("DcUsbIoc")?.SelectedIndex ?? 1) == 1,
                    UsbLinkPower = this.FindControl<ComboBox>("DcUsbLinkPower")?.SelectedIndex ?? 1
                };

                // Récupérer le GUID existant du plan
                var existingPlan = _powerPlanManager.GetProfile(settings.StartupProfile);
                if (existingPlan != null && !string.IsNullOrEmpty(existingPlan.Guid))
                {
                    powerPlan.Guid = existingPlan.Guid;
                }

                // Générer les commandes PowerCFG pour les nouveaux paramètres
                powerPlan.GenerateCommands();

                _powerPlanManager.SaveProfile(settings.StartupProfile, powerPlan);
                _logger.Log($"Saved power plan profile: {powerPlan.Name}");

                // Appliquer immédiatement les changements
                _powerPlanManager.UpdatePowerPlanSettings();
                _logger.Log("Applied power plan settings");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error saving power plan values: {ex.Message}");
            }
        }

        private void IntelCpuProfileSelector_SelectionChanged(object? sender, SelectionChangedEventArgs e)
        {
            if (sender is ComboBox comboBox && comboBox.SelectedItem is ComboBoxItem selectedItem)
            {
                var profileType = selectedItem.Content?.ToString()?.ToLower() ?? "balanced";
                LoadIntelCpuValues(profileType);
            }
        }

        private void LoadIntelCpuValues(string profileType)
        {
            try
            {
                var profile = _intelCpuManager.GetProfile(profileType);
                if (profile == null)
                {
                    ClearIntelCpuValues();
                    return;
                }

                if (IntelPL1 != null) IntelPL1.Value = profile.Pl1;
                if (IntelPL2 != null) IntelPL2.Value = profile.Pl2;
                if (IntelTurboTime != null) IntelTurboTime.Value = profile.TurboTime;
                if (IntelTemperature != null) IntelTemperature.Value = profile.Temperature;
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error loading Intel CPU values: {ex.Message}");
            }
        }

        private void ClearIntelCpuValues()
        {
            if (IntelPL1 != null) IntelPL1.Value = 28;
            if (IntelPL2 != null) IntelPL2.Value = 45;
            if (IntelTurboTime != null) IntelTurboTime.Value = 28;
            if (IntelTemperature != null) IntelTemperature.Value = 95;
        }

        private void SaveIntelCpuValues()
        {
            try
            {
                if (IntelCpuProfileSelector?.SelectedItem is not ComboBoxItem selectedItem)
                {
                    _logger.LogError("No Intel CPU profile selected");
                    return;
                }

                var profileType = selectedItem.Content?.ToString()?.ToLower();
                if (string.IsNullOrEmpty(profileType))
                {
                    _logger.LogError("Invalid profile type");
                    return;
                }

                if (IntelPL1?.Value == null || IntelPL2?.Value == null || 
                    IntelTurboTime?.Value == null || IntelTemperature?.Value == null)
                {
                    _logger.LogError("One or more Intel CPU values are null");
                    return;
                }

                var profile = new IntelProfile
                {
                    Name = profileType,
                    Pl1 = (int)IntelPL1.Value,
                    Pl2 = (int)IntelPL2.Value,
                    TurboTime = (int)IntelTurboTime.Value,
                    Temperature = (int)IntelTemperature.Value
                };

                _logger.Log($"Saving Intel CPU profile '{profileType}' with values:");
                _logger.Log($"  PL1: {profile.Pl1}W");
                _logger.Log($"  PL2: {profile.Pl2}W");
                _logger.Log($"  Turbo Time: {profile.TurboTime}s");
                _logger.Log($"  Temperature: {profile.Temperature}°C");

                _intelCpuManager.SaveProfile(profileType, profile);

                // Vérifier que le profil a été correctement sauvegardé
                var savedProfile = _intelCpuManager.GetProfile(profileType);
                if (savedProfile == null || savedProfile.Pl1 != profile.Pl1)
                {
                    _logger.LogError("Profile verification failed after save");
                    return;
                }

                _logger.Log("Intel CPU profile saved and verified successfully");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error saving Intel CPU values: {ex.Message}");
            }
        }

        private void ApplyIntelProfile(string profileType)
        {
            try
            {
                if (_intelCpuManager.IsSupported())
                {
                    _intelCpuManager.ApplyProfile(profileType);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error applying Intel CPU profile: {ex.Message}");
            }
        }
    }
}
