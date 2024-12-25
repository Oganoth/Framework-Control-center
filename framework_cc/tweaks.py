"""Windows tweaks management module."""

import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class WindowsTweaks:
    """Windows tweaks manager."""
    
    def __init__(self):
        """Initialize tweaks manager."""
        self.powershell_path = "powershell.exe"
        self.task_name = "FrameworkControlCenter"
    
    def run_powershell_command(self, command: str, as_admin: bool = True) -> tuple[bool, str]:
        """Run PowerShell command."""
        try:
            # Configure process to hide window
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            # Create a temporary script file
            script_path = Path.home() / ".framework_cc" / "temp_script.ps1"
            script_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Escape the command for PowerShell
            escaped_command = command.replace('"', '`"')
            
            # Add elevation if needed
            if as_admin:
                # Write the script content
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(f'''
                    $ErrorActionPreference = "Stop"
                    $scriptBlock = {{
                        {escaped_command}
                    }}
                    
                    # Create a new process with hidden window
                    $psi = New-Object System.Diagnostics.ProcessStartInfo
                    $psi.FileName = "powershell.exe"
                    $psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command & {{$scriptBlock}}"
                    $psi.UseShellExecute = $false
                    $psi.RedirectStandardOutput = $true
                    $psi.RedirectStandardError = $true
                    $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
                    $psi.CreateNoWindow = $true
                    
                    $process = New-Object System.Diagnostics.Process
                    $process.StartInfo = $psi
                    [void]$process.Start()
                    
                    $output = $process.StandardOutput.ReadToEnd()
                    $error_output = $process.StandardError.ReadToEnd()
                    $process.WaitForExit()
                    
                    if ($process.ExitCode -eq 0) {{
                        Write-Output $output
                    }} else {{
                        Write-Error $error_output
                    }}
                    ''')
                
                # Run the script with hidden window
                process = subprocess.run(
                    [self.powershell_path, "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", str(script_path)],
                    capture_output=True,
                    text=True,
                    startupinfo=startupinfo
                )
            else:
                # For non-admin commands, run directly with hidden window
                process = subprocess.run(
                    [self.powershell_path, "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", escaped_command],
                    capture_output=True,
                    text=True,
                    startupinfo=startupinfo
                )
            
            try:
                # Clean up the temporary script file
                if script_path.exists():
                    script_path.unlink()
            except Exception as e:
                logger.debug(f"Failed to delete temporary script: {e}")
            
            if process.returncode == 0:
                return True, process.stdout
            else:
                logger.error(f"PowerShell command failed: {process.stderr}")
                return False, process.stderr
                
        except Exception as e:
            logger.error(f"Error running PowerShell command: {e}")
            return False, str(e)
    
    def create_restore_point(self, description: str = "Framework CC Tweaks") -> bool:
        """Create a system restore point."""
        command = f'''
        # Enable System Restore if it's disabled
        Enable-ComputerRestore -Drive "C:\\" -ErrorAction SilentlyContinue

        # Create the restore point
        try {{
            Checkpoint-Computer -Description "{description}" -RestorePointType MODIFY_SETTINGS -ErrorAction Stop
            Write-Output "Restore point created successfully"
            return $true
        }} catch {{
            Write-Error "Failed to create restore point: $_"
            return $false
        }}
        '''
        
        success, output = self.run_powershell_command(command)
        return success
    
    def disable_telemetry(self) -> bool:
        """Disable Windows telemetry."""
        command = '''
        # Disable telemetry
        New-Item -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" -Force | Out-Null
        Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\DataCollection" -Name "AllowTelemetry" -Type DWord -Value 0
        Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" -Name "AllowTelemetry" -Type DWord -Value 0
        
        # Disable feedback
        New-Item -Path "HKCU:\\SOFTWARE\\Microsoft\\Siuf\\Rules" -Force | Out-Null
        Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Siuf\\Rules" -Name "NumberOfSIUFInPeriod" -Type DWord -Value 0
        
        # Disable scheduled tasks
        Get-ScheduledTask -TaskName "Microsoft\\Windows\\Application Experience\\Microsoft Compatibility Appraiser" | Disable-ScheduledTask
        Get-ScheduledTask -TaskName "Microsoft\\Windows\\Application Experience\\ProgramDataUpdater" | Disable-ScheduledTask
        Get-ScheduledTask -TaskName "Microsoft\\Windows\\Autochk\\Proxy" | Disable-ScheduledTask
        Get-ScheduledTask -TaskName "Microsoft\\Windows\\Customer Experience Improvement Program\\Consolidator" | Disable-ScheduledTask
        Get-ScheduledTask -TaskName "Microsoft\\Windows\\Customer Experience Improvement Program\\UsbCeip" | Disable-ScheduledTask
        Get-ScheduledTask -TaskName "Microsoft\\Windows\\DiskDiagnostic\\Microsoft-Windows-DiskDiagnosticDataCollector" | Disable-ScheduledTask
        
        # Disable services
        Stop-Service "DiagTrack" -Force
        Set-Service "DiagTrack" -StartupType Disabled
        Stop-Service "dmwappushservice" -Force
        Set-Service "dmwappushservice" -StartupType Disabled
        '''
        
        success, _ = self.run_powershell_command(command)
        return success
    
    def disable_activity_history(self) -> bool:
        """Disable activity history."""
        command = '''
        # Create registry path if it doesn't exist
        New-Item -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" -Force | Out-Null
        
        # Disable activity history
        Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" -Name "EnableActivityFeed" -Type DWord -Value 0
        Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" -Name "PublishUserActivities" -Type DWord -Value 0
        Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" -Name "UploadUserActivities" -Type DWord -Value 0
        '''
        
        success, _ = self.run_powershell_command(command)
        return success
    
    def disable_location_tracking(self) -> bool:
        """Disable location tracking."""
        command = '''
        # Create registry paths if they don't exist
        New-Item -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Sensor\\Overrides\\{BFA794E4-F964-4FDB-90F6-51056BFE4B44}" -Force | Out-Null
        New-Item -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\lfsvc\\Service\\Configuration" -Force | Out-Null
        New-Item -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\LocationAndSensors" -Force | Out-Null
        
        # Disable location tracking
        Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Sensor\\Overrides\\{BFA794E4-F964-4FDB-90F6-51056BFE4B44}" -Name "SensorPermissionState" -Type DWord -Value 0
        Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\lfsvc\\Service\\Configuration" -Name "Status" -Type DWord -Value 0
        
        # Disable location services
        Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\LocationAndSensors" -Name "DisableLocation" -Type DWord -Value 1
        Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\LocationAndSensors" -Name "DisableLocationScripting" -Type DWord -Value 1
        '''
        
        success, _ = self.run_powershell_command(command)
        return success
    
    def disable_consumer_features(self) -> bool:
        """Disable consumer features."""
        command = '''
        # Create registry path if it doesn't exist
        New-Item -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\CloudContent" -Force | Out-Null
        
        # Disable consumer features
        Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\CloudContent" -Name "DisableWindowsConsumerFeatures" -Type DWord -Value 1
        Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\CloudContent" -Name "DisableThirdPartySuggestions" -Type DWord -Value 1
        Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\CloudContent" -Name "DisableTailoredExperiencesWithDiagnosticData" -Type DWord -Value 1
        '''
        
        success, _ = self.run_powershell_command(command)
        return success
    
    def disable_storage_sense(self) -> bool:
        """Disable storage sense."""
        command = '''
        # Create registry path if it doesn't exist
        New-Item -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\StorageSense\\Parameters\\StoragePolicy" -Force | Out-Null
        
        # Disable storage sense
        Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\StorageSense\\Parameters\\StoragePolicy" -Name "01" -Type DWord -Value 0
        Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\StorageSense\\Parameters\\StoragePolicy" -Name "04" -Type DWord -Value 0
        Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\StorageSense\\Parameters\\StoragePolicy" -Name "08" -Type DWord -Value 0
        Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\StorageSense\\Parameters\\StoragePolicy" -Name "32" -Type DWord -Value 0
        Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\StorageSense\\Parameters\\StoragePolicy" -Name "StoragePoliciesNotified" -Type DWord -Value 1
        '''
        
        success, _ = self.run_powershell_command(command)
        return success
    
    def disable_wifi_sense(self) -> bool:
        """Disable WiFi Sense."""
        command = '''
        # Create registry paths if they don't exist
        New-Item -Path "HKLM:\\SOFTWARE\\Microsoft\\PolicyManager\\default\\WiFi\\AllowWiFiHotSpotReporting" -Force | Out-Null
        New-Item -Path "HKLM:\\SOFTWARE\\Microsoft\\PolicyManager\\default\\WiFi\\AllowAutoConnectToWiFiSenseHotspots" -Force | Out-Null
        
        # Disable WiFi Sense
        Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\PolicyManager\\default\\WiFi\\AllowWiFiHotSpotReporting" -Name "Value" -Type DWord -Value 0
        Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\PolicyManager\\default\\WiFi\\AllowAutoConnectToWiFiSenseHotspots" -Name "Value" -Type DWord -Value 0
        '''
        
        success, _ = self.run_powershell_command(command)
        return success
    
    def disable_game_dvr(self) -> bool:
        """Disable Game DVR."""
        command = '''
        # Create registry paths if they don't exist
        New-Item -Path "HKCU:\\System\\GameConfigStore" -Force | Out-Null
        New-Item -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR" -Force | Out-Null
        
        # Disable Game DVR
        Set-ItemProperty -Path "HKCU:\\System\\GameConfigStore" -Name "GameDVR_Enabled" -Type DWord -Value 0
        Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR" -Name "AllowGameDVR" -Type DWord -Value 0
        '''
        
        success, _ = self.run_powershell_command(command)
        return success
    
    def disable_hibernation(self) -> bool:
        """Disable hibernation."""
        command = '''
        # Create registry path if it doesn't exist
        New-Item -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FlyoutMenuSettings" -Force | Out-Null
        
        # Disable hibernation
        powercfg /hibernate off
        Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power" -Name "HibernateEnabled" -Type DWord -Value 0
        Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FlyoutMenuSettings" -Name "ShowHibernateOption" -Type DWord -Value 0
        '''
        
        success, _ = self.run_powershell_command(command)
        return success
    
    def disable_homegroup(self) -> bool:
        """Disable homegroup."""
        command = '''
        # Disable homegroup services
        Stop-Service "HomeGroupListener" -Force -ErrorAction SilentlyContinue
        Set-Service "HomeGroupListener" -StartupType Disabled -ErrorAction SilentlyContinue
        Stop-Service "HomeGroupProvider" -Force -ErrorAction SilentlyContinue
        Set-Service "HomeGroupProvider" -StartupType Disabled -ErrorAction SilentlyContinue
        '''
        
        success, _ = self.run_powershell_command(command)
        return success
    
    def run_disk_cleanup(self) -> bool:
        """Run disk cleanup."""
        command = '''
        cleanmgr /sagerun:1 | Out-Null
        Get-Process -Name cleanmgr | Wait-Process
        '''
        
        success, _ = self.run_powershell_command(command)
        return success
    
    def prefer_ipv4_over_ipv6(self) -> bool:
        """Prefer IPv4 over IPv6."""
        command = '''
        # Create registry path if it doesn't exist
        New-Item -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Tcpip6\\Parameters" -Force | Out-Null
        
        # Prefer IPv4 over IPv6
        Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Tcpip6\\Parameters" -Name "DisabledComponents" -Type DWord -Value 0x20
        Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Tcpip6\\Parameters" -Name "Dhcpv6DUID" -Type String -Value "00010001*"
        '''
        
        success, _ = self.run_powershell_command(command)
        return success
    
    def set_powershell7_default(self) -> bool:
        """Set PowerShell 7 as default terminal."""
        command = '''
        # Check if PowerShell 7 is installed
        if (Test-Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\pwsh.exe") {
            # Create registry paths if they don't exist
            New-Item -Path "HKCU:\\Console\\%%Startup" -Force | Out-Null
            
            # Set PowerShell 7 as default
            Set-ItemProperty -Path "HKCU:\\Console\\%%Startup" -Name "DelegationConsole" -Type String -Value "{574e775e-4f2a-5b96-ac1e-a2962a402336}"
            Set-ItemProperty -Path "HKCU:\\Console\\%%Startup" -Name "DelegationTerminal" -Type String -Value "{574e775e-4f2a-5b96-ac1e-a2962a402336}"
        }
        '''
        
        success, _ = self.run_powershell_command(command)
        return success
    
    def disable_powershell7_telemetry(self) -> bool:
        """Disable PowerShell 7 telemetry."""
        command = '''
        [System.Environment]::SetEnvironmentVariable('POWERSHELL_TELEMETRY_OPTOUT', '1', [System.EnvironmentVariableTarget]::Machine)
        '''
        
        success, _ = self.run_powershell_command(command)
        return success
    
    def set_hibernation_default(self) -> bool:
        """Set hibernation as default power action."""
        command = '''
        # Create registry path if it doesn't exist
        New-Item -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FlyoutMenuSettings" -Force | Out-Null
        
        # Enable hibernation
        powercfg /hibernate on
        Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power" -Name "HibernateEnabled" -Type DWord -Value 1
        Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FlyoutMenuSettings" -Name "ShowHibernateOption" -Type DWord -Value 1
        
        # Set hibernation as default
        powercfg -setacvalueindex SCHEME_CURRENT SUB_BUTTONS PBUTTONACTION 2
        powercfg -setdcvalueindex SCHEME_CURRENT SUB_BUTTONS PBUTTONACTION 2
        powercfg -setactive SCHEME_CURRENT
        '''
        
        success, _ = self.run_powershell_command(command)
        return success
    
    def set_services_manual(self) -> bool:
        """Set non-essential services to manual start."""
        command = '''
        $services = @(
            'DiagTrack',                   # Connected User Experiences and Telemetry
            'dmwappushservice',            # Device Management Wireless Application Protocol
            'HomeGroupListener',           # HomeGroup Listener
            'HomeGroupProvider',           # HomeGroup Provider
            'lfsvc',                       # Geolocation Service
            'MapsBroker',                  # Downloaded Maps Manager
            'NetTcpPortSharing',           # Net.Tcp Port Sharing Service
            'RemoteAccess',                # Routing and Remote Access
            'RemoteRegistry',              # Remote Registry
            'SharedAccess',                # Internet Connection Sharing
            'TrkWks',                      # Distributed Link Tracking Client
            'WMPNetworkSvc',               # Windows Media Player Network Sharing Service
            'WSearch',                     # Windows Search
            'XblAuthManager',              # Xbox Live Auth Manager
            'XblGameSave',                 # Xbox Live Game Save Service
            'XboxNetApiSvc',               # Xbox Live Networking Service
            'edgeupdate',                  # Microsoft Edge Update Service
            'edgeupdatem',                 # Microsoft Edge Update Service
            'GraphicsPerfSvc',             # Graphics Performance Monitor Service
            'RetailDemo',                  # Retail Demo Service
            'SEMgrSvc',                    # Payments and NFC/SE Manager
            'PhoneSvc',                    # Phone Service
            'OneSyncSvc',                  # Sync Host
            'MessagingService',            # Messaging Service
            'PimIndexMaintenanceSvc',      # Contact Data
            'UnistoreSvc',                 # User Data Storage
            'UserDataSvc',                 # User Data Access
            'WalletService',               # WalletService
            'MixedRealityOpenXRSvc',       # Mixed Reality OpenXR Service
            'wisvc',                       # Windows Insider Service
            'WerSvc',                      # Windows Error Reporting Service
            'WpnService',                  # Windows Push Notifications System Service
            'fhsvc',                       # File History Service
            'icssvc',                      # Windows Mobile Hotspot Service
            'InstallService',              # Microsoft Store Install Service
            'SCardSvr',                    # Smart Card
            'ScDeviceEnum',                # Smart Card Device Enumeration Service
            'SCPolicySvc',                 # Smart Card Removal Policy
            'WebClient'                    # WebClient
        )

        foreach ($service in $services) {
            try {
                $svc = Get-Service -Name $service -ErrorAction SilentlyContinue
                if ($svc) {
                    Stop-Service -Name $service -Force -ErrorAction SilentlyContinue
                    Set-Service -Name $service -StartupType Manual -ErrorAction SilentlyContinue
                    Write-Host "Service $service set to manual"
                }
            }
            catch {
                Write-Host "Failed to set $service to manual: $_"
            }
        }
        '''
        
        success, _ = self.run_powershell_command(command)
        return success
    
    def debloat_edge(self) -> bool:
        """Remove unnecessary Edge components."""
        commands = [
            # Disable Edge telemetry
            'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Edge" -Name "MetricsReportingEnabled" -Type DWord -Value 0',
            'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Edge" -Name "SendSiteInfoToImproveServices" -Type DWord -Value 0',
            
            # Disable Edge features
            'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Edge" -Name "BackgroundModeEnabled" -Type DWord -Value 0',
            'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Edge" -Name "EdgeShoppingAssistantEnabled" -Type DWord -Value 0',
            'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Edge" -Name "PersonalizationReportingEnabled" -Type DWord -Value 0'
        ]
        
        success = True
        for command in commands:
            cmd_success, _ = self.run_powershell_command(command)
            success = success and cmd_success
        return success 
    
    def is_telemetry_disabled(self) -> bool:
        """Check if telemetry is disabled."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.run(
                [self.powershell_path, "-WindowStyle", "Hidden", "-Command", "Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\DataCollection' -Name 'AllowTelemetry' -ErrorAction SilentlyContinue"],
                capture_output=True,
                text=True,
                startupinfo=startupinfo
            )
            return "0" in process.stdout
        except Exception:
            return False

    def is_activity_history_disabled(self) -> bool:
        """Check if activity history is disabled."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.run(
                [self.powershell_path, "-WindowStyle", "Hidden", "-Command", "Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\System' -Name 'EnableActivityFeed' -ErrorAction SilentlyContinue"],
                capture_output=True,
                text=True,
                startupinfo=startupinfo
            )
            return "0" in process.stdout
        except Exception:
            return False

    def is_location_tracking_disabled(self) -> bool:
        """Check if location tracking is disabled."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.run(
                [self.powershell_path, "-WindowStyle", "Hidden", "-Command", "Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Sensor\\Overrides\\{BFA794E4-F964-4FDB-90F6-51056BFE4B44}' -Name 'SensorPermissionState' -ErrorAction SilentlyContinue"],
                capture_output=True,
                text=True,
                startupinfo=startupinfo
            )
            return "0" in process.stdout
        except Exception:
            return False

    def is_consumer_features_disabled(self) -> bool:
        """Check if consumer features are disabled."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.run(
                [self.powershell_path, "-WindowStyle", "Hidden", "-Command", "Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\CloudContent' -Name 'DisableWindowsConsumerFeatures' -ErrorAction SilentlyContinue"],
                capture_output=True,
                text=True,
                startupinfo=startupinfo
            )
            return "1" in process.stdout
        except Exception:
            return False

    def is_storage_sense_disabled(self) -> bool:
        """Check if storage sense is disabled."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.run(
                [self.powershell_path, "-WindowStyle", "Hidden", "-Command", "Get-ItemProperty -Path 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\StorageSense\\Parameters\\StoragePolicy' -Name '01' -ErrorAction SilentlyContinue"],
                capture_output=True,
                text=True,
                startupinfo=startupinfo
            )
            return "0" in process.stdout
        except Exception:
            return False

    def is_wifi_sense_disabled(self) -> bool:
        """Check if WiFi Sense is disabled."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.run(
                [self.powershell_path, "-WindowStyle", "Hidden", "-Command", "Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\PolicyManager\\default\\WiFi\\AllowWiFiHotSpotReporting' -Name 'Value' -ErrorAction SilentlyContinue"],
                capture_output=True,
                text=True,
                startupinfo=startupinfo
            )
            return "0" in process.stdout
        except Exception:
            return False

    def is_game_dvr_disabled(self) -> bool:
        """Check if Game DVR is disabled."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.run(
                [self.powershell_path, "-WindowStyle", "Hidden", "-Command", "Get-ItemProperty -Path 'HKCU:\\System\\GameConfigStore' -Name 'GameDVR_Enabled' -ErrorAction SilentlyContinue"],
                capture_output=True,
                text=True,
                startupinfo=startupinfo
            )
            return "0" in process.stdout
        except Exception:
            return False

    def is_hibernation_disabled(self) -> bool:
        """Check if hibernation is disabled."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.run(
                [self.powershell_path, "-WindowStyle", "Hidden", "-Command", "Get-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power' -Name 'HibernateEnabled' -ErrorAction SilentlyContinue"],
                capture_output=True,
                text=True,
                startupinfo=startupinfo
            )
            return "0" in process.stdout
        except Exception:
            return False

    def is_homegroup_disabled(self) -> bool:
        """Check if homegroup services are disabled."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.run(
                [self.powershell_path, "-WindowStyle", "Hidden", "-Command", "Get-Service 'HomeGroupListener' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty StartType"],
                capture_output=True,
                text=True,
                startupinfo=startupinfo
            )
            return "Disabled" in process.stdout
        except Exception:
            return False

    def is_ipv4_preferred(self) -> bool:
        """Check if IPv4 is preferred over IPv6."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.run(
                [self.powershell_path, "-WindowStyle", "Hidden", "-Command", "Get-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Tcpip6\\Parameters' -Name 'DisabledComponents' -ErrorAction SilentlyContinue"],
                capture_output=True,
                text=True,
                startupinfo=startupinfo
            )
            return "32" in process.stdout
        except Exception:
            return False

    def is_powershell7_default(self) -> bool:
        """Check if PowerShell 7 is the default terminal."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.run(
                [self.powershell_path, "-WindowStyle", "Hidden", "-Command", "Get-ItemProperty -Path 'HKCU:\\Console\\%%Startup' -Name 'DelegationConsole' -ErrorAction SilentlyContinue"],
                capture_output=True,
                text=True,
                startupinfo=startupinfo
            )
            return "{574e775e-4f2a-5b96-ac1e-a2962a402336}" in process.stdout
        except Exception:
            return False

    def is_powershell7_telemetry_disabled(self) -> bool:
        """Check if PowerShell 7 telemetry is disabled."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.run(
                [self.powershell_path, "-WindowStyle", "Hidden", "-Command", "[System.Environment]::GetEnvironmentVariable('POWERSHELL_TELEMETRY_OPTOUT', [System.EnvironmentVariableTarget]::Machine)"],
                capture_output=True,
                text=True,
                startupinfo=startupinfo
            )
            return "1" in process.stdout
        except Exception:
            return False

    def is_hibernation_default(self) -> bool:
        """Check if hibernation is the default power action."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.run(
                [self.powershell_path, "-WindowStyle", "Hidden", "-Command", "powercfg /query SCHEME_CURRENT SUB_BUTTONS PBUTTONACTION"],
                capture_output=True,
                text=True,
                startupinfo=startupinfo
            )
            return "0x00000002" in process.stdout
        except Exception:
            return False

    def are_services_manual(self) -> bool:
        """Check if specified services are set to manual."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            services = [
                "DiagTrack",
                "dmwappushservice",
                "HomeGroupListener",
                "HomeGroupProvider",
                "lfsvc",
                "MapsBroker",
                "NetTcpPortSharing",
                "RemoteAccess",
                "RemoteRegistry",
                "SharedAccess",
                "TrkWks",
                "WbioSrvc",
                "WMPNetworkSvc",
                "WSearch",
                "XblAuthManager",
                "XblGameSave",
                "XboxNetApiSvc"
            ]
            
            for service in services:
                process = subprocess.run(
                    [self.powershell_path, "-WindowStyle", "Hidden", "-Command", f"Get-Service -Name '{service}' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty StartType"],
                    capture_output=True,
                    text=True,
                    startupinfo=startupinfo
                )
                if "Manual" not in process.stdout:
                    return False
            return True
        except Exception:
            return False

    def is_edge_debloated(self) -> bool:
        """Check if Edge is debloated."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.run(
                [self.powershell_path, "-WindowStyle", "Hidden", "-Command", "Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Edge' -Name 'MetricsReportingEnabled' -ErrorAction SilentlyContinue"],
                capture_output=True,
                text=True,
                startupinfo=startupinfo
            )
            return "0" in process.stdout
        except Exception:
            return False

    def restore_services(self) -> bool:
        """Restore services back to automatic startup."""
        command = '''
        $services = @(
            'DiagTrack',                   # Connected User Experiences and Telemetry
            'dmwappushservice',            # Device Management Wireless Application Protocol
            'HomeGroupListener',           # HomeGroup Listener
            'HomeGroupProvider',           # HomeGroup Provider
            'lfsvc',                       # Geolocation Service
            'MapsBroker',                  # Downloaded Maps Manager
            'NetTcpPortSharing',           # Net.Tcp Port Sharing Service
            'RemoteAccess',                # Routing and Remote Access
            'RemoteRegistry',              # Remote Registry
            'SharedAccess',                # Internet Connection Sharing
            'TrkWks',                      # Distributed Link Tracking Client
            'WMPNetworkSvc',               # Windows Media Player Network Sharing Service
            'WSearch',                     # Windows Search
            'XblAuthManager',              # Xbox Live Auth Manager
            'XblGameSave',                 # Xbox Live Game Save Service
            'XboxNetApiSvc',               # Xbox Live Networking Service
            'edgeupdate',                  # Microsoft Edge Update Service
            'edgeupdatem',                 # Microsoft Edge Update Service
            'GraphicsPerfSvc',             # Graphics Performance Monitor Service
            'RetailDemo',                  # Retail Demo Service
            'SEMgrSvc',                    # Payments and NFC/SE Manager
            'PhoneSvc',                    # Phone Service
            'OneSyncSvc',                  # Sync Host
            'MessagingService',            # Messaging Service
            'PimIndexMaintenanceSvc',      # Contact Data
            'UnistoreSvc',                 # User Data Storage
            'UserDataSvc',                 # User Data Access
            'WalletService',               # WalletService
            'MixedRealityOpenXRSvc',       # Mixed Reality OpenXR Service
            'wisvc',                       # Windows Insider Service
            'WerSvc',                      # Windows Error Reporting Service
            'WpnService',                  # Windows Push Notifications System Service
            'fhsvc',                       # File History Service
            'icssvc',                      # Windows Mobile Hotspot Service
            'InstallService',              # Microsoft Store Install Service
            'SCardSvr',                    # Smart Card
            'ScDeviceEnum',                # Smart Card Device Enumeration Service
            'SCPolicySvc',                 # Smart Card Removal Policy
            'WebClient'                    # WebClient
        )

        foreach ($service in $services) {
            try {
                $svc = Get-Service -Name $service -ErrorAction SilentlyContinue
                if ($svc) {
                    Set-Service -Name $service -StartupType Automatic -ErrorAction SilentlyContinue
                    Start-Service -Name $service -ErrorAction SilentlyContinue
                    Write-Host "Service $service set to automatic and started"
                }
            }
            catch {
                Write-Host "Failed to restore $service: $_"
            }
        }
        '''
        
        success, _ = self.run_powershell_command(command)
        return success 

    def create_startup_task(self, exe_path: str) -> bool:
        """Create Windows scheduled task to run app at startup with admin rights."""
        command = f'''
        $Action = New-ScheduledTaskAction -Execute "{exe_path}"
        $Trigger = New-ScheduledTaskTrigger -AtLogon
        $Principal = New-ScheduledTaskPrincipal -UserId (Get-CimInstance -ClassName Win32_ComputerSystem | Select-Object -ExpandProperty UserName) -RunLevel Highest
        $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 0)

        # Remove existing task if it exists
        Unregister-ScheduledTask -TaskName "{self.task_name}" -Confirm:$false -ErrorAction SilentlyContinue

        # Create new task
        Register-ScheduledTask -TaskName "{self.task_name}" -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force
        '''
        
        success, _ = self.run_powershell_command(command)
        return success

    def remove_startup_task(self) -> bool:
        """Remove Windows scheduled task."""
        command = f'''
        Unregister-ScheduledTask -TaskName "{self.task_name}" -Confirm:$false -ErrorAction SilentlyContinue
        '''
        
        success, _ = self.run_powershell_command(command)
        return success

    def is_startup_task_exists(self) -> bool:
        """Check if startup task exists."""
        command = f'''
        $task = Get-ScheduledTask -TaskName "{self.task_name}" -ErrorAction SilentlyContinue
        if ($task) {{
            Write-Output "True"
        }} else {{
            Write-Output "False"
        }}
        '''
        
        success, output = self.run_powershell_command(command, as_admin=False)
        return success and "True" in output 