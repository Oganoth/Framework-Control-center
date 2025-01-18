using Avalonia;
using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Threading;
using System;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using System.Windows.Input;
using System.Runtime.Versioning;
using System.Diagnostics;
using FrameworkControl.Models;

namespace FrameworkControl
{
    [SupportedOSPlatform("windows")]
    public partial class UpdatesWindow : Window
    {
        private readonly PackageManager _packageManager;
        private readonly ObservableCollection<PackageUpdate> _wingetUpdates;
        private TextBlock? _statusMessage;
        private ProgressBar? _progressBar;
        private const string FrameworkDriversUrl = "https://knowledgebase.frame.work/en_us/bios-and-drivers-downloads-rJ3PaCexh";
        private const string AmdDriversUrl = "https://www.amd.com/en/support/download/drivers.html";
        private const string IntelDriversUrl = "https://www.intel.com/content/www/us/en/download-center/home.html";

        public ICommand UpdatePackageCommand { get; }

        public UpdatesWindow()
        {
            InitializeComponent();

            _packageManager = new PackageManager();
            _wingetUpdates = new ObservableCollection<PackageUpdate>();

            UpdatePackageCommand = new RelayCommand<PackageUpdate>(async package => await UpdatePackageAsync(package));

            InitializeControls();
            AttachEventHandlers();
        }

        private void InitializeControls()
        {
            if (this.FindControl<ListBox>("WingetUpdatesList") is ListBox wingetList)
                wingetList.ItemsSource = _wingetUpdates;
            
            _statusMessage = this.FindControl<TextBlock>("StatusMessage");
            _progressBar = this.FindControl<ProgressBar>("ProgressBar");
        }

        private void AttachEventHandlers()
        {
            if (this.FindControl<Button>("RefreshWingetButton") is Button refreshWinget)
                refreshWinget.Click += async (s, e) => await RefreshUpdatesAsync();

            if (this.FindControl<Button>("FrameworkDriversButton") is Button frameworkDrivers)
                frameworkDrivers.Click += FrameworkDriversButton_Click;

            if (this.FindControl<Button>("AmdDriversButton") is Button amdDrivers)
                amdDrivers.Click += AmdDriversButton_Click;

            if (this.FindControl<Button>("IntelDriversButton") is Button intelDrivers)
                intelDrivers.Click += IntelDriversButton_Click;

            if (this.FindControl<Button>("CttWinutilsButton") is Button cttWinutils)
                cttWinutils.Click += CttWinutilsButton_Click;
        }

        private void FrameworkDriversButton_Click(object? sender, RoutedEventArgs e)
        {
            OpenUrl(FrameworkDriversUrl, "Framework Drivers");
        }

        private void AmdDriversButton_Click(object? sender, RoutedEventArgs e)
        {
            OpenUrl(AmdDriversUrl, "AMD Drivers");
        }

        private void IntelDriversButton_Click(object? sender, RoutedEventArgs e)
        {
            OpenUrl(IntelDriversUrl, "Intel Drivers");
        }

        private void CttWinutilsButton_Click(object? sender, RoutedEventArgs e)
        {
            try
            {
                var startInfo = new ProcessStartInfo
                {
                    FileName = "powershell.exe",
                    Arguments = "-NoExit -NoProfile -ExecutionPolicy Bypass -Command \"Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iwr -useb https://christitus.com/win | iex\"",
                    UseShellExecute = false,
                    CreateNoWindow = false,
                    RedirectStandardInput = false,
                    RedirectStandardOutput = false,
                    RedirectStandardError = false,
                    WorkingDirectory = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile)
                };
                Process.Start(startInfo);
            }
            catch (Exception ex)
            {
                ShowErrorDialog("Error", $"Failed to launch CTT Winutils: {ex.Message}").Wait();
            }
        }

        private void OpenUrl(string url, string name)
        {
            try
            {
                var psi = new ProcessStartInfo
                {
                    FileName = url,
                    UseShellExecute = true
                };
                Process.Start(psi);
            }
            catch (Exception ex)
            {
                ShowErrorDialog("Error", $"Failed to open {name} page: {ex.Message}").Wait();
            }
        }

        private async Task ShowProgress(bool show, string? message = null)
        {
            await Dispatcher.UIThread.InvokeAsync(() =>
            {
                if (_progressBar != null)
                    _progressBar.IsVisible = show;
                
                if (_statusMessage != null)
                {
                    _statusMessage.IsVisible = show && !string.IsNullOrEmpty(message);
                    if (!string.IsNullOrEmpty(message))
                        _statusMessage.Text = message;
                }
            });
        }

        private async Task RefreshUpdatesAsync()
        {
            try
            {
                await ShowProgress(true, UpdateMessages.GetRandomCheckingMessage());
                var updates = await _packageManager.CheckForUpdatesAsync(PackageManagerType.Winget);
                
                await Dispatcher.UIThread.InvokeAsync(() =>
                {
                    _wingetUpdates.Clear();
                    foreach (var update in updates)
                    {
                        _wingetUpdates.Add(update);
                    }
                });
            }
            catch (Exception ex)
            {
                await ShowErrorDialog("Error", $"Failed to check for updates: {ex.Message}");
            }
            finally
            {
                await ShowProgress(false);
            }
        }

        private async Task UpdatePackageAsync(PackageUpdate package)
        {
            try
            {
                await ShowProgress(true, UpdateMessages.GetRandomUpdatingMessage());
                await _packageManager.UpdatePackageAsync(package);
                await RefreshUpdatesAsync();
            }
            catch (Exception ex)
            {
                await ShowErrorDialog("Error", $"Failed to update {package.Name}: {ex.Message}");
            }
            finally
            {
                await ShowProgress(false);
            }
        }

        private async Task ShowErrorDialog(string title, string message)
        {
            await ShowProgress(false);
            
            var dialog = new MessageDialog
            {
                DialogTitle = title,
                Message = message
            };

            await dialog.ShowDialog(this);
        }

        private class RelayCommand<T> : ICommand
        {
            private readonly Action<T> _execute;
            private readonly Func<T, bool>? _canExecute;

            public RelayCommand(Action<T> execute, Func<T, bool>? canExecute = null)
            {
                _execute = execute ?? throw new ArgumentNullException(nameof(execute));
                _canExecute = canExecute;
            }

            public bool CanExecute(object? parameter)
            {
                return _canExecute?.Invoke((T)parameter!) ?? true;
            }

            public void Execute(object? parameter)
            {
                _execute((T)parameter!);
            }

            public event EventHandler? CanExecuteChanged
            {
                add { }
                remove { }
            }
        }
    }
} 