🔥⚙️ Framework Hub Devlog - January 14, 2025 

Hey Everyone! 

Today marks a significant milestone in Framework Control Center's development. I've made the decision to implement direct CPU power management using WinRing0 instead of ThrottleStop. My goal has always been to keep Framework Control Center lightweight, efficient, and independent. By implementing direct MSR control, I can ensure that our application remains self-contained without relying on external programs.

This architectural change brings several advantages. With the Intel Core Ultra processors, having direct control over power management features allows for better optimization and a more streamlined user experience. By using WinRing0, I can now provide:
- Native power management without external dependencies
- Optimized support for Intel Core Ultra processors
- Lightweight and efficient implementation
- Full secure boot compatibility (For PL1 at least)
- Direct integration with Framework Control Center

This change sets a strong foundation for future improvements while keeping the application clean and self-contained. Thank you for your continued support!

✨ New Features:
- Replaced ThrottleStop with direct WinRing0 implementation for Intel CPU power management
- Implemented new power profiles specifically tuned for Intel Core Ultra

🪛 Optimizations & User Experience:
- Improved error handling and user feedback for power limit changes
- Added detailed logging for CPU power management operations
- Enhanced profile switching with clear success/failure indicators

🛠️ Technical Improvements:
- Direct MSR register access through WinRing0 for power limit control
- Improved CPU model detection for Intel Core Ultra processors
- Enhanced error handling for locked MSR registers

📝 Technical Deep Dive: Intel Core Ultra Power Management

1. Power Limit Behavior on Intel Core Ultra:
   - PL1 (Power Limit 1): Successfully controllable through MSR 0x610 With Secure Boot Enabled !
     * Long-term sustained power limit
     * Configurable on the 165H model and below 
     * Critical for managing sustained performance and heat
   
   - PL2 (Power Limit 2): Locked by firmware (MSR 0x611)
     * Short-term burst power limit 
     * Cannot be modified on Core Ultra
     * Firmware/BIOS maintains control for system stability
   
   - Turbo Time: Also locked (MSR 0x612)
     * Controls duration of PL2 power limit
     * Managed by firmware on Core Ultra
   
   - Temperature Limit: Protected (MSR 0x613)
     * Thermal throttling threshold
     * Controlled by system firmware

2. Implementation Changes:
   - Added graceful handling of locked registers
   - Implemented partial profile application when some settings are locked
   - Enhanced logging to show exactly which settings were applied

3. Profile Adjustments for 165H:
   Eco Profile:
   - PL1: 28W (Tested, Configurable)
   - PL2: 45W (Tested, Locked by firmware)
   - Temperature: 95°C (Tested, Protected)

   Balanced Profile:
   - PL1: 35W (Tested, Configurable)
   - PL2: 55W (Tested, Locked by firmware)
   - Temperature: 95°C (Tested, Protected)

   Boost Profile:
   - PL1: 45W (Tested, Configurable)
   - PL2: 65W (Tested, Locked by firmware)
   - Temperature: 95°C (Tested, Protected)

4. Future Improvements:
   - Investigate alternative methods for PL2 control if possible

These changes mark a significant improvement in how I handle Intel CPU power management, particularly for the new Core Ultra series. While I have some limitations with locked registers, I've implemented a robust solution that provides users with meaningful control over their CPU's sustained performance characteristics.