using System;
using System.Management;
using System.Runtime.InteropServices;

namespace FrameworkControl.Models
{
    public class DisplayRefreshRate
    {
        private readonly Logger _logger;

        public DisplayRefreshRate()
        {
            _logger = new Logger("DisplayRefreshRate");
        }

        [DllImport("user32.dll")]
        private static extern int EnumDisplaySettings(string? deviceName, int modeNum, ref DEVMODE devMode);

        [StructLayout(LayoutKind.Sequential)]
        private struct DEVMODE
        {
            private const int CCHDEVICENAME = 32;
            private const int CCHFORMNAME = 32;

            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = CCHDEVICENAME)]
            public string dmDeviceName;
            public short dmSpecVersion;
            public short dmDriverVersion;
            public short dmSize;
            public short dmDriverExtra;
            public int dmFields;
            public int dmPositionX;
            public int dmPositionY;
            public int dmDisplayOrientation;
            public int dmDisplayFixedOutput;
            public short dmColor;
            public short dmDuplex;
            public short dmYResolution;
            public short dmTTOption;
            public short dmCollate;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = CCHFORMNAME)]
            public string dmFormName;
            public short dmLogPixels;
            public int dmBitsPerPel;
            public int dmPelsWidth;
            public int dmPelsHeight;
            public int dmDisplayFlags;
            public int dmDisplayFrequency;
            public int dmICMMethod;
            public int dmICMIntent;
            public int dmMediaType;
            public int dmDitherType;
            public int dmReserved1;
            public int dmReserved2;
            public int dmPanningWidth;
            public int dmPanningHeight;

            public DEVMODE()
            {
                dmDeviceName = string.Empty;
                dmFormName = string.Empty;
                dmSpecVersion = 0;
                dmDriverVersion = 0;
                dmSize = 0;
                dmDriverExtra = 0;
                dmFields = 0;
                dmPositionX = 0;
                dmPositionY = 0;
                dmDisplayOrientation = 0;
                dmDisplayFixedOutput = 0;
                dmColor = 0;
                dmDuplex = 0;
                dmYResolution = 0;
                dmTTOption = 0;
                dmCollate = 0;
                dmLogPixels = 0;
                dmBitsPerPel = 0;
                dmPelsWidth = 0;
                dmPelsHeight = 0;
                dmDisplayFlags = 0;
                dmDisplayFrequency = 0;
                dmICMMethod = 0;
                dmICMIntent = 0;
                dmMediaType = 0;
                dmDitherType = 0;
                dmReserved1 = 0;
                dmReserved2 = 0;
                dmPanningWidth = 0;
                dmPanningHeight = 0;
            }
        }

        private const int ENUM_CURRENT_SETTINGS = -1;
        private const int ENUM_REGISTRY_SETTINGS = -2;
        private const int DISP_CHANGE_SUCCESSFUL = 0;
        private const int CDS_UPDATEREGISTRY = 0x01;
        private const int CDS_TEST = 0x02;

        [DllImport("user32.dll")]
        private static extern int ChangeDisplaySettings(ref DEVMODE devMode, int flags);

        private int? _maxRefreshRate;

        public int GetMaxRefreshRate()
        {
            if (_maxRefreshRate.HasValue)
                return _maxRefreshRate.Value;

            int maxRefreshRate = 60; // Default minimum
            DEVMODE devMode = new DEVMODE();
            devMode.dmSize = (short)Marshal.SizeOf(devMode);

            try
            {
                int modeNum = 0;
                while (EnumDisplaySettings(null, modeNum, ref devMode) != 0)
                {
                    // Only consider modes with the same resolution as current
                    DEVMODE currentMode = new DEVMODE();
                    currentMode.dmSize = (short)Marshal.SizeOf(currentMode);
                    EnumDisplaySettings(null, ENUM_CURRENT_SETTINGS, ref currentMode);

                    if (devMode.dmPelsWidth == currentMode.dmPelsWidth && 
                        devMode.dmPelsHeight == currentMode.dmPelsHeight && 
                        devMode.dmDisplayFrequency > maxRefreshRate)
                    {
                        maxRefreshRate = devMode.dmDisplayFrequency;
                    }
                    modeNum++;
                }

                _maxRefreshRate = maxRefreshRate;
                _logger.Log($"Maximum refresh rate detected: {maxRefreshRate}Hz at resolution {devMode.dmPelsWidth}x{devMode.dmPelsHeight}");
                return maxRefreshRate;
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error detecting maximum refresh rate: {ex.Message}");
                _maxRefreshRate = 60;
                return 60;
            }
        }

        public void SetRefreshRate(int refreshRate)
        {
            try
            {
                DEVMODE devMode = new DEVMODE();
                devMode.dmSize = (short)Marshal.SizeOf(devMode);
                
                if (EnumDisplaySettings(null, ENUM_CURRENT_SETTINGS, ref devMode) != 0)
                {
                    int currentRate = devMode.dmDisplayFrequency;
                    devMode.dmDisplayFrequency = refreshRate;
                    devMode.dmFields = 0x400000; // DM_DISPLAYFREQUENCY

                    // Test the settings first
                    int result = ChangeDisplaySettings(ref devMode, CDS_TEST);
                    if (result == DISP_CHANGE_SUCCESSFUL)
                    {
                        // If test was successful, actually change the settings
                        result = ChangeDisplaySettings(ref devMode, CDS_UPDATEREGISTRY);
                        if (result == DISP_CHANGE_SUCCESSFUL)
                        {
                            _logger.Log($"Successfully changed refresh rate from {currentRate}Hz to {refreshRate}Hz");
                        }
                        else
                        {
                            _logger.LogError($"Failed to apply refresh rate change to {refreshRate}Hz (Error code: {result})");
                        }
                    }
                    else
                    {
                        _logger.LogError($"Failed to test refresh rate change to {refreshRate}Hz (Error code: {result})");
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error setting refresh rate to {refreshRate}Hz: {ex.Message}");
            }
        }

        public int GetCurrentRefreshRate()
        {
            try
            {
                DEVMODE devMode = new DEVMODE();
                devMode.dmSize = (short)Marshal.SizeOf(devMode);
                
                if (EnumDisplaySettings(null, ENUM_CURRENT_SETTINGS, ref devMode) != 0)
                {
                    _logger.Log($"Current refresh rate: {devMode.dmDisplayFrequency}Hz");
                    return devMode.dmDisplayFrequency;
                }
                
                _logger.LogWarning("Could not get current refresh rate, returning default 60Hz");
                return 60; // Default fallback
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error getting current refresh rate: {ex.Message}");
                return 60;
            }
        }

        public void SetAutoRefreshRate(bool isCharging)
        {
            try
            {
                int maxRate = GetMaxRefreshRate();
                _logger.Log($"Auto refresh rate: Setting to {(isCharging ? maxRate : 60)}Hz (Charging: {isCharging})");
                SetRefreshRate(isCharging ? maxRate : 60);
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error in auto refresh rate: {ex.Message}");
            }
        }
    }
}
