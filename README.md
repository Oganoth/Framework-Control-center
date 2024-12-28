# Framework Hub Mini

<div align="center">

<img src="screenshots/main.png" width="600" alt="Framework Hub Mini Main Interface"/>

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%2011-orange.svg)
![License](https://img.shields.io/badge/License-GPL--3.0-green.svg)
![Framework](https://img.shields.io/badge/Framework-AMD%20Only-red.svg)
![Status](https://img.shields.io/badge/Status-Beta-yellow.svg)
![RyzenADJ](https://img.shields.io/badge/RyzenADJ-v0.14.0-purple.svg)

<p align="center">
  <a href="#english">English</a> •
  <a href="#français">Français</a> •
  <a href="#-key-features">Features</a> •
  <a href="#-installation">Install</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-contributing">Contribute</a> •
  <a href="#-support">Support</a>
</p>

</div>

<div align="center">
  <sub>Built with ❤️ by <a href="https://patreon.com/Oganoth">Oganoth</a> and <a href="#-acknowledgments">contributors</a></sub>
</div>

<hr>

## English

### 🎯 Overview

Framework Hub Mini is a powerful system management tool designed specifically for Framework AMD laptops. Built with Python and modern UI components, it provides comprehensive control over power management, performance optimization, and hardware monitoring through an elegant, feature-rich interface.

### 📸 Screenshots

<div align="center">
<p float="left">
  <img src="screenshots/main.png" width="250" alt="Main Interface"/>
  <img src="screenshots/theme1.png" width="250" alt="Fedora Light Theme"/>
  <img src="screenshots/theme2.png" width="250" alt="Fedora Dark Theme"/>
</p>
<p float="left">
  <img src="screenshots/Updates%20manager.png" width="375" alt="Updates Manager"/>
  <img src="screenshots/Tweaks.png" width="375" alt="System Tweaks"/>
</p>

<em>Framework Hub Mini in action - Modern UI with multiple themes, system management, and monitoring capabilities</em>
</div>

### ✨ Key Features

### 🎨 Theme System

#### Built-in Themes
- **Default Dark**: Modern dark theme with orange accents
- **Fedora Dark**: GNOME-inspired dark theme with blue accents
- **Fedora Light**: Clean light theme based on GNOME

#### Theme Features
- Complete UI customization
- Color schemes for all elements
- Font configuration (family and sizes)
- Spacing and border radius control
- Real-time theme switching

For detailed information about creating and customizing themes, check out our [Theming Guide](Theming_guide.md).

### 🔋 Power Management

#### AMD Power Profiles
- **Framework 13 AMD (7840U)**:
  - Silent/ECO: STAPM 15W, Fast 20W, Slow 15W
  - Balanced: STAPM 25W, Fast 30W, Slow 25W
  - Boost: STAPM 28W, Fast 35W, Slow 28W
- **Framework 16 AMD (7840HS/7940HS)**:
  - Silent/ECO: STAPM 30W, Fast 35W, Slow 30W
  - Balanced: STAPM 95W, Fast 95W, Slow 95W
  - Boost: STAPM 120W, Fast 120W, Slow 120W

#### Power Features
- RyzenADJ integration for AMD models
- Windows power plan synchronization (Silent/Balanced/Performance)
- Temperature limits management
- VRM current control
- Automatic hardware detection

### 💻 Hardware Monitoring

#### Real-time Metrics
- CPU usage and temperature
- RAM usage monitoring
- iGPU usage and temperature
- dGPU metrics (Framework 16)
- Battery status and time remaining

#### System Integration
- LibreHardwareMonitor integration
- Automatic sensor detection
- Real-time metrics update
- Progress bar visualizations

### 🖥️ Display Management

#### Display Features
- Brightness control via WMI
- Hotkey support (F12)
- System tray integration
- Minimized mode operation

### ⚡ System Features

#### Core Features
- Multi-language support (English/French/Italian/Spanish/German/Chinese/Klingon)
- Automatic model detection
- Configuration persistence
- Logging system with rotation

#### Updates & Tools
- Built-in updates manager (winget integration)
- Framework drivers shortcuts
- AMD drivers shortcuts
- System information display

### 🛠️ Technical Details

#### Dependencies
```python
customtkinter>=5.2.0    # Modern UI framework
pydantic>=2.5.0        # Data validation
requests>=2.31.0       # Network operations
psutil>=5.9.0         # System monitoring
Pillow>=10.0.0        # Image processing
aiohttp>=3.9.0        # Async HTTP client
pywin32>=306          # Windows API integration
wmi>=1.5.1            # Hardware information
comtypes>=1.2.0       # COM interface
pythonnet>=3.0.3      # .NET integration
pystray>=0.19.4       # System tray
keyboard>=0.13.5      # Hotkey support
```

### 🔧 Installation

#### Prerequisites
- Windows 11 (22H2 or later)
- Administrator privileges
- .NET Framework 4.8
- Visual C++ Redistributable 2015-2022

#### Python Edition (Open Source)
```bash
# Clone repository
git clone https://github.com/Oganoth/Framework-Hub-PY.git
cd Framework-Hub-PY

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

#### Framework-Hub.exe (Easy Install)
Download the all-in-one installer from [Patreon](https://patreon.com/Oganoth)

### 📋 Usage

#### First Launch
- Run as administrator
- Hardware detection is automatic
- Initial configuration wizard

#### Daily Use
- Access via system tray
- Quick profile switching
- Real-time monitoring

#### Advanced Features
- Create custom power profiles
- Configure fan curves
- Set up automation rules
- Switch between themes

### 🤝 Contributing

#### Code Contributions
1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Submit a pull request

#### Other Ways to Help
- Report bugs and issues
- Suggest new features
- Improve documentation
- Help with translations
- Create custom themes

### ❤️ Support

<div align="center">

[![Become a Patron](https://img.shields.io/badge/Patreon-Support%20Framework%20Hub-FF424D?style=for-the-badge&logo=patreon)](https://patreon.com/Oganoth)

</div>

Framework Hub Mini is a passion project that requires significant time and effort. Your support helps:
- Develop new features
- Improve existing functionality
- Provide faster support
- Create better documentation

### 📜 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

<hr>

