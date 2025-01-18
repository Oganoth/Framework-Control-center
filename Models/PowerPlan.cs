using System.Text.Json.Serialization;
using System.Collections.Generic;

namespace FrameworkControl.Models
{
    public class PowerPlan
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("description")]
        public string Description { get; set; } = string.Empty;

        [JsonPropertyName("guid")]
        public string Guid { get; set; } = string.Empty;

        [JsonPropertyName("ac_settings")]
        public PowerPlanSettings AcSettings { get; set; } = new PowerPlanSettings();

        [JsonPropertyName("dc_settings")]
        public PowerPlanSettings DcSettings { get; set; } = new PowerPlanSettings();

        [JsonPropertyName("commands")]
        public Dictionary<string, PowerPlanCommand> Commands { get; set; } = new Dictionary<string, PowerPlanCommand>();

        public void GenerateCommands()
        {
            Commands.Clear();

            // Processor power management
            AddCommand("processor_minimum_state", "54533251-82be-4824-96c1-47b60b740d00", "893dee8e-2bef-41e0-89c6-b55d0929964c",
                AcSettings.ProcessorMinimumState.ToString(), DcSettings.ProcessorMinimumState.ToString());

            AddCommand("processor_maximum_state", "54533251-82be-4824-96c1-47b60b740d00", "bc5038f7-23e0-4960-96da-33abaf5935ec",
                AcSettings.ProcessorMaximumState.ToString(), DcSettings.ProcessorMaximumState.ToString());

            AddCommand("processor_performance_boost_mode", "54533251-82be-4824-96c1-47b60b740d00", "be337238-0d82-4146-a960-4f3749d470c7",
                AcSettings.ProcessorPerformanceBoostMode.ToString(), DcSettings.ProcessorPerformanceBoostMode.ToString());

            AddCommand("processor_performance_boost_policy", "54533251-82be-4824-96c1-47b60b740d00", "45bcc044-d885-43e2-8605-ee0ec6e96b59",
                AcSettings.ProcessorPerformanceBoostPolicy.ToString(), DcSettings.ProcessorPerformanceBoostPolicy.ToString());

            AddCommand("processor_boost_time_window", "54533251-82be-4824-96c1-47b60b740d00", "45bcc044-d885-43e2-8605-ee0ec6e96b59",
                AcSettings.ProcessorBoostTimeWindow.ToString(), DcSettings.ProcessorBoostTimeWindow.ToString());

            // System cooling policy
            AddCommand("system_cooling_policy", "238c9fa8-0aad-41ed-83f4-97be242c8f20", "94d3a615-a899-4ac5-ae2b-e4d8f634367f",
                AcSettings.SystemCoolingPolicy.ToString(), DcSettings.SystemCoolingPolicy.ToString());

            // Hard disk idle timeout
            AddCommand("disk_idle_timeout", "6738e2c4-e8a5-4a42-b16a-e040e769756e", "DISKIDLE",
                AcSettings.DiskIdleTimeout.ToString(), DcSettings.DiskIdleTimeout.ToString());

            // AMD Dynamic Graphics
            AddCommand("dynamic_graphics_mode", "54533251-82be-4824-96c1-47b60b740d00", "dd848b2a-8a5d-4451-9ae2-39cd41658f6c",
                AcSettings.DynamicGraphicsMode.ToString(), DcSettings.DynamicGraphicsMode.ToString());

            // Adaptive Brightness
            AddCommand("adaptive_brightness", "7516b95f-f776-4464-8c53-06167f40cc99", "fbd9aa66-9553-4097-ba44-ed6e9d65eab8",
                AcSettings.AdaptiveBrightness.ToString(), DcSettings.AdaptiveBrightness.ToString());

            // Advanced Color Quality Bias
            AddCommand("advanced_color_quality_bias", "7516b95f-f776-4464-8c53-06167f40cc99", "684c3e69-a4f7-4014-8754-d45179a56167",
                AcSettings.AdvancedColorQualityBias.ToString(), DcSettings.AdvancedColorQualityBias.ToString());

            // USB Hub Suspend Timeout
            AddCommand("usb_hub_timeout", "2a737441-1930-4402-8d77-b2bebba308a3", "0853a681-27c8-4100-a2fd-82013e970683",
                AcSettings.UsbHubTimeout.ToString(), DcSettings.UsbHubTimeout.ToString());

            // USB Selective Suspend
            AddCommand("usb_suspend", "2a737441-1930-4402-8d77-b2bebba308a3", "48e6b7a6-50f5-4782-a5d4-53bb8f07e226",
                (AcSettings.UsbSuspend ? "1" : "0"), (DcSettings.UsbSuspend ? "1" : "0"));

            // USB IOC Setting
            AddCommand("usb_ioc", "2a737441-1930-4402-8d77-b2bebba308a3", "498c044a-201b-4631-a522-5c744ed4e678",
                (AcSettings.UsbIoc ? "1" : "0"), (DcSettings.UsbIoc ? "1" : "0"));

            // USB 3 Link Power Management
            AddCommand("usb_link_power", "2a737441-1930-4402-8d77-b2bebba308a3", "d4e98f31-5ffe-4ce1-be31-1b38b384c009",
                AcSettings.UsbLinkPower.ToString(), DcSettings.UsbLinkPower.ToString());

            // Processor Performance Increase Policy
            AddCommand("processor_performance_increase_policy", "54533251-82be-4824-96c1-47b60b740d00", "465e1f50-b610-473a-ab58-00d1077dc418",
                AcSettings.ProcessorPerformanceIncreasePolicy.ToString(), DcSettings.ProcessorPerformanceIncreasePolicy.ToString());
        }

        private void AddCommand(string name, string subgroupGuid, string settingGuid, string acValue, string dcValue)
        {
            Commands[name] = new PowerPlanCommand
            {
                SubgroupGuid = subgroupGuid,
                SettingGuid = settingGuid,
                AcValue = acValue,
                DcValue = dcValue
            };
        }
    }

    public class PowerPlanCommand
    {
        [JsonPropertyName("subgroup_guid")]
        public string SubgroupGuid { get; set; } = string.Empty;

        [JsonPropertyName("setting_guid")]
        public string SettingGuid { get; set; } = string.Empty;

        [JsonPropertyName("ac_value")]
        public string AcValue { get; set; } = string.Empty;

        [JsonPropertyName("dc_value")]
        public string DcValue { get; set; } = string.Empty;
    }

    public class PowerPlanSettings
    {
        [JsonPropertyName("processor_performance_increase_threshold")]
        public int ProcessorPerformanceIncreaseThreshold { get; set; }

        [JsonPropertyName("processor_performance_decrease_threshold")]
        public int ProcessorPerformanceDecreaseThreshold { get; set; }

        [JsonPropertyName("processor_performance_cores_parking_min")]
        public int ProcessorPerformanceCoresParkingMin { get; set; }

        [JsonPropertyName("processor_performance_cores_parking_max")]
        public int ProcessorPerformanceCoresParkingMax { get; set; }

        [JsonPropertyName("processor_idle_disable")]
        public int ProcessorIdleDisable { get; set; }

        [JsonPropertyName("processor_performance_time_check")]
        public int ProcessorPerformanceTimeCheck { get; set; }

        [JsonPropertyName("processor_duty_cycling")]
        public int ProcessorDutyCycling { get; set; }

        [JsonPropertyName("processor_performance_boost_mode")]
        public int ProcessorPerformanceBoostMode { get; set; }

        [JsonPropertyName("processor_performance_boost_policy")]
        public int ProcessorPerformanceBoostPolicy { get; set; }

        [JsonPropertyName("processor_boost_time_window")]
        public int ProcessorBoostTimeWindow { get; set; }

        [JsonPropertyName("processor_minimum_state")]
        public int ProcessorMinimumState { get; set; }

        [JsonPropertyName("processor_maximum_state")]
        public int ProcessorMaximumState { get; set; }

        [JsonPropertyName("system_cooling_policy")]
        public int SystemCoolingPolicy { get; set; }

        [JsonPropertyName("disk_idle_timeout")]
        public int DiskIdleTimeout { get; set; } = 0;

        // AMD Dynamic Graphics Settings
        [JsonPropertyName("dynamic_graphics_mode")]
        public int DynamicGraphicsMode { get; set; } = 1; // Default: Optimize power savings

        [JsonPropertyName("adaptive_brightness")]
        public int AdaptiveBrightness { get; set; } = 0; // 0 = Off, 1 = On

        [JsonPropertyName("advanced_color_quality_bias")]
        public int AdvancedColorQualityBias { get; set; } = 1; // 0 = Power saving bias, 1 = Visual quality bias

        [JsonPropertyName("usb_hub_timeout")]
        public int UsbHubTimeout { get; set; } = 50; // 50ms default

        [JsonPropertyName("usb_suspend")]
        public bool UsbSuspend { get; set; } = true;

        [JsonPropertyName("usb_ioc")]
        public bool UsbIoc { get; set; } = true;

        [JsonPropertyName("usb_link_power")]
        public int UsbLinkPower { get; set; } = 2; // Moderate power savings by default

        [JsonPropertyName("processor_performance_increase_policy")]
        public int ProcessorPerformanceIncreasePolicy { get; set; } = 0; // Default: Ideal
    }

    public class PowerSettings
    {
        [JsonPropertyName("usb_hub_timeout")]
        public int UsbHubTimeout { get; set; } = 50; // 50ms default

        [JsonPropertyName("usb_suspend")]
        public bool UsbSuspend { get; set; } = true;

        [JsonPropertyName("usb_ioc")]
        public bool UsbIoc { get; set; } = true;

        [JsonPropertyName("usb_link_power")]
        public int UsbLinkPower { get; set; } = 2; // Moderate power savings by default
    }
} 