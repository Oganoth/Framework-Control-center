# Framework Laptop Hub PY Edition | Hub Framework PY Edition

[English](#english) | [Français](#français)

![Framework Laptop Hub](main.png)

![Framework Hub Screenshot](https://github.com/Oganoth/Framework-Hub-PY/blob/main/Screens/Capture%20d'écran%202024-12-16%20192147.png)

## English

A powerful control center for Framework laptops running Windows. This application provides comprehensive system monitoring and power management capabilities, specifically designed for Framework laptop users.

### 🚀 Download

Get the latest release from the [GitHub Releases page](https://github.com/Oganoth/Framework-Hub-PY/releases/tag/latest).

### 🚀 Features

- **System Monitoring**: Real-time tracking of:
  - CPU usage and temperature
  - GPU status and performance
  - RAM utilization
  - Storage information
- **Power Profiles**: 
  - Silent: Optimized for quiet operation
  - Balanced: Default profile for everyday use
  - Performance: Maximum power mode
  - Custom: Create your own profile
- **Multi-language Support**:
  - English
  - French
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
2. Select your preferred power profile
3. Monitor system performance in the System tab
4. Customize settings as needed

### 📝 Note

Administrator privileges are required for certain features.

### ⚠️ Known Issues

- **Performance Monitoring**: CPU and GPU usage metrics may occasionally show delayed or incorrect updates
- **System Requirements**: The application requires administrator privileges for full functionality

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

### 🚀 Téléchargement

Téléchargez la dernière version depuis la [page des versions GitHub](https://github.com/Oganoth/Framework-Hub-PY/releases/tag/latest).

### 🚀 Fonctionnalités

- **Surveillance Système**: Suivi en temps réel de :
  - Utilisation et température du CPU
  - État et performance du GPU
  - Utilisation de la RAM
  - Informations sur le stockage
- **Profils d'Alimentation**: 
  - Silencieux : Optimisé pour un fonctionnement discret
  - Équilibré : Profil par défaut pour une utilisation quotidienne
  - Performance : Mode puissance maximale
  - Personnalisé : Créez votre propre profil
- **Support Multilingue**:
  - Anglais
  - Français
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
2. Sélectionnez votre profil d'alimentation préféré
3. Surveillez les performances système dans l'onglet Système
4. Personnalisez les paramètres selon vos besoins

### 📝 Note

Les privilèges administrateur sont nécessaires pour certaines fonctionnalités.

### ⚠️ Problèmes Connus

- **Surveillance des Performances**: Les mesures d'utilisation du CPU et du GPU peuvent parfois montrer des mises à jour retardées ou incorrectes
- **Prérequis Système**: L'application nécessite des privilèges administrateur pour une fonctionnalité complète

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