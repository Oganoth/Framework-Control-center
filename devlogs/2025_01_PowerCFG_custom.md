🔋⚙️ Framework Hub Devlog (January 13, 2025)🔧

Today I was focused on improving power plan management and adding user customization options for PowerCFG in Framework Control Center. Here are the key changes:

✨ New Features:
- Implemented a new tab in Settings to manage PowerCFG settings (Following your votes on Discord 👍)
- Added a rule to keep the default "Balanced" powerplan untouched by the app and creating 3 new powerplans:

    - Framework-Eco: Power-saving focused settings with AC & DC customizations  
    - Framework-Balanced: Balanced performance and efficiency with AC & DC customizations
    - Framework-Boost: Maximum performance settings with AC & DC customizations
    *Be careful tho, don't set Maximum Performance State under 40-50% if you don't want to turn your Laptop into a potato


🪛 Optimizations & User Experience:

1. AMD Dynamic Graphics Mode Implementation:
   - Added proper value mapping for AMD Dynamic Graphics settings (For AMD users)
   - Implemented 4 power states with correct hexadecimal values:
     * Force power-saving graphics (0x00000000)
     * Optimize power savings (0x00000001)
     * Optimize performance (0x00000002)
     * Maximize performance (0x00000003)
   - Added validation to ensure values are within valid range
   - Applied settings for both AC and DC power states

2. Power Plan Settings Fixes:
   - Fixed processor boost time window parameter
     * Changed from incorrect PERFBOOSTPERCENT to correct PERFBOOSTTIME
     * Applied fix for both AC and DC power states
   - Removed unsupported Advanced Color Quality Bias settings
     * Removed settings that were causing errors in powercfg
     * Cleaned up related code to improve stability

3. Error Handling & Logging:
   - Added detailed error logging for powercfg operations
   - Improved error messages for unsupported settings
   - Added validation checks before applying power settings
   - Enhanced logging for power plan creation and modification

4. Code Structure Improvements:
   - Reorganized power plan settings application
   - Added constants for power setting values
   - Improved code readability and maintainability
   - Added comments for better code documentation

🔍 Technical Details:

- PowerCFG GUIDs and Settings:
  * AMD Dynamic Graphics: e276e160-7cb0-43c6-b20b-73f5dce39954
  * AMD Dynamic Graphics Setting: a1662ab2-9d34-4e53-ba8b-2639b9e20857
  * Processor Settings: SUB_PROCESSOR
  * Windows Balanced Plan: 381b4222-f694-41f0-9685-ff5bb260df2e

- Power Plan Structure:
  * Framework-Eco: Power-saving focused settings
  * Framework-Balanced: Balanced performance and efficiency
  * Framework-Boost: Maximum performance settings


📝 Notes:
- All changes have been tested on AMD Ryzen 7840HS laptop with dGPU 
- Settings are properly persisted between system reboots
( The new powerplans can be fully deleted by the user if they want to by doing "Powercfg /restoredefaultschemes" in a admin cmd )
- Power plans are automatically recreated if deleted by error at the next app launch  