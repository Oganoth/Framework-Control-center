# Framework Laptop Hub Mini

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%2011-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Framework](https://img.shields.io/badge/Framework-AMD%20Only-red.svg)
![Status](https://img.shields.io/badge/Status-Beta-yellow.svg)
![RyzenADJ](https://img.shields.io/badge/RyzenADJ-v0.14.0-purple.svg)

A lightweight yet powerful control center for Framework AMD laptops, focusing on performance and battery optimization.

[English](#english) | [Français](#français)

<img src="screenshots/main.png" alt="Framework Hub Mini" width="300"/>

</div>

## English

### 🎯 Overview

Framework Hub Mini is a streamlined power management tool designed specifically for Framework AMD laptops. Built with Python and modern UI components, it offers essential controls for optimizing your laptop's performance and battery life through an elegant, minimalist interface.

### 📸 Supported Models

- **Framework Laptop 13**
  - AMD Ryzen 7 7840U
  - AMD Ryzen 5 7640U
- **Framework Laptop 16**
  - AMD Ryzen 7 7840HS
  - AMD Ryzen 9 7940HS

### 📋 System Requirements

- Windows 11 (22H2 or later)
- 4GB RAM
- 100MB disk space
- Administrator privileges
- .NET Framework 4.8
- Visual C++ Redistributable 2015-2022

### 📸 Screenshots

<div align="center">
<table>
<tr>
<td><img src="screenshots/main.png" alt="Main Interface" width="300"/></td>
<td><img src="screenshots/settings.png" alt="Settings Window" width="300"/></td>
</tr>
<tr>
<td align="center">Main Interface</td>
<td align="center">Settings Window</td>
</tr>
</table>
</div>

### ✨ Key Features

#### Power Management
- **Intelligent Power Profiles**
  - Framework 13 (7640U/7840U):
    - Silent/ECO (15W TDP)
    - Balanced (30W TDP)
    - Boost (60W TDP)
  - Framework 16 (7840HS/7940HS):
    - Silent/ECO (30W TDP)
    - Balanced (95W TDP)
    - Boost (120W TDP)

#### Display Control
- **Dynamic Refresh Rate Management**
  - Auto-switching based on power source
  - Framework 13: 60Hz/120Hz
  - Framework 16: 60Hz/165Hz
- **Brightness Control**
  - Hardware-level adjustment
  - Hotkey support

#### Battery Optimization
- **Advanced Charging Control**
  - Customizable charge limit (60-100%)
  - Battery longevity optimization
  - Real-time status monitoring

#### System Monitoring
- **Real-time Performance Metrics**
  - CPU usage and temperature
  - RAM utilization
  - Power consumption tracking

#### User Experience
- **Modern Interface**
  - System tray integration
  - Global hotkey (F12)
  - Clean, intuitive design
- **Automatic Model Detection**
  - CPU-based laptop model identification
  - Profile auto-configuration

### 🛠️ Technical Details

#### Dependencies
```python
customtkinter==5.2.0    # Modern UI components
Pillow==10.0.0         # Image processing
psutil==5.9.5          # System monitoring
pywin32==306           # Windows API integration
requests==2.31.0       # Network operations (WIP)
wmi==1.5.1             # Hardware information
keyboard==0.13.5       # Hotkey support
pystray==0.19.4        # System tray integration
```

#### Architecture
- **Core Components**
  - `SystemMonitor`: Hardware monitoring and metrics
  - `MiniFrameworkHub`: Main application logic
  - `SettingsWindow`: Configuration interface
  - `UpdateWindow`: Driver update management (WIP)

#### Key Technologies
- RyzenADJ integration for power management
- WMI for hardware interaction
- Modern CTk-based UI
- Multi-threaded monitoring system

### 📥 Installation

1. Download the latest release
2. Run the installer with administrator privileges
3. Access via:
   - Desktop shortcut
   - Start menu
   - System tray (F12)

### 🔧 Usage

1. **Launch**: Press F12 or use system tray icon
2. **Configure**:
   - Select laptop model (auto-detected)
   - Choose power profile
   - Set refresh rate
   - Adjust battery limits
3. **Monitor**: Track system performance in real-time

### 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

### ❤️ Support the Project

If you find Framework Hub Mini useful and would like to support its development, you can become a patron! Your support helps me maintain and improve the project, while keeping my cats well fed 😺

[![Become a Patron](https://img.shields.io/badge/Patreon-Support%20the%20project-FF424D?style=for-the-badge&logo=patreon)](https://patreon.com/Oganoth?utm_medium=unknown&utm_source=join_link&utm_campaign=creatorshare_creator&utm_content=copyLink)

A huge thank you to all patrons who make this project possible! ❤️

### ❤️ Acknowledgments

- **[JamesCJ60](https://github.com/JamesCJ60)** - Original concept inspiration
- **[FlyGoat](https://github.com/FlyGoat)** - RyzenADJ development

---

## Français

### 🎯 Aperçu

Framework Hub Mini est un outil de gestion d'énergie optimisé pour les ordinateurs portables Framework AMD. Développé en Python avec une interface moderne, il offre les contrôles essentiels pour optimiser les performances et l'autonomie de votre ordinateur portable via une interface minimaliste et élégante.

### 💻 Modèles Supportés

- **Framework Laptop 13**
  - AMD Ryzen 7 7840U
  - AMD Ryzen 5 7640U
- **Framework Laptop 16**
  - AMD Ryzen 7 7840HS
  - AMD Ryzen 9 7940HS

### 📋 Conditions Système

- Windows 11 (22H2 ou version ultérieure)
- 4GB RAM
- 100MB d'espace disque
- Privilèges d'administrateur
- .NET Framework 4.8
- Visual C++ Redistributable 2015-2022

### 📸 Captures d'écran

<div align="center">
<table>
<tr>
<td><img src="screenshots/main.png" alt="Interface Principale" width="300"/></td>
<td><img src="screenshots/settings.png" alt="Fenêtre des Paramètres" width="300"/></td>
</tr>
<tr>
<td align="center">Interface Principale</td>
<td align="center">Fenêtre des Paramètres</td>
</tr>
</table>
</div>

### ✨ Fonctionnalités Principales

#### Gestion d'Énergie
- **Profils d'Alimentation Intelligents**
  - Framework 13 (7640U/7840U):
    - Silencieux/ECO (TDP 15W)
    - Équilibré (TDP 30W)
    - Boost (TDP 60W)
  - Framework 16 (7840HS/7940HS):
    - Silencieux/ECO (TDP 30W)
    - Équilibré (TDP 95W)
    - Boost (TDP 120W)

#### Contrôle de l'Affichage
- **Gestion Dynamique du Taux de Rafraîchissement**
  - Commutation automatique selon l'alimentation
  - Framework 13 : 60Hz/120Hz
  - Framework 16 : 60Hz/165Hz
- **Contrôle de la Luminosité**
  - Ajustement matériel
  - Support des raccourcis

#### Optimisation de la Batterie
- **Contrôle Avancé de la Charge**
  - Limite de charge personnalisable (60-100%)
  - Optimisation de la longévité
  - Surveillance en temps réel

#### Surveillance Système
- **Métriques de Performance en Temps Réel**
  - Utilisation et température CPU
  - Utilisation de la RAM
  - Suivi de la consommation

#### Expérience Utilisateur
- **Interface Moderne**
  - Intégration dans la barre des tâches
  - Raccourci global (F12)
  - Design épuré et intuitif
- **Détection Automatique du Modèle**
  - Identification basée sur le CPU
  - Configuration automatique des profils

### 🛠️ Détails Techniques

#### Dépendances
```python
customtkinter==5.2.0    # Composants UI modernes
Pillow==10.0.0         # Traitement d'images
psutil==5.9.5          # Surveillance système
pywin32==306           # Intégration Windows
requests==2.31.0       # Opérations réseau
wmi==1.5.1             # Info matériel
keyboard==0.13.5       # Support raccourcis
pystray==0.19.4        # Intégration barre des tâches
```

#### Architecture
- **Composants Principaux**
  - `SystemMonitor`: Surveillance matérielle
  - `MiniFrameworkHub`: Logique principale
  - `SettingsWindow`: Configuration
  - `UpdateWindow`: Gestion des mises à jour (WIP)

#### Technologies Clés
- Intégration RyzenADJ pour la gestion d'énergie
- WMI pour l'interaction matérielle
- Interface moderne basée sur CTk
- Système de surveillance multi-thread

### 📥 Installation

1. Téléchargez la dernière version
2. Exécutez l'installateur en tant qu'administrateur
3. Accédez via :
   - Raccourci bureau
   - Menu démarrer
   - Barre des tâches (F12)

### 🔧 Utilisation

1. **Lancement** : Appuyez sur F12 ou utilisez l'icone de la barre des tâches
2. **Configuration** :
   - Sélectionnez le modèle (détection auto)
   - Choisissez le profil d'alimentation
   - Réglez le taux de rafraîchissement
   - Ajustez les limites de batterie
3. **Surveillance** : Suivez les performances en temps réel

### 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à soumettre des problèmes et des pull requests.

### ❤️ Soutenir le projet

Si vous trouvez Framework Hub Mini utile et que vous souhaitez contribuer à son développement, vous pouvez devenir mécène ! Votre soutien m'aide à maintenir et améliorer le projet, tout en gardant mes chats bien nourris 😺

[![Devenez mécène](https://img.shields.io/badge/Patreon-Soutenez%20le%20projet-FF424D?style=for-the-badge&logo=patreon)](https://patreon.com/Oganoth?utm_medium=unknown&utm_source=join_link&utm_campaign=creatorshare_creator&utm_content=copyLink)

Un immense merci à tous les mécènes qui rendent ce projet possible ! ❤️
