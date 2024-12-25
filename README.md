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
  <img src="screenshots/main.png" width="400" alt="Main Interface"/>

  <img src="screenshots/Updates%20manager.png" width="400" alt="Updates Manager"/>
</p>
<p float="left">
  <img src="screenshots/Tweaks.png" width="400" alt="System Tweaks"/>

  <em>Framework Hub Mini in action - Control, Monitor, and Optimize your laptop</em>
</p>
</div>

### ✨ Key Features

<details>
<summary>🔋 Power Management</summary>

#### Advanced Power Profiles
- **Framework 13 AMD (7640U/7840U)**:
  - Silent/ECO (15W TDP)
  - Balanced (25W TDP)
  - Boost (28W TDP)
- **Framework 16 AMD (7840HS/7940HS)**:
  - Silent/ECO (30W TDP)
  - Balanced (95W TDP)
  - Boost (120W TDP)
- **Framework 13 Intel** (WIP):
  - Silent (PL1: 10W, PL2: 15W)
  - Balanced (PL1: 20W, PL2: 40W)
  - Boost (PL1: 28W, PL2: 55W)
</details>

<details>
<summary>💻 Hardware Control</summary>

- **CPU Management**
  - Real-time frequency control 
  - Temperature monitoring
  - Core parking optimization
- **GPU Control**
  - iGPU frequency management
  - Temperature monitoring
- **Fan Control**
  - Custom fan curves
  - Temperature-based adjustment
</details>

<details>
<summary>🖥️ Display Management</summary>

- **Advanced Display Control**
  - Dynamic refresh rate (60Hz-165Hz)
  - Power-source based automation
  - Brightness control with hotkeys
- **Multi-Monitor Support**
  - External display detection
  - Resolution management
</details>

<details>
<summary>⚡ System Optimization</summary>

- **Performance Monitoring**
  - Real-time CPU/GPU metrics
  - Power consumption tracking
  - Temperature monitoring
- **Power Optimization**
  - Battery charge limiting
  - Power plan automation
</details>

### 🛠️ Technical Details

<details>
<summary>View Dependencies</summary>

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
</details>

### 🔧 Installation

<details>
<summary>View Installation Steps</summary>

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
</details>

### 📋 Usage

<details>
<summary>View Usage Guide</summary>

1. **First Launch**
   - Run as administrator
   - Hardware detection is automatic
   - Initial configuration wizard

2. **Daily Use**
   - Access via system tray
   - Quick profile switching
   - Real-time monitoring

3. **Advanced Features**
   - Create custom power profiles
   - Configure fan curves
   - Set up automation rules
</details>

### 🤝 Contributing

<details>
<summary>How to Contribute</summary>

We welcome all contributions! Here's how you can help:

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
</details>

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

## Français

### 🎯 Aperçu

Framework Hub Mini est un outil puissant de gestion système conçu spécifiquement pour les ordinateurs portables Framework AMD. Développé en Python avec des composants d'interface moderne, il offre un contrôle complet sur la gestion de l'alimentation, l'optimisation des performances et la surveillance du matériel.

### 📸 Captures d'écran

<div align="center">
<p float="left">
  <img src="screenshots/main.png" width="400" alt="Interface Principale"/>
  <img src="screenshots/Updates%20manager.png" width="400" alt="Gestionnaire de mises à jour"/>
</p>
<p float="left">
  <img src="screenshots/Tweaks.png" width="400" alt="Ajustements système"/>
  <em>Framework Hub Mini en action - Contrôlez, Surveillez et Optimisez votre ordinateur portable</em>
</p>
</div>

### ✨ Fonctionnalités Principales

<details>
<summary>🔋 Gestion de l'Alimentation</summary>

#### Profils de Puissance Avancés
- **Framework 13 AMD (7640U/7840U)**:
![Gestionnaire de mises à jour](screenshots/Updates%20manager.png)

*Gestionnaire de mises à jour - Gardez votre système à jour*

![Ajustements système](screenshots/Tweaks.png)

*Ajustements système - Affinez les paramètres de votre ordinateur portable*

</div>

### ✨ Fonctionnalités Principales

#### Gestion de l'Alimentation
- **Profils de Puissance Avancés**
  - Framework 13 AMD (7640U/7840U):
    - Silencieux/ECO (15W TDP)
    - Équilibré (25W TDP)
    - Performance (28W TDP)
  - Framework 16 AMD (7840HS/7940HS):
    - Silencieux/ECO (30W TDP)
    - Équilibré (95W TDP)
    - Performance (120W TDP)
  - Framework 13 Intel (En développement):
    - Silencieux (PL1: 10W, PL2: 15W)
    - Équilibré (PL1: 20W, PL2: 40W)
    - Performance (PL1: 28W, PL2: 55W)
- **Plans d'Alimentation Personnalisés**
  - Création et sauvegarde de configurations TDP personnalisées (Temporairement désactivé)
  - Réglage fin des limites de puissance CPU et GPU (Temporairement désactivé)
  - Gestion des profils basée sur l'utilisation

#### Contrôle Matériel
- **Gestion du CPU**
  - Contrôle de fréquence en temps réel
  - Surveillance de la température
  - Optimisation du parking des cœurs
  - Ajustements spécifiques à la plateforme
- **Contrôle du GPU**
  - Gestion de la fréquence iGPU (et dGPU si disponible)
  - Surveillance de la température
- **Contrôle des Ventilateurs**
  - Courbes personnalisées
  - Ajustement basé sur la température
  - Optimisation du mode silencieux

#### Gestion de l'Affichage
- **Contrôle Avancé de l'Affichage**
  - Changement dynamique du taux de rafraîchissement (60Hz-165Hz)
  - Automatisation basée sur la source d'alimentation
  - Contrôle de la luminosité avec raccourcis
  - Gestion HDR
- **Support Multi-Écrans**
  - Détection des écrans externes
  - Gestion de la résolution
  - Synchronisation du taux de rafraîchissement

#### Optimisation Système
- **Surveillance des Performances**
  - Métriques CPU/GPU en temps réel
  - Suivi de la consommation d'énergie
  - Surveillance de la température
  - Analyse de l'utilisation de la mémoire
- **Optimisation Énergétique**
  - Limitation de charge de la batterie
  - Automatisation des plans d'alimentation
  - Gestion des états de veille
  - Optimisation de la consommation en temps réel

#### Fonctionnalités Additionnelles
- **Intégration dans la Barre des Tâches**
  - Accès rapide aux paramètres courants
  - Indicateurs d'état
  - Changement de profil
- **Support des Raccourcis**
  - Raccourcis personnalisables
  - Changement de profil
  - Gestion de l'affichage
- **Support Multi-Langues**
  - Anglais (par défaut)
  - Français
  - Espagnol
  - Allemand
  - Italien
  - Chinois
  - Klingon
- **Mises à Jour Automatiques**
  - Mises à jour des pilotes
  - Mises à jour logicielles
  - Optimisation des profils

### 🔧 Installation

1. **Prérequis**
   - Windows 11 (22H2 ou plus récent)
   - Privilèges administrateur
   - .NET Framework 4.8
   - Visual C++ Redistributable 2015-2022

2. **Options d'Installation**

   #### Édition Python (Open Source)
   - Nécessite Python 3.10+
   ```bash
   # Cloner le dépôt
   git clone https://github.com/Oganoth/Framework-Hub-PY.git
   cd Framework-Hub-PY

   # Installer les dépendances
   pip install -r requirements.txt

   # Lancer l'application
   python main.py
   ```

   #### Framework-Hub.exe (Installation Facile)
   - Installateur tout-en-un disponible sur [Patreon](https://patreon.com/Oganoth)
   - Pas besoin de Python ni de dépendances
   - Installation en un clic

### 📋 Utilisation

1. **Premier Lancement**
   - Exécuter en tant qu'administrateur
   - Détection automatique du matériel
   - Assistant de configuration initial

2. **Utilisation Quotidienne**
   - Accès via la barre des tâches
   - Changement rapide de profil
   - Surveillance en temps réel
   - Gestion des profils personnalisés

3. **Fonctionnalités Avancées**
   - Création de profils de puissance personnalisés
   - Configuration des courbes de ventilation
   - Configuration des règles d'automatisation
   - Gestion des paramètres d'affichage

### 🤝 Contribution

Nous accueillons toutes les contributions pour améliorer Framework Hub Mini ! Voici comment vous pouvez aider :

#### Contributions au Code
- Forker le dépôt
- Créer une branche de fonctionnalité
- Ajouter vos améliorations
- Soumettre une pull request

#### Autres Façons d'Aider
- Signaler des bugs et problèmes
- Suggérer de nouvelles fonctionnalités
- Améliorer la documentation
- Partager vos profils de puissance
- Aider aux traductions
- Tester sur différents modèles Framework

Rejoignez notre communauté et aidez à rendre Framework Hub Mini encore meilleur !

### ❤️ Support

Si vous trouvez Framework Hub Mini utile, vous pouvez :
- Mettre une étoile au dépôt
- Signaler des bugs
- Contribuer au code
- Faire connaître le projet

### 📜 Soutien sur Patreon

Framework Hub Mini est un projet passionnant qui nécessite beaucoup de temps et d'efforts pour être maintenu et amélioré. Votre soutien sur [Patreon](https://patreon.com/Oganoth) m'aide à consacrer plus de temps à :
- Développer de nouvelles fonctionnalités
- Améliorer les fonctionnalités existantes
- Fournir un support plus rapide
- Tester sur différentes configurations matérielles
- Créer une meilleure documentation

En devenant mécène, vous obtenez également :
- La version avec installateur facile à utiliser
- Un support prioritaire
- Un accès anticipé aux nouvelles fonctionnalités
- La possibilité de voter pour les futures fonctionnalités
- Des informations exclusives sur le développement

[![Devenir Mécène](https://img.shields.io/badge/Patreon-Soutenir%20Framework%20Hub-FF424D?style=for-the-badge&logo=patreon)](https://patreon.com/Oganoth)

Un grand merci à tous les mécènes qui rendent ce projet possible ! ❤️

### 📜 Licence

Ce projet est sous licence GNU General Public License v3.0 - voir le fichier [LICENSE](LICENSE) pour plus de détails.

### ❤️ Remerciements

Un grand merci à :

#### Mes Formidables Mécènes
- Jonathan Webber

#### La Communauté Framework
Merci à tous les membres de la communauté Framework qui ont aidé à tester, fournir des retours et soutenir ce projet.

#### Remerciements Spéciaux
- Nirav Patel pour le soutien à venir
- Tous les contributeurs qui ont aidé à améliorer ce projet
