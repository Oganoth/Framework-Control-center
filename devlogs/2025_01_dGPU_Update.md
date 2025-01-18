🎨⚙️ Framework Hub Devlog (January 11, 2025)🔧

Today I focused on improving the GPU detection and display system in Framework Control Center. Here are the key changes:

✨ New Features:
- Implemented dynamic dGPU detection using LibreHardwareMonitor
- Added automatic UI adaptation based on hardware presence
- The dGPU monitoring section now only appears when a discrete GPU is actually present in the system

🎨 UI Improvements:
- Fixed visual inconsistencies in the monitoring section
- Removed unnecessary background from the dGPU metrics to match other hardware stats
- Ensured seamless integration with the existing monitoring layout
- Maintained the clean, modern look of the interface

🔍 Technical Details:
- Continued to implement Intel CPU support and tweaking profiles
( I only have a 165H, so if you have any profiles to share with me, tell me everything about it 🙏)
- Added a new `HasDiscreteGpu()` method to detect AMD, Intel and Nvidia GPUs (If Framework add one in the future) 
- Improved error handling for hardware detection
- Optimized the UI update process to handle dynamic hardware changes
- Integrated with the existing debug settings system

🎯 Benefits:
- Cleaner interface for users without a dGPU
- More accurate hardware representation
- Better user experience with automatic hardware detection
- Reduced visual clutter

📦 Project Management:
- Created a private GitHub repository for better version control (I'll give you access to it later)
- Set up the initial project structure with proper .gitignore
- Implemented best practices for C# and Avalonia development
- Prepared the groundwork for future collaboration and code sharing

💬 Community:
- Launched the official Discord server for better community interaction
- Integrated Patreon roles with Discord for automatic permission management 
(You just need to link your Discord account with your Patreon account to get invited)
- Created dedicated channels for log sharing and troubleshooting, a pub for random discussions,...
- If you want to be a Moderator, you can send me a message on Discord 👮
- Can you tell me if you'd like to have a "Wiki" Where I can add some informations about the Framework Control Center ?

These changes make Framework Control Center more adaptable to different Framework Laptop configurations, whether they include a discrete GPU or not. The app now intelligently shows only the relevant information for your specific hardware setup.

Next up: I'll work on fine-tuning the defaults profiles for 7640U and 7840U ( if you have some profiles you want to share with me, tell me everything about it 😊).
         I'll also try to find-out about a bug HansDerKrieger found with WallpapersEngine where the Gui flickers when using certain wallpapers.
As always, thank you for your continued support! 🙏

#FrameworkLaptop #Development #SoftwareUpdate

