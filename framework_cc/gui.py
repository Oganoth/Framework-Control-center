"""GUI module for Framework Control Center."""

import asyncio
import json
import webbrowser
from pathlib import Path
from typing import Optional
import customtkinter as ctk
from PIL import Image
import threading
import subprocess
import sys
import os
import logging
from tkinter import font
from datetime import datetime

from .models import SystemConfig, PowerProfile, HardwareMetrics
from .hardware import HardwareMonitor
from .power import PowerManager
from .display import DisplayManager
from .detector import ModelDetector
from .logger import logger, check_and_rotate_log
from .tweaks import WindowsTweaks
from .translations import get_text, language_names

logger = logging.getLogger(__name__)

def get_resource_path(relative_path):
    """Get absolute path to resource for PyInstaller bundled app."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def load_custom_font(language_code: str = "en") -> tuple:
    """Load custom font based on language and return font family name."""
    try:
        # Get the absolute path to the fonts directory
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_path = os.path.join(base_path, "fonts", "Ubuntu-Regular.ttf")
        klingon_font_path = os.path.join(base_path, "fonts", "klingon font.ttf")
        
        # Load the appropriate font based on language
        if language_code == "tlh" and os.path.exists(klingon_font_path):
            # Register Klingon font
            ctk.FontManager.load_font(klingon_font_path)
            return "klingon font"
        elif os.path.exists(font_path):
            # Register Ubuntu font with smaller size
            ctk.FontManager.load_font(font_path)
            # Return font name with size specification
            return ("Ubuntu-Regular", 10)
    except Exception as e:
        logger.error(f"Error loading custom font: {e}")
    
    # Return fallback font with size specification
    return ("Helvetica", 10)  # Fallback font that's guaranteed to exist

class FrameworkControlCenter(ctk.CTk):
    # Class-level variables for tray icon management
    _tray_lock = threading.Lock()
    _tray_instance = None
    _open_windows = []  # Track all open windows
    
    def __init__(self):
        super().__init__()
        FrameworkControlCenter._open_windows.append(self)  # Add main window to list
        
        # Setup theme and colors first
        self._setup_theme()
        
        # Configuration de la fenêtre
        self.title("Framework Control Center")
        self.geometry("300x700")  # Increased height from 650 to 700
        self.resizable(False, False)
        
        # Configurer l'icône
        try:
            if sys.platform.startswith('win'):
                self.after(200, lambda: self.iconbitmap(str(Path("assets/logo.ico").absolute())))
            else:
                self.iconbitmap(str(Path("assets/logo.ico")))
        except Exception as e:
            logger.error(f"Failed to set window icon: {e}")
        
        # Configurer le style de la fenêtre
        self.configure(fg_color="#1E1E1E", corner_radius=10)
        
        # Positionner la fenêtre dans le coin inférieur droit
        self._position_window()
        
        # Initialize tweaks manager
        self.tweaks = WindowsTweaks()
        
        # Initialize model detection first
        detector = ModelDetector()
        self.model = detector.detect_model()
        if not self.model:
            logger.error("No compatible Framework laptop detected")
            raise RuntimeError("No compatible Framework laptop detected")
            
        # Load configuration
        self.config_path = Path.home() / ".framework_cc" / "config.json"
        self.config = self._load_config()
        
        # Load custom font
        self.current_font = load_custom_font(self.config.language)
        
        # Initialize managers with detected model
        self.hardware = HardwareMonitor()
        self.power = PowerManager(self.model)
        self.display = DisplayManager()
        
        # Setup window
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Setup UI
        self._create_widgets()
        self._setup_hotkeys()
        
        # Setup tray icon
        self._setup_tray()

        # Start monitoring
        self.after(self.config.monitoring_interval, self._update_metrics)
        
        # Initialize default profiles after a short delay to ensure all components are loaded
        self.after(1000, self._initialize_default_profiles)

        # Start log file check timer
        self._check_log_file_size()

    def _position_window(self) -> None:
        """Positionner la fenêtre dans le coin inférieur droit."""
        # Dimensions fixes de la fenêtre
        window_width = 300
        window_height = 700  # Updated from 650 to 700
        
        try:
            # Désactiver le DPI awareness pour obtenir les vraies dimensions
            import ctypes
            awareness = ctypes.c_int()
            ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
            ctypes.windll.shcore.SetProcessDpiAwareness(0)
            
            # Obtenir les dimensions réelles de l'écran
            screen_width = ctypes.windll.user32.GetSystemMetrics(0)  # SM_CXSCREEN
            screen_height = ctypes.windll.user32.GetSystemMetrics(1)  # SM_CYSCREEN
            
            # Restaurer le DPI awareness original
            ctypes.windll.shcore.SetProcessDpiAwareness(awareness.value)
            
            # Position dans le coin inférieur droit avec marges ajustées
            x = screen_width - window_width - 170  # 170 pixels de marge à droite
            y = screen_height - window_height - 380  # 380 pixels de marge en bas
            
            logger.debug(f"Screen dimensions: {screen_width}x{screen_height}")
            logger.debug(f"Window position: {x},{y}")
            
        except Exception as e:
            logger.error(f"Error getting screen metrics: {e}")
            # Fallback en cas d'erreur
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            x = screen_width - window_width - 170
            y = screen_height - window_height - 380
        
        # Définir la géométrie
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Toujours au premier plan et sans barre de titre
        self.attributes('-topmost', True)
        self.overrideredirect(True)
        
        # Configurer la couleur de fond sombre
        self.configure(fg_color=self.colors["background"])

    def _setup_theme(self) -> None:
        """Setup the application theme."""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Custom colors
        self.colors = {
            "primary": "#FF7043",
            "hover": "#F4511E",
            "background": "#1E1E1E",  # Fond plus sombre
            "text": "#FFFFFF",
            "text_active": "#FFFFFF",
            "border_active": "#FFFFFF",
            "button": "#FF7043"  # Même couleur que primary
        }

        # Garder une référence aux boutons actifs
        self.active_buttons = {
            "profile": None,
            "refresh": None
        }

    def _create_widgets(self) -> None:
        """Create all GUI widgets."""
        # Main container with dark background and rounded corners
        self.container = ctk.CTkFrame(
            self,
            fg_color=self.colors["background"],
            corner_radius=10
        )
        self.container.pack(fill="both", expand=True, padx=0, pady=0)

        # Ajouter la barre de titre personnalisée
        title_bar = ctk.CTkFrame(
            self.container,
            fg_color=self.colors["background"],
            height=30,
            corner_radius=10
        )
        title_bar.pack(fill="x", padx=2, pady=(2, 0))
        title_bar.pack_propagate(False)

        # Titre
        title_label = ctk.CTkLabel(
            title_bar,
            text="Framework Control Center",
            text_color=self.colors["text"],
            font=("Roboto", 11, "bold")
        )
        title_label.pack(side="left", padx=10)

        # Boutons de contrôle (dans un frame pour les garder ensemble)
        control_buttons = ctk.CTkFrame(title_bar, fg_color="transparent")
        control_buttons.pack(side="right", padx=5)

        # Bouton réduire
        minimize_button = ctk.CTkButton(
            control_buttons,
            text="−",
            width=20,
            height=20,
            command=self._minimize_to_tray,
            fg_color="transparent",
            hover_color=self.colors["hover"],
            text_color=self.colors["text"],
            corner_radius=5
        )
        minimize_button.pack(side="left", padx=2)

        # Bouton fermer
        close_button = ctk.CTkButton(
            control_buttons,
            text="×",
            width=20,
            height=20,
            command=self._on_close,
            fg_color="#FF4444",
            hover_color="#FF6666",
            text_color=self.colors["text"],
            corner_radius=5
        )
        close_button.pack(side="left", padx=2)

        # Permettre de déplacer la fenêtre en cliquant sur la barre de titre
        title_bar.bind("<Button-1>", self._start_drag)
        title_bar.bind("<B1-Motion>", self._on_drag)
        title_label.bind("<Button-1>", self._start_drag)
        title_label.bind("<B1-Motion>", self._on_drag)

        # Create event loop for async operations
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Power profiles
        self._create_power_profiles()

        # Refresh rate controls
        self._create_refresh_controls()

        # System metrics
        self._create_metrics_display()

        # Grand spacer pour pousser les éléments vers le bas
        spacer = ctk.CTkFrame(self.container, fg_color="transparent", height=20)
        spacer.pack(fill="x")

        # Additional buttons
        self._create_utility_buttons()

        # Petit spacer avant brightness
        spacer2 = ctk.CTkFrame(self.container, fg_color="transparent", height=20)
        spacer2.pack(fill="x")

        # Brightness control
        self._create_brightness_control()

        # Battery status
        self._create_battery_status()

        # Additional buttons
        buttons_frame = ctk.CTkFrame(self.container, fg_color=self.colors["background"])
        buttons_frame.pack(fill="x", padx=10, pady=5)

    def _create_power_profiles(self) -> None:
        """Create power profile buttons."""
        profiles_frame = ctk.CTkFrame(self.container, fg_color=self.colors["background"])
        profiles_frame.pack(fill="x", padx=10, pady=5)

        # Créer un sous-frame pour les boutons avec distribution égale
        buttons_frame = ctk.CTkFrame(profiles_frame, fg_color=self.colors["background"])
        buttons_frame.pack(fill="x", padx=5)
        buttons_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Charger les icônes
        icons = {
            "Silent": ctk.CTkImage(Image.open(get_resource_path("assets/eco.png")), size=(24, 24)),
            "Balanced": ctk.CTkImage(Image.open(get_resource_path("assets/balanced.png")), size=(24, 24)),
            "Boost": ctk.CTkImage(Image.open(get_resource_path("assets/performance.png")), size=(24, 24))
        }

        self.profile_buttons = {}
        for i, profile in enumerate(["Silent", "Balanced", "Boost"]):
            btn = ctk.CTkButton(
                buttons_frame,
                text=profile,
                image=icons[profile],
                compound="top",  # Place l'icône au-dessus du texte
                command=lambda p=profile: self._set_power_profile_sync(p),
                fg_color=self.colors["primary"],
                hover_color=self.colors["hover"],
                text_color=self.colors["text"],
                height=60,  # Plus haut pour accommoder l'icône au-dessus du texte
                width=90,
                border_width=2,
                border_color=self.colors["background"],
                corner_radius=10  # Ajout des coins arrondis
            )
            btn.grid(row=0, column=i, padx=3)
            self.profile_buttons[profile] = btn

            # Définir le profil actif par défaut
            if profile == self.config.current_profile:
                self._update_button_state("profile", btn)

    def _create_refresh_controls(self) -> None:
        """Create refresh rate control buttons."""
        refresh_frame = ctk.CTkFrame(self.container, fg_color=self.colors["background"])
        refresh_frame.pack(fill="x", padx=10, pady=5)

        # Créer un sous-frame pour les boutons avec distribution égale
        buttons_frame = ctk.CTkFrame(refresh_frame, fg_color=self.colors["background"])
        buttons_frame.pack(fill="x", padx=5)
        buttons_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.refresh_buttons = {}
        for i, mode in enumerate(["Auto", "60Hz", "165Hz"]):
            btn = ctk.CTkButton(
                buttons_frame,
                text=mode,
                command=lambda m=mode: self._set_refresh_rate_sync(m),
                fg_color=self.colors["primary"],
                hover_color=self.colors["hover"],
                text_color=self.colors["text"],
                height=35,  # Plus haut
                width=90,  # Plus large
                border_width=2,
                border_color=self.colors["background"],
                corner_radius=10  # Ajout des coins arrondis
            )
            btn.grid(row=0, column=i, padx=3)  # Réduit le padding pour compenser la largeur
            self.refresh_buttons[mode] = btn

            # Définir le mode actif par défaut
            if mode == self.config.refresh_rate_mode:
                self._update_button_state("refresh", self.refresh_buttons[mode])

    def _create_metrics_display(self) -> None:
        """Create system metrics display."""
        metrics_frame = ctk.CTkFrame(self.container, fg_color=self.colors["background"])
        metrics_frame.pack(fill="x", padx=10, pady=5)

        # Create labels and progress bars for metrics
        self.metric_bars = {}
        self.metric_labels = {}
        
        # Métriques de base toujours affichées
        metrics = [
            ("CPU", "cpu_load", "%"),
            ("CPU TEMP", "cpu_temp", "°C"),
            ("RAM", "ram_usage", "%"),
            ("iGPU", "igpu_load", "%"),
            ("iGPU TEMP", "igpu_temp", "°C")
        ]

        # Ajouter les métriques dGPU pour le modèle 16_AMD
        if self.model.has_dgpu:
            logger.info(f"Detected {self.model.name} with dGPU, adding dGPU metrics to display")
            metrics.extend([
                ("dGPU", "dgpu_load", "%"),
                ("dGPU TEMP", "dgpu_temp", "°C")
            ])
            logger.debug("Final metrics list: %s", metrics)
        else:
            logger.info(f"Model {self.model.name} has no dGPU, skipping dGPU metrics")

        # Créer les widgets pour chaque métrique
        for label, key, unit in metrics:
            frame = ctk.CTkFrame(metrics_frame, fg_color=self.colors["background"])
            frame.pack(fill="x", pady=2)

            # Label with value
            label_text = ctk.CTkLabel(frame, text=f"{label}: 0{unit}", text_color=self.colors["text"])
            label_text.pack(side="left", padx=5)
            self.metric_labels[key] = label_text
            logger.debug(f"Created metric label: {label} -> {key}")

            # Progress bar
            progress = ctk.CTkProgressBar(
                frame,
                progress_color=self.colors["primary"],
                fg_color="#2D2D2D",
                height=15,
                width=120
            )
            progress.pack(side="right", padx=5)
            progress.set(0)
            self.metric_bars[key] = progress
            logger.debug(f"Created progress bar for: {key}")

    def _create_utility_buttons(self) -> None:
        """Create utility buttons."""
        buttons = [
            ("Keyboard", self._open_keyboard_config),
            (get_text(self.config.language, "utility_buttons.updates_manager", "Updates manager"), self._open_updates_manager),
            ("Tweaks", self._open_tweaks),
            ("Settings", self._open_settings)
        ]

        for text, command in buttons:
            btn = ctk.CTkButton(
                self.container,
                text=text,
                command=command,
                fg_color=self.colors["primary"],
                hover_color=self.colors["hover"],
                height=30,
                text_color=self.colors["text"],
                corner_radius=10
            )
            btn.pack(fill="x", padx=10, pady=2)
            if text in ["Keyboard", get_text(self.config.language, "utility_buttons.updates_manager", "Updates manager"), "Tweaks", "Settings"]:
                btn.configure(width=120)

    def _create_brightness_control(self) -> None:
        """Create brightness control slider."""
        brightness_frame = ctk.CTkFrame(self.container, fg_color=self.colors["background"])
        brightness_frame.pack(fill="x", padx=10, pady=10)

        label = ctk.CTkLabel(brightness_frame, text="BRIGHTNESS:", text_color=self.colors["text"])
        label.pack(side="left")

        self.brightness_value = ctk.CTkLabel(
            brightness_frame,
            text="VALUE: 100%",
            text_color=self.colors["text"]
        )
        self.brightness_value.pack(side="right")

        self.brightness_slider = ctk.CTkSlider(
            brightness_frame,
            from_=0,
            to=100,
            command=self._on_brightness_change,
            progress_color=self.colors["primary"],
            button_color=self.colors["primary"],
            button_hover_color=self.colors["hover"],
            corner_radius=10
        )
        self.brightness_slider.pack(fill="x", padx=5)
        self.brightness_slider.set(100)

    def _update_metrics(self) -> None:
        """Update system metrics display."""
        async def update():
            try:
                metrics = await self.hardware.get_metrics()
                logger.debug("Got metrics update: %s", metrics.dict())

                # Update progress bars and labels
                for key, bar in self.metric_bars.items():
                    value = getattr(metrics, key, None)
                    if value is not None:
                        if "temp" in key:
                            # Normalize temperature to 0-100 range for progress bar
                            # Mais afficher la vraie valeur dans le label
                            normalized = min(100, max(0, value - 40) * 1.67)
                            bar.set(normalized / 100)
                            
                            # Formater le label selon le type de température
                            if "cpu" in key:
                                label_text = f"CPU: {value:.1f}°C"
                            elif "igpu" in key:
                                label_text = f"iGPU: {value:.1f}°C"
                            elif "dgpu" in key:
                                label_text = f"dGPU: {value:.1f}°C"
                            else:
                                label_text = f"{key.split('_')[0].upper()}: {value:.1f}°C"
                            
                            self.metric_labels[key].configure(text=label_text)
                            logger.debug(f"Updated temperature metric: {label_text}")
                        else:
                            # Pour les métriques de charge (load)
                            bar.set(value / 100)
                            
                            # Formater le label selon le type de charge
                            if "cpu" in key:
                                label_text = f"CPU: {value:.1f}%"
                            elif "igpu" in key:
                                label_text = f"iGPU: {value:.1f}%"
                            elif "dgpu" in key:
                                label_text = f"dGPU: {value:.1f}%"
                            elif "ram" in key:
                                label_text = f"RAM: {value:.1f}%"
                            else:
                                label_text = f"{key.split('_')[0].upper()}: {value:.1f}%"
                            
                            self.metric_labels[key].configure(text=label_text)
                            logger.debug(f"Updated load metric: {label_text}")
                    else:
                        logger.warning(f"No value for metric: {key}")

                # Update battery indicator
                self._update_battery_status(metrics)
            except Exception as e:
                logger.error(f"Error updating metrics: {e}")
                import traceback
                logger.error("Traceback: %s", traceback.format_exc())

        # Run coroutine in the event loop
        if hasattr(self, 'loop'):
            self.loop.run_until_complete(update())

        # Schedule next update
        self.after(self.config.monitoring_interval, self._update_metrics)

    def _update_battery_status(self, metrics: HardwareMetrics) -> None:
        """Update battery status display."""
        try:
            # Update battery percentage and charging status
            status = f"BATTERY: {metrics.battery_percentage:.0f}% | {'AC' if metrics.is_charging else 'BATTERY'}"
            self.battery_status.configure(text=status)

            # Update time remaining
            if metrics.is_charging:
                time_text = "Plugged In"
            elif metrics.battery_time_remaining > 0:
                hours = int(metrics.battery_time_remaining / 60)
                minutes = int(metrics.battery_time_remaining % 60)
                time_text = f"Time remaining: {hours:02d}:{minutes:02d}"
            else:
                time_text = "Time remaining: --:--"
            
            self.battery_time.configure(text=time_text)
        except Exception as e:
            logger.error(f"Error updating battery status: {e}")
            self.battery_status.configure(text="BATTERY: --% | --")
            self.battery_time.configure(text="Time remaining: --:--")

    def _on_brightness_change(self, value: float) -> None:
        """Handle brightness slider change."""
        async def update_brightness():
            await self.display.set_brightness(int(value))
        
        if hasattr(self, 'loop'):
            self.loop.run_until_complete(update_brightness())
        self.brightness_value.configure(text=f"ACTUEL: {int(value)}%")

    def _open_keyboard_config(self) -> None:
        """Open keyboard configuration website."""
        webbrowser.open("https://keyboard.frame.work/")

    def _open_updates_manager(self) -> None:
        """Open updates manager window."""
        UpdatesManager(self)

    def _open_tweaks(self) -> None:
        """Open tweaks window."""
        TweaksWindow(self)

    def _open_settings(self) -> None:
        """Open settings window."""
        self._create_settings_window()

    def _toggle_window(self) -> None:
        """Toggle window visibility."""
        if self.winfo_viewable():
            self._minimize_to_tray()
        else:
            self.deiconify()
            self.lift()

    def _on_close(self) -> None:
        """Gérer la fermeture de l'application."""
        # Cleanup
        if hasattr(self.power, 'cleanup'):
            self.power.cleanup()
        
        # Destroy window
        self.quit()

    def _quit_app(self) -> None:
        """Quit the application."""
        try:
            # Stop the tray icon at class level
            with self._tray_lock:
                if FrameworkControlCenter._tray_instance is not None:
                    try:
                        FrameworkControlCenter._tray_instance.stop()
                    except Exception as e:
                        logger.error(f"Error stopping tray icon: {e}")
                    FrameworkControlCenter._tray_instance = None
                    self.tray_icon = None
            
            # Clean up async event loop
            if hasattr(self, 'loop'):
                try:
                    pending = asyncio.all_tasks(self.loop)
                    for task in pending:
                        task.cancel()
                    self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    self.loop.close()
                except Exception as e:
                    logger.error(f"Error cleaning up async tasks: {e}")
            
            self.quit()
        except Exception as e:
            logger.error(f"Error during application quit: {e}")
            # Forcer la fermeture en cas d'erreur
            self.quit()

    def _load_config(self) -> SystemConfig:
        """Load configuration from file or create default."""
        try:
            if self.config_path.exists():
                with open(self.config_path, encoding="utf-8") as f:
                    config_data = json.load(f)
                
                # Create config object from loaded data
                config = SystemConfig(**config_data)
                
                # Check if startup task exists and update config accordingly
                config.start_with_windows = self.tweaks.is_startup_task_exists()
                
                # Apply settings immediately
                if config.start_minimized:
                    self.withdraw()
                
                if config.minimize_to_tray:
                    self._setup_tray()
                
                # Apply theme
                ctk.set_appearance_mode(config.theme)
                
                # Apply monitoring interval
                if hasattr(self, '_update_metrics'):
                    self.after_cancel(self._update_metrics)
                    self.after(config.monitoring_interval, self._update_metrics)
                
                return config
            else:
                # Create default config if file doesn't exist
                config = SystemConfig()
                # Save default config
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(config.dict(), f, indent=4)
                return config
                
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return SystemConfig()  # Return default config if loading fails

    def _create_default_icon(self) -> None:
        """Create a default tray icon."""
        try:
            icon_path = Path("assets/logo.ico")
            if icon_path.exists():
                return Image.open(icon_path)
        except Exception as e:
            logger.error(f"Failed to load icon: {e}")
            
        # Fallback to creating a new icon if logo.ico is not found
        img = Image.new("RGB", (64, 64), self.colors["primary"])
        img.save("assets/icon.png")
        return img

    def _set_power_profile_sync(self, profile_name: str) -> None:
        """Synchronous wrapper for _set_power_profile."""
        try:
            if not hasattr(self, 'loop'):
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._set_power_profile(profile_name))
        except Exception as e:
            logger.error(f"Error in _set_power_profile_sync: {e}")

    async def _set_power_profile(self, profile_name: str) -> None:
        """Set power profile."""
        try:
            defaults_path = get_resource_path("configs/defaults.json")
            if not Path(defaults_path).exists():
                logger.error("Defaults configuration file not found")
                return

            with open(defaults_path) as f:
                config = json.load(f)
                if "profiles" not in config or profile_name not in config["profiles"]:
                    logger.error(f"Profile {profile_name} not found in defaults.json")
                    return
                profile_data = config["profiles"][profile_name]
                profile = PowerProfile(
                    name=profile_name,
                    **profile_data
                )
            
            success = await self.power.apply_profile(profile)
            if success:
                self.config.current_profile = profile_name
                
                # Mettre à jour l'état des boutons
                if profile_name in self.profile_buttons:
                    self._update_button_state("profile", self.profile_buttons[profile_name])
                
                # Show notification if minimized
                if not self.winfo_viewable():
                    with self._tray_lock:
                        if self.tray_icon is not None:
                            try:
                                self.tray_icon.notify(
                                    title="Profile Changed",
                                    message=f"Power profile changed to {profile_name}"
                                )
                            except Exception as e:
                                logger.error(f"Error showing tray notification: {e}")
            else:
                logger.error(f"Failed to apply power profile: {profile_name}")
        except Exception as e:
            logger.error(f"Error setting power profile: {e}")

    def _set_refresh_rate_sync(self, mode: str) -> None:
        """Synchronous wrapper for _set_refresh_rate."""
        if hasattr(self, 'loop'):
            self.loop.run_until_complete(self._set_refresh_rate(mode))

    async def _set_refresh_rate(self, mode: str) -> None:
        """Set display refresh rate."""
        try:
            # Déterminer le taux de rafraîchissement maximum en fonction du modèle
            max_rate = "165" if "16" in self.model.name else "60"
            
            # Traiter le mode
            if mode == "Auto":
                actual_mode = "auto"
            else:
                # Si le mode est déjà en Hz, on le nettoie
                actual_mode = mode.replace("Hz", "")
            
            logger.debug(f"Setting refresh rate: mode={actual_mode}, max_rate={max_rate}")
            await self.display.set_refresh_rate(actual_mode, max_rate)
            self.config.refresh_rate_mode = mode
            
            # Mettre à jour l'état des boutons
            if mode in self.refresh_buttons:
                self._update_button_state("refresh", self.refresh_buttons[mode])
            
            # Show notification if minimized
            if not self.winfo_viewable():
                with self._tray_lock:
                    if self.tray_icon is not None:
                        try:
                            self.tray_icon.notify(
                                title="Refresh Rate Changed",
                                message=f"Display refresh rate mode changed to {mode}"
                            )
                        except Exception as e:
                            logger.error(f"Error showing tray notification: {e}")
        except Exception as e:
            logger.error(f"Error setting refresh rate: {e}")
            import traceback
            logger.error("Traceback: %s", traceback.format_exc())

    def _setup_tray(self) -> None:
        """Setup system tray icon and menu."""
        with self._tray_lock:
            # If class already has a tray icon instance, use it
            if FrameworkControlCenter._tray_instance is not None:
                self.tray_icon = FrameworkControlCenter._tray_instance
                return

            try:
                import pystray
                from PIL import Image
                import sys
                import os

                # Get the correct path for the icon file
                if getattr(sys, 'frozen', False):
                    # If the application is run from the exe
                    base_path = sys._MEIPASS
                else:
                    # If the application is run from a Python interpreter
                    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

                # Create tray icon
                icon_path = os.path.join(base_path, "assets", "logo.ico")
                logger.debug(f"Looking for icon at: {icon_path}")
                
                if not os.path.exists(icon_path):
                    logger.error("Icon file not found: %s", icon_path)
                    # Create a default icon as fallback
                    img = Image.new("RGB", (64, 64), self.colors["primary"])
                    fallback_path = os.path.join(base_path, "assets", "icon.png")
                    os.makedirs(os.path.dirname(fallback_path), exist_ok=True)
                    img.save(fallback_path)
                    icon_path = fallback_path

                # Create the icon instance
                icon = pystray.Icon(
                    name="Framework CC",
                    icon=Image.open(icon_path),
                    title="Framework Control Center",
                    menu=pystray.Menu(
                        pystray.MenuItem("Show/Hide", self._toggle_window),
                        pystray.MenuItem("Exit", self._quit_app)
                    )
                )

                # Store the icon instance at class level
                FrameworkControlCenter._tray_instance = icon
                self.tray_icon = icon

                # Start the icon in a separate thread
                threading.Thread(target=self.tray_icon.run, daemon=True).start()

            except Exception as e:
                logger.error(f"Error setting up tray icon: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                FrameworkControlCenter._tray_instance = None
                self.tray_icon = None

    def _start_drag(self, event):
        """Commencer le déplacement de la fenêtre."""
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()
        
    def _on_drag(self, event):
        """Déplacer la fenêtre."""
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.geometry(f"+{x}+{y}")
        
    def _minimize_to_tray(self) -> None:
        """Minimize window to system tray."""
        self.withdraw()
        with self._tray_lock:
            if self.tray_icon is not None:
                try:
                    self.tray_icon.notify(
                        title="Framework Control Center",
                        message="Application minimized to tray"
                    )
                except Exception as e:
                    logger.error(f"Error showing tray notification: {e}")

    def _create_battery_status(self) -> None:
        """Create battery status display."""
        battery_frame = ctk.CTkFrame(self.container, fg_color=self.colors["background"])
        battery_frame.pack(fill="x", padx=10, pady=5)

        # Battery percentage and charging status
        self.battery_status = ctk.CTkLabel(
            battery_frame,
            text="BATTERY: --% | --",
            text_color=self.colors["text"],
            font=("Roboto", 11)
        )
        self.battery_status.pack(side="top", pady=(0, 2))

        # Battery time remaining
        self.battery_time = ctk.CTkLabel(
            battery_frame,
            text="Time remaining: --:--",
            text_color=self.colors["text"],
            font=("Roboto", 11)
        )
        self.battery_time.pack(side="top")

    def _setup_hotkeys(self) -> None:
        """Setup global hotkeys."""
        import keyboard
        keyboard.add_hotkey("F12", self._toggle_window)

    def _update_button_state(self, button_type: str, active_button: ctk.CTkButton) -> None:
        """Update button states when a new button becomes active."""
        # Réinitialiser l'ancien bouton actif
        if self.active_buttons[button_type]:
            self.active_buttons[button_type].configure(
                border_color=self.colors["background"],
                text_color=self.colors["text"],
                fg_color=self.colors["primary"]
            )

        # Mettre à jour le nouveau bouton actif
        active_button.configure(
            border_color=self.colors["border_active"],
            text_color=self.colors["text_active"],
            fg_color=self.colors["hover"]
        )

        # Sauvegarder le nouveau bouton actif
        self.active_buttons[button_type] = active_button

    def _update_window_text(self) -> None:
        """Update all text in the window with the current language."""
        # Update window title
        self.title(get_text(self.config.language, "window_title"))
        
        # Update power profile buttons
        for profile, btn in self.profile_buttons.items():
            btn.configure(text=get_text(self.config.language, f"power_profiles.{profile.lower()}"))
        
        # Update refresh rate buttons
        for mode, btn in self.refresh_buttons.items():
            btn.configure(text=get_text(self.config.language, f"refresh_rates.{mode.lower()}"))
        
        # Update utility buttons
        for widget in self.container.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                text = widget.cget("text")
                if text in ["Keyboard", get_text(self.language, "utility_buttons.updates_manager", "Updates manager"), "Tweaks", "Settings"]:
                    key = text.lower().replace(" ", "_")
                    widget.configure(text=get_text(self.config.language, f"utility_buttons.{key}"))
        
        # Update brightness labels
        for widget in self.container.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                text = widget.cget("text")
                if text.startswith("BRIGHTNESS:"):
                    widget.configure(text=get_text(self.config.language, "brightness"))
                elif text.startswith("ACTUEL:"):
                    current_value = text.split(":")[1].strip()
                    widget.configure(text=f"{get_text(self.config.language, 'current')} {current_value}")
                elif text.startswith("BATTERY:"):
                    battery_value = text.split(":")[1].strip()
                    widget.configure(text=f"{get_text(self.config.language, 'battery')} {battery_value}")
                elif text.startswith("Time remaining:"):
                    if "Plugged In" in text:
                        widget.configure(text=get_text(self.config.language, "plugged_in"))
                    else:
                        time_value = text.split(":")[1].strip()
                        widget.configure(text=f"{get_text(self.config.language, 'time_remaining')} {time_value}")

    def _initialize_default_profiles(self) -> None:
        """Initialize default power and refresh rate profiles at startup."""
        try:
            # Set Balanced power profile
            self._set_power_profile_sync("Balanced")
            
            # Set Auto refresh rate
            self._set_refresh_rate_sync("Auto")
            
            logger.info("Default profiles initialized: Balanced power profile and Auto refresh rate")
            
            # Update window text with current language
            self._update_window_text()
            
        except Exception as e:
            logger.error(f"Error initializing default profiles: {e}")

    def _on_language_change(self, value: str) -> None:
        """Handle language change."""
        self.config.language = value
        # Update font when language changes
        self.current_font = load_custom_font(value)
        # Update all open windows
        for window in FrameworkControlCenter._open_windows:
            if window.winfo_exists():
                if hasattr(window, 'current_font'):
                    window.current_font = self.current_font
                if hasattr(window, '_update_window_text'):
                    window._update_window_text()
                if hasattr(window, '_update_widgets_font'):
                    window._update_widgets_font()
            else:
                FrameworkControlCenter._open_windows.remove(window)

    def _update_widgets_font(self) -> None:
        """Update font in all widgets."""
        def update_widget_font(widget):
            try:
                if hasattr(widget, 'cget') and 'font' in widget.keys():
                    current_font = widget.cget('font')
                    if isinstance(current_font, tuple):
                        # Keep the current font size if it's explicitly set
                        size = current_font[1]
                        weight = current_font[2] if len(current_font) > 2 else "normal"
                    else:
                        # Use the default size from the custom font
                        if isinstance(self.current_font, tuple):
                            size = self.current_font[1]
                        else:
                            size = 10
                        weight = "normal"
                    
                    # Use the font name from current_font
                    font_name = self.current_font[0] if isinstance(self.current_font, tuple) else self.current_font
                    widget.configure(font=(font_name, size))
                
                # Recursively update child widgets
                for child in widget.winfo_children():
                    update_widget_font(child)
            except Exception as e:
                logger.error(f"Error updating font for widget: {e}")

        update_widget_font(self)

    def _create_settings_window(self) -> None:
        """Create settings window."""
        if hasattr(self, 'settings_window') and self.settings_window.winfo_exists():
            self.settings_window.focus()
            return

        self.settings_window = ctk.CTkToplevel(self)
        self.settings_window.title(get_text(self.config.language, "settings_title"))
        self.settings_window.geometry("400x500")
        self.settings_window.resizable(False, False)
        
        # Configure window style
        self.settings_window.configure(fg_color=self.colors["background"])
        
        try:
            if sys.platform.startswith('win'):
                self.settings_window.after(200, lambda: self.settings_window.iconbitmap(str(Path("assets/logo.ico").absolute())))
            else:
                self.settings_window.iconbitmap(str(Path("assets/logo.ico")))
        except Exception as e:
            logger.error(f"Failed to set window icon: {e}")
        
        # Main container with dark background
        container = ctk.CTkFrame(self.settings_window, fg_color=self.colors["background"])
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Theme selection
        theme_label = ctk.CTkLabel(
            container,
            text=get_text(self.config.language, "theme"),
            text_color=self.colors["text"],
            font=("Roboto", 11)
        )
        theme_label.pack(anchor="w", pady=(0, 5))
        
        theme_var = ctk.StringVar(value=self.config.theme)
        theme_menu = ctk.CTkOptionMenu(
            container,
            values=["dark", "light"],
            variable=theme_var,
            fg_color="#2D2D2D",
            button_color=self.colors["primary"],
            button_hover_color=self.colors["hover"],
            text_color=self.colors["text"]
        )
        theme_menu.pack(fill="x", pady=(0, 15))

        # Language selection
        lang_label = ctk.CTkLabel(
            container,
            text=get_text(self.config.language, "language"),
            text_color=self.colors["text"],
            font=("Roboto", 11)
        )
        lang_label.pack(anchor="w", pady=(0, 5))
        
        lang_var = ctk.StringVar(value=self.config.language)
        language_menu = ctk.CTkOptionMenu(
            container,
            values=list(language_names.keys()),
            variable=lang_var,
            fg_color="#2D2D2D",
            button_color=self.colors["primary"],
            button_hover_color=self.colors["hover"],
            text_color=self.colors["text"]
        )
        language_menu.pack(fill="x", pady=(0, 15))

        # Minimize to tray option
        minimize_var = ctk.BooleanVar(value=self.config.minimize_to_tray)
        minimize_check = ctk.CTkCheckBox(
            container,
            text=get_text(self.config.language, "minimize_to_tray"),
            variable=minimize_var,
            fg_color=self.colors["primary"],
            hover_color=self.colors["hover"],
            text_color=self.colors["text"],
            border_color=self.colors["text"],
            corner_radius=6
        )
        minimize_check.pack(anchor="w", pady=(0, 10))

        # Start minimized option
        start_min_var = ctk.BooleanVar(value=self.config.start_minimized)
        start_min_check = ctk.CTkCheckBox(
            container,
            text=get_text(self.config.language, "start_minimized"),
            variable=start_min_var,
            fg_color=self.colors["primary"],
            hover_color=self.colors["hover"],
            text_color=self.colors["text"],
            border_color=self.colors["text"],
            corner_radius=6
        )
        start_min_check.pack(anchor="w", pady=(0, 10))

        # Start with Windows option
        start_windows_var = ctk.BooleanVar(value=self.config.start_with_windows)
        start_windows_check = ctk.CTkCheckBox(
            container,
            text=get_text(self.config.language, "start_with_windows"),
            variable=start_windows_var,
            fg_color=self.colors["primary"],
            hover_color=self.colors["hover"],
            text_color=self.colors["text"],
            border_color=self.colors["text"],
            corner_radius=6
        )
        start_windows_check.pack(anchor="w", pady=(0, 15))

        # Monitoring interval
        interval_label = ctk.CTkLabel(
            container,
            text=get_text(self.config.language, "monitoring_interval"),
            text_color=self.colors["text"],
            font=("Roboto", 11)
        )
        interval_label.pack(anchor="w", pady=(0, 5))
        
        interval_var = ctk.StringVar(value=str(self.config.monitoring_interval))
        interval_entry = ctk.CTkEntry(
            container,
            textvariable=interval_var,
            fg_color="#2D2D2D",
            text_color=self.colors["text"],
            border_color=self.colors["primary"]
        )
        interval_entry.pack(fill="x", pady=(0, 15))
        
        # Save button
        save_btn = ctk.CTkButton(
            container,
            text=get_text(self.config.language, "save"),
            command=lambda: self._save_settings(
                theme_var.get(),
                lang_var.get(),
                minimize_var.get(),
                start_min_var.get(),
                start_windows_var.get(),
                interval_var.get()
            ),
            fg_color=self.colors["primary"],
            hover_color=self.colors["hover"],
            text_color=self.colors["text"],
            height=35,
            corner_radius=6
        )
        save_btn.pack(fill="x", pady=(20, 0))

    def _save_settings(self, theme: str, language: str, minimize_to_tray: bool,
                      start_minimized: bool, start_with_windows: bool, monitoring_interval: str) -> None:
        """Save settings to config file."""
        try:
            # Update config values
            self.config.theme = theme
            self.config.language = language
            self.config.minimize_to_tray = minimize_to_tray
            self.config.start_minimized = start_minimized
            self.config.start_with_windows = start_with_windows
            self.config.monitoring_interval = int(monitoring_interval)
            
            # Save to file
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config.dict(), f, indent=4)
            
            # Apply settings immediately
            ctk.set_appearance_mode(theme)
            self.current_font = load_custom_font(language)
            self._update_window_text()
            self._update_widgets_font()
            
            # Update startup task if needed
            if start_with_windows:
                # Get the path to the executable
                if getattr(sys, 'frozen', False):
                    # Running as compiled executable
                    exe_path = sys.executable
                else:
                    # Running as script
                    exe_path = os.path.abspath(sys.argv[0])
                
                success = self.tweaks.create_startup_task(exe_path)
                if not success:
                    logger.error("Failed to create startup task")
            else:
                success = self.tweaks.remove_startup_task()
                if not success:
                    logger.error("Failed to remove startup task")
            
            # Apply minimize_to_tray setting immediately
            if minimize_to_tray and not hasattr(self, 'tray_icon'):
                self._setup_tray()
            elif not minimize_to_tray and hasattr(self, 'tray_icon'):
                with self._tray_lock:
                    if self.tray_icon is not None:
                        self.tray_icon.stop()
                        self.tray_icon = None
            
            # Apply monitoring interval immediately
            if hasattr(self, '_update_metrics'):
                self.after_cancel(self._update_metrics)
                self.after(self.config.monitoring_interval, self._update_metrics)
            
            # Close settings window
            if hasattr(self, 'settings_window') and self.settings_window.winfo_exists():
                self.settings_window.destroy()
            
            logger.info("Settings saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    def _update_theme(self, value: str) -> None:
        """Handle theme change."""
        self.config.theme = value
        ctk.set_appearance_mode(value)

    def _update_language(self, value: str) -> None:
        """Handle language change."""
        self.config.language = value
        # Update font when language changes
        self.current_font = load_custom_font(value)
        # Update all open windows
        for window in FrameworkControlCenter._open_windows:
            if window.winfo_exists():
                if hasattr(window, 'current_font'):
                    window.current_font = self.current_font
                if hasattr(window, '_update_window_text'):
                    window._update_window_text()
                if hasattr(window, '_update_widgets_font'):
                    window._update_widgets_font()
            else:
                FrameworkControlCenter._open_windows.remove(window)

    def _update_minimize_to_tray(self, value: bool) -> None:
        """Handle minimize to tray change."""
        self.config.minimize_to_tray = value

    def _update_start_minimized(self, value: bool) -> None:
        """Handle start minimized change."""
        self.config.start_minimized = value

    def _update_start_with_windows(self, value: bool) -> None:
        """Handle start with Windows change."""
        try:
            if value:
                # Get the path to the executable
                if getattr(sys, 'frozen', False):
                    # Running as compiled executable
                    exe_path = sys.executable
                else:
                    # Running as script
                    exe_path = os.path.abspath(sys.argv[0])

                success = self.tweaks.create_startup_task(exe_path)
            else:
                success = self.tweaks.remove_startup_task()

            if success:
                self.config.start_with_windows = value
                self._save_config()
                logger.info(f"Start with Windows {'enabled' if value else 'disabled'}")
            else:
                logger.error("Failed to update start with Windows setting")
                # Revert checkbox if operation failed
                if hasattr(self, 'settings_window') and self.settings_window.winfo_exists():
                    for widget in self.settings_window.winfo_children():
                        if isinstance(widget, ctk.CTkCheckBox) and widget.cget("text") == get_text("start_with_windows", self.config.language):
                            widget.deselect() if value else widget.select()
        except Exception as e:
            logger.error(f"Error updating start with Windows setting: {e}")

    def _restore_services(self) -> None:
        """Restore services to automatic startup."""
        try:
            tweaks = WindowsTweaks()
            self._add_log("\nRestoring services to automatic startup...\n")
            
            success = tweaks.restore_services()
            
            if success:
                self._add_log("✅ Services restored successfully\n")
                # Re-enable all service-related checkboxes
                for checkbox in self.system_checkboxes.values():
                    checkbox.configure(state="normal")
            else:
                self._add_log("❌ Failed to restore services\n")
        except Exception as e:
            logger.error(f"Error restoring services: {e}")
            self._add_log(f"❌ Error restoring services: {e}\n") 

    def _check_log_file_size(self) -> None:
        """Periodically check and rotate log file if needed."""
        try:
            log_file = Path("logs") / f"{datetime.now().strftime('%Y-%m-%d')}.log"
            check_and_rotate_log(log_file)
        except Exception as e:
            logger.error(f"Error checking log file size: {e}")
        finally:
            # Schedule next check in 5 minutes
            self.after(300000, self._check_log_file_size)


class UpdatesManager(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        FrameworkControlCenter._open_windows.append(self)  # Add window to list
        self.parent = parent
        self.title(get_text(self.parent.config.language, "updates_title"))
        self.geometry("800x600")
        self.colors = parent.colors
        self.current_font = load_custom_font(self.parent.config.language)
        
        # Configurer la couleur de fond de la fenêtre
        self.configure(fg_color=self.colors["background"])
        
        # Configurer l'icône
        try:
            if sys.platform.startswith('win'):
                self.after(200, lambda: self.iconbitmap(str(Path("assets/logo.ico").absolute())))
            else:
                self.iconbitmap(str(Path("assets/logo.ico")))
        except Exception as e:
            logger.error(f"Failed to set window icon: {e}")
        
        # Initialiser les variables
        self.packages = {
            'winget': []
        }
        
        # Créer l'interface
        self._create_widgets()
        
        # Rendre la fenêtre modale
        self.transient(parent)
        self.grab_set()
        self.focus_set()
        
        # Gérer la fermeture de la fenêtre
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        """Gérer la fermeture propre de la fenêtre."""
        try:
            FrameworkControlCenter._open_windows.remove(self)  # Remove window from list
            self.grab_release()
            self.destroy()
        except Exception as e:
            logger.error(f"Error closing Update Manager: {e}")
            self.destroy()

    def _create_widgets(self) -> None:
        """Create updates manager widgets."""
        # Main container
        container = ctk.CTkFrame(self, fg_color=self.colors["background"])
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top frame pour les boutons de drivers
        top_frame = ctk.CTkFrame(container, fg_color=self.colors["background"])
        top_frame.pack(fill="x", pady=(0, 10))
        
        # Label "Drivers"
        drivers_label = ctk.CTkLabel(
            top_frame,
            text="Drivers & BIOS",
            text_color=self.colors["text"],
            font=("Roboto", 12, "bold")
        )
        drivers_label.pack(side="left", padx=5)
        
        # Frame pour les boutons de drivers (alignés à droite)
        drivers_buttons = ctk.CTkFrame(top_frame, fg_color="transparent")
        drivers_buttons.pack(side="right")
        
        # Bouton Framework Drivers
        framework_btn = ctk.CTkButton(
            drivers_buttons,
            text="Framework Drivers",
            command=lambda: webbrowser.open("https://knowledgebase.frame.work/en_us/bios-and-drivers-downloads-rJ3PaCexh"),
            fg_color=self.colors["primary"],
            hover_color=self.colors["hover"],
            text_color=self.colors["text"],
            height=32,
            width=150
        )
        framework_btn.pack(side="left", padx=5)
        
        # Bouton AMD Drivers
        amd_btn = ctk.CTkButton(
            drivers_buttons,
            text="AMD Drivers",
            command=lambda: webbrowser.open("https://www.amd.com/en/support/download/drivers.html"),
            fg_color=self.colors["primary"],
            hover_color=self.colors["hover"],
            text_color=self.colors["text"],
            height=32,
            width=150
        )
        amd_btn.pack(side="left", padx=5)
        
        # Separator
        separator = ctk.CTkFrame(container, height=2, fg_color=self.colors["primary"])
        separator.pack(fill="x", pady=10)
        
        # Frame principal pour la liste des paquets
        main_frame = ctk.CTkFrame(container, fg_color=self.colors["background"])
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        main_frame.grid_columnconfigure(0, weight=70)
        main_frame.grid_columnconfigure(1, weight=30)
        
        # Frame pour la liste des paquets (70% de la largeur)
        packages_frame = ctk.CTkFrame(main_frame, fg_color=self.colors["background"])
        packages_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Label pour la section des paquets avec un style amélioré
        packages_header = ctk.CTkFrame(packages_frame, fg_color=self.colors["primary"], height=40)
        packages_header.pack(fill="x", pady=(0, 10))
        packages_header.pack_propagate(False)
        
        ctk.CTkLabel(
            packages_header,
            text="System Packages",
            text_color=self.colors["text"],
            font=("Roboto", 12, "bold")
        ).pack(side="left", padx=10, pady=5)
        
        # En-tête des colonnes avec un style amélioré
        header_frame = ctk.CTkFrame(packages_frame, fg_color="#2D2D2D", height=35)
        header_frame.pack(fill="x", padx=5, pady=(0, 5))
        header_frame.pack_propagate(False)
        header_frame.grid_columnconfigure(0, weight=0)  # Checkbox
        header_frame.grid_columnconfigure(1, weight=2)  # Nom
        header_frame.grid_columnconfigure(2, weight=1)  # Version actuelle
        header_frame.grid_columnconfigure(3, weight=1)  # Nouvelle version
        
        # Checkbox "Select All"
        self.select_all_var = ctk.BooleanVar()
        select_all = ctk.CTkCheckBox(
            header_frame,
            text="",
            variable=self.select_all_var,
            command=self._toggle_all_packages,
            width=20,
            height=20,
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=5,
            fg_color=self.colors["primary"],
            hover_color=self.colors["hover"],
            border_color=self.colors["text"]
        )
        select_all.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        # Nom
        ctk.CTkLabel(
            header_frame,
            text="Name",
            text_color=self.colors["text"],
            font=("Roboto", 11, "bold"),
            anchor="w",
            width=200
        ).grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        # Version actuelle
        ctk.CTkLabel(
            header_frame,
            text="Current",
            text_color=self.colors["text"],
            font=("Roboto", 11, "bold"),
            anchor="e",
            width=100
        ).grid(row=0, column=2, sticky="e", padx=10, pady=5)
        
        # Nouvelle version
        ctk.CTkLabel(
            header_frame,
            text="Available",
            text_color=self.colors["text"],
            font=("Roboto", 11, "bold"),
            anchor="e",
            width=100
        ).grid(row=0, column=3, sticky="e", padx=10, pady=5)
        
        # Liste des paquets avec scrollbar et style amélioré
        self.packages_list = ctk.CTkScrollableFrame(
            packages_frame,
            fg_color="#2D2D2D",
            label_text="",
            label_fg_color=self.colors["background"],
            corner_radius=10
        )
        self.packages_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Frame pour les logs (30% de la largeur)
        logs_frame = ctk.CTkFrame(main_frame, fg_color=self.colors["background"])
        logs_frame.grid(row=0, column=1, sticky="nsew")
        
        # En-tête des logs avec style amélioré
        logs_header = ctk.CTkFrame(logs_frame, fg_color=self.colors["primary"], height=40)
        logs_header.pack(fill="x", pady=(0, 10))
        logs_header.pack_propagate(False)
        
        ctk.CTkLabel(
            logs_header,
            text="Logs",
            text_color=self.colors["text"],
            font=("Roboto", 12, "bold")
        ).pack(side="left", padx=10, pady=5)
        
        # Zone de texte pour les logs avec style amélioré
        self.log_text = ctk.CTkTextbox(
            logs_frame,
            fg_color="#2D2D2D",
            text_color=self.colors["text"],
            wrap="word",
            corner_radius=10
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create bottom buttons frame
        bottom_buttons = ctk.CTkFrame(container, fg_color="transparent")
        bottom_buttons.pack(fill="x", pady=(10, 0))
        
        # Create Check Updates button
        check_button = ctk.CTkButton(
            bottom_buttons,
            text="Check installed apps",
            command=lambda: threading.Thread(
                target=self._check_updates,
                daemon=True
            ).start(),
            height=35,
            fg_color=self.colors["button"],
            hover_color=self.colors["hover"],
            text_color=self.colors["text"],
            corner_radius=10
        )
        check_button.pack(side="left", padx=5)
        
        # Create Update Selected button
        update_button = ctk.CTkButton(
            bottom_buttons,
            text="Update selection",
            command=self._update_selected,
            height=35,
            fg_color=self.colors["button"],
            hover_color=self.colors["hover"],
            text_color=self.colors["text"],
            corner_radius=10
        )
        update_button.pack(side="left", padx=5)
        
        # Create Refresh List button
        refresh_button = ctk.CTkButton(
            bottom_buttons,
            text="Refresh List",
            command=lambda: threading.Thread(
                target=self._check_updates,
                daemon=True
            ).start(),
            height=35,
            fg_color=self.colors["button"],
            hover_color=self.colors["hover"],
            text_color=self.colors["text"],
            corner_radius=10
        )
        refresh_button.pack(side="left", padx=5)
        
        # Initial update check
        threading.Thread(target=self._check_updates, daemon=True).start()

    def _check_updates(self) -> None:
        """Vérifier les mises à jour disponibles."""
        try:
            # Nettoyer la liste des paquets
            for widget in self.packages_list.winfo_children():
                widget.destroy()
            
            # Effacer les logs existants
            self.log_text.delete("1.0", "end")
            
            # Ajouter un message de démarrage dans les logs
            self._add_log("Checking for system updates...\n")
            
            self._check_winget_updates()
                
        except Exception as e:
            self._add_log(f"Error checking updates: {str(e)}\n")
            logger.error(f"Error checking updates: {e}")

    def _check_winget_updates(self) -> None:
        """Vérifier les mises à jour winget."""
        try:
            # Configure process to hide window
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            # Liste des paquets installés
            process = subprocess.run(
                ["winget", "list", "--accept-source-agreements", "--disable-interactivity"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                startupinfo=startupinfo
            )
            
            if process.returncode != 0:
                raise ValueError(f"winget list failed: {process.stderr}")
            
            self._add_log("Scanning installed packages...\n")
            
            # Parser la sortie pour extraire les paquets installés
            installed = {}
            lines = process.stdout.split('\n')
            
            # Chercher la ligne d'en-tête (plusieurs formats possibles)
            header_index = -1
            for i, line in enumerate(lines):
                if any(all(col in line for col in combo) for combo in [
                    ["Name", "Id", "Version"],  # Format standard
                    ["Nom", "ID", "Version"],   # Format français
                    ["名称", "ID", "版"]      # Format autres langues
                ]):
                    header_index = i
                    break
            
            if header_index == -1:
                # Essayer une autre commande
                process = subprocess.run(
                    ["winget", "list", "--source", "winget", "--accept-source-agreements"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    startupinfo=startupinfo
                )
                lines = process.stdout.split('\n')
                for i, line in enumerate(lines):
                    if any(all(col in line for col in combo) for combo in [
                        ["Name", "Id", "Version"],
                        ["Nom", "ID", "Version"],
                        ["名称", "ID", "版本"]
                    ]):
                        header_index = i
                        break
            
            if header_index == -1:
                self._add_log("Warning: Could not parse winget list output format\n")
                self._add_log("Raw output:\n" + process.stdout + "\n")
                return
            
            # Extraire les positions des colonnes
            header = lines[header_index]
            # Chercher les colonnes dans différentes langues
            name_pos = max(header.find("Name"), header.find("Nom"), header.find("名称"))
            id_pos = max(header.find("Id"), header.find("ID"), header.find("标识符"))
            version_pos = max(header.find("Version"), header.find("版本"))
            
            # Parser les paquets installés
            for line in lines[header_index + 2:]:  # Skip header and separator
                if line.strip() and not line.startswith("-"):
                    try:
                        if len(line) > version_pos:
                            name = line[name_pos:id_pos].strip()
                            version = line[version_pos:].strip().split()[0]
                            if name and version:
                                installed[name] = version
                    except Exception as e:
                        logger.debug(f"Failed to parse line: {line}, error: {e}")
                        continue
            
            self._add_log(f"Found {len(installed)} installed packages\n")
            self._add_log("Checking for updates...\n")
            
            # Vérifier les mises à jour disponibles
            process = subprocess.run(
                ["winget", "upgrade", "--include-unknown", "--disable-interactivity", "--accept-source-agreements"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                startupinfo=startupinfo
            )
            
            if process.returncode != 0:
                raise ValueError(f"winget upgrade check failed: {process.stderr}")
            
            # Parser la sortie des mises à jour
            updates = {}
            lines = process.stdout.split('\n')
            
            # Chercher la ligne d'en-tête
            header_index = -1
            for i, line in enumerate(lines):
                if any(all(col in line for col in combo) for combo in [
                    ["Name", "Version", "Available"],
                    ["Nom", "Version", "Disponible"],
                    ["名称", "版本", "可用"]
                ]):
                    header_index = i
                    break
            
            if header_index != -1:
                # Extraire les positions des colonnes
                header = lines[header_index]
                name_pos = max(header.find("Name"), header.find("Nom"), header.find("名称"))
                version_pos = header.find("Version")
                available_pos = max(header.find("Available"), header.find("Disponible"), header.find("可用"))
                
                # Parser les mises à jour disponibles
                for line in lines[header_index + 2:]:  # Skip header and separator
                    if line.strip() and not line.startswith("-"):
                        try:
                            if len(line) > available_pos:
                                name = line[name_pos:version_pos].strip()
                                current = line[version_pos:available_pos].strip()
                                new = line[available_pos:].strip()
                                if name and current and new:
                                    updates[name] = (current, new)
                        except Exception as e:
                            logger.debug(f"Failed to parse update line: {line}, error: {e}")
                            continue
            
            # Afficher d'abord les paquets avec des mises à jour
            for name, (current, new) in updates.items():
                self._add_package_to_list(name, current, new)
                self._add_log(f"Update available: {name} ({current} → {new})\n")
            
            # Puis afficher les autres paquets installés
            for name, version in installed.items():
                if name not in updates:
                    self._add_package_to_list(name, version, None)
            
            self._add_log(f"\nFound {len(updates)} updates available.\n")
            
        except Exception as e:
            self._add_log(f"Error: {str(e)}\n")
            logger.error(f"Error checking winget updates: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    def _add_package_to_list(
        self,
        name: str,
        current_version: str,
        new_version: Optional[str]
    ) -> None:
        """Ajouter un paquet à la liste avec son statut de mise à jour."""
        # Frame pour le paquet avec fond transparent
        package_frame = ctk.CTkFrame(self.packages_list, fg_color="transparent")
        package_frame.pack(fill="x", padx=5, pady=2)
        package_frame.grid_columnconfigure(0, weight=0)  # Checkbox
        package_frame.grid_columnconfigure(1, weight=2)  # Nom (plus large)
        package_frame.grid_columnconfigure(2, weight=1)  # Version actuelle
        package_frame.grid_columnconfigure(3, weight=1)  # Flèche et nouvelle version
        
        # Checkbox pour la sélection (colonne 0)
        checkbox_var = ctk.BooleanVar()
        checkbox = ctk.CTkCheckBox(
            package_frame,
            text="",
            variable=checkbox_var,
            width=20,
            height=20,
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=5,
            fg_color=self.colors["primary"],
            hover_color=self.colors["hover"],
            border_color=self.colors["text"]
        )
        checkbox.grid(row=0, column=0, sticky="w", padx=5)
        
        # Stocker la référence à la checkbox dans le frame
        package_frame.checkbox = checkbox_var
        package_frame.package_name = name
        
        # Nom du paquet (colonne 1)
        name_label = ctk.CTkLabel(
            package_frame,
            text=name,
            text_color=self.colors["text"],
            anchor="w",
            width=200  # Largeur fixe pour le nom
        )
        name_label.grid(row=0, column=1, sticky="w", padx=5)
        
        # Version actuelle (colonne 2)
        current_label = ctk.CTkLabel(
            package_frame,
            text=current_version,
            text_color=self.colors["text"],
            anchor="e",
            width=100  # Largeur fixe pour la version
        )
        current_label.grid(row=0, column=2, sticky="e", padx=5)
        
        # Nouvelle version (colonne 3)
        if new_version:
            version_frame = ctk.CTkFrame(package_frame, fg_color="transparent")
            version_frame.grid(row=0, column=3, sticky="e", padx=5)
            
            # Flèche
            arrow_label = ctk.CTkLabel(
                version_frame,
                text="→",
                text_color="#4CAF50",  # Vert
                anchor="e"
            )
            arrow_label.pack(side="left", padx=2)
            
            # Nouvelle version
            update_label = ctk.CTkLabel(
                version_frame,
                text=new_version,
                text_color="#4CAF50",  # Vert
                anchor="e",
                width=100  # Largeur fixe pour la version
            )
            update_label.pack(side="left", padx=2)
            
            # Activer la checkbox seulement si une mise à jour est disponible
            checkbox.configure(state="normal")
        else:
            checkbox.configure(state="disabled")

    def _add_log(self, message: str) -> None:
        """Add message to log window."""
        try:
            if hasattr(self, 'log_text'):
                self.log_text.configure(state="normal")
                self.log_text.insert("end", message)
                self.log_text.configure(state="disabled")
                self.log_text.see("end")
                self.update_idletasks()
        except Exception as e:
            logger.error(f"Error adding log message: {e}")

    def _update_selected(self) -> None:
        """Mettre à jour les paquets sélectionnés."""
        # Lancer la mise à jour en arrière-plan
        threading.Thread(
            target=self._update_selected_thread,
            daemon=True
        ).start()

    def _update_selected_thread(self) -> None:
        """Thread pour mettre à jour les paquets sélectionnés."""
        try:
            # Configure process to hide window
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            # Récupérer les paquets sélectionnés
            selected_packages = []
            for widget in self.packages_list.winfo_children():
                if hasattr(widget, 'checkbox') and widget.checkbox.get():
                    selected_packages.append(widget.package_name)
            
            if not selected_packages:
                self._add_log("\nNo packages selected for update.\n")
                return
            
            self._add_log(f"\nUpdating {len(selected_packages)} selected packages...\n")
            
            # Mettre à jour chaque paquet sélectionné
            for package in selected_packages:
                self._add_log(f"\nUpdating {package}...\n")
                process = subprocess.run(
                    ["winget", "upgrade", package],
                    capture_output=True,
                    text=True,
                    startupinfo=startupinfo
                )
                self._add_log(process.stdout)
                
            self._add_log("\nUpdate process completed.\n")
            
            # Rafraîchir la liste
            self._check_updates()
            
        except Exception as e:
            self._add_log(f"Error during update: {str(e)}\n")
            logger.error(f"Error updating packages: {e}")

    def _toggle_all_packages(self) -> None:
        """Sélectionner/désélectionner tous les paquets."""
        selected = self.select_all_var.get()
        for widget in self.packages_list.winfo_children():
            if hasattr(widget, 'checkbox'):
                checkbox = widget.winfo_children()[0]  # La checkbox est le premier enfant
                if checkbox.cget("state") == "normal":  # Ne changer que les checkboxes actives
                    widget.checkbox.set(selected)


class TweaksWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        FrameworkControlCenter._open_windows.append(self)  # Add window to list
        self.parent = parent
        self.title(get_text(self.parent.config.language, "tweaks_title"))
        self.geometry("600x800")
        self.colors = parent.colors
        self.current_font = load_custom_font(self.parent.config.language)
        
        # Configurer l'icône
        try:
            if sys.platform.startswith('win'):
                self.after(200, lambda: self.iconbitmap(str(Path("assets/logo.ico").absolute())))
            else:
                self.iconbitmap(str(Path("assets/logo.ico")))
        except Exception as e:
            logger.error(f"Failed to set window icon: {e}")
        
        # Rendre la fenêtre modale
        self.transient(parent)
        self.grab_set()
        
        # Initialiser les dictionnaires pour stocker les références des checkboxes
        self.privacy_checkboxes = {}
        self.performance_checkboxes = {}
        self.system_checkboxes = {}
        
        # Créer l'interface
        self._create_widgets()
        
        # Vérifier l'état des tweaks
        self._check_tweaks_status()
        
        # Gérer la fermeture de la fenêtre
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _check_tweaks_status(self) -> None:
        """Check which tweaks are already applied."""
        try:
            tweaks = WindowsTweaks()
            
            # Vérifier les tweaks de confidentialité
            for name, var in self.privacy_vars.items():
                is_applied = False
                if name == "Disable Telemetry":
                    is_applied = tweaks.is_telemetry_disabled()
                elif name == "Disable Activity History":
                    is_applied = tweaks.is_activity_history_disabled()
                elif name == "Disable Location Tracking":
                    is_applied = tweaks.is_location_tracking_disabled()
                elif name == "Disable Consumer Features":
                    is_applied = tweaks.is_consumer_features_disabled()
                elif name == "Disable Storage Sense":
                    is_applied = tweaks.is_storage_sense_disabled()
                elif name == "Disable Wifi-Sense":
                    is_applied = tweaks.is_wifi_sense_disabled()
                
                if is_applied:
                    self.privacy_checkboxes[name].configure(state="disabled")
                    self._add_log(f"✓ {name} is already applied\n")
            
            # Vérifier les tweaks de performance
            for name, var in self.performance_vars.items():
                is_applied = False
                if name == "Disable GameDVR":
                    is_applied = tweaks.is_game_dvr_disabled()
                elif name == "Disable Hibernation":
                    is_applied = tweaks.is_hibernation_disabled()
                elif name == "Disable Homegroup":
                    is_applied = tweaks.is_homegroup_disabled()
                elif name == "Prefer IPv4 over IPv6":
                    is_applied = tweaks.is_ipv4_preferred()
                
                if is_applied:
                    self.performance_checkboxes[name].configure(state="disabled")
                    self._add_log(f"✓ {name} is already applied\n")
            
            # Vérifier les tweaks système
            for name, var in self.system_vars.items():
                is_applied = False
                if name == "Change Windows Terminal default: PowerShell 5 -> PowerShell 7":
                    is_applied = tweaks.is_powershell7_default()
                elif name == "Disable Powershell 7 Telemetry":
                    is_applied = tweaks.is_powershell7_telemetry_disabled()
                elif name == "Set Hibernation as default (good for laptops)":
                    is_applied = tweaks.is_hibernation_default()
                elif name == "Set Services to Manual":
                    is_applied = tweaks.are_services_manual()
                elif name == "Debloat Edge":
                    is_applied = tweaks.is_edge_debloated()
                
                if is_applied:
                    self.system_checkboxes[name].configure(state="disabled")
                    self._add_log(f"✓ {name} is already applied\n")
            
        except Exception as e:
            logger.error(f"Error checking tweaks status: {e}")

    def _reset_tweaks(self) -> None:
        """Reset all tweaks to default state."""
        # Réactiver toutes les checkboxes
        for checkbox_dict in [self.privacy_checkboxes, self.performance_checkboxes, self.system_checkboxes]:
            for checkbox in checkbox_dict.values():
                checkbox.configure(state="normal")
        
        # Décocher toutes les cases
        for var_dict in [self.privacy_vars, self.performance_vars, self.system_vars]:
            for var in var_dict.values():
                var.set(False)
        
        # Add log message
        self._add_log("\n✨ All tweaks have been reset to default state.\n")

    def _create_privacy_tweaks(self, parent) -> None:
        """Create privacy tweaks section."""
        # Section frame
        section = ctk.CTkFrame(parent, fg_color=self.colors["background"])
        section.pack(fill="x", pady=(0, 20))

        # Section title
        ctk.CTkLabel(
            section,
            text="Privacy Tweaks",
            font=("Roboto", 12, "bold"),
            text_color=self.colors["text"]
        ).pack(anchor="w", pady=(0, 10))

        # Privacy tweaks
        self.privacy_vars = {}
        privacy_tweaks = [
            ("Disable Telemetry", "Disable Windows telemetry and data collection"),
            ("Disable Activity History", "Disable Windows activity history tracking"),
            ("Disable Location Tracking", "Disable location tracking and services"),
            ("Disable Consumer Features", "Disable consumer features and suggestions"),
            ("Disable Storage Sense", "Disable automatic storage management"),
            ("Disable Wifi-Sense", "Disable automatic WiFi network sharing")
        ]

        for name, tooltip in privacy_tweaks:
            var = ctk.BooleanVar(value=False)
            self.privacy_vars[name] = var
            
            checkbox = ctk.CTkCheckBox(
                section,
                text=name,
                variable=var,
                fg_color=self.colors["primary"],
                hover_color=self.colors["hover"],
                text_color=self.colors["text"],
                border_color=self.colors["text"]
            )
            checkbox.pack(anchor="w", pady=2)
            
            # Store checkbox reference
            self.privacy_checkboxes[name] = checkbox
            
            # Add tooltip functionality
            self._create_tooltip(checkbox, tooltip)

    def _create_performance_tweaks(self, parent) -> None:
        """Create performance tweaks section."""
        # Section frame
        section = ctk.CTkFrame(parent, fg_color=self.colors["background"])
        section.pack(fill="x", pady=(0, 20))

        # Section title
        ctk.CTkLabel(
            section,
            text="Performance Tweaks",
            font=("Roboto", 12, "bold"),
            text_color=self.colors["text"]
        ).pack(anchor="w", pady=(0, 10))

        # Performance tweaks
        self.performance_vars = {}
        performance_tweaks = [
            ("Disable GameDVR", "Disable Game DVR and Game Bar for better gaming performance"),
            ("Disable Hibernation", "Disable system hibernation to free up disk space"),
            ("Disable Homegroup", "Disable homegroup services"),
            ("Run Disk Cleanup", "Clean up system files and free disk space"),
            ("Prefer IPv4 over IPv6", "Prioritize IPv4 connections over IPv6")
        ]

        for name, tooltip in performance_tweaks:
            var = ctk.BooleanVar(value=False)
            self.performance_vars[name] = var
            
            checkbox = ctk.CTkCheckBox(
                section,
                text=name,
                variable=var,
                fg_color=self.colors["primary"],
                hover_color=self.colors["hover"],
                text_color=self.colors["text"],
                border_color=self.colors["text"]
            )
            checkbox.pack(anchor="w", pady=2)
            
            # Store checkbox reference
            self.performance_checkboxes[name] = checkbox
            
            # Add tooltip functionality
            self._create_tooltip(checkbox, tooltip)

    def _create_system_tweaks(self, parent) -> None:
        """Create system tweaks section."""
        # Section frame
        section = ctk.CTkFrame(parent, fg_color=self.colors["background"])
        section.pack(fill="x", pady=(0, 20))

        # Section title
        ctk.CTkLabel(
            section,
            text="System Tweaks",
            font=("Roboto", 12, "bold"),
            text_color=self.colors["text"]
        ).pack(anchor="w", pady=(0, 10))

        # System tweaks
        self.system_vars = {}
        system_tweaks = [
            ("Delete Temporary Files", "Delete temporary files to free up space"),
            ("Change Windows Terminal default: PowerShell 5 -> PowerShell 7", "Set PowerShell 7 as default terminal"),
            ("Disable Powershell 7 Telemetry", "Disable telemetry in PowerShell 7"),
            ("Set Hibernation as default (good for laptops)", "Configure hibernation as default power action"),
            ("Set Services to Manual", "Set non-essential services to manual start"),
            ("Debloat Edge", "Remove unnecessary Edge browser components")
        ]

        for name, tooltip in system_tweaks:
            var = ctk.BooleanVar(value=False)
            self.system_vars[name] = var
            
            checkbox = ctk.CTkCheckBox(
                section,
                text=name,
                variable=var,
                fg_color=self.colors["primary"],
                hover_color=self.colors["hover"],
                text_color=self.colors["text"],
                border_color=self.colors["text"]
            )
            checkbox.pack(anchor="w", pady=2)
            
            # Store checkbox reference
            self.system_checkboxes[name] = checkbox
            
            # Add tooltip functionality
            self._create_tooltip(checkbox, tooltip)

    def _create_tooltip(self, widget, text):
        """Create tooltip for widget."""
        def show_tooltip(event):
            tooltip = ctk.CTkToplevel(self)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            
            label = ctk.CTkLabel(
                tooltip,
                text=text,
                fg_color="#2D2D2D",
                text_color=self.colors["text"],
                corner_radius=6
            )
            label.pack(padx=5, pady=5)
            
            def hide_tooltip():
                tooltip.destroy()
            
            widget.tooltip = tooltip
            widget.after(2000, hide_tooltip)

        def hide_tooltip(event):
            if hasattr(widget, "tooltip"):
                widget.tooltip.destroy()
                del widget.tooltip

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)

    def _apply_tweaks(self) -> None:
        """Apply selected tweaks."""
        try:
            tweaks = WindowsTweaks()

            # Apply privacy tweaks
            for name, var in self.privacy_vars.items():
                if var.get():
                    self._add_log(f"Applying {name}...\n")
                    success = False
                    
                    if name == "Disable Telemetry":
                        success = tweaks.disable_telemetry()
                    elif name == "Disable Activity History":
                        success = tweaks.disable_activity_history()
                    elif name == "Disable Location Tracking":
                        success = tweaks.disable_location_tracking()
                    elif name == "Disable Consumer Features":
                        success = tweaks.disable_consumer_features()
                    elif name == "Disable Storage Sense":
                        success = tweaks.disable_storage_sense()
                    elif name == "Disable Wifi-Sense":
                        success = tweaks.disable_wifi_sense()
                        
                    self._add_log(f"{'✅ Success' if success else '❌ Failed'}\n")

            # Apply performance tweaks
            for name, var in self.performance_vars.items():
                if var.get():
                    self._add_log(f"Applying {name}...\n")
                    success = False
                    
                    if name == "Disable GameDVR":
                        success = tweaks.disable_game_dvr()
                    elif name == "Disable Hibernation":
                        success = tweaks.disable_hibernation()
                    elif name == "Disable Homegroup":
                        success = tweaks.disable_homegroup()
                    elif name == "Run Disk Cleanup":
                        success = tweaks.run_disk_cleanup()
                    elif name == "Prefer IPv4 over IPv6":
                        success = tweaks.prefer_ipv4_over_ipv6()
                        
                    self._add_log(f"{'✅ Success' if success else '❌ Failed'}\n")

            # Apply system tweaks
            for name, var in self.system_vars.items():
                if var.get():
                    self._add_log(f"Applying {name}...\n")
                    success = False
                    
                    if name == "Delete Temporary Files":
                        success = tweaks.run_disk_cleanup()
                    elif name == "Change Windows Terminal default: PowerShell 5 -> PowerShell 7":
                        success = tweaks.set_powershell7_default()
                    elif name == "Disable Powershell 7 Telemetry":
                        success = tweaks.disable_powershell7_telemetry()
                    elif name == "Set Hibernation as default (good for laptops)":
                        success = tweaks.set_hibernation_default()
                    elif name == "Set Services to Manual":
                        success = tweaks.set_services_manual()
                    elif name == "Debloat Edge":
                        success = tweaks.debloat_edge()
                        
                    self._add_log(f"{'✅ Success' if success else '❌ Failed'}\n")

            self._add_log("\n✅ All selected tweaks have been applied.\n")
            
        except Exception as e:
            self._add_log(f"\n❌ Error applying tweaks: {str(e)}\n")
            logger.error(f"Error applying tweaks: {e}")

    def _add_log(self, message: str) -> None:
        """Add message to log window."""
        try:
            if hasattr(self, 'log_text'):
                self.log_text.configure(state="normal")
                self.log_text.insert("end", message)
                self.log_text.configure(state="disabled")
                self.log_text.see("end")
                self.update_idletasks()
        except Exception as e:
            logger.error(f"Error adding log message: {e}")

    def _on_close(self) -> None:
        """Handle window close."""
        try:
            FrameworkControlCenter._open_windows.remove(self)  # Remove window from list
            self.grab_release()
            self.destroy()
        except Exception as e:
            logger.error(f"Error closing Tweaks Window: {e}")
            self.destroy() 

    def _reset_tweaks(self) -> None:
        """Reset all tweaks to default state."""
        # Reset all checkboxes
        for var_dict in [self.privacy_vars, self.performance_vars, self.system_vars]:
            for var in var_dict.values():
                var.set(False)
        
        # Add log message
        self._add_log("\n✨ All tweaks have been reset to default state.\n") 

    def _create_widgets(self) -> None:
        """Create tweaks window widgets."""
        # Main container
        container = ctk.CTkFrame(self, fg_color=self.colors["background"])
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Scrollable frame for tweaks
        scrollable_frame = ctk.CTkScrollableFrame(
            container,
            fg_color=self.colors["background"],
            label_text="Windows Tweaks",
            label_fg_color=self.colors["background"]
        )
        scrollable_frame.pack(fill="both", expand=True)

        # Tweaks sections
        self._create_privacy_tweaks(scrollable_frame)
        self._create_performance_tweaks(scrollable_frame)
        self._create_system_tweaks(scrollable_frame)

        # Log text area
        self.log_text = ctk.CTkTextbox(
            container,
            height=100,
            fg_color=self.colors["background"],
            text_color=self.colors["text"]
        )
        self.log_text.pack(fill="x", pady=(10, 0))
        self.log_text.configure(state="disabled")

        # Buttons frame
        buttons_frame = ctk.CTkFrame(container, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(20, 0))

        # Apply button
        apply_btn = ctk.CTkButton(
            buttons_frame,
            text="Apply Selected Tweaks",
            command=self._apply_tweaks,
            fg_color=self.colors["primary"],
            hover_color=self.colors["hover"],
            text_color=self.colors["text"]
        )
        apply_btn.pack(side="left", padx=5)

        # Reset button
        reset_btn = ctk.CTkButton(
            buttons_frame,
            text="Reset All",
            command=self._reset_tweaks,
            fg_color="#FF4444",
            hover_color="#FF6666",
            text_color=self.colors["text"]
        )
        reset_btn.pack(side="right", padx=5)

        # Restore Services button
        restore_services_btn = ctk.CTkButton(
            buttons_frame,
            text="Restore Services",
            command=self._restore_services,
            fg_color="#4444FF",
            hover_color="#6666FF",
            text_color=self.colors["text"]
        )
        restore_services_btn.pack(side="right", padx=5)

    def _restore_services(self) -> None:
        """Restore services to automatic startup."""
        try:
            tweaks = WindowsTweaks()
            self._add_log("\nRestoring services to automatic startup...\n")
            
            success = tweaks.restore_services()
            
            if success:
                self._add_log("✅ Services restored successfully\n")
                # Re-enable all service-related checkboxes
                for checkbox in self.system_checkboxes.values():
                    checkbox.configure(state="normal")
            else:
                self._add_log("❌ Failed to restore services\n")
        except Exception as e:
            logger.error(f"Error restoring services: {e}")
            self._add_log(f"❌ Error restoring services: {e}\n") 
