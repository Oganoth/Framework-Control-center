🔥⚙️ Framework Hub Devlog (January 12, 2025)🔧

Today I was focused on improving the profiles system in Framework Control Center. Here are the key changes:

🪛 Optimizations & User Experience:

    - Default profils RyzenADJ/ThrottleStop added/fine-tuned for :

        - AMD 7640U
        - AMD 7840U
        - AMD 7940HS
        - AMD 7840HS
        - Intel Ultra 5 125H
        - Intel Ultra 7 155H
        - Intel Ultra 7 165H
        - Intel i5-1340P
        - Intel i7-1360P
        - Intel i7-1370P

    - Tweaked the dynamic display of supported max refresh rate 
    ( If your screen support 120Hz, it will be displayed 120Hz instead of 165hz, if your screen only support 60Hz too ) 
    - Added more logs generation for ThrottleStop for better debugging (And a better rotation of logs)
    - Framework Control Center profiles button now fully functional ( Fully tested on the AMD 7840HS with dGPU & Intel Ultra 7 165H )
    - Fixed a strange bug where some wallpapers from WallpapersEngine were creating flickers with the GUI. 
    - Fixed a bug where the profiles were not being applied correctly on some Framework Laptops. 

🛠️ Hardware Monitoring Improvements:

    - Fixed hardware monitoring initialization issues
    - Ensured proper loading of WinRing0x64.dll and inpoutx64.dll
    - Improved error handling and logging for hardware monitoring
    - Added better error messages for missing dependencies
    - Optimized hardware monitoring refresh rates for better performance

🔄 Build System:

    - Optimized build output size
    - Ensured all required files are included in the distribution
    - Added proper file organization in the release package

