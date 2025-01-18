using System;

namespace FrameworkControl.Models
{
    public class DebugSettingsChangedEventArgs : EventArgs
    {
        public DebugSettings Settings { get; }

        public DebugSettingsChangedEventArgs(DebugSettings settings)
        {
            Settings = settings;
        }
    }
} 