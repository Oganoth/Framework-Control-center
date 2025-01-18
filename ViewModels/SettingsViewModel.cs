using ReactiveUI;
using FrameworkControl.Models;

namespace FrameworkControl.ViewModels
{
    [System.Runtime.Versioning.SupportedOSPlatform("windows")]
    public class SettingsViewModel : ReactiveObject
    {
        private readonly PowerPlanManager _powerPlanManager;
        private readonly CpuInfo _cpuInfo;
        private bool _isAmdCpu;

        public bool IsAmdCpu
        {
            get => _isAmdCpu;
            private set => this.RaiseAndSetIfChanged(ref _isAmdCpu, value);
        }

        public SettingsViewModel(PowerPlanManager powerPlanManager, CpuInfo cpuInfo)
        {
            _powerPlanManager = powerPlanManager;
            _cpuInfo = cpuInfo;
            IsAmdCpu = _cpuInfo.IsAmd;
        }
    }
} 