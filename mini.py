import json
import os
import sys
import ctypes
import keyboard
import pystray
from PIL import Image
import customtkinter as ctk
from pathlib import Path
import webbrowser
from threading import Thread
import time
import logging
import psutil
from typing import Dict, Any, Optional, List
import subprocess

from translations import TRANSLATIONS
from settings_window import SettingsWindow
from hardware_manager import HardwareManager
from ui_manager import UIManager
from power_manager import PowerManager
from update_window import UpdateWindow

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mini_hub.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MiniFrameworkHub(ctk.CTk):
    def __init__(self):
        try:
            # D'abord initialiser la classe parent
            super().__init__()
            
            # Forcer la fenêtre au premier plan
            self.attributes('-topmost', True)
            
            # Initialiser les icônes de notification
            self.error_icon = None  # À initialiser dans setup_tray()
            self.info_icon = None   # À initialiser dans setup_tray()
            self.notification_icon = None  # À initialiser dans setup_tray()
            
            # Ensuite configurer le logging
            self._setup_logging()
            logger.info("Initialisation de MiniFrameworkHub")
            
            # Configurer les bibliothèques
            from setup_libs import setup_monitoring_libs
            if not setup_monitoring_libs():
                raise RuntimeError("Impossible de configurer les bibliothèques de monitoring")
            
            # Variables pour le déplacement de la fenêtre
            self._drag_start_x = 0
            self._drag_start_y = 0
            
            # Force English as default language
            self.current_language = "en"
            self.translations = TRANSLATIONS["en"]
            
            # Load settings (but keep English if no language is set)
            self.settings = self.load_settings()
            if "language" in self.settings:
                saved_lang = self.settings["language"]
                if saved_lang in TRANSLATIONS and saved_lang != "en":
                    self.current_language = saved_lang
                    self.translations = TRANSLATIONS[saved_lang]
            else:
                self.settings["language"] = "en"
                self.save_settings()
            
            # Initialisation des gestionnaires
            self.hardware_manager = HardwareManager()
            self.ui_manager = UIManager(self, self.settings, self.translations)
            self.power_manager = PowerManager(self.settings)
            
            # Configuration de l'interface
            self.ui_manager.setup_window("Framework Mini Hub", "300x650")
            
            # Initialisation du modèle
            self.model_var = ctk.StringVar()
            self._init_model()
            
            # Configuration système
            self.setup_tray()
            self.setup_hotkey()
            self.create_widgets()
            
            # Démarrage du monitoring
            self.start_monitoring()
            
            # Appliquer le profil Balanced au démarrage
            self.apply_profile("Balanced")
            
            # Mettre en évidence le bouton Balanced
            if hasattr(self, 'profile_buttons'):
                for profile, button in self.profile_buttons.items():
                    if profile == "Balanced":
                        button.configure(fg_color="#FF4B1F")  # Couleur active
                    else:
                        button.configure(fg_color="#FF7F5C")  # Couleur normale
            
            # Cacher la fenêtre au démarrage
            self.withdraw()
            logger.info("Initialisation terminée")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation: {str(e)}", exc_info=True)
            raise
            
    def _setup_logging(self):
        """Configure le système de logging"""
        try:
            # Vérifier si le handler existe déjà
            if not logger.handlers:
                # Configuration du logging
                file_handler = logging.FileHandler('mini_hub.log')
                console_handler = logging.StreamHandler()
                
                formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                file_handler.setFormatter(formatter)
                console_handler.setFormatter(formatter)
                
                logger.addHandler(file_handler)
                logger.addHandler(console_handler)
                logger.setLevel(logging.DEBUG)
                
        except Exception as e:
            print(f"Erreur lors de la configuration du logging: {e}")
            raise
            
    def verify_ryzenadj_profiles(self) -> bool:
        """Vérifie les profils RyzenADJ"""
        try:
            logger.info("Vérification des profils RyzenADJ...")
            
            # Vérifier si RyzenADJ est disponible
            ryzenadj_path = self.power_manager.get_ryzenadj_path()
            if not os.path.exists(ryzenadj_path):
                logger.error(f"RyzenADJ non trouvé à {ryzenadj_path}")
                self.show_notification(
                    "Erreur",
                    "RyzenADJ non trouvé. Les profils de puissance ne fonctionneront pas.",
                    error=True
                )
                return False
            
            # Tester chaque profil
            model = self.model_var.get() if hasattr(self, 'model_var') else "Framework 13 AMD"
            profiles = ["Silent", "Balanced", "Boost"]
            
            for profile in profiles:
                logger.info(f"Test du profil {profile}...")
                success = self.power_manager.apply_profile(profile, model, test_mode=True)
                
                if not success:
                    logger.error(f"Échec de l'application du profil {profile}")
                    self.show_notification(
                        "Erreur",
                        f"Le profil {profile} n'a pas pu être appliqué.",
                        error=True
                    )
                    return False
                
            logger.info("Tous les profils RyzenADJ ont été vérifiés avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des profils RyzenADJ: {e}")
            self.show_notification(
                "Erreur",
                "Erreur lors de la vérification des profils RyzenADJ",
                error=True
            )
            return False
            
    def _init_model(self) -> None:
        """Initialise le modèle de l'ordinateur"""
        try:
            cpu_info = self.hardware_manager.cpu_info
            if cpu_info:
                model = "Framework 16 AMD" if cpu_info['model'] == "model_16" else "Framework 13 AMD"
                self.model_var.set(model)
                logger.info(f"Modèle détecté: {model}")
            else:
                self.model_var.set("Framework 13 AMD")
                logger.warning("Impossible de détecter le modèle, utilisation du modèle par défaut")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du modèle: {e}")
            self.model_var.set("Framework 13 AMD")
            
    def load_settings(self) -> Dict[str, Any]:
        """Charge les paramètres depuis le fichier settings.json"""
        default_settings = {
            "language": "en",
            "theme": "dark",
            "ryzenadj_profile": "Balanced",
            "laptop_model": "model_13_amd",
            "last_refresh_rate": "Auto",
            "window_position": None
        }
        
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    loaded_settings = json.load(f)
                    merged_settings = default_settings.copy()
                    merged_settings.update(loaded_settings)
                    logger.info(f"Paramètres chargés: {merged_settings}")
                    return merged_settings
        except Exception as e:
            logger.error(f"Erreur lors du chargement des paramètres: {e}")
            
        logger.info("Utilisation des paramètres par défaut")
        return default_settings
        
    def save_settings(self) -> None:
        """Sauvegarde les paramètres"""
        try:
            with open("settings.json", "w") as f:
                json.dump(self.settings, f, indent=4)
            logger.info("Paramètres sauvegardés")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des paramètres: {e}")
            
    def setup_tray(self) -> None:
        """Configure l'icône de la barre des tâches"""
        try:
            # Obtenir le chemin absolu des icônes
            if getattr(sys, 'frozen', False):
                # Si on est dans un exe PyInstaller
                base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            else:
                # Si on est en développement
                base_path = os.path.dirname(os.path.abspath(__file__))
                
            # Charger les icônes
            tray_icon_path = os.path.join(base_path, 'assets', 'tray_icon.png')
            error_icon_path = os.path.join(base_path, 'assets', 'error_icon.png')
            info_icon_path = os.path.join(base_path, 'assets', 'info_icon.png')
            
            # Vérifier que les fichiers existent
            if not all(os.path.exists(p) for p in [tray_icon_path, error_icon_path, info_icon_path]):
                raise FileNotFoundError("Fichiers d'icônes manquants")
            
            # Charger les images
            self.error_icon = Image.open(error_icon_path)
            self.info_icon = Image.open(info_icon_path)
            tray_icon = Image.open(tray_icon_path)
            
            # Créer le menu
            menu = (
                pystray.MenuItem(self.tr("show"), self.show_window),
                pystray.MenuItem(self.tr("settings"), self.open_settings),
                pystray.MenuItem(self.tr("quit"), self.quit_app)
            )
            
            # Créer l'icône
            self.notification_icon = pystray.Icon(
                "Framework Hub",
                tray_icon,
                "Framework Hub",
                menu
            )
            
            # Démarrer l'icône dans un thread séparé
            Thread(target=self.notification_icon.run, daemon=True).start()
            
            logger.info("Icône de la barre des tâches configurée avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration de l'icône: {e}")
            self.notification_icon = None
            
    def setup_hotkey(self) -> None:
        """Configure le raccourci clavier"""
        try:
            keyboard.add_hotkey('F12', self.toggle_window, suppress=True)
            logger.info("Raccourci clavier configuré")
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du raccourci clavier: {e}")
            
    def create_widgets(self) -> None:
        """Crée les widgets de l'interface"""
        try:
            # Frame de sélection du modèle
            model_frame = self.ui_manager.create_frame("model")
            model_frame.pack(fill="x", padx=10, pady=5)
            
            # Menu de sélection du modèle
            model_menu = ctk.CTkOptionMenu(
                model_frame,
                values=["Framework 13 AMD", "Framework 16 AMD"],
                command=self.change_laptop_model,
                variable=self.model_var,
                fg_color=self.ui_manager.colors['button'],
                button_color=self.ui_manager.colors['button'],
                button_hover_color=self.ui_manager.colors['hover'],
                text_color="black",
                height=28
            )
            model_menu.pack(expand=True, padx=5, pady=2)
            
            # Frame des profils
            profile_frame = self.ui_manager.create_frame("profiles")
            profile_frame.pack(fill="x", padx=10, pady=5)
            
            # Container pour centrer les boutons
            button_container = ctk.CTkFrame(profile_frame, fg_color="transparent")
            button_container.pack(expand=True, pady=2)
            
            # Création des boutons de profil avec traduction
            icons = self._load_profile_icons()
            self.profile_buttons = {}
            button_width = 75
            
            for profile in ["silent", "balanced", "boost"]:
                btn = ctk.CTkButton(
                    button_container,
                    text=self.tr(profile),
                    image=icons.get(profile.capitalize()),
                    compound="top",
                    command=lambda p=profile.capitalize(): self.apply_profile(p),
                    width=button_width,
                    height=40,
                    fg_color=self.ui_manager.colors['button'],
                    hover_color=self.ui_manager.colors['hover'],
                    text_color="black",
                    corner_radius=8
                )
                btn.pack(side="left", padx=3)
                self.profile_buttons[profile.capitalize()] = btn
            
            # Frame du taux de rafraîchissement
            screen_frame = self.ui_manager.create_frame("refresh")
            screen_frame.pack(fill="x", padx=10, pady=3)
            
            self.refresh_label = self.ui_manager.create_label(
                screen_frame,
                text=f"{self.tr('refresh_rate')}:",
                anchor="w"
            )
            self.refresh_label.pack(side="left", padx=(5, 0), pady=2)
            
            # Container pour les boutons de rafraîchissement
            self.refresh_container = ctk.CTkFrame(screen_frame, fg_color="transparent")
            self.refresh_container.pack(side="right", padx=(0, 5), pady=2)
            
            # Initialiser les boutons de rafraîchissement
            self.refresh_buttons = {}
            self._update_refresh_rate_buttons()

            # Frame de monitoring système
            stats_frame = self.ui_manager.create_frame("stats")
            stats_frame.pack(fill="x", padx=10, pady=5)
            
            # Créer les widgets de monitoring via UIManager
            monitoring_widgets = self.ui_manager.create_monitoring_widgets(stats_frame)
            
            # Stocker les références aux widgets
            self.cpu_label = monitoring_widgets['cpu_label']
            self.cpu_progress = monitoring_widgets['cpu_progress']
            self.ram_label = monitoring_widgets['ram_label']
            self.ram_progress = monitoring_widgets['ram_progress']
            self.temp_label = monitoring_widgets['temp_label']
            self.temp_progress = monitoring_widgets['temp_progress']
            self.igpu_label = monitoring_widgets['igpu_label']
            self.igpu_progress = monitoring_widgets['igpu_progress']
            self.igpu_temp_label = monitoring_widgets['igpu_temp_label']
            self.igpu_temp_progress = monitoring_widgets['igpu_temp_progress']
            self.dgpu_label = monitoring_widgets['dgpu_label']
            self.dgpu_progress = monitoring_widgets['dgpu_progress']
            self.dgpu_temp_label = monitoring_widgets['dgpu_temp_label']
            self.dgpu_temp_progress = monitoring_widgets['dgpu_temp_progress']
            
            # Frame des actions rapides
            actions_frame = self.ui_manager.create_frame("actions")
            actions_frame.pack(fill="x", padx=10, pady=5)
            
            # Boutons d'action avec traduction
            self.keyboard_button = self.ui_manager.create_button(
                actions_frame,
                text=self.tr("keyboard"),
                command=self.open_keyboard_page,
                height=28
            )
            self.keyboard_button.pack(fill="x", padx=5, pady=2)
            
            self.updates_button = self.ui_manager.create_button(
                actions_frame,
                text=self.tr("updates"),
                command=self.open_updates,
                height=28
            )
            self.updates_button.pack(fill="x", padx=5, pady=2)
            
            self.settings_button = self.ui_manager.create_button(
                actions_frame,
                text=self.tr("settings"),
                command=self.open_settings,
                height=28
            )
            self.settings_button.pack(fill="x", padx=5, pady=2)
            
            # Frame de contrôle de la luminosité
            brightness_frame = self.ui_manager.create_frame("brightness")
            brightness_frame.pack(fill="x", padx=10, pady=(5, 0))
            
            # En-tête avec label et valeur
            header_frame = ctk.CTkFrame(brightness_frame, fg_color="transparent")
            header_frame.pack(fill="x", padx=5, pady=(2, 0))
            
            self.brightness_label = self.ui_manager.create_label(
                header_frame,
                text=f"{self.tr('brightness')}:",
                anchor="w"
            )
            self.brightness_label.pack(side="left")
            
            self.brightness_value_label = self.ui_manager.create_label(
                header_frame,
                text=f"{self.tr('current')}: 50%",
                anchor="e"
            )
            self.brightness_value_label.pack(side="right")
            
            # Slider de luminosité
            self.brightness_slider = ctk.CTkSlider(
                brightness_frame,
                from_=0,
                to=100,
                number_of_steps=100,
                command=self.on_brightness_change,
                button_color=self.ui_manager.colors['button'],
                button_hover_color=self.ui_manager.colors['hover'],
                progress_color=self.ui_manager.colors['button'],
                fg_color=self.ui_manager.colors['progress_bg'],
                height=12
            )
            self.brightness_slider.pack(fill="x", padx=5, pady=(2, 3))
            self.brightness_slider.set(50)
            self.brightness_slider.bind("<ButtonRelease-1>", self.on_brightness_release)
            
            # Frame de contrôle de la batterie
            battery_frame = self.ui_manager.create_frame("battery")
            battery_frame.pack(fill="x", padx=10, pady=3)
            
            self.battery_status = self.ui_manager.create_label(
                battery_frame,
                text=f"{self.tr('battery')}: ",
                anchor="w"
            )
            self.battery_status.pack(side="top", padx=5, pady=(2, 0))
            
            # Slider de limite de charge
            self.charge_slider = ctk.CTkSlider(
                battery_frame,
                from_=60,
                to=100,
                number_of_steps=40,
                command=self.on_charge_slider_change,
                button_color=self.ui_manager.colors['button'],
                button_hover_color=self.ui_manager.colors['hover'],
                progress_color=self.ui_manager.colors['button'],
                fg_color=self.ui_manager.colors['progress_bg'],
                height=12
            )
            self.charge_slider.pack(fill="x", padx=5, pady=(2, 1))
            self.charge_slider.set(80)
            self.charge_slider.bind("<ButtonRelease-1>", self.on_charge_slider_release)
            
            # Label de limite actuelle
            self.limit_label = self.ui_manager.create_label(
                battery_frame,
                text=f"{self.tr('current_limit')}: 80%",
                anchor="e"
            )
            self.limit_label.pack(side="right", padx=5, pady=1)
            
            # Initialiser les valeurs
            self._init_brightness()
            self._init_charge_limit()
            
            # Démarrer le monitoring de la batterie
            self.start_battery_monitor()
            
            logger.info("Widgets créés avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création des widgets: {e}")
            raise
            
    def _create_profile_frame(self) -> None:
        """Crée le frame des profils de puissance"""
        profile_frame = self.ui_manager.create_frame("profiles")
        profile_frame.pack(fill="x", padx=15, pady=10)
        
        # Chargement des icônes
        icons = self._load_profile_icons()
        
        # Container pour centrer les boutons
        button_container = ctk.CTkFrame(profile_frame, fg_color="transparent")
        button_container.pack(expand=True, pady=5)
        
        # Création des boutons de profil
        self.profile_buttons = {}
        button_width = 80
        
        for profile in ["Silent", "Balanced", "Boost"]:
            btn = ctk.CTkButton(
                button_container,
                text=profile,
                image=icons.get(profile),
                compound="top",
                command=lambda p=profile: self.apply_profile(p),
                width=button_width,
                height=50,
                fg_color=self.ui_manager.colors['button'],
                hover_color=self.ui_manager.colors['hover'],
                text_color="black",
                corner_radius=8
            )
            btn.pack(side="left", padx=5)
            self.profile_buttons[profile] = btn
            
    def _load_profile_icons(self) -> Dict[str, ctk.CTkImage]:
        """Charge les icônes des profils"""
        try:
            return {
                "Silent": ctk.CTkImage(
                    light_image=Image.open("assets/eco.png"),
                    dark_image=Image.open("assets/eco.png"),
                    size=(16, 16)
                ),
                "Balanced": ctk.CTkImage(
                    light_image=Image.open("assets/balanced.png"),
                    dark_image=Image.open("assets/balanced.png"),
                    size=(16, 16)
                ),
                "Boost": ctk.CTkImage(
                    light_image=Image.open("assets/performance.png"),
                    dark_image=Image.open("assets/performance.png"),
                    size=(16, 16)
                )
            }
        except Exception as e:
            logger.error(f"Erreur lors du chargement des icônes: {e}")
            return {}
            
    def _create_refresh_rate_frame(self) -> None:
        """Crée le frame du taux de rafraîchissement"""
        screen_frame = self.ui_manager.create_frame("refresh")
        screen_frame.pack(fill="x", padx=15, pady=5)
        
        refresh_label = self.ui_manager.create_label(
            screen_frame,
            text="Taux de rafraîchissement:",
            anchor="w"
        )
        refresh_label.pack(side="left", padx=(10, 0), pady=5)
        
        # Container pour les boutons
        self.refresh_container = ctk.CTkFrame(screen_frame, fg_color="transparent")
        self.refresh_container.pack(side="right", padx=(0, 10), pady=5)
        
        # Création des boutons
        self.refresh_buttons = {}
        rates = ["Auto", "60Hz", "165Hz"]
        
        for rate in rates:
            btn = self.ui_manager.create_button(
                self.refresh_container,
                text=rate,
                command=lambda r=rate: self.set_refresh_rate_wrapper(r),
                width=50,
                height=24
            )
            btn.pack(side="left", padx=2)
            self.refresh_buttons[rate] = btn
            
    def _create_monitoring_frame(self) -> None:
        """Crée le frame de monitoring système"""
        try:
            stats_frame = self.ui_manager.create_frame("stats")
            stats_frame.pack(fill="x", padx=15, pady=10)
            
            # CPU
            cpu_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
            cpu_frame.pack(fill="x", pady=3, padx=10)
            
            self.cpu_label = self.ui_manager.create_label(
                cpu_frame,
                text="CPU: 0%",
                anchor="w"
            )
            self.cpu_label.pack(side="left", padx=5)
            
            self.cpu_bar = self.ui_manager.create_progress_bar(cpu_frame)
            self.cpu_bar.pack(side="right", padx=5, fill="x", expand=True)
            self.cpu_bar.set(0)
            
            # RAM
            ram_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
            ram_frame.pack(fill="x", pady=3, padx=10)
            
            self.ram_label = self.ui_manager.create_label(
                ram_frame,
                text="RAM: 0%",
                anchor="w"
            )
            self.ram_label.pack(side="left", padx=5)
            
            self.ram_bar = self.ui_manager.create_progress_bar(ram_frame)
            self.ram_bar.pack(side="right", padx=5, fill="x", expand=True)
            self.ram_bar.set(0)
            
            # Température CPU
            temp_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
            temp_frame.pack(fill="x", pady=3, padx=10)
            
            self.temp_label = self.ui_manager.create_label(
                temp_frame,
                text="CPU Temp: 0°C",
                anchor="w"
            )
            self.temp_label.pack(side="left", padx=5)
            
            self.temp_bar = self.ui_manager.create_progress_bar(temp_frame)
            self.temp_bar.pack(side="right", padx=5, fill="x", expand=True)
            self.temp_bar.set(0)
            
            # GPU
            gpu_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
            gpu_frame.pack(fill="x", pady=3, padx=10)
            
            self.gpu_label = self.ui_manager.create_label(
                gpu_frame,
                text="GPU: 0%",
                anchor="w"
            )
            self.gpu_label.pack(side="left", padx=5)
            
            self.gpu_bar = self.ui_manager.create_progress_bar(gpu_frame)
            self.gpu_bar.pack(side="right", padx=5, fill="x", expand=True)
            self.gpu_bar.set(0)
            
            # Température GPU
            gpu_temp_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
            gpu_temp_frame.pack(fill="x", pady=3, padx=10)
            
            self.gpu_temp_label = self.ui_manager.create_label(
                gpu_temp_frame,
                text="GPU Temp: 0°C",
                anchor="w"
            )
            self.gpu_temp_label.pack(side="left", padx=5)
            
            self.gpu_temp_bar = self.ui_manager.create_progress_bar(gpu_temp_frame)
            self.gpu_temp_bar.pack(side="right", padx=5, fill="x", expand=True)
            self.gpu_temp_bar.set(0)
            
            # GPU intégré (780M)
            igpu_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
            igpu_frame.pack(fill="x", pady=3, padx=10)
            
            self.igpu_label = self.ui_manager.create_label(
                igpu_frame,
                text="iGPU (780M): 0%",
                anchor="w"
            )
            self.igpu_label.pack(side="left", padx=5)
            
            self.igpu_progress = self.ui_manager.create_progress_bar(igpu_frame)
            self.igpu_progress.pack(side="right", padx=5, fill="x", expand=True)
            self.igpu_progress.set(0)
            
            # Température iGPU
            igpu_temp_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
            igpu_temp_frame.pack(fill="x", pady=3, padx=10)
            
            self.igpu_temp_label = self.ui_manager.create_label(
                igpu_temp_frame,
                text="iGPU Temp: 0°C",
                anchor="w"
            )
            self.igpu_temp_label.pack(side="left", padx=5)
            
            self.igpu_temp_bar = self.ui_manager.create_progress_bar(igpu_temp_frame)
            self.igpu_temp_bar.pack(side="right", padx=5, fill="x", expand=True)
            self.igpu_temp_bar.set(0)
            
            # GPU dédié (7700S)
            dgpu_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
            dgpu_frame.pack(fill="x", pady=3, padx=10)
            
            self.dgpu_label = self.ui_manager.create_label(
                dgpu_frame,
                text="dGPU (7700S): 0%",
                anchor="w"
            )
            self.dgpu_label.pack(side="left", padx=5)
            
            self.dgpu_progress = self.ui_manager.create_progress_bar(dgpu_frame)
            self.dgpu_progress.pack(side="right", padx=5, fill="x", expand=True)
            self.dgpu_progress.set(0)
            
            # Température dGPU
            dgpu_temp_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
            dgpu_temp_frame.pack(fill="x", pady=3, padx=10)
            
            self.dgpu_temp_label = self.ui_manager.create_label(
                dgpu_temp_frame,
                text="dGPU Temp: 0°C",
                anchor="w"
            )
            self.dgpu_temp_label.pack(side="left", padx=5)
            
            self.dgpu_temp_bar = self.ui_manager.create_progress_bar(dgpu_temp_frame)
            self.dgpu_temp_bar.pack(side="right", padx=5, fill="x", expand=True)
            self.dgpu_temp_bar.set(0)
            
            logger.info("Widgets de monitoring créés avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création des widgets de monitoring: {e}")
            raise
        
    def _create_brightness_frame(self) -> None:
        """Crée le frame de contrôle de la luminosité"""
        brightness_frame = self.ui_manager.create_frame("brightness")
        brightness_frame.pack(fill="x", padx=15, pady=(10, 0))
        
        # En-tête avec label et valeur
        header_frame = ctk.CTkFrame(brightness_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(2, 0))
        
        self.ui_manager.create_label(
            header_frame,
            text="Luminosité:",
            anchor="w"
        ).pack(side="left")
        
        self.brightness_value_label = self.ui_manager.create_label(
            header_frame,
            text="Actuel: 50%",
            anchor="e"
        )
        self.brightness_value_label.pack(side="right")
        
        # Slider de luminosité
        self.brightness_slider = ctk.CTkSlider(
            brightness_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self.on_brightness_change,
            button_color=self.ui_manager.colors['button'],
            button_hover_color=self.ui_manager.colors['hover'],
            progress_color=self.ui_manager.colors['button'],
            fg_color=self.ui_manager.colors['progress_bg']
        )
        self.brightness_slider.pack(fill="x", padx=10, pady=(2, 5))
        self.brightness_slider.set(50)
        self.brightness_slider.bind("<ButtonRelease-1>", self.on_brightness_release)
        
    def _create_battery_frame(self) -> None:
        """Crée le frame de contrôle de la batterie"""
        battery_frame = self.ui_manager.create_frame("battery")
        battery_frame.pack(fill="x", padx=15, pady=5)
        
        self.battery_status = self.ui_manager.create_label(
            battery_frame,
            text="Limite de charge:",
            anchor="w"
        )
        self.battery_status.pack(side="top", padx=10, pady=(2, 0))
        
        # Slider de limite de charge
        self.charge_slider = ctk.CTkSlider(
            battery_frame,
            from_=60,
            to=100,
            number_of_steps=40,
            command=self.on_charge_slider_change,
            button_color=self.ui_manager.colors['button'],
            button_hover_color=self.ui_manager.colors['hover'],
            progress_color=self.ui_manager.colors['button'],
            fg_color=self.ui_manager.colors['progress_bg']
        )
        self.charge_slider.pack(fill="x", padx=10, pady=(2, 2))
        self.charge_slider.set(80)  # Valeur par défaut
        self.charge_slider.bind("<ButtonRelease-1>", self.on_charge_slider_release)
        
        # Label de limite actuelle
        self.limit_label = self.ui_manager.create_label(
            battery_frame,
            text="Limite actuelle: 80%",
            anchor="e"
        )
        self.limit_label.pack(side="right", padx=10, pady=2)
        
        # Démarrer le monitoring de la batterie
        self.start_battery_monitor()
        
    def toggle_window(self) -> None:
        """Affiche ou masque la fenêtre"""
        if self.winfo_viewable():
            self.withdraw()
        else:
            self.ui_manager._position_window()
            self.deiconify()
            self.lift()
            self.focus_force()
            
    def quit_app(self) -> None:
        """Quitte l'application"""
        try:
            if self.notification_icon:
                self.notification_icon.stop()
            self.quit()
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture de l'application: {e}")
            
    def start_monitoring(self) -> None:
        """Démarre le monitoring système"""
        def update_stats():
            try:
                metrics = self.hardware_manager.get_system_metrics()
                
                def update_ui():
                    try:
                        # CPU
                        cpu_usage = metrics['cpu']['usage']
                        self.cpu_progress.set(cpu_usage / 100)
                        self.cpu_label.configure(text=f"{self.tr('cpu')}: {cpu_usage:.1f}%")
                        
                        # RAM
                        ram_usage = metrics['ram']['usage']
                        self.ram_progress.set(ram_usage / 100)
                        self.ram_label.configure(text=f"{self.tr('ram')}: {ram_usage:.1f}%")
                        
                        # Température CPU
                        cpu_temp = metrics['cpu']['temperature']
                        self.temp_progress.set(cpu_temp / 100)
                        self.temp_label.configure(text=f"{self.tr('cpu_temp')}: {cpu_temp:.1f}°C")
                        
                        # GPU intégré (780M)
                        igpu_usage = metrics['igpu']['usage']
                        self.igpu_progress.set(igpu_usage / 100)
                        self.igpu_label.configure(text=f"iGPU (780M): {igpu_usage:.1f}%")
                        
                        # Température iGPU
                        igpu_temp = metrics['igpu']['temperature']
                        self.igpu_temp_progress.set(igpu_temp / 100)
                        self.igpu_temp_label.configure(text=f"iGPU Temp: {igpu_temp:.1f}°C")
                        
                        # GPU dédié (7700S)
                        dgpu_usage = metrics['dgpu']['usage']
                        self.dgpu_progress.set(dgpu_usage / 100)
                        self.dgpu_label.configure(text=f"dGPU (7700S): {dgpu_usage:.1f}%")
                        
                        # Température dGPU
                        dgpu_temp = metrics['dgpu']['temperature']
                        self.dgpu_temp_progress.set(dgpu_temp / 100)
                        self.dgpu_temp_label.configure(text=f"dGPU Temp: {dgpu_temp:.1f}°C")
                        
                    except Exception as e:
                        logger.error(f"Erreur lors de la mise à jour de l'interface: {e}")
                        
                if self.winfo_exists():
                    self.after(0, update_ui)
                    
            except Exception as e:
                logger.error(f"Erreur monitoring: {e}")
                
            if self.winfo_exists():
                self.after(1000, update_stats)
                
        self.after(0, update_stats)  # Démarrer dans le thread principal
        
    def start_battery_monitor(self) -> None:
        """Démarre le monitoring de la batterie"""
        def monitor_battery():
            while True:
                try:
                    if not self.winfo_exists():
                        return
                        
                    battery = psutil.sensors_battery()
                    if battery:
                        status = {
                            "percent": battery.percent,
                            "plugged": battery.power_plugged,
                            "secsleft": battery.secsleft,
                            "charge_limit": self.charge_slider.get() if hasattr(self, 'charge_slider') else 80
                        }
                        
                        # Utiliser after pour les mises à jour UI
                        if self.winfo_exists():
                            self.after(0, lambda s=status: self.update_battery_ui(s))
                            
                except Exception as e:
                    logger.error(f"Erreur dans le monitoring batterie: {e}")
                finally:
                    time.sleep(5)
                    
        # S'assurer qu'un seul thread de monitoring est actif
        if hasattr(self, '_battery_monitor_thread') and self._battery_monitor_thread.is_alive():
            return
            
        self._battery_monitor_thread = Thread(target=monitor_battery, daemon=True)
        self._battery_monitor_thread.start()
        logger.info("Thread de monitoring batterie démarré")
        
    def update_battery_ui(self, battery_info: Dict[str, Any]) -> None:
        """Met à jour l'interface avec les informations de batterie"""
        try:
            if not self.winfo_exists():
                return
            
            status_text = f"{self.tr('battery')}: {int(battery_info['percent'])}% | {self.tr('charge_limit')}: {int(battery_info['charge_limit'])}%"
            if battery_info['plugged']:
                status_text += f" | {self.tr('plugged')}"
                if battery_info['percent'] < battery_info['charge_limit']:
                    status_text += f" ({self.tr('power_saving')})"
            else:
                status_text += f" | {self.tr('on_battery')}"
            
            if hasattr(self, 'battery_status'):
                self.battery_status.configure(text=status_text)
            
            # Mettre à jour le tooltip de l'icône système
            tooltip = f"Framework Hub - {battery_info['percent']}%"
            if battery_info['plugged']:
                tooltip += " (Branché)"
                
            if self.notification_icon:
                self.notification_icon.title = tooltip
                
        except Exception as e:
            logger.error(f"Erreur mise à jour UI batterie: {e}")
        
    def change_laptop_model(self, model_name: str) -> None:
        """Change le modèle d'ordinateur"""
        try:
            logger.info(f"Changement de modèle vers: {model_name}")
            model_id = "model_13_amd" if model_name == "Framework 13 AMD" else "model_16"
            
            # Mise à jour des paramètres
            self.settings["laptop_model"] = model_id
            self.save_settings()
            
            # Mise à jour des boutons de rafraîchissement
            self._update_refresh_rate_buttons()
            
            # Réappliquer le profil actuel
            current_profile = self.settings.get("ryzenadj_profile", "Balanced")
            self.apply_profile(current_profile)
            
        except Exception as e:
            logger.error(f"Erreur lors du changement de modèle: {e}")
            
    def apply_profile(self, profile_name: str) -> None:
        """Applique un profil de puissance"""
        try:
            logger.info(f"🔄 Début d'application du profil {profile_name}")
            
            # 1. Appliquer les paramètres RyzenADJ
            ryzenadj_success = self.power_manager.apply_power_profile(profile_name, self.model_var.get())
            logger.info(f"✓ RyzenADJ appliqué: {ryzenadj_success}")
            
            # 2. Appliquer les paramètres d'affichage
            display_settings = {
                "Silent": {"brightness": 30, "refresh_rate": "60Hz"},
                "Balanced": {"brightness": 50, "refresh_rate": "Auto"},
                "Boost": {"brightness": 100, "refresh_rate": "165Hz" if "16" in self.model_var.get() else "120Hz"}
            }
            
            settings = display_settings.get(profile_name, {})
            
            # Appliquer la luminosité
            current_brightness = self.brightness_slider.get()
            target_brightness = settings.get("brightness", 50)
            logger.info(f"Luminosité: {current_brightness} -> {target_brightness}")
            self.brightness_slider.set(target_brightness)
            self.on_brightness_release(None)
            
            # Appliquer le taux de rafraîchissement
            current_rate = self.settings.get("last_refresh_rate", "Auto")
            target_rate = settings.get("refresh_rate", "Auto")
            logger.info(f"Taux de rafraîchissement: {current_rate} -> {target_rate}")
            self.set_refresh_rate_wrapper(target_rate)
            
            # Mettre à jour l'interface
            if hasattr(self, 'profile_buttons'):
                for profile, button in self.profile_buttons.items():
                    if profile == profile_name:
                        button.configure(fg_color="#FF4B1F")  # Couleur active
                    else:
                        button.configure(fg_color="#FF7F5C")  # Couleur normale
            
            # Sauvegarder le profil actuel
            self.settings["ryzenadj_profile"] = profile_name
            self.save_settings()
            
            logger.info(f"✅ Profil {profile_name} appliqué avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'application du profil {profile_name}: {e}")

    def apply_display_settings(self, profile_name: str) -> bool:
        """Applique les paramètres d'affichage selon le profil"""
        try:
            settings = {
                "Silent": {
                    "brightness": 30,
                    "refresh_rate": "60Hz"
                },
                "Balanced": {
                    "brightness": 50,
                    "refresh_rate": "Auto"
                },
                "Boost": {
                    "brightness": 100,
                    "refresh_rate": "165Hz" if self.model_var.get() == "Framework 16 AMD" else "120Hz"
                }
            }
            
            profile_settings = settings.get(profile_name)
            if not profile_settings:
                return False
            
            # Appliquer la luminosité
            self.brightness_slider.set(profile_settings["brightness"])
            self.on_brightness_release(None)
            
            # Appliquer le taux de rafraîchissement
            self.set_refresh_rate_wrapper(profile_settings["refresh_rate"])
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'application des paramètres d'affichage: {e}")
            return False

    def apply_battery_settings(self, profile_name: str) -> bool:
        """Applique les paramètres de batterie selon le profil"""
        try:
            settings = {
                "Silent": {
                    "power_plan": "power_saver",
                    "battery_saver": True,
                    "charge_limit": 60
                },
                "Balanced": {
                    "power_plan": "balanced",
                    "battery_saver": False,
                    "charge_limit": 80
                },
                "Boost": {
                    "power_plan": "high_performance",
                    "battery_saver": False,
                    "charge_limit": 100
                }
            }
            
            profile_settings = settings.get(profile_name)
            if not profile_settings:
                return False
            
            # Appliquer la limite de charge
            self.charge_slider.set(profile_settings["charge_limit"])
            self.on_charge_slider_release(None)
            
            # Appliquer le mode d'économie de batterie
            ps_command = f'''
            powercfg /setdcvalueindex SCHEME_CURRENT SUB_ENERGYSAVER ESBATTTHRESHOLD {1 if profile_settings["battery_saver"] else 0}
            powercfg /setactive SCHEME_CURRENT
            '''
            
            subprocess.run(["powershell", "-Command", ps_command], capture_output=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'application des paramètres de batterie: {e}")
            return False
        
    def set_refresh_rate_wrapper(self, rate: str) -> None:
        """Wrapper pour le changement de taux de rafraîchissement"""
        try:
            if rate == "Auto":
                # Sauvegarder le choix Auto
                self.settings["last_refresh_rate"] = "Auto"
                self.save_settings()
                
                # Démarrer le monitoring de l'alimentation si pas déjà en cours
                if not hasattr(self, 'power_monitor_thread') or not self.power_monitor_thread.is_alive():
                    self.power_monitor_thread = Thread(target=self.monitor_power_state, daemon=True)
                    self.power_monitor_thread.start()
                
                # Appliquer le taux initial basé sur l'état de l'alimentation
                self.auto_refresh_rate()
            else:
                # Mode manuel - appliquer directement
                self.settings["last_refresh_rate"] = rate
                self.save_settings()
                
                # Mettre à jour l'UI avant le changement
                self._update_refresh_rate_buttons()
                
                # Démarrer le changement dans un thread séparé
                Thread(target=self.set_refresh_rate, args=(rate,), daemon=True).start()
                
        except Exception as e:
            logger.error(f"Erreur lors du changement de taux de rafraîchissement: {e}")
            
    def set_refresh_rate(self, rate: str) -> bool:
        """Change le taux de rafraîchissement de l'écran"""
        try:
            # Convertir le taux en entier (ex: "165Hz" -> 165)
            refresh_rate = int(rate.replace("Hz", ""))
            
            # Commande PowerShell pour changer le taux
            ps_command = f'''
            Add-Type @"
            using System;
            using System.Runtime.InteropServices;

            public class DisplaySettings
            {{
                [DllImport("user32.dll")]
                public static extern int EnumDisplaySettings(string deviceName, int modeNum, ref DEVMODE devMode);
                
                [DllImport("user32.dll")]
                public static extern int ChangeDisplaySettings(ref DEVMODE devMode, int flags);

                [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Ansi)]
                public struct DEVMODE
                {{
                    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
                    public string dmDeviceName;
                    public short dmSpecVersion;
                    public short dmDriverVersion;
                    public short dmSize;
                    public short dmDriverExtra;
                    public int dmFields;
                    public int dmPositionX;
                    public int dmPositionY;
                    public int dmDisplayOrientation;
                    public int dmDisplayFixedOutput;
                    public short dmColor;
                    public short dmDuplex;
                    public short dmYResolution;
                    public short dmTTOption;
                    public short dmCollate;
                    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
                    public string dmFormName;
                    public short dmLogPixels;
                    public int dmBitsPerPel;
                    public int dmPelsWidth;
                    public int dmPelsHeight;
                    public int dmDisplayFlags;
                    public int dmDisplayFrequency;
                    public int dmICMMethod;
                    public int dmICMIntent;
                    public int dmMediaType;
                    public int dmDitherType;
                    public int dmReserved1;
                    public int dmReserved2;
                    public int dmPanningWidth;
                    public int dmPanningHeight;
                }}
            }}
"@

            $dm = New-Object DisplaySettings+DEVMODE
            $dm.dmSize = [System.Runtime.InteropServices.Marshal]::SizeOf($dm)
            $dm.dmFields = 0x400000  # DMFIELDS_DISPLAYFREQUENCY

            # Obtenir les paramètres actuels
            [DisplaySettings]::EnumDisplaySettings($null, -1, [ref]$dm)
            
            # Sauvegarder la fréquence actuelle
            $originalFrequency = $dm.dmDisplayFrequency
            
            # Définir la nouvelle fréquence
            $dm.dmDisplayFrequency = {refresh_rate}
            
            Write-Output "Tentative de changement de $originalFrequency Hz à {refresh_rate} Hz"
            
            $result = [DisplaySettings]::ChangeDisplaySettings([ref]$dm, 0)
            
            switch ($result) {{
                0 {{ 
                    Write-Output "Taux de rafraîchissement changé avec succès"
                    exit 0
                }}
                1 {{ 
                    Write-Output "Changement effectif au prochain redémarrage"
                    exit 0
                }}
                -1 {{ 
                    throw "Échec: Paramètres invalides"
                }}
                -2 {{ 
                    throw "Échec: Paramètres non supportés"
                }}
                -3 {{ 
                    throw "Échec: Flags invalides"
                }}
                -4 {{ 
                    throw "Échec: Mode non supporté"
                }}
                -5 {{ 
                    throw "Échec: Plus d'un écran présent"
                }}
                default {{ 
                    throw "Échec: Erreur inconnue (code: $result)"
                }}
            }}
            '''
            
            # Créer startupinfo pour cacher la fenêtre
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # Exécuter la commande PowerShell
            result = subprocess.run(
                ["powershell", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                timeout=5  # Timeout de 5 secondes
            )
            
            # Logger la sortie complète
            if result.stdout:
                logger.info(f"Sortie du changement de taux: {result.stdout.strip()}")
            if result.stderr:
                logger.error(f"Erreur du changement de taux: {result.stderr.strip()}")
            
            if result.returncode == 0:
                logger.info(f"Taux de rafraîchissement changé à {refresh_rate}")
                self._update_refresh_rate_buttons()
                return True
            else:
                logger.error(f"Échec du changement de taux (code: {result.returncode})")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Timeout lors du changement de taux de rafraîchissement")
            return False
        except Exception as e:
            logger.error(f"Erreur lors du changement de taux: {e}")
            return False
            
    def monitor_power_state(self) -> None:
        """Surveille l'état de l'alimentation pour le mode Auto"""
        last_power_state = None
        
        while True:
            try:
                battery = psutil.sensors_battery()
                if battery:
                    current_power_state = battery.power_plugged
                    if current_power_state != last_power_state:
                        if not current_power_state:  # Si débranché
                            logger.info("Secteur débranché, attente de 5 secondes...")
                            time.sleep(5)  # Attendre pour éviter les faux positifs
                            # Revérifier après le délai
                            battery = psutil.sensors_battery()
                            if battery and not battery.power_plugged:
                                last_power_state = current_power_state
                                if self.settings.get("last_refresh_rate") == "Auto":
                                    self.auto_refresh_rate()
                        else:  # Si branché
                            last_power_state = current_power_state
                            if self.settings.get("last_refresh_rate") == "Auto":
                                self.auto_refresh_rate()
                time.sleep(2)  # Vérifier toutes les 2 secondes
            except Exception as e:
                logger.error(f"Erreur dans le monitoring d'alimentation: {e}")
                time.sleep(5)  # Attendre plus longtemps en cas d'erreur
                
    def auto_refresh_rate(self) -> None:
        """Ajuste le taux de rafraîchissement selon l'alimentation"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                model = self.model_var.get()
                max_rate = "165Hz" if model == "Framework 16 AMD" else "120Hz"
                
                if battery.power_plugged:
                    logger.info("Secteur détecté, passage au taux maximum")
                    self.set_refresh_rate(max_rate)
                else:
                    logger.info("Batterie détectée, passage à 60Hz")
                    self.set_refresh_rate("60Hz")
        except Exception as e:
            logger.error(f"Erreur dans auto_refresh_rate: {e}")
            
    def _update_refresh_rate_buttons(self) -> None:
        """Met à jour les boutons de taux de rafraîchissement"""
        try:
            model = self.model_var.get()
            
            # Définir les taux selon le modèle
            if model == "Framework 16 AMD":
                rates = ["Auto", "60Hz", "165Hz"]
                max_rate = 165
            else:  # Framework 13 AMD
                rates = ["Auto", "60Hz", "120Hz"]
                max_rate = 120
            
            # Supprimer les anciens boutons
            for widget in self.refresh_container.winfo_children():
                widget.destroy()
            self.refresh_buttons.clear()
            
            # Récupérer le taux actuel
            last_rate = self.settings.get("last_refresh_rate", "Auto")
            
            # Créer les nouveaux boutons
            for rate in rates:
                # Déterminer si le bouton est actif
                is_active = rate == last_rate
                
                # Styles des boutons
                if is_active:
                    style = {
                        "fg_color": "#FF4B1F",
                        "hover_color": "#FF6B47",
                        "text_color": "white"
                    }
                else:
                    style = {
                        "fg_color": self.ui_manager.colors['button'],
                        "hover_color": self.ui_manager.colors['hover'],
                        "text_color": "black"
                    }
                
                # Créer le bouton
                btn = ctk.CTkButton(
                    self.refresh_container,
                    text=rate,
                    command=lambda r=rate: self.set_refresh_rate_wrapper(r),
                    width=50,
                    height=24,
                    **style
                )
                btn.pack(side="left", padx=2)
                self.refresh_buttons[rate] = btn
                
            logger.info(f"Boutons de rafraîchissement mis à jour pour le modèle {model}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des boutons de rafraîchissement: {e}")
            # Créer au moins les boutons par défaut en cas d'erreur
            default_rates = ["Auto", "60Hz", "120Hz"]
            for rate in default_rates:
                btn = ctk.CTkButton(
                    self.refresh_container,
                    text=rate,
                    command=lambda r=rate: self.set_refresh_rate_wrapper(r),
                    width=50,
                    height=24,
                    fg_color=self.ui_manager.colors['button'],
                    hover_color=self.ui_manager.colors['hover'],
                    text_color="black"
                )
                btn.pack(side="left", padx=2)
                self.refresh_buttons[rate] = btn
        
    def on_brightness_change(self, value: float) -> None:
        """Gère le changement de luminosité"""
        try:
            brightness = int(value)
            self.brightness_value_label.configure(text=f"Actuel: {brightness}%")
        except Exception as e:
            logger.error(f"Erreur lors du changement de luminosité: {e}")
            
    def on_brightness_release(self, event) -> None:
        """Applique le changement de luminosité"""
        try:
            brightness = int(self.brightness_slider.get())
            
            # Commande PowerShell pour changer la luminosité
            ps_command = f'''
            try {{
                $monitors = Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods
                if ($monitors) {{
                    foreach ($monitor in $monitors) {{
                        $monitor.WmiSetBrightness(0, {brightness})
                    }}
                    Write-Output "Luminosité changée à {brightness}%"
                    exit 0
                }} else {{
                    throw "Aucun moniteur compatible trouvé"
                }}
            }} catch {{
                Write-Error $_.Exception.Message
                exit 1
            }}
            '''
            
            # Créer startupinfo pour cacher la fenêtre
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # Exécuter la commande PowerShell
            result = subprocess.run(
                ["powershell", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                timeout=5  # Timeout de 5 secondes
            )
            
            # Logger la sortie
            if result.stdout:
                logger.info(f"Sortie du changement de luminosité: {result.stdout.strip()}")
            if result.stderr:
                logger.error(f"Erreur du changement de luminosité: {result.stderr.strip()}")
            
            if result.returncode == 0:
                logger.info(f"Luminosité changée à {brightness}%")
                # Sauvegarder la valeur
                self.settings["last_brightness"] = brightness
                self.save_settings()
            else:
                logger.error(f"Échec du changement de luminosité (code: {result.returncode})")
                
        except subprocess.TimeoutExpired:
            logger.error("Timeout lors du changement de luminosité")
        except Exception as e:
            logger.error(f"Erreur lors de l'application de la luminosité: {e}")
            
    def _init_brightness(self) -> None:
        """Initialise la luminosité au démarrage"""
        try:
            # Commande PowerShell pour obtenir la luminosité actuelle
            ps_command = '''
            try {
                $monitor = Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness
                if ($monitor) {
                    Write-Output $monitor.CurrentBrightness
                    exit 0
                } else {
                    throw "Aucun moniteur compatible trouvé"
                }
            } catch {
                Write-Error $_.Exception.Message
                exit 1
            }
            '''
            
            # Créer startupinfo pour cacher la fenêtre
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # Exécuter la commande PowerShell
            result = subprocess.run(
                ["powershell", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                current_brightness = int(result.stdout.strip())
                logger.info(f"Luminosité actuelle: {current_brightness}%")
                
                # Mettre à jour le slider et le label
                self.brightness_slider.set(current_brightness)
                self.brightness_value_label.configure(text=f"Actuel: {current_brightness}%")
                
                # Sauvegarder la valeur
                self.settings["last_brightness"] = current_brightness
                self.save_settings()
            else:
                logger.warning("Impossible de récupérer la luminosité actuelle")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la luminosité: {e}")
            # Utiliser la dernière valeur connue ou la valeur par défaut
            last_brightness = self.settings.get("last_brightness", 50)
            self.brightness_slider.set(last_brightness)
            self.brightness_value_label.configure(text=f"Actuel: {last_brightness}%")
        
    def on_charge_slider_change(self, value: float) -> None:
        """Gère le changement de limite de charge"""
        try:
            limit = int(value)
            self.limit_label.configure(text=f"Limite actuelle: {limit}%")
        except Exception as e:
            logger.error(f"Erreur lors du changement de limite de charge: {e}")
            
    def on_charge_slider_release(self, event) -> None:
        """Appelé quand le slider de charge est relâché"""
        try:
            value = self.charge_slider.get()
            if isinstance(value, (int, float)) and 20 <= value <= 100:
                logger.info(f"Limite de charge définie à {int(value)}%")
                self.settings["battery_charge_limit"] = int(value)
                self.save_settings()
        except Exception as e:
            logger.error(f"Erreur lors de la définition de la limite de charge: {e}")

    def show_notification(self, title: str, message: str, error: bool = False) -> None:
        """Affiche une notification système"""
        try:
            # Ne pas afficher les notifications liées à la batterie
            if "charge" in message.lower():
                return
            
            if self.notification_icon is not None:
                # Utiliser la méthode notify de pystray
                self.notification_icon.notify(
                    title=title,
                    message=message
                )
                logger.info(f"Notification: {title} - {message}")
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de la notification: {e}")

    def _init_charge_limit(self) -> None:
        """Initialise la limite de charge au démarrage"""
        try:
            # Commande PowerShell pour obtenir la limite actuelle
            ps_command = '''
            try {
                # Vérifier si le service Framework est installé
                $service = Get-Service -Name "FrameworkService" -ErrorAction SilentlyContinue
                if ($service) {
                    $result = & "C:\\Program Files\\Framework\\FrameworkService\\FrameworkCLI.exe" get-battery-limit
                    if ($LASTEXITCODE -eq 0) {
                        Write-Output $result
                        exit 0
                    }
                }
                
                # Vérifier via WMI
                $battery = Get-CimInstance -Namespace "root\\WMI" -ClassName "BatteryStatus" -ErrorAction SilentlyContinue
                if ($battery) {
                    Write-Output $battery.ChargeLimit
                    exit 0
                }
                
                # Vérifier via le registre
                $limit = Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Power\\BatteryConfig" -Name "ChargeLimit" -ErrorAction SilentlyContinue
                if ($limit) {
                    Write-Output $limit.ChargeLimit
                    exit 0
                }
                
                Write-Error "Impossible de vérifier la limite de charge"
                exit 1
            } catch {
                Write-Error $_.Exception.Message
                exit 1
            }
            '''
            
            # Créer startupinfo pour cacher la fenêtre
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # Exécuter la commande PowerShell
            result = subprocess.run(
                ["powershell", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                current_limit = int(float(result.stdout.strip()))
                logger.info(f"Limite de charge actuelle: {current_limit}%")
                
                # Mettre à jour le slider et le label
                self.charge_slider.set(current_limit)
                self.limit_label.configure(text=f"Limite actuelle: {current_limit}%")
                
                # Sauvegarder la valeur
                self.settings["battery_charge_limit"] = current_limit
                self.save_settings()
            else:
                logger.warning("Impossible de récupérer la limite de charge actuelle")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la limite de charge: {e}")
            # Utiliser la dernière valeur connue ou la valeur par défaut
            last_limit = self.settings.get("battery_charge_limit", 80)
            self.charge_slider.set(last_limit)
            self.limit_label.configure(text=f"Limite actuelle: {last_limit}%")
        
    def open_keyboard_page(self) -> None:
        """Ouvre la page du clavier"""
        webbrowser.open("https://keyboard.frame.work/")
        
    def open_updates(self) -> None:
        """Ouvre la fenêtre des mises à jour"""
        try:
            if not hasattr(self, 'update_window') or not self.update_window.winfo_exists():
                self.update_window = UpdateWindow(self)
                self.update_window.focus()
            else:
                self.update_window.focus()
                
            logger.info("Fenêtre des mises à jour ouverte")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture de la fenêtre des mises à jour: {e}")
            self.show_notification(
                self.tr("error"),
                str(e),
                error=True
            )
        
    def open_settings(self) -> None:
        """Ouvre la fenêtre des paramètres"""
        if not hasattr(self, 'settings_window') or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self)
            self.settings_window.focus()
        else:
            self.settings_window.focus()

    def start_move(self, event):
        """Commence le déplacement de la fenêtre"""
        self._drag_start_x = event.x_root - self.winfo_x()
        self._drag_start_y = event.y_root - self.winfo_y()
        
    def on_move(self, event):
        """Déplace la fenêtre"""
        x = event.x_root - self._drag_start_x
        y = event.y_root - self._drag_start_y
        self.geometry(f"+{x}+{y}")
        # Sauvegarder la nouvelle position
        self.settings["window_position"] = {"x": x, "y": y}

    def update_ui_language(self):
        """Update all UI elements with new language"""
        try:
            # Update window title
            self.title(self.tr("Framework Mini Hub"))
            
            # Update profile buttons
            for profile, btn in self.profile_buttons.items():
                btn.configure(text=self.tr(profile.lower()))
            
            # Update refresh rate label
            if hasattr(self, 'refresh_label'):
                self.refresh_label.configure(text=f"{self.tr('refresh_rate')}:")
            
            # Update brightness labels
            if hasattr(self, 'brightness_label'):
                self.brightness_label.configure(text=f"{self.tr('brightness')}:")
            
            if hasattr(self, 'brightness_value_label'):
                current_brightness = int(self.brightness_slider.get())
                self.brightness_value_label.configure(text=f"{self.tr('current')}: {current_brightness}%")
            
            # Update battery labels
            if hasattr(self, 'battery_status'):
                battery = psutil.sensors_battery()
                if battery:
                    status = f"{self.tr('battery')}: {int(battery.percent)}% | {self.tr('charge_limit')}: {int(self.charge_slider.get())}%"
                    if battery.power_plugged:
                        status += f" | {self.tr('plugged')}"
                    self.battery_status.configure(text=status)
            
            if hasattr(self, 'limit_label'):
                current_limit = int(self.charge_slider.get())
                self.limit_label.configure(text=f"{self.tr('current_limit')}: {current_limit}%")
            
            # Update action buttons
            if hasattr(self, 'keyboard_button'):
                self.keyboard_button.configure(text=self.tr("keyboard"))
            if hasattr(self, 'updates_button'):
                self.updates_button.configure(text=self.tr("updates"))
            if hasattr(self, 'settings_button'):
                self.settings_button.configure(text=self.tr("settings"))
            
            logger.info("Main window UI updated to new language")
        except Exception as e:
            logger.error(f"Error updating main window UI: {e}")

    def tr(self, key: str) -> str:
        """Get translation for key"""
        try:
            return self.translations.get(key, key)
        except:
            return key

    def update_interface(self):
        """Met à jour l'interface avec les dernières métriques"""
        try:
            # Utiliser la bonne fonction get_system_metrics()
            metrics = self.hardware_manager.get_system_metrics()
            
            # CPU
            cpu_usage = metrics['cpu']['usage']
            self.cpu_progress.set(cpu_usage / 100)
            self.cpu_label.configure(text=f"{self.tr('cpu')}: {cpu_usage:.1f}%")
            
            # RAM
            ram_usage = metrics['ram']['usage']
            self.ram_progress.set(ram_usage / 100)
            self.ram_label.configure(text=f"{self.tr('ram')}: {ram_usage:.1f}%")
            
            # Température CPU
            cpu_temp = metrics['cpu']['temperature']
            self.temp_progress.set(cpu_temp / 100)
            self.temp_label.configure(text=f"{self.tr('cpu_temp')}: {cpu_temp:.1f}°C")
            
            # GPU intégré (780M)
            igpu_usage = metrics['igpu']['usage']
            self.igpu_progress.set(igpu_usage / 100)
            self.igpu_label.configure(text=f"iGPU (780M): {igpu_usage:.1f}%")
            
            # Température iGPU
            igpu_temp = metrics['igpu']['temperature']
            self.igpu_temp_progress.set(igpu_temp / 100)
            self.igpu_temp_label.configure(text=f"iGPU Temp: {igpu_temp:.1f}°C")
            
            # GPU dédié (7700S)
            dgpu_usage = metrics['dgpu']['usage']
            self.dgpu_progress.set(dgpu_usage / 100)
            self.dgpu_label.configure(text=f"dGPU (7700S): {dgpu_usage:.1f}%")
            
            # Température dGPU
            dgpu_temp = metrics['dgpu']['temperature']
            self.dgpu_temp_progress.set(dgpu_temp / 100)
            self.dgpu_temp_label.configure(text=f"dGPU Temp: {dgpu_temp:.1f}°C")
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'interface: {e}")

    def create_profile_buttons(self, parent: ctk.CTkFrame) -> None:
        """Crée les boutons de profil"""
        try:
            # Créer les boutons de profil
            self.profile_buttons: Dict[str, ctk.CTkButton] = {}
            
            # Obtenir le modèle actuel
            current_model = self.settings.get("laptop_model", "model_13_amd")
            
            # Obtenir les profils pour ce modèle
            model_profiles = self.settings["power_profiles"].get(current_model, {})
            
            # Configuration des boutons
            button_config = {
                "corner_radius": 8,  # int
                "border_width": 0,   # int
                "border_spacing": 2, # int
                "font": ("Arial", 12),  # tuple[str, int]
                "width": 50,        # int
                "height": 24,       # int
                "hover": True,      # bool
                "round_width_to_even_numbers": True,  # bool
                "round_height_to_even_numbers": True  # bool
            }
            
            for profile in ["Silent", "Balanced", "Boost"]:
                if profile in model_profiles:
                    btn = ctk.CTkButton(
                        master=parent,
                        text=profile,
                        command=lambda p=profile: self.apply_profile(p),
                        fg_color=self.ui_manager.colors['button'],
                        hover_color=self.ui_manager.colors['hover'],
                        **button_config
                    )
                    btn.pack(side="left", padx=2)
                    self.profile_buttons[profile] = btn
            
        except Exception as e:
            logger.error(f"Erreur création boutons: {e}")

    def show_window(self) -> None:
        """Affiche la fenêtre"""
        self.deiconify()
        self.lift()
        self.focus_force()

if __name__ == "__main__":
    try:
        logger.info("Démarrage de l'application")
        if not ctypes.windll.shell32.IsUserAnAdmin():
            logger.info("Demande de privilèges administrateur")
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{__file__}"', None, 1
            )
        else:
            logger.info("Exécution avec privilèges administrateur")
            app = MiniFrameworkHub()
            app.mainloop()
    except Exception as e:
        logger.error(f"Erreur critique: {str(e)}", exc_info=True)
        import tkinter.messagebox as messagebox
        messagebox.showerror(
            "Erreur",
            f"Une erreur est survenue au démarrage:\n{str(e)}\n\nConsultez mini_hub.log pour plus de détails."
        )