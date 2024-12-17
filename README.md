# Framework Laptop Hub PY Edition | Hub Framework PY Edition

[English](#english) | [Français](#français)

![Framework Laptop Hub](main.png)

![Framework Hub Screenshot](https://github.com/Oganoth/Framework-Hub-PY/blob/main/Screens/Capture%20d'écran%202024-12-16%20192147.png)

## English

A powerful control center for Framework laptops running Windows. This application provides comprehensive system monitoring and power management capabilities, specifically designed for Framework laptop users.

### 🚀 What's New in Version 1.1

- **New Hardware Support**:
  - Added support for Framework Laptop 13 AMD
  - Added support for Framework Laptop 16 AMD
  - Optimized power profiles for each model
- **Enhanced Power Management**:
  - Refined power profiles with model-specific optimizations
  - Improved TDP control for better performance/battery balance
  - Added ECO mode for maximum battery life
- **UI Improvements**:
  - New compact 2-column layout
  - Dark/Light theme support with proper system integration
  - Improved performance monitoring display
- **Language Support**:
  - Added German and Spanish localizations
  - Improved translations across all languages
- **Technical Improvements**:
  - Better RyzenADJ integration
  - Improved error handling and stability
  - Reduced memory usage

### 🚀 Features

- **System Monitoring**: Real-time tracking of:
  - CPU usage and temperature
  - GPU status and performance
  - RAM utilization
  - Storage information

- **Framework 13 AMD Power Profiles**: 
  - Silent/ECO: Optimized for quiet operation and battery life (15W TDP)
  - Balanced: Optimal balance of performance and power (30W TDP)
  - Performance: Maximum power mode (up to 60W TDP)
  - Custom: Create your own profile

- **Framework 16 AMD Power Profiles**:
  - Silent/ECO: Battery-focused profile (30W TDP)
  - Balanced: High-performance balance (95W TDP)
  - Performance: Maximum power with GPU boost (up to 120W TDP)
  - Custom: Create your own profile

- **Hardware-Specific Features**:
  - Framework 13 AMD:
    - Optimized for mobility and battery life
    - Power management for Ryzen 7 7840U
    - TDP control affecting integrated GPU performance
  - Framework 16 AMD:
    - Combined CPU/GPU power management
    - Thermal profiles affecting both CPU and GPU
    - Power limit controls impacting GPU performance

- **Multi-language Support**:
  - English
  - French
  - German
  - Spanish

- **Theme Support**:
  - Light theme
  - Dark theme
  - System theme integration

- **Settings Persistence**: All preferences saved in JSON format

### 🔧 Requirements

```
customtkinter==5.2.0
Pillow==10.0.0
psutil==5.9.5
pywin32==306
requests==2.31.0
wmi==1.5.1
json5==0.9.14
```

### 📥 Installation

#### Option 1: Using the Installer (Recommended)
1. Download the latest release archive (.7z) from the [releases page](https://github.com/Oganoth/Framework-Hub-PY/releases/tag/latest)
2. Extract the downloaded .7z file using [7-Zip](https://www.7-zip.org/) to a location of your choice
3. Navigate to the extracted folder and run `Framework_Laptop_Hub_Setup.exe`
4. If prompted by Windows Security, click "More Info" and then "Run Anyway"
5. Follow the installation wizard:
   - Choose your installation directory (default is recommended)
   - Wait for the installation to complete
   - Click "Finish" to close the installer
6. Launch Framework Laptop Hub from:
   - The desktop shortcut
   - The Start menu
   - Or directly from the installation folder

**Note**: Administrator privileges are required for installation.

#### Option 2: Manual Installation
1. Clone this repository
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python framework_laptop_hub.py
   ```

### ⚙️ Usage

1. Launch the application
2. Select your Framework laptop model
3. Choose your preferred power profile
4. Monitor system performance in real-time
5. Customize theme and language settings as needed

### 📝 Note

Administrator privileges are required for power management features.

### ⚠️ Known Issues

- **Performance Monitoring**: CPU and GPU usage metrics may occasionally show delayed updates
- **System Requirements**: The application requires administrator privileges for full functionality
- **Theme Switching**: Occasional UI refresh needed after theme changes

### ❤️ Acknowledgments

I want to express my sincere gratitude to:

- **[JamesCJ60](https://github.com/JamesCJ60)** - For the initial idea and inspiration for this project. Since I'm not proficient in C#, I recreated my own version in Python.

- **RyzenADJ Implementation Contributors**:
  - [1MrEnot](https://github.com/1MrEnot)
  - [eltociear](https://github.com/eltociear)
  - [KWagnerCS](https://github.com/KWagnerCS)
  For their valuable insights and ideas on RyzenADJ implementation.

- **[FlyGoat](https://github.com/FlyGoat)** - For creating RyzenADJ, which served as a foundation for power management features.

---

## Français

Un centre de contrôle puissant pour les ordinateurs portables Framework sous Windows. Cette application offre une surveillance complète du système et des capacités de gestion d'énergie, spécialement conçue pour les utilisateurs d'ordinateurs Framework.

### 🚀 Nouveautés de la Version 1.1

- **Support de Nouveaux Matériels**:
  - Ajout du support pour Framework Laptop 13 AMD
  - Ajout du support pour Framework Laptop 16 AMD
  - Profils d'alimentation optimisés pour chaque modèle
- **Gestion d'Énergie Améliorée**:
  - Profils d'alimentation affinés avec optimisations spécifiques par modèle
  - Contrôle TDP amélioré pour un meilleur équilibre performance/batterie
  - Ajout du mode ECO pour une autonomie maximale
- **Améliorations de l'Interface**:
  - Nouvelle disposition compacte à 2 colonnes
  - Support des thèmes clair/sombre avec intégration système
  - Affichage amélioré du monitoring de performance
- **Support Linguistique**:
  - Ajout des localisations allemande et espagnole
  - Traductions améliorées dans toutes les langues
- **Améliorations Techniques**:
  - Meilleure intégration de RyzenADJ
  - Gestion des erreurs et stabilité améliorées
  - Utilisation mémoire réduite

### 🚀 Fonctionnalités

- **Surveillance Système**: Suivi en temps réel de :
  - Utilisation et température du CPU
  - État et performance du GPU
  - Utilisation de la RAM
  - Informations sur le stockage

- **Profils d'Alimentation Framework 13 AMD**: 
  - Silencieux/ECO : Optimisé pour un fonctionnement discret et l'autonomie (TDP 15W)
  - Équilibré : Équilibre optimal entre performance et consommation (TDP 30W)
  - Performance : Mode puissance maximale (jusqu'à 60W TDP)
  - Personnalisé : Créez votre propre profil

- **Profils d'Alimentation Framework 16 AMD**:
  - Silencieux/ECO : Profil orienté autonomie (TDP 30W)
  - Équilibré : Équilibre haute performance (TDP 95W)
  - Performance : Puissance maximale avec boost GPU (jusqu'à 120W TDP)
  - Personnalisé : Créez votre propre profil

- **Fonctionnalités Spécifiques au Matériel**:
  - Framework 13 AMD :
    - Optimisé pour la mobilité et l'autonomie
    - Gestion d'énergie pour Ryzen 7 7840U
    - Contrôle TDP affectant les performances du GPU intégré
  - Framework 16 AMD :
    - Gestion d'énergie combinée CPU/GPU
    - Profils thermiques affectant CPU et GPU
    - Contrôles de puissance impactant les performances GPU

- **Support Multilingue**:
  - Anglais
  - Français
  - Allemand
  - Espagnol

- **Support des Thèmes**:
  - Thème clair
  - Thème sombre
  - Intégration avec le thème système

- **Persistance des Paramètres**: Toutes les préférences sauvegardées au format JSON

### 🔧 Prérequis

```
customtkinter==5.2.0
Pillow==10.0.0
psutil==5.9.5
pywin32==306
requests==2.31.0
wmi==1.5.1
json5==0.9.14
```

### 📥 Installation

#### Option 1 : Utiliser l'installateur (Recommandé)
1. Téléchargez la dernière archive (.7z) depuis la [page des versions](https://github.com/Oganoth/Framework-Hub-PY/releases/tag/latest)
2. Extrayez le fichier .7z téléchargé avec [7-Zip](https://www.7-zip.org/) à l'emplacement de votre choix
3. Naviguez vers le dossier extrait et exécutez `Framework_Laptop_Hub_Setup.exe`
4. Si Windows Security vous avertit, cliquez sur "Plus d'infos" puis "Exécuter quand même"
5. Suivez l'assistant d'installation :
   - Choisissez votre répertoire d'installation (par défaut recommandé)
   - Attendez que l'installation se termine
   - Cliquez sur "Terminer" pour fermer l'installateur
6. Lancez Framework Laptop Hub depuis :
   - Le raccourci sur le bureau
   - Le menu Démarrer
   - Ou directement depuis le dossier d'installation

**Note** : Les privilèges administrateur sont nécessaires pour l'installation.

#### Option 2 : Installation manuelle
1. Clonez ce dépôt
2. Installez les packages requis :
   ```
   pip install -r requirements.txt
   ```
3. Lancez l'application :
   ```
   python framework_laptop_hub.py
   ```

### ⚙️ Utilisation

1. Lancez l'application
2. Sélectionnez votre modèle de Framework laptop
3. Choisissez votre profil d'alimentation préféré
4. Surveillez les performances système en temps réel
5. Personnalisez le thème et la langue selon vos préférences

### 📝 Note

Les privilèges administrateur sont nécessaires pour les fonctionnalités de gestion d'énergie.

### ⚠️ Problèmes Connus

- **Surveillance des Performances**: Les mesures d'utilisation du CPU et du GPU peuvent parfois montrer des mises à jour retardées
- **Prérequis Système**: L'application nécessite des privilèges administrateur pour une fonctionnalité complète
- **Changement de Thème**: Rafraîchissement occasionnel de l'interface nécessaire après les changements de thème

### ❤️ Remerciements

Je tiens à exprimer ma sincère gratitude à :

- **[JamesCJ60](https://github.com/JamesCJ60)** - Pour l'idée initiale et l'inspiration de ce projet. N'étant pas compétent en C#, j'ai recréé ma propre version en Python.

- **Contributeurs à l'implémentation RyzenADJ** :
  - [1MrEnot](https://github.com/1MrEnot)
  - [eltociear](https://github.com/eltociear)
  - [KWagnerCS](https://github.com/KWagnerCS)
  Pour leurs précieuses idées sur l'implémentation de RyzenADJ.

- **[FlyGoat](https://github.com/FlyGoat)** - Pour la création de RyzenADJ, qui a servi de base aux fonctionnalités de gestion d'énergie.

---

## Contributing | Contribution

Feel free to submit issues and enhancement requests! | N'hésitez pas à soumettre des problèmes et des demandes d'amélioration !