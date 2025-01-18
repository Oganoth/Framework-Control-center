using System;
using System.Management;
using System.Runtime.Versioning;

namespace FrameworkControl.Models
{
    [SupportedOSPlatform("windows")]
    public class BrightnessController
    {
        private const string WMI_MONITOR_BRIGHTNESS_QUERY = "SELECT * FROM WmiMonitorBrightness";
        private const string WMI_MONITOR_BRIGHTNESS_METHOD = "WmiSetBrightness";
        private const string WMI_NAMESPACE = @"root\wmi";

        public int GetCurrentBrightness()
        {
            try
            {
                using var searcher = new ManagementObjectSearcher(WMI_NAMESPACE, WMI_MONITOR_BRIGHTNESS_QUERY);
                using var collection = searcher.Get();

                foreach (ManagementObject obj in collection)
                {
                    return Convert.ToInt32(obj["CurrentBrightness"]);
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error getting brightness: {ex.Message}");
            }

            return 50; // Default value if we can't get the actual brightness
        }

        public void SetBrightness(int brightness)
        {
            try
            {
                using var searcher = new ManagementObjectSearcher(WMI_NAMESPACE, "SELECT * FROM WmiMonitorBrightnessMethods");
                using var collection = searcher.Get();

                foreach (ManagementObject obj in collection)
                {
                    obj.InvokeMethod(WMI_MONITOR_BRIGHTNESS_METHOD, new object[] { 1, brightness });
                    break; // Only set for the first monitor
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error setting brightness: {ex.Message}");
            }
        }
    }
}
