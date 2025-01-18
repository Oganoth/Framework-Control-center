🔥⚙️ Framework Hub Devlog - January 14, 2025 

Hey Everyone ! 

✨ New Features:
- Added the PowerCFG settings choiced by you in the Discord server 
- Added a new tab in Settings to manage ThrottleStop profiles (Hidden for AMD users, RyzenADJ is used instead and vice versa)
  - Customizable power profiles for Intel processors:
    - Power Limit 1 (PL1): 15W to 115W
    - Power Limit 2 (PL2): 15W to 115W
    - Turbo Time Limit: 1s to 120s
    - Temperature Limit: 85°C to 100°C
  - Settings are saved per CPU model in Intel_profiles.json
  - Changes are applied immediately when switching profiles
  - Default values are displayed for reference


🪛 Optimizations & User Experience:
- Automatic CPU detection for Intel/AMD to show appropriate power management tools
- Seamless integration with existing profile system
- Profile settings persist between application restarts
- Real-time profile application using ThrottleStop.exe
- Added help icons with detailed tooltips for each PowerCFG setting
- Improved UI consistency with Windows 11 accent colors
- Enhanced button and ComboBox styling
- Fixed flickering issues in Settings window
- Optimized rendering performance
- Added "Close" button functionality in Settings window

🛠️ Technical Improvements:
- Implemented profile serialization and deserialization
- Added safety checks for supported CPU models
- Integrated with existing power management system
- Improved UI update handling to reduce possible flickering
- Enhanced error handling and logging
- Added tooltips with detailed explanations for all power settings


I'll continue to work on the ThrottleStop custom profiles and the PowerCFG settings tomorrow.
As always, thanks for your support and feedback ! :heart:
