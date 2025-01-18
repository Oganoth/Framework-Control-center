using System;
using System.Management;
using System.Runtime.Versioning;

namespace FrameworkControl.Models
{
    [SupportedOSPlatform("windows")]
    public class BatteryMonitor
    {
        public event EventHandler<bool>? ChargingStatusChanged;
        
        public int BatteryPercentage { get; private set; }
        private bool _isCharging;
        public bool IsCharging 
        { 
            get => _isCharging;
            private set
            {
                if (_isCharging != value)
                {
                    _isCharging = value;
                    ChargingStatusChanged?.Invoke(this, _isCharging);
                }
            }
        }
        public TimeSpan? TimeRemaining { get; private set; }

        public void UpdateBatteryInfo()
        {
            try
            {
                using (var searcher = new ManagementObjectSearcher("root\\CIMV2", "SELECT * FROM Win32_Battery"))
                using (var collection = searcher.Get())
                {
                    foreach (ManagementObject mo in collection)
                    {
                        // Get battery percentage
                        BatteryPercentage = Convert.ToInt32(mo["EstimatedChargeRemaining"]);

                        // Get charging status (1 = Discharging, 2 = AC, 3 = Fully Charged, etc.)
                        int status = Convert.ToInt32(mo["BatteryStatus"]);
                        IsCharging = status == 2;

                        if (IsCharging)
                        {
                            // Get time to full charge
                            int timeToFull = Convert.ToInt32(mo["TimeToFullCharge"]);
                            if (timeToFull > 0 && timeToFull < 1000) // Filter out invalid values
                            {
                                TimeRemaining = TimeSpan.FromMinutes(timeToFull);
                            }
                            else
                            {
                                TimeRemaining = null;
                            }
                        }
                        else
                        {
                            // Get estimated runtime in minutes
                            int estimatedRuntime = Convert.ToInt32(mo["EstimatedRunTime"]);
                            if (estimatedRuntime > 0 && estimatedRuntime < 71582) // Filter out invalid values
                            {
                                TimeRemaining = TimeSpan.FromMinutes(estimatedRuntime);
                            }
                            else
                            {
                                TimeRemaining = null;
                            }
                        }
                        break; // We only need the first battery
                    }
                }
            }
            catch (Exception)
            {
                // Handle any potential errors
                BatteryPercentage = 0;
                IsCharging = false;
                TimeRemaining = null;
            }
        }

        public string GetStatusText()
        {
            string status = $"{BatteryPercentage}% - {(IsCharging ? "AC" : "DC")}";
            if (TimeRemaining.HasValue)
            {
                status += IsCharging 
                    ? $" - {TimeRemaining.Value.Hours}h {TimeRemaining.Value.Minutes}m until full"
                    : $" - {TimeRemaining.Value.Hours}h {TimeRemaining.Value.Minutes}m remaining";
            }
            return status;
        }

        public string GetTimeText()
        {
            return ""; // On n'utilise plus cette méthode
        }
    }
}
