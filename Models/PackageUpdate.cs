using System;

namespace FrameworkControl.Models
{
    public class PackageUpdate
    {
        public string Name { get; set; } = string.Empty;
        public string Id { get; set; } = string.Empty;
        public string CurrentVersion { get; set; } = string.Empty;
        public string NewVersion { get; set; } = string.Empty;
        public PackageManagerType PackageManager { get; set; }

        public string Version => $"{CurrentVersion} → {NewVersion}";
    }

    public enum PackageManagerType
    {
        Winget
    }
} 