import json
import os
import sys
import psutil
import ctypes
import keyboard
import pystray
from PIL import Image
import customtkinter as ctk
from pathlib import Path
import subprocess
import webbrowser
from threading import Thread
import time
import logging
import requests
import zipfile
import winreg
import win32api
import win32con
from win32con import ENUM_CURRENT_SETTINGS, ENUM_REGISTRY_SETTINGS
import shutil
import win32gui
import pythoncom
import wmi
import platform
from translations import TRANSLATIONS
from settings_window import SettingsWindow

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mini_hub.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def detect_framework_model():
    """Detect the Framework laptop model based on CPU model"""
    try:
        c = wmi.WMI()
        processor = c.Win32_Processor()[0]
        cpu_name = processor.Name.upper()
        logger.info(f"Detected CPU: {cpu_name}")
        
        # Framework 16 CPUs
        if "7840HS" in cpu_name or "7940HS" in cpu_name:
            logger.info("Detected Framework 16 AMD CPU")
            return "model_16"
        # Framework 13 CPUs
        elif "7640U" in cpu_name or "7840U" in cpu_name:
            logger.info("Detected Framework 13 AMD CPU")
            return "model_13_amd"
        else:
            logger.warning(f"Unknown CPU model: {cpu_name}, defaulting to Framework 13")
            return "model_13_amd"
    except Exception as e:
        logger.error(f"Error detecting CPU model: {str(e)}")
        return "model_13_amd"  # Default to Framework 13 if detection fails

class SystemMonitor:
    def __init__(self):
        try:
            logger.info("Initializing Windows Resource Monitor")
            self.cpu_count = psutil.cpu_count(logical=True)
        except Exception as e:
            logger.error(f"Error initializing system monitor: {e}")

    def get_cpu_load(self):
        try:
            return psutil.cpu_percent(interval=None)
        except Exception as e:
            logger.error(f"Error reading CPU load: {e}")
            return 0

    def get_ram_usage(self):
        try:
            return psutil.virtual_memory().percent
        except Exception as e:
            logger.error(f"Error reading RAM usage: {e}")
            return 0

    def get_cpu_temp(self):
        try:
            # Utiliser WMI pour obtenir la température CPU sur Windows 11
            pythoncom.CoInitialize()
            w = wmi.WMI(namespace="root\\cimv2")
            # Rechercher d'abord les capteurs AMD
            temps = w.query("SELECT * FROM Win32_PerfFormattedData_Counters_ThermalZoneInformation")
            if temps:
                for temp in temps:
                    try:
                        # La température est en dixièmes de degrés
                        temp_value = float(temp.Temperature) / 10.0
                        if temp_value > 0 and temp_value < 125:  # Vérification de validité
                            return round(temp_value, 1)
                    except:
                        continue

            # Si aucune température valide n'est trouvée, essayer ryzenadj
            ryzenadj_path = str(Path("ryzenadj") / "ryzenadj.exe")
            if os.path.exists(ryzenadj_path):
                try:
                    result = subprocess.run([ryzenadj_path, "-i"], capture_output=True, text=True)
                    for line in result.stdout.split('\n'):
                        if 'TCTL Temperature' in line:
                            temp = float(line.split(':')[1].strip().split()[0])
                            if temp > 0 and temp < 125:  # Vérification de validité
                                return round(temp, 1)
                except Exception as e:
                    logger.error(f"Error reading temperature from ryzenadj: {e}")

            logger.warning("No valid temperature reading available")
            return 0
        except Exception as e:
            logger.error(f"Error reading CPU temperature: {e}", exc_info=True)
            return 0
        finally:
            try:
                pythoncom.CoUninitialize()
            except:
                pass

    def cleanup(self):
        pass  # Nothing to clean up

class MiniFrameworkHub(ctk.CTk):
    def __init__(self):
        try:
            super().__init__()
            logger.info("Initializing MiniFrameworkHub")
            
            # Initialize monitoring flags
            self.power_monitor_thread = None
            self.stop_power_monitor = False
            self.battery_monitor_thread = None
            
            # Initialize system monitor
            self.monitor = SystemMonitor()
            logger.info("System monitor initialized")
            
            # Initialize settings
            self.settings = self.load_settings()
            self.current_language = self.settings.get("language", "en")
            self.translations = TRANSLATIONS[self.current_language]
            logger.info(f"Settings loaded, language: {self.current_language}")
            
            # Initialize system info
            self.system_info = self.initialize_system_info()
            logger.info("System info initialized")
            
            # Detect screen capabilities
            self.screen_capabilities = self.detect_screen_capabilities()
            logger.info(f"Screen capabilities detected: {self.screen_capabilities}")
            
            # Initialize GPU monitoring
            self.gpu_control = AMDGPUControl()
            self.gpu_info = self.gpu_control.get_gpu_info()
            if self.gpu_info:
                for gpu_id, gpu_data in self.gpu_info.items():
                    logger.info(f"AMD GPU detected: {gpu_data['name']}")
            else:
                logger.warning("No AMD GPUs detected")
                
            # IMPORTANT: Initialize model var with default value
            self.model_var = ctk.StringVar()
            saved_model = self.settings.get("laptop_model", "model_13_amd")
            model = "Framework 16 AMD" if saved_model == "model_16" else "Framework 13 AMD"
            self.model_var.set(model)
            logger.info(f"Model initialized to: {model}")
            
            # UI Setup
            self.setup_window()
            logger.info("Window setup complete")
            
            self.setup_tray()
            logger.info("Tray setup complete")
            
            self.setup_hotkey()
            logger.info("Hotkey setup complete")
            
            self.create_widgets()
            logger.info("Widgets created")
            
            self.start_monitoring()
            logger.info("Monitoring started")
            
            # Hide window on startup
            self.withdraw()
            logger.info("Window hidden")
            
        except Exception as e:
            logger.error(f"Error in initialization: {str(e)}", exc_info=True)
            raise
            
    def tr(self, key):
        """Get translation for key"""
        return self.translations.get(key, key)
        
    def update_ui_language(self):
        """Update UI text based on selected language"""
        self.current_language = self.settings.get("language", "en")
        self.translations = TRANSLATIONS[self.current_language]
        logger.info(f"Language updated to: {self.current_language}")
        
        # Update window title
        self.title(self.tr("settings"))
        
        # Update all labels and buttons
        self.update_all_widgets_text(self)
        
    def update_all_widgets_text(self, parent):
        """Recursively update text of all widgets"""
        for widget in parent.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                text = widget.cget("text")
                if text in self.translations:
                    widget.configure(text=self.tr(text))
            elif isinstance(widget, ctk.CTkButton):
                text = widget.cget("text")
                if text in self.translations:
                    widget.configure(text=self.tr(text))
            elif isinstance(widget, ctk.CTkFrame) or isinstance(widget, ctk.CTkScrollableFrame):
                self.update_all_widgets_text(widget)
                
        # Update settings window if open
        if hasattr(self, 'settings_window') and self.settings_window:
            self.settings_window.update_ui_language()
            
    def open_settings(self):
        """Open settings window"""
        if not hasattr(self, 'settings_window') or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self)
            self.settings_window.focus()
        else:
            self.settings_window.focus()
    
    def setup_window(self):
        self.title("Framework Mini Hub")
        self.geometry("300x750")
        self.minsize(300, 750)
        
        # Set dark theme
        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#1A1A1A")
        
        # Set icon
        try:
            icon_path = Path("assets") / "logo.ico"
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except Exception as e:
            print(f"Error setting icon: {e}")
            
        # Add minimize and close buttons in title bar
        title_bar = ctk.CTkFrame(self, fg_color="#1A1A1A", height=30)
        title_bar.pack(fill="x", pady=0)
        
        # Title label
        title_label = ctk.CTkLabel(
            title_bar,
            text="Framework Mini Hub",
            text_color="#E0E0E0",
            anchor="w"
        )
        title_label.pack(side="left", padx=10)
        
        # Close button
        close_button = ctk.CTkButton(
            title_bar,
            text="×",
            width=30,
            height=30,
            command=self.withdraw,
            fg_color="#1A1A1A",
            hover_color="#FF4B1F",
            text_color="#E0E0E0"
        )
        close_button.pack(side="right", padx=0)
        
        # Minimize button
        minimize_button = ctk.CTkButton(
            title_bar,
            text="−",
            width=30,
            height=30,
            command=self.withdraw,
            fg_color="#1A1A1A",
            hover_color="#FF7F5C",
            text_color="#E0E0E0"
        )
        minimize_button.pack(side="right", padx=0)
        
        # Make window draggable
        title_bar.bind("<Button-1>", self.start_move)
        title_bar.bind("<B1-Motion>", self.on_move)
        title_label.bind("<Button-1>", self.start_move)
        title_label.bind("<B1-Motion>", self.on_move)
        
        # Bind focus events
        self.bind("<FocusIn>", self.on_focus_in)
        self.bind("<FocusOut>", self.on_focus_out)
        
        # Position window
        self.position_window()
        
    def on_focus_in(self, event):
        """When window gets focus, bring it to front"""
        self.attributes('-topmost', True)
        
    def on_focus_out(self, event):
        """When window loses focus, allow it to go behind other windows"""
        self.attributes('-topmost', False)
        
    def position_window(self):
        """Position the window in the saved position or default bottom right corner"""
        try:
            # Check if we have a saved position
            saved_position = self.settings.get("window_position")
            
            if saved_position:
                # Use saved position
                x = saved_position["x"]
                y = saved_position["y"]
                self.geometry(f"300x750+{x}+{y}")
            else:
                # Calculate default position (bottom right)
                screen_width = self.winfo_screenwidth()
                screen_height = self.winfo_screenheight()
                
                # Get taskbar height
                taskbar = win32gui.FindWindow("Shell_TrayWnd", None)
                if taskbar:
                    taskbar_rect = win32gui.GetWindowRect(taskbar)
                    taskbar_height = taskbar_rect[3] - taskbar_rect[1]
                else:
                    taskbar_height = 40
                
                # Calculate position
                window_width = 300
                window_height = 750
                x = screen_width - window_width - 15
                y = screen_height - window_height - taskbar_height - 5
                
                # Save and use this position
                self.settings["window_position"] = {"x": x, "y": y}
                self.save_settings()
                self.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # Remove window decorations and set topmost temporarily
            self.overrideredirect(True)
            self.attributes('-topmost', True)
            self.after(100, lambda: self.attributes('-topmost', False))
            
        except Exception as e:
            logger.error(f"Error positioning window: {str(e)}")

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")
        
        # Save new position after moving
        self.settings["window_position"] = {"x": x, "y": y}
        self.save_settings()

    def setup_tray(self):
        icon_path = Path("assets") / "logo.ico"
        if icon_path.exists():
            image = Image.open(icon_path)
            menu = (
                pystray.MenuItem("Show/Hide", self.toggle_window),
                pystray.MenuItem("Exit", self.quit_app)
            )
            self.tray_icon = pystray.Icon("Framework Mini Hub", image, "Framework Mini Hub", menu)
            Thread(target=self.tray_icon.run, daemon=True).start()
            
    def setup_hotkey(self):
        keyboard.add_hotkey('F12', self.toggle_window, suppress=True)
        
    def create_widgets(self):
        # Couleurs modernes
        button_color = "#FF7F5C"     # Orange Framework
        hover_color = "#FF9B80"      # Orange plus clair pour hover
        active_color = "#E85D3A"     # Orange plus foncé pour le profil actif
        bg_color = "#242424"         # Gris foncé pour les frames
        progress_bg = "#2D2D2D"      # Gris un peu plus clair pour les barres
        text_color = "#E0E0E0"       # Gris clair pour le texte
        
        # Chargement des icones
        icons = {
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
        
        # Style commun pour les frames
        frame_style = {"fg_color": bg_color, "corner_radius": 10}
        
        # Model selection frame
        self.model_frame = ctk.CTkFrame(self, **frame_style)
        self.model_frame.pack(fill="x", padx=15, pady=10)
        
        # Utiliser le model_var déjà initialisé dans __init__
        model_menu = ctk.CTkOptionMenu(
            self.model_frame,
            values=["Framework 13 AMD", "Framework 16 AMD"],
            command=self.change_laptop_model,
            variable=self.model_var,  # Utiliser la variable existante
            fg_color=button_color,
            button_color=button_color,
            button_hover_color=hover_color,
            text_color="black",
            dropdown_fg_color=bg_color,
            dropdown_text_color=text_color,
            dropdown_hover_color=hover_color,
            corner_radius=8
        )
        model_menu.pack(expand=True, padx=10, pady=5)
        
        # Profile buttons frame
        self.profile_frame = ctk.CTkFrame(self, **frame_style)
        self.profile_frame.pack(fill="x", padx=15, pady=10)
        
        # Container pour centrer les boutons
        button_container = ctk.CTkFrame(self.profile_frame, fg_color="transparent")
        button_container.pack(expand=True, pady=5)
        
        # Stocker les boutons pour pouvoir les mettre à jour
        self.profile_buttons = {}
        
        # Définir une largeur fixe plus petite pour tous les boutons
        button_width = 80  # Réduction de la largeur
        
        profiles = ["Silent", "Balanced", "Boost"]
        for profile in profiles:
            btn = ctk.CTkButton(
                button_container,
                text=profile,
                image=icons[profile],
                compound="top",
                command=lambda p=profile: self.apply_profile(p),
                width=button_width,  # Largeur fixe plus petite
                height=50,
                fg_color=button_color if profile != self.settings["ryzenadj_profile"] else active_color,
                hover_color=hover_color,
                text_color="black",
                corner_radius=8
            )
            btn.pack(side="left", padx=5)  # Garde le padding uniforme
            self.profile_buttons[profile] = btn
        
        # Déplacer la frame du taux de rafraîchissement ici, après les boutons de profils
        # Screen refresh rate frame
        self.screen_frame = ctk.CTkFrame(self, **frame_style)
        self.screen_frame.pack(fill="x", padx=15, pady=5)
        
        # Label pour le taux de rafraîchissement
        refresh_label = ctk.CTkLabel(
            self.screen_frame,
            text="Refresh rate:",
            text_color=text_color,
            anchor="w"
        )
        refresh_label.pack(side="left", padx=(10, 0), pady=5)
        
        # Container pour les boutons de rafraîchissement
        self.refresh_container = ctk.CTkFrame(self.screen_frame, fg_color="transparent")
        self.refresh_container.pack(side="right", padx=(0, 10), pady=5)
        
        # Sauvegarder les couleurs comme attributs de classe
        self.button_color = button_color
        self.hover_color = hover_color
        
        # Boutons pour les différents taux de rafraîchissement
        refresh_rates = ["Auto", "60Hz", "165Hz"]
        self.refresh_buttons = {}
        
        for rate in refresh_rates:
            btn = ctk.CTkButton(
                self.refresh_container,
                text=rate,
                command=lambda r=rate: self.set_refresh_rate_wrapper(r),
                width=50,
                height=24,
                fg_color=button_color,
                hover_color=hover_color,
                text_color="black",
                corner_radius=8
            )
            btn.pack(side="left", padx=2)
            self.refresh_buttons[rate] = btn
        
        # System monitoring - Updated for dual GPUs
        self.stats_frame = ctk.CTkFrame(self, **frame_style)
        self.stats_frame.pack(fill="x", padx=15, pady=10)
        
        def create_monitor_bar(parent, label_text, initial_value="0%"):
            frame = ctk.CTkFrame(parent, fg_color="transparent")
            frame.pack(fill="x", pady=3, padx=10)
            
            label = ctk.CTkLabel(
                frame, 
                text=f"{label_text} {initial_value}", 
                anchor="w",
                text_color=text_color
            )
            label.pack(side="left", padx=5)
            
            bar = ctk.CTkProgressBar(frame)
            bar.pack(side="right", padx=5, fill="x", expand=True)
            bar.configure(
                progress_color=button_color,
                fg_color=progress_bg,
                height=8,
                corner_radius=4,
                border_width=0
            )
            bar.set(0)
            return label, bar
        
        self.cpu_label, self.cpu_bar = create_monitor_bar(self.stats_frame, "CPU:")
        
        # Remove GPU monitoring bars
        self.ram_label, self.ram_bar = create_monitor_bar(self.stats_frame, "RAM:")
        self.temp_label, self.temp_bar = create_monitor_bar(self.stats_frame, "Temp:")
        
        # Quick actions
        self.actions_frame = ctk.CTkFrame(self, **frame_style)
        self.actions_frame.pack(fill="x", padx=15, pady=10)
        
        for btn_text, cmd in [
            ("Keyboard", self.open_keyboard_page), 
            ("Updates", self.open_updates),
            ("Settings", self.open_settings)
        ]:
            btn = ctk.CTkButton(
                self.actions_frame,
                text=btn_text,
                command=cmd,
                fg_color=button_color,
                hover_color=hover_color,
                text_color="black",
                height=35,
                corner_radius=8
            )
            btn.pack(fill="x", padx=10, pady=5)
        
        # Add brightness control frame
        brightness_frame = ctk.CTkFrame(self, **frame_style)
        brightness_frame.pack(fill="x", padx=15, pady=(10, 0))  # Remove bottom padding
        
        # Get current brightness before creating controls
        try:
            c = wmi.WMI(namespace='wmi')
            brightness_info = c.WmiMonitorBrightness()[0]
            current_brightness = brightness_info.CurrentBrightness
        except Exception as e:
            logger.error(f"Error getting current brightness: {str(e)}")
            current_brightness = 50  # Default value if we can't get current brightness
        
        # Brightness label and value in the same row
        brightness_header = ctk.CTkFrame(brightness_frame, fg_color="transparent")
        brightness_header.pack(fill="x", padx=10, pady=(2, 0))
        
        brightness_label = ctk.CTkLabel(
            brightness_header,
            text="Screen Brightness:",
            text_color=text_color,
            anchor="w"
        )
        brightness_label.pack(side="left")
        
        # Brightness value label
        self.brightness_value_label = ctk.CTkLabel(
            brightness_header,
            text=f"Current: {current_brightness}%",
            text_color=text_color,
            anchor="e"
        )
        self.brightness_value_label.pack(side="right")
        
        # Brightness slider
        self.brightness_slider = ctk.CTkSlider(
            brightness_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self.on_brightness_change,
            button_color=button_color,
            button_hover_color=hover_color,
            progress_color=button_color,
            fg_color=progress_bg
        )
        self.brightness_slider.pack(fill="x", padx=10, pady=(2, 5))
        self.brightness_slider.set(current_brightness)
        
        # Bind the release event
        self.brightness_slider.bind("<ButtonRelease-1>", self.on_brightness_release)
        
        # Add battery control frame right after brightness
        self.battery_frame = ctk.CTkFrame(self, **frame_style)
        self.battery_frame.pack(fill="x", padx=15, pady=5)  # Adjusted padding
        
        # Battery status label
        self.battery_status = ctk.CTkLabel(
            self.battery_frame,
            text="Battery Charge Limit:",
            text_color=text_color,
            anchor="w"
        )
        self.battery_status.pack(side="top", padx=10, pady=(2, 0))
        
        # Battery charge limit slider
        self.charge_slider = ctk.CTkSlider(
            self.battery_frame,
            from_=60,
            to=100,
            number_of_steps=40,
            command=self.on_slider_change,
            button_color=button_color,
            button_hover_color=hover_color,
            progress_color=button_color,
            fg_color=progress_bg
        )
        self.charge_slider.pack(fill="x", padx=10, pady=(2, 2))
        self.charge_slider.set(self.charge_limit)
        
        # Bind the release event
        self.charge_slider.bind("<ButtonRelease-1>", self.on_slider_release)
        
        # Current limit label
        self.limit_label = ctk.CTkLabel(
            self.battery_frame,
            text=f"Current limit: {self.charge_limit}%",
            text_color=text_color,
            anchor="e"
        )
        self.limit_label.pack(side="right", padx=10, pady=2)
        
        # Start battery monitoring
        self.start_battery_monitor()
        
    def toggle_window(self):
        if self.winfo_viewable():
            self.withdraw()
        else:
            # Use saved position when showing window
            self.position_window()
            self.deiconify()
            self.lift()  # Bring window to front
            self.focus_force()  # Force focus to trigger focus_in event
        
    def quit_app(self):
        self.tray_icon.stop()
        self.quit()
        
    def load_settings(self):
        default_settings = {
            "language": "en",
            "theme": "dark",
            "ryzenadj_profile": "Balanced",
            "laptop_model": detect_framework_model(),  # Use CPU detection to set default model
            "last_refresh_rate": "Auto",
            "window_position": None,
            "power_profiles": {
                "Silent": {
                    "tdp": 15,
                    "fast_limit": 20,
                    "slow_limit": 15,
                    "boost_enabled": False,
                    "current_limit": 150,
                    "temp_limit": 85,
                    "skin_temp": 40,
                    "win_power": 0
                },
                "Balanced": {
                    "tdp": 30,
                    "fast_limit": 35,
                    "slow_limit": 30,
                    "boost_enabled": True,
                    "current_limit": 180,
                    "temp_limit": 90,
                    "skin_temp": 45,
                    "win_power": 1
                },
                "Boost": {
                    "tdp": 60,
                    "fast_limit": 70,
                    "slow_limit": 60,
                    "boost_enabled": True,
                    "current_limit": 200,
                    "temp_limit": 95,
                    "skin_temp": 50,
                    "win_power": 2
                }
            }
        }
        
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    loaded_settings = json.load(f)
                    # If no laptop_model in settings or force_detect is True, detect it
                    if "laptop_model" not in loaded_settings:
                        loaded_settings["laptop_model"] = detect_framework_model()
                    # Merge loaded settings with defaults, preserving loaded values
                    merged_settings = default_settings.copy()
                    merged_settings.update(loaded_settings)
                    logger.info(f"Loaded settings from file with model: {merged_settings.get('laptop_model', 'unknown')}")
                    return merged_settings
        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}", exc_info=True)
            
        logger.info("Using default settings with detected model")
        return default_settings
        
    def save_settings(self):
        try:
            with open("settings.json", "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")
            
    def initialize_system_info(self):
        try:
            c = wmi.WMI()
            processor = c.Win32_Processor()[0]
            
            # Log detailed CPU information
            logger.info(f"Processor Name: {processor.Name}")
            logger.info(f"Processor Manufacturer: {processor.Manufacturer}")
            logger.info(f"Processor ID: {processor.ProcessorId}")
            logger.info(f"CPU Family: {processor.Family}")
            
            # Verify this is an AMD processor
            if "AMD" not in processor.Manufacturer.upper():
                raise Exception("This application only supports AMD Ryzen processors")
            
            # Extract CPU model information
            cpu_info = {
                "name": processor.Name,
                "manufacturer": processor.Manufacturer,
                "family": processor.Family,
                "model": processor.ProcessorId,
                "is_amd": "AMD" in processor.Manufacturer.upper()
            }
            
            # Check and download RyzenADJ if needed
            ryzenadj_path = self.ensure_ryzenadj()
            
            return {
                "wmi": c,
                "ryzenadj_path": ryzenadj_path,
                "cpu_info": cpu_info
            }
        except Exception as e:
            logger.error(f"Error initializing system info: {str(e)}", exc_info=True)
            raise
            
    def ensure_ryzenadj(self):
        """Ensure RyzenADJ is present and up to date"""
        try:
            ryzenadj_dir = Path("ryzenadj")
            ryzenadj_path = ryzenadj_dir / "ryzenadj.exe"
            
            # If RyzenADJ doesn't exist, download it
            if not ryzenadj_path.exists():
                logger.info("RyzenADJ not found, downloading...")
                ryzenadj_dir.mkdir(exist_ok=True)
                
                # Download latest RyzenADJ that supports Ryzen 7000 series
                url = "https://github.com/FlyGoat/RyzenAdj/releases/download/v0.14.0/ryzenadj-win64.zip"
                response = requests.get(url)
                zip_path = ryzenadj_dir / "ryzenadj.zip"
                
                with open(zip_path, 'wb') as f:
                    f.write(response.content)
                
                # Extract the zip
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(ryzenadj_dir)
                
                # Clean up
                zip_path.unlink()
                logger.info("RyzenADJ downloaded and extracted")
                
                # Copy WinRing0x64.sys to Windows directory
                try:
                    winring0_src = ryzenadj_dir / "WinRing0x64.sys"
                    winring0_dst = Path(os.environ["WINDIR"]) / "System32" / "drivers" / "WinRing0x64.sys"
                    if winring0_src.exists():
                        import shutil
                        shutil.copy2(str(winring0_src), str(winring0_dst))
                        logger.info("Copied WinRing0x64.sys to System32/drivers")
                except Exception as e:
                    logger.error(f"Failed to copy WinRing0x64.sys: {e}")
            
            return ryzenadj_path
            
        except Exception as e:
            logger.error(f"Error ensuring RyzenADJ: {str(e)}", exc_info=True)
            return Path("ryzenadj") / "ryzenadj.exe"
            
    def start_monitoring(self):
        def update_stats():
            """Update system statistics in the UI"""
            while True:  # Changed to infinite loop
                try:
                    # CPU stats
                    cpu_load = self.monitor.get_cpu_load()
                    cpu_temp = self.monitor.get_cpu_temp()
                    ram_usage = self.monitor.get_ram_usage()
                    
                    # Log stats for debugging
                    logger.debug(f"Stats - CPU: {cpu_load}%, Temp: {cpu_temp}°C, RAM: {ram_usage}%")
                    
                    # Update UI elements in a single after call
                    def update_ui():
                        # Update CPU
                        self.cpu_bar.set(cpu_load / 100)
                        self.cpu_label.configure(text=f"CPU: {cpu_load}%")
                        
                        # Update Temperature
                        self.temp_bar.set(min(cpu_temp / 100, 1.0))  # Cap at 100%
                        self.temp_label.configure(text=f"Temp: {cpu_temp}°C")
                        
                        # Update RAM
                        self.ram_bar.set(ram_usage / 100)
                        self.ram_label.configure(text=f"RAM: {ram_usage}%")
                    
                    # Schedule UI update on main thread
                    self.after(0, update_ui)
                    
                except Exception as e:
                    logger.error(f"Error in monitoring thread: {str(e)}")
                finally:
                    time.sleep(1)  # Update every second
                
        # Start monitoring in a daemon thread
        monitoring_thread = Thread(target=update_stats, daemon=True)
        monitoring_thread.name = "MonitoringThread"  # Name the thread for debugging
        monitoring_thread.start()
        
    def open_keyboard_page(self):
        webbrowser.open("https://keyboard.frame.work/")
        
    def open_updates(self):
        if not hasattr(self, 'update_window') or not self.update_window.winfo_exists():
            self.update_window = UpdateWindow(self)
            self.update_window.focus()
        else:
            self.update_window.focus()
        
    def change_laptop_model(self, model_name):
        """Change laptop model and update all related settings"""
        try:
            logger.info(f"Changing laptop model to: {model_name}")
            
            if model_name == "Framework 13 AMD":
                model_id = "model_13_amd"
                profiles = {
                    "Silent": {
                        "tdp": 15,
                        "fast_limit": 20,
                        "slow_limit": 15,
                        "boost_enabled": False,
                        "current_limit": 150,
                        "temp_limit": 85,
                        "skin_temp": 40,
                        "win_power": 0
                    },
                    "Balanced": {
                        "tdp": 30,
                        "fast_limit": 35,
                        "slow_limit": 30,
                        "boost_enabled": True,
                        "current_limit": 180,
                        "temp_limit": 90,
                        "skin_temp": 45,
                        "win_power": 1
                    },
                    "Boost": {
                        "tdp": 60,
                        "fast_limit": 70,
                        "slow_limit": 60,
                        "boost_enabled": True,
                        "current_limit": 200,
                        "temp_limit": 95,
                        "skin_temp": 50,
                        "win_power": 2
                    }
                }
            else:  # Framework 16 AMD
                model_id = "model_16"
                profiles = {
                    "Silent": {
                        "tdp": 30,
                        "fast_limit": 35,
                        "slow_limit": 30,
                        "boost_enabled": False,
                        "current_limit": 180,
                        "temp_limit": 95,
                        "skin_temp": 45,
                        "win_power": 0
                    },
                    "Balanced": {
                        "tdp": 95,
                        "fast_limit": 95,
                        "slow_limit": 95,
                        "boost_enabled": True,
                        "current_limit": 180,
                        "temp_limit": 95,
                        "skin_temp": 50,
                        "win_power": 1
                    },
                    "Boost": {
                        "tdp": 120,
                        "fast_limit": 140,
                        "slow_limit": 120,
                        "boost_enabled": True,
                        "current_limit": 200,
                        "temp_limit": 100,
                        "skin_temp": 50,
                        "win_power": 2
                    }
                }
            
            # Update settings
            self.settings["laptop_model"] = model_id
            self.settings["power_profiles"] = profiles
            
            # Save settings to file
            self.save_settings()
            logger.info(f"Settings saved for model: {model_name} ({model_id})")
            
            # Update refresh rate buttons for the new model
            self.update_refresh_rate_buttons()
            logger.info("Refresh rate buttons updated")
            
            # Re-apply current profile with new model settings
            current_profile = self.settings.get("ryzenadj_profile", "Balanced")
            self.apply_profile(current_profile)
            logger.info(f"Re-applied profile {current_profile} with new model settings")
            
            # Update UI elements
            self.model_var.set(model_name)  # Update model selector
            logger.info("UI updated to reflect new model")
            
        except Exception as e:
            logger.error(f"Error changing laptop model: {str(e)}")
            # Revert to previous model if there's an error
            try:
                previous_model = "Framework 16 AMD" if self.settings["laptop_model"] == "model_16" else "Framework 13 AMD"
                self.model_var.set(previous_model)
                logger.info(f"Reverted to previous model: {previous_model}")
            except:
                logger.error("Failed to revert to previous model")
        
    def get_windows_power_guid(self, power_level):
        """Get Windows power plan GUID based on power level"""
        power_guids = {
            0: "a1841308-3541-4fab-bc81-f71556f20b4a",  # Power saver
            1: "381b4222-f694-41f0-9685-ff5bb260df2e",  # Balanced
            2: "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"   # High performance
        }
        return power_guids.get(power_level, power_guids[1])  # Default to balanced
        
    def apply_profile(self, profile_name):
        try:
            logger.info(f"Attempting to apply profile: {profile_name}")
            logger.info(f"Available profiles: {list(self.settings['power_profiles'].keys())}")
            
            # Map UI profile names to settings profile names - Maintenant en majuscules
            profile_map = {
                "Silent": "Silent",
                "Balanced": "Balanced",
                "Boost": "Boost"  # Changé de "performance" à "Boost"
            }
            
            # Get the correct profile name from the map
            settings_profile_name = profile_map.get(profile_name)
            
            # Verify we're running on an AMD processor
            if not self.system_info.get("cpu_info", {}).get("is_amd", False):
                logger.error("This application only supports AMD Ryzen processors")
                return False
                
            if settings_profile_name not in self.settings["power_profiles"]:
                logger.error(f"Profile {profile_name} ({settings_profile_name}) not found")
                return False
            
            profile = self.settings["power_profiles"][settings_profile_name]
            logger.info(f"Applying profile: {profile_name} ({settings_profile_name})")
            
            # Update settings
            self.settings["ryzenadj_profile"] = profile_name
            self.save_settings()
            
            # Build RyzenADJ command
            ryzenadj_path = str(self.system_info["ryzenadj_path"])
            ryzenadj_args = []
            
            # Map profile settings to RyzenADJ arguments
            arg_mapping = {
                "tdp": "stapm-limit",
                "fast_limit": "fast-limit",
                "slow_limit": "slow-limit",
                "temp_limit": "tctl-temp",
                "skin_temp": "apu-skin-temp",
                "current_limit": "vrmmax-current"
            }
            
            for setting, arg in arg_mapping.items():
                if setting in profile:
                    value = profile[setting]
                    logger.info(f"Setting {arg} to {value}")
                    if "limit" in setting and "temp" not in setting:
                        value *= 1000
                    ryzenadj_args.extend([f"--{arg}", str(int(value))])
            
            logger.info(f"Final RyzenADJ command: {ryzenadj_path} {' '.join(ryzenadj_args)}")
            
            # Avant d'exécuter RyzenADJ, loggons les valeurs exactes
            logger.info(f"Profile settings to be applied: {profile}")
            logger.info(f"RyzenADJ arguments: {ryzenadj_args}")
            
            # Create PowerShell command with better error handling
            ps_command = f'''
$ErrorActionPreference = "Stop"
try {{
    $ryzenadj = "{ryzenadj_path}"
    Write-Output "Using RyzenADJ at: $ryzenadj"
    
    # Test if RyzenADJ exists
    if (-not (Test-Path $ryzenadj)) {{
        throw "RyzenADJ executable not found at: $ryzenadj"
    }}
    
    # Build arguments array
    $ryzenadj_args = @(
{chr(10).join([f'        "{arg}"' for arg in ryzenadj_args])}
    )
    Write-Output "Arguments: $($ryzenadj_args -join ' ')"
    
    # Check if running as admin
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    Write-Output "Running as admin: $isAdmin"
    
    if (-not $isAdmin) {{
        Write-Output "Elevating privileges..."
        $argString = $ryzenadj_args -join ' '
        
        # Create a new process with hidden window
        $pinfo = New-Object System.Diagnostics.ProcessStartInfo
        $pinfo.FileName = "powershell.exe"
        $pinfo.Arguments = "-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -Command & `"$ryzenadj`" $argString"
        $pinfo.Verb = "runas"
        $pinfo.RedirectStandardError = $true
        $pinfo.RedirectStandardOutput = $true
        $pinfo.UseShellExecute = $false
        $pinfo.CreateNoWindow = $true
        $pinfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
        
        $p = New-Object System.Diagnostics.Process
        $p.StartInfo = $pinfo
        $p.Start() | Out-Null
        $p.WaitForExit()
        
        $stdout = $p.StandardOutput.ReadToEnd()
        $stderr = $p.StandardError.ReadToEnd()
        
        Write-Output "Output: $stdout"
        if ($stderr) {{ Write-Error "Error: $stderr" }}
        
        if ($p.ExitCode -ne 0) {{
            throw "RyzenADJ failed with exit code: $($p.ExitCode)"
        }}
    }} else {{
        Write-Output "Running RyzenADJ directly..."
        $output = & $ryzenadj $ryzenadj_args 2>&1
        Write-Output "Output: $output"
        if ($LASTEXITCODE -ne 0) {{
            throw "RyzenADJ failed with exit code: $LASTEXITCODE`nOutput: $output"
        }}
    }}
    
    Write-Output "Profile applied successfully"
    exit 0
}} catch {{
    Write-Error $_.Exception.Message
    Write-Error $_.Exception.StackTrace
    exit 1
}}
'''
            
            # Save PowerShell script
            ps_script_path = Path("ryzenadj") / "apply_profile.ps1"
            ps_script_path.parent.mkdir(exist_ok=True)
            
            logger.info(f"Saving PowerShell script to: {ps_script_path}")
            with open(ps_script_path, "w", encoding='utf-8') as f:
                f.write(ps_command)
            
            # Execute PowerShell script with output capture
            logger.info("Executing RyzenADJ command")
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            result = subprocess.run(
                ["powershell.exe", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", str(ps_script_path)],
                capture_output=True,
                text=True,
                check=False,
                startupinfo=startupinfo
            )
            
            # Log the complete output
            if result.stdout:
                logger.info(f"PowerShell output: {result.stdout}")
            if result.stderr:
                logger.error(f"PowerShell error: {result.stderr}")
            
            if result.returncode == 0:
                logger.info(f"Profile {profile_name} applied successfully")
                
                # Set Windows power plan if specified
                if "win_power" in profile:
                    power_guid = self.get_windows_power_guid(profile["win_power"])
                    subprocess.run(
                        ["powercfg", "/setactive", power_guid],
                        check=False,
                        startupinfo=startupinfo
                    )
                
                # Mise à jour des couleurs des boutons avec plus de contraste
                for btn_name, btn in self.profile_buttons.items():
                    if btn_name == profile_name:
                        # Couleur plus vive et saturée pour le profil actif
                        btn.configure(
                            fg_color="#FF4B1F",  # Orange plus vif
                            text_color="white"    # Texte blanc pour plus de contraste
                        )
                    else:
                        # Retour à l'état normal pour les autres boutons
                        btn.configure(
                            fg_color="#FF7F5C",  # Orange normal
                            text_color="black"    # Texte noir
                        )
                
                return True
            else:
                logger.error(f"Failed to apply profile (exit code: {result.returncode})")
                return False
                
        except Exception as e:
            logger.error(f"Error in apply_profile: {str(e)}", exc_info=True)
            return False
        
    def set_refresh_rate_wrapper(self, rate: str) -> None:
        """Wrapper for set_refresh_rate with Auto mode handling"""
        try:
            if rate == "Auto":
                # Save Auto choice in settings
                self.settings["last_refresh_rate"] = "Auto"
                self.save_settings()
                
                # Start power monitoring if not already running
                if not self.power_monitor_thread or not self.power_monitor_thread.is_alive():
                    self.stop_power_monitor = False
                    self.power_monitor_thread = Thread(target=self.monitor_power_state, daemon=True)
                    self.power_monitor_thread.start()
                
                # Set initial rate based on current power state
                self.auto_refresh_rate()
            else:
                # Manual mode - apply rate directly
                self.settings["last_refresh_rate"] = rate
                self.save_settings()
                
                # Stop power monitoring if running
                self.stop_power_monitor = True
                
                # Update UI before attempting to change rate
                self.update_refresh_rate_buttons()
                
                # Start refresh rate change in a separate thread to prevent freezing
                Thread(target=self.set_refresh_rate, args=(rate,), daemon=True).start()
                
        except Exception as e:
            logger.error(f"Error in set_refresh_rate_wrapper: {str(e)}")

    def set_refresh_rate(self, rate):
        """Set display refresh rate using PowerShell"""
        try:
            # Convert rate string to integer (e.g., "165Hz" -> 165)
            if rate == "Auto":
                # For Auto mode, just update the UI and let the power monitor handle it
                self.update_refresh_rate_buttons()
                return True

            refresh_rate = int(rate.replace("Hz", ""))
            
            # PowerShell command to set refresh rate
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

            # Get current display settings
            [DisplaySettings]::EnumDisplaySettings($null, -1, [ref]$dm)
            
            # Store original frequency
            $originalFrequency = $dm.dmDisplayFrequency
            
            # Set new frequency
            $dm.dmDisplayFrequency = {refresh_rate}
            
            Write-Output "Attempting to change refresh rate from $originalFrequency Hz to {refresh_rate} Hz"
            
            $result = [DisplaySettings]::ChangeDisplaySettings([ref]$dm, 0)
            
            switch ($result) {{
                0 {{ 
                    Write-Output "Successfully changed refresh rate to {refresh_rate} Hz"
                    exit 0
                }}
                1 {{ 
                    Write-Output "Changes will be made on next restart"
                    exit 0
                }}
                -1 {{ 
                    throw "Failed to change refresh rate: Invalid parameters"
                }}
                -2 {{ 
                    throw "Failed to change refresh rate: Settings not supported"
                }}
                -3 {{ 
                    throw "Failed to change refresh rate: Invalid flags"
                }}
                -4 {{ 
                    throw "Failed to change refresh rate: Mode not supported"
                }}
                -5 {{ 
                    throw "Failed to change refresh rate: More than one display present"
                }}
                default {{ 
                    throw "Failed to change refresh rate: Unknown error (code: $result)"
                }}
            }}
            '''
            
            # Create startupinfo to hide window
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            # Execute PowerShell command
            result = subprocess.run(
                ["powershell", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
                capture_output=True,
                text=True,
                startupinfo=startupinfo
            )
            
            # Log the complete output
            if result.stdout:
                logger.info(f"Refresh rate change output: {result.stdout.strip()}")
            if result.stderr:
                logger.error(f"Refresh rate change error: {result.stderr.strip()}")
            
            if result.returncode == 0:
                logger.info(f"Successfully changed refresh rate to {refresh_rate}")
                self.update_refresh_rate_buttons()
                return True
            else:
                logger.error(f"Failed to change refresh rate (exit code: {result.returncode})")
                return False
                
        except Exception as e:
            logger.error(f"Error setting refresh rate: {str(e)}")
            return False

    def detect_screen_capabilities(self):
        try:
            # PowerShell command to get available display modes
            ps_command = '''
            Add-Type -TypeDefinition @"
            using System;
            using System.Runtime.InteropServices;
            
            public class DisplaySettings {
                [DllImport("user32.dll")]
                public static extern bool EnumDisplaySettings(string deviceName, int modeNum, ref DEVMODE devMode);
                
                [StructLayout(LayoutKind.Sequential)]
                public struct DEVMODE {
                    private const int CCHDEVICENAME = 32;
                    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = CCHDEVICENAME)]
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
                    public short dmBitsPerPel;
                    public int dmPelsWidth;
                    public int dmPelsHeight;
                    public int dmDisplayFlags;
                    public int dmDisplayFrequency;
                }
            }
"@
            
            $modes = @()
            $dm = New-Object DisplaySettings+DEVMODE
            $dm.dmSize = [System.Runtime.InteropServices.Marshal]::SizeOf($dm)
            $i = 0
            
            while ([DisplaySettings]::EnumDisplaySettings($null, $i, [ref]$dm)) {
                if ($dm.dmDisplayFrequency -gt 0) {
                    $modes += $dm.dmDisplayFrequency
                }
                $i++
            }
            
            $modes = $modes | Where-Object { $_ -gt 0 } | Select-Object -Unique | Sort-Object
            Write-Output ($modes -join "`n")
            '''
            
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                available_rates = [int(rate) for rate in result.stdout.strip().split('\n') if rate.strip()]
                if available_rates:  # Check if list is not empty
                    return {
                        'max_rate': max(available_rates),
                        'available_rates': available_rates
                    }
            
            # Default values if no rates detected
            logger.warning("No refresh rates detected, using default values")
            return {
                'max_rate': 165,  # Default max value
                'available_rates': [60, 120, 165]  # Default supported rates
            }
            
        except Exception as e:
            logger.error(f"Error detecting screen capabilities: {str(e)}", exc_info=True)
            # Default values on error
            return {
                'max_rate': 165,
                'available_rates': [60, 120, 165]
            }

    def update_refresh_rate_buttons(self):
        model = self.model_var.get()
        
        # Define rates based on model
        if model == "Framework 16 AMD":
            rates = ["Auto", "60Hz", "165Hz"]
            max_rate = 165
        else:  # Framework 13 AMD
            rates = ["Auto", "60Hz", "120Hz"]
            max_rate = 120
        
        # Remove old buttons safely
        try:
            for btn in list(self.refresh_buttons.values()):
                btn.pack_forget()  # Unpack first
                btn.destroy()      # Then destroy
            self.refresh_buttons.clear()
        except Exception as e:
            logger.error(f"Error clearing old buttons: {str(e)}")
        
        # Create new buttons
        last_rate = self.settings.get("last_refresh_rate", "Auto")
        
        # Style configurations
        active_style = {
            "fg_color": "#FF4B1F",      # Bright orange for active
            "hover_color": "#FF6B47",    # Lighter orange for hover
            "text_color": "white",       # White text for contrast
            "border_width": 2,           # Add border for emphasis
            "border_color": "#FFE4E1"    # Light border for glow effect
        }
        
        inactive_style = {
            "fg_color": "#FF7F5C",       # Normal orange
            "hover_color": self.hover_color,
            "text_color": "black",
            "border_width": 0,
            "border_color": None
        }
        
        disabled_style = {
            "fg_color": "#666666",       # Dark gray
            "hover_color": "#666666",
            "text_color": "#999999",     # Light gray text
            "border_width": 0,
            "border_color": None
        }
        
        def create_button_command(rate):
            def command():
                if rate == "Auto":
                    self.set_refresh_rate_wrapper("Auto")
                else:
                    self.set_refresh_rate_wrapper(rate)
            return command
        
        for rate in rates:
            try:
                # Check if rate is supported
                rate_value = int(rate.replace("Hz", "")) if rate != "Auto" else max_rate
                is_supported = rate == "Auto" or rate_value in self.screen_capabilities['available_rates']
                
                # Determine if this is the active rate
                is_active = rate == last_rate
                
                # Choose style based on button state
                style = active_style if is_active else (inactive_style if is_supported else disabled_style)
                
                btn = ctk.CTkButton(
                    self.refresh_container,
                    text=rate,
                    command=create_button_command(rate),
                    width=50,
                    height=24,
                    corner_radius=8,
                    state="normal" if is_supported else "disabled",
                    **style
                )
                btn.pack(side="left", padx=2)
                self.refresh_buttons[rate] = btn
                
            except Exception as e:
                logger.error(f"Error creating button for rate {rate}: {str(e)}")
        
        # Force update the container
        self.refresh_container.update()

    def monitor_power_state(self):
        """Thread function to monitor power state changes"""
        import psutil
        last_power_state = None
        
        while not self.stop_power_monitor:
            try:
                battery = psutil.sensors_battery()
                if battery:
                    current_power_state = battery.power_plugged
                    if current_power_state != last_power_state:
                        if not current_power_state:  # Si on débranche le chargeur
                            logger.info("AC power unplugged, waiting 5 seconds before applying changes...")
                            time.sleep(5)  # Attendre 5 secondes
                            # Vérifier à nouveau l'état après le délai
                            battery = psutil.sensors_battery()
                            if battery and not battery.power_plugged:  # Si toujours sur batterie
                                last_power_state = current_power_state
                                if self.settings.get("last_refresh_rate") == "Auto":
                                    self.auto_refresh_rate()
                        else:  # Si on branche le chargeur, appliquer immédiatement
                            last_power_state = current_power_state
                            if self.settings.get("last_refresh_rate") == "Auto":
                                self.auto_refresh_rate()
                time.sleep(2)  # Check every 2 seconds
            except Exception as e:
                logger.error(f"Error monitoring power state: {str(e)}")
                time.sleep(5)  # Wait longer on error

    def on_closing(self):
        """Clean up before closing"""
        try:
            # Stop all monitoring
            self.stop_power_monitor = True
            if self.power_monitor_thread:
                self.power_monitor_thread.join(timeout=1)
            if self.battery_monitor_thread:
                self.battery_monitor_thread.join(timeout=1)
            
            # Cleanup OpenHardwareMonitor
            if hasattr(self, 'monitor'):
                self.monitor.cleanup()
            
            # Hide to tray instead of closing
            self.withdraw()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    def load_battery_settings(self):
        """Load battery settings from config file"""
        try:
            with open('battery_config.json', 'r') as f:
                config = json.load(f)
                self.charge_limit = config.get('charge_limit', 80)
        except FileNotFoundError:
            self.charge_limit = 80  # Default optimized charge limit
            self.save_battery_settings()

    def save_battery_settings(self):
        """Save battery settings to config file"""
        try:
            with open('battery_config.json', 'w') as f:
                json.dump({
                    'charge_limit': self.charge_limit
                }, f)
        except Exception as e:
            logger.error(f"Error saving battery settings: {str(e)}")

    def set_charge_limit(self, limit: int):
        """Set battery charge limit using RyzenADJ"""
        try:
            if 60 <= limit <= 100:
                self.charge_limit = limit
                self.save_battery_settings()
                
                # Build RyzenADJ command with power saving options
                ryzenadj_path = str(self.system_info["ryzenadj_path"])
                
                # Calculate power limits based on charge limit percentage
                # Scale power limits proportionally to the charge limit
                power_factor = limit / 100.0
                
                # Base values for power limits
                base_stapm = 15000  # 15W base for power saving
                base_fast = 20000   # 20W base for fast limit
                base_slow = 15000   # 15W base for slow limit
                
                # Calculate adjusted limits
                stapm_limit = int(base_stapm * power_factor)
                fast_limit = int(base_fast * power_factor)
                slow_limit = int(base_slow * power_factor)
                
                # Execute command with PowerShell elevation
                ps_command = f'''
                try {{
                    $ryzenadj = "{ryzenadj_path}"
                    $output = & $ryzenadj --stapm-limit={stapm_limit} --fast-limit={fast_limit} --slow-limit={slow_limit} --power-saving 2>&1
                    if ($LASTEXITCODE -eq 0) {{
                        Write-Output "Successfully set power limits for {limit}% charge limit"
                        exit 0
                    }} else {{
                        throw "Failed to set power limits: $output"
                    }}
                }} catch {{
                    Write-Error $_.Exception.Message
                    exit 1
                }}
                '''
                
                result = subprocess.run(
                    ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info(f"Battery charge limit set to {limit}% with adjusted power limits")
                    # Update the slider value
                    if hasattr(self, 'charge_slider'):
                        self.charge_slider.set(limit)
                else:
                    logger.error(f"Failed to set power limits: {result.stderr}")
                    
        except Exception as e:
            logger.error(f"Error setting charge limit: {str(e)}")

    def on_slider_change(self, value):
        """Update label during slider movement"""
        limit = int(value)
        self.limit_label.configure(text=f"Current limit: {limit}%")

    def on_slider_release(self, event):
        """Apply charge limit when slider is released"""
        limit = int(self.charge_slider.get())
        self.set_charge_limit(limit)

    def start_battery_monitor(self):
        """Start battery monitoring thread"""
        def monitor_battery():
            while not self.stop_power_monitor:
                try:
                    battery = psutil.sensors_battery()
                    if battery:
                        # Update system tray tooltip
                        tooltip = f"Framework Mini Hub\nBattery: {int(battery.percent)}%"
                        if battery.power_plugged:
                            tooltip += " (Plugged in"
                            if battery.percent < self.charge_limit:
                                tooltip += ", Power saving active)"
                            else:
                                tooltip += ")"
                        if battery.secsleft != -1:
                            hours = battery.secsleft / 3600
                            tooltip += f"\nTime left: {hours:.1f}h"
                        
                        # Update tray icon tooltip
                        if hasattr(self, 'tray_icon'):
                            self.tray_icon.title = tooltip
                            
                        # Update battery status label with power mode info
                        status_text = f"Battery: {int(battery.percent)}% | Power Limit: {self.charge_limit}%"
                        if battery.power_plugged:
                            status_text += " | AC Power"
                            if battery.percent < self.charge_limit:
                                status_text += " (Power saving)"
                        else:
                            status_text += " | Battery Power"
                        self.battery_status.configure(text=status_text)
                        
                except Exception as e:
                    logger.error(f"Error monitoring battery: {str(e)}")
                time.sleep(5)  # Update every 5 seconds

        self.battery_monitor_thread = Thread(target=monitor_battery, daemon=True)
        self.battery_monitor_thread.start()

    def on_brightness_change(self, value):
        """Update brightness label during slider movement"""
        brightness = int(value)
        self.brightness_value_label.configure(text=f"Current: {brightness}%")

    def on_brightness_release(self, event):
        """Apply brightness when slider is released"""
        try:
            brightness = int(self.brightness_slider.get())
            c = wmi.WMI(namespace='wmi')
            methods = c.WmiMonitorBrightnessMethods()[0]
            methods.WmiSetBrightness(brightness, 0)
            logger.info(f"Successfully set brightness to {brightness}%")
        except Exception as e:
            logger.error(f"Error setting brightness: {str(e)}")

    def auto_refresh_rate(self):
        """Adjusts refresh rate based on power source"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                model = self.model_var.get()
                max_rate = "165Hz" if model == "Framework 16 AMD" else "120Hz"
                
                if battery.power_plugged:
                    logger.info("AC power detected, setting max refresh rate")
                    self.set_refresh_rate(max_rate)
                else:
                    logger.info("Battery power detected, setting 60Hz")
                    self.set_refresh_rate("60Hz")
        except Exception as e:
            logger.error(f"Error in auto refresh rate: {str(e)}")

    def set_dgpu_state(self, enable: bool):
        """Switch between iGPU and dGPU using Windows graphics settings"""
        try:
            # PowerShell script to manage GPU preference
            ps_command = f'''
            # Get all display adapters
            $gpus = Get-WmiObject Win32_VideoController | Where-Object {{ $_.Name -match 'AMD' }}
            
            foreach ($gpu in $gpus) {{
                if ($gpu.Name -match 'Ryzen') {{
                    Write-Output "Found iGPU: $($gpu.Name)"
                }} elseif ($gpu.Name -match 'AMD') {{
                    Write-Output "Found dGPU: $($gpu.Name)"
                }}
            }}
            
            # Set the GPU preference using AMD Radeon Settings
            try {{
                $regPath = "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Class\\{{4d36e968-e325-11ce-bfc1-08002be10318}}"
                $subKeys = Get-ChildItem -Path $regPath -ErrorAction SilentlyContinue
                
                foreach ($key in $subKeys) {{
                    $driverDesc = Get-ItemProperty -Path $key.PSPath -Name "DriverDesc" -ErrorAction SilentlyContinue
                    if ($driverDesc -and $driverDesc.DriverDesc -match 'AMD') {{
                        $keyPath = $key.PSPath
                        
                        # Set power mode
                        if ("{enable}" -eq "True") {{
                            Write-Output "Setting high performance mode"
                            Set-ItemProperty -Path $keyPath -Name "PowerMode" -Value 2  # Performance mode
                            Set-ItemProperty -Path $keyPath -Name "EnableUlps" -Value 0  # Disable ULPS
                        }} else {{
                            Write-Output "Setting power saving mode"
                            Set-ItemProperty -Path $keyPath -Name "PowerMode" -Value 1  # Power saving mode
                            Set-ItemProperty -Path $keyPath -Name "EnableUlps" -Value 1  # Enable ULPS
                        }}
                        
                        Write-Output "GPU power settings updated successfully"
                    }}
                }}
                
                # Restart the AMD driver service to apply changes
                $service = Get-Service "amdwddmg" -ErrorAction SilentlyContinue
                if ($service) {{
                    if ($service.Status -eq "Running") {{
                        Write-Output "Restarting AMD display driver..."
                        Stop-Service "amdwddmg" -Force
                        Start-Sleep -Seconds 2
                        Start-Service "amdwddmg"
                        Write-Output "AMD display driver restarted"
                    }}
                }}
                
            }} catch {{
                Write-Error "Failed to update GPU settings: $_"
                exit 1
            }}
            '''
            
            # Execute PowerShell command
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True
            )
            
            # Log the output
            if result.stdout:
                logger.info(f"GPU control output: {result.stdout.strip()}")
            if result.stderr:
                logger.error(f"GPU control error: {result.stderr.strip()}")
                
        except Exception as e:
            logger.error(f"Error setting GPU state: {str(e)}")

    def apply_saved_settings(self):
        """Apply all saved settings on startup"""
        pass  # Removed functionality - settings will not be auto-applied

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        # Window setup
        self.title("Settings")
        self.geometry("600x800")  # Increased size for more content
        self.minsize(600, 800)
        
        # Set dark theme
        self.configure(fg_color="#1A1A1A")
        
        # Colors
        self.button_color = "#FF7F5C"
        self.hover_color = "#FF9B80"
        self.bg_color = "#242424"
        self.text_color = "#E0E0E0"
        
        # Load current profile settings
        self.current_model = self.parent.model_var.get()
        self.current_profile = self.parent.settings["ryzenadj_profile"]
        self.profiles = self.parent.settings["power_profiles"]
        
        # Create main scrollable frame
        self.main_frame = ctk.CTkScrollableFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create widgets
        self.create_widgets()
        
        # Center window
        self.center_window()
        
    def create_widgets(self):
        frame_style = {"fg_color": self.bg_color, "corner_radius": 10}
        
        # Title
        title_label = ctk.CTkLabel(
            self.main_frame,
            text="Advanced Settings",
            text_color=self.text_color,
            font=("Arial", 20, "bold")
        )
        title_label.pack(pady=10)
        
        # Language Selection
        language_frame = ctk.CTkFrame(self.main_frame, **frame_style)
        language_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            language_frame,
            text="Language",
            text_color=self.text_color,
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        # Language mapping for display
        self.language_display = {
            "en": "English",
            "fr": "Français",
            "de": "Deutsch",
            "it": "Italiano",
            "es": "Español",
            "zh": "中文"
        }
        
        # Create list of language display names in the same order as language codes
        language_codes = ["en", "fr", "de", "it", "es", "zh"]
        language_names = [self.language_display[code] for code in language_codes]
        
        self.language_var = ctk.StringVar(value=self.language_display[self.parent.settings.get("language", "en")])
        language_menu = ctk.CTkOptionMenu(
            language_frame,
            values=language_names,
            command=lambda name: self.on_language_change(language_codes[language_names.index(name)]),
            variable=self.language_var,
            fg_color=self.button_color,
            button_color=self.button_color,
            button_hover_color=self.hover_color,
            text_color="black"
        )
        language_menu.pack(fill="x", padx=10, pady=5)
        
        # Model Selection
        model_frame = ctk.CTkFrame(self.main_frame, **frame_style)
        model_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            model_frame,
            text="Laptop Model",
            text_color=self.text_color,
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        self.model_var = ctk.StringVar(value=self.current_model)
        model_menu = ctk.CTkOptionMenu(
            model_frame,
            values=["Framework 13 AMD", "Framework 16 AMD"],
            command=self.on_model_change,
            variable=self.model_var,
            fg_color=self.button_color,
            button_color=self.button_color,
            button_hover_color=self.hover_color,
            text_color="black"
        )
        model_menu.pack(fill="x", padx=10, pady=5)
        
        # Profile Selection
        profile_frame = ctk.CTkFrame(self.main_frame, **frame_style)
        profile_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            profile_frame,
            text="Power Profile",
            text_color=self.text_color,
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        self.profile_var = ctk.StringVar(value=self.current_profile)
        profile_menu = ctk.CTkOptionMenu(
            profile_frame,
            values=["Silent", "Balanced", "Boost"],
            command=self.on_profile_change,
            variable=self.profile_var,
            fg_color=self.button_color,
            button_color=self.button_color,
            button_hover_color=self.hover_color,
            text_color="black"
        )
        profile_menu.pack(fill="x", padx=10, pady=5)
        
        # Create sliders for all RyzenADJ parameters
        self.create_ryzenadj_settings()
        
        # Save and Reset buttons at the bottom
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10, side="bottom")
        
        # Reset button
        self.reset_button = ctk.CTkButton(
            button_frame,
            text="Reset to Defaults",
            command=self.reset_settings,
            fg_color="#666666",
            hover_color="#888888",
            text_color="white",
            height=35,
            corner_radius=8
        )
        self.reset_button.pack(side="left", fill="x", expand=True, padx=5)
        
        # Save button
        self.save_button = ctk.CTkButton(
            button_frame,
            text="Save Changes",
            command=self.save_settings,
            fg_color=self.button_color,
            hover_color=self.hover_color,
            text_color="black",
            height=35,
            corner_radius=8
        )
        self.save_button.pack(side="right", fill="x", expand=True, padx=5)
        
    def on_language_change(self, language_code):
        """Handle language change"""
        self.parent.settings["language"] = language_code
        self.parent.save_settings()
        self.update_ui_language()
        
    def update_ui_language(self):
        """Update UI text based on selected language"""
        lang = self.parent.settings.get("language", "en")
        translations = TRANSLATIONS[lang]
        
        # Update window title
        self.title(translations["settings"])
        
        # Update main title
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "Advanced Settings":
                widget.configure(text=translations["advanced_settings"])
                break
                
        # Update frame labels
        for frame in self.main_frame.winfo_children():
            if isinstance(frame, ctk.CTkFrame):
                for widget in frame.winfo_children():
                    if isinstance(widget, ctk.CTkLabel):
                        text = widget.cget("text")
                        if text == "Language":
                            widget.configure(text=translations["language"])
                        elif text == "Laptop Model":
                            widget.configure(text=translations["laptop_model"])
        
    def create_ryzenadj_settings(self):
        # Clear existing settings if any
        for widget in self.main_frame.winfo_children():
            if widget.winfo_name().startswith('ryzenadj_'):
                widget.destroy()
        
        # Get current profile settings
        profile_settings = self.profiles[self.profile_var.get()]
        
        # Create frame for RyzenADJ settings
        settings_frame = ctk.CTkFrame(self.main_frame, fg_color=self.bg_color, corner_radius=10)
        settings_frame.pack(fill="x", pady=5)
        settings_frame.winfo_name = lambda: 'ryzenadj_frame'
        
        # Header
        ctk.CTkLabel(
            settings_frame,
            text="RyzenADJ Parameters",
            text_color=self.text_color,
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        # Define all RyzenADJ parameters with their ranges and default values
        self.parameters = {
            "tdp": {"name": "TDP (STAPM) Limit", "range": (15, 120), "unit": "W"},
            "fast_limit": {"name": "Fast Limit", "range": (20, 140), "unit": "W"},
            "slow_limit": {"name": "Slow Limit", "range": (15, 120), "unit": "W"},
            "current_limit": {"name": "VRM Current", "range": (100, 200), "unit": "A"},
            "temp_limit": {"name": "Temperature Limit", "range": (80, 100), "unit": "°C"},
            "skin_temp": {"name": "Skin Temperature", "range": (40, 50), "unit": "°C"}
        }
        
        # Create sliders for each parameter
        self.sliders = {}
        self.labels = {}
        
        for param, config in self.parameters.items():
            frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
            frame.pack(fill="x", padx=10, pady=5)
            
            # Label showing current value
            self.labels[param] = ctk.CTkLabel(
                frame,
                text=f"{config['name']}: {profile_settings.get(param, config['range'][0])}{config['unit']}",
                text_color=self.text_color
            )
            self.labels[param].pack(side="top", anchor="w")
            
            # Slider
            self.sliders[param] = ctk.CTkSlider(
                frame,
                from_=config['range'][0],
                to=config['range'][1],
                number_of_steps=int(config['range'][1] - config['range'][0]),
                command=lambda value, p=param: self.update_parameter(p, value),
                button_color=self.button_color,
                button_hover_color=self.hover_color,
                progress_color=self.button_color
            )
            self.sliders[param].pack(fill="x", pady=2)
            self.sliders[param].set(profile_settings.get(param, config['range'][0]))
        
        # CPU Boost switch
        boost_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        boost_frame.pack(fill="x", padx=10, pady=5)
        
        self.cpu_boost = ctk.CTkSwitch(
            boost_frame,
            text="CPU Boost",
            command=self.toggle_cpu_boost,
            button_color=self.button_color,
            button_hover_color=self.hover_color,
            progress_color=self.button_color
        )
        self.cpu_boost.pack(anchor="w")
        self.cpu_boost.select() if profile_settings.get("boost_enabled", True) else self.cpu_boost.deselect()
        
    def update_parameter(self, param, value):
        """Update parameter label when slider is moved"""
        unit = self.parameters[param]["unit"]
        self.labels[param].configure(
            text=f"{self.parameters[param]['name']}: {int(value)}{unit}"
        )
        
    def toggle_cpu_boost(self):
        """Handle CPU boost toggle"""
        pass  # Will be implemented with save_settings
        
    def on_model_change(self, model):
        """Handle model change"""
        self.current_model = model
        
        # Update profiles based on model
        if model == "Framework 13 AMD":
            self.profiles = {
                "Silent": {
                    "tdp": 15, "fast_limit": 20, "slow_limit": 15,
                    "boost_enabled": False, "current_limit": 150,
                    "temp_limit": 85, "skin_temp": 40
                },
                "Balanced": {
                    "tdp": 30, "fast_limit": 35, "slow_limit": 30,
                    "boost_enabled": True, "current_limit": 180,
                    "temp_limit": 90, "skin_temp": 45
                },
                "Boost": {
                    "tdp": 60, "fast_limit": 70, "slow_limit": 60,
                    "boost_enabled": True, "current_limit": 200,
                    "temp_limit": 95, "skin_temp": 50
                }
            }
        else:  # Framework 16 AMD
            self.profiles = {
                "Silent": {
                    "tdp": 30, "fast_limit": 35, "slow_limit": 30,
                    "boost_enabled": False, "current_limit": 180,
                    "temp_limit": 95, "skin_temp": 45
                },
                "Balanced": {
                    "tdp": 95, "fast_limit": 95, "slow_limit": 95,
                    "boost_enabled": True, "current_limit": 180,
                    "temp_limit": 95, "skin_temp": 50
                },
                "Boost": {
                    "tdp": 120, "fast_limit": 140, "slow_limit": 120,
                    "boost_enabled": True, "current_limit": 200,
                    "temp_limit": 100, "skin_temp": 50
                }
            }
        
        # Update the UI with the new profile values
        self.create_ryzenadj_settings()
        
    def on_profile_change(self, profile):
        """Handle profile change"""
        self.create_ryzenadj_settings()  # Recreate settings with new profile's values
        
    def reset_settings(self):
        """Reset all settings to defaults based on model and profile"""
        if self.current_model == "Framework 13 AMD":
            defaults = {
                "Silent": {
                    "tdp": 15, "fast_limit": 20, "slow_limit": 15,
                    "boost_enabled": False, "current_limit": 150,
                    "temp_limit": 85, "skin_temp": 40
                },
                "Balanced": {
                    "tdp": 30, "fast_limit": 35, "slow_limit": 30,
                    "boost_enabled": True, "current_limit": 180,
                    "temp_limit": 90, "skin_temp": 45
                },
                "Boost": {
                    "tdp": 60, "fast_limit": 70, "slow_limit": 60,
                    "boost_enabled": True, "current_limit": 200,
                    "temp_limit": 95, "skin_temp": 50
                }
            }
        else:  # Framework 16 AMD
            defaults = {
                "Silent": {
                    "tdp": 30, "fast_limit": 35, "slow_limit": 30,
                    "boost_enabled": False, "current_limit": 180,
                    "temp_limit": 95, "skin_temp": 45
                },
                "Balanced": {
                    "tdp": 95, "fast_limit": 95, "slow_limit": 95,
                    "boost_enabled": True, "current_limit": 180,
                    "temp_limit": 95, "skin_temp": 50
                },
                "Boost": {
                    "tdp": 120, "fast_limit": 140, "slow_limit": 120,
                    "boost_enabled": True, "current_limit": 200,
                    "temp_limit": 100, "skin_temp": 50
                }
            }
        
        # Apply defaults
        default_values = defaults[self.profile_var.get()]
        for param, value in default_values.items():
            if param in self.sliders:
                self.sliders[param].set(value)
                self.update_parameter(param, value)
        
        # Set CPU Boost
        if default_values["boost_enabled"]:
            self.cpu_boost.select()
        else:
            self.cpu_boost.deselect()
        
    def save_settings(self):
        """Save all settings"""
        # Get current profile
        profile = self.profile_var.get()
        
        # Collect all values
        new_settings = {
            param: int(slider.get()) for param, slider in self.sliders.items()
        }
        new_settings["boost_enabled"] = bool(self.cpu_boost.get())
        
        # Update the parent's settings with the correct model
        model_id = "model_13_amd" if self.current_model == "Framework 13 AMD" else "model_16"
        
        # If model changed, update laptop_model in settings
        if self.parent.settings["laptop_model"] != model_id:
            self.parent.settings["laptop_model"] = model_id
            # Update all profiles for the new model
            self.parent.settings["power_profiles"] = self.profiles
        else:
            # Just update the current profile
            self.parent.settings["power_profiles"][profile].update(new_settings)
        
        # Save settings
        self.parent.save_settings()
        
        # Apply the new profile if it's the current one and model hasn't changed
        if profile == self.parent.settings["ryzenadj_profile"] and self.parent.model_var.get() == self.current_model:
            self.parent.apply_profile(profile)
        else:
            # If model changed, update the parent's model selector
            self.parent.model_var.set(self.current_model)
        
        # Close settings window
        self.destroy()
        
    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

class AMDGPUControl:
    def __init__(self):
        self.wmi = None
        self.gpu_info = {}
        try:
            pythoncom.CoInitialize()
            self.wmi = wmi.WMI()
            self._init_gpu_info()
        except Exception as e:
            logger.error(f"Error initializing AMDGPUControl: {e}")

    def get_gpu_info(self):
        """Return stored GPU information"""
        return self.gpu_info

    def get_gpu_metrics(self):
        """Get real-time GPU metrics for both GPUs"""
        metrics = {}
        try:
            # Create a new WMI instance for each call to avoid COM errors
            pythoncom.CoInitialize()
            wmi_instance = wmi.WMI()
            
            # Get basic GPU info from Windows WMI
            for gpu in wmi_instance.Win32_VideoController():
                if "AMD" in gpu.Name:
                    gpu_metrics = {
                        'name': gpu.Name,
                        'status': gpu.Status,
                        'memory': {},
                        'utilization': 0,
                        'temperature': None
                    }

                    # Get GPU utilization
                    try:
                        for perf in wmi_instance.Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine():
                            if gpu.Name in perf.Name:
                                gpu_metrics['utilization'] = float(perf.UtilizationPercentage)
                                break
                    except Exception as e:
                        logger.debug(f"Could not get GPU utilization: {e}")

                    # Get temperature from WMI
                    try:
                        # Try to get temperature from AMD WMI provider
                        for temp in wmi_instance.MSAcpi_ThermalZoneTemperature():
                            temp_celsius = (float(temp.CurrentTemperature) / 10.0) - 273.15
                            gpu_metrics['temperature'] = temp_celsius
                            break
                    except Exception as e:
                        logger.debug(f"Could not get GPU temperature: {e}")

                    # Store metrics using DeviceID as key
                    metrics[gpu.DeviceID] = gpu_metrics

            return metrics

        except Exception as e:
            logger.error(f"Error getting GPU metrics: {str(e)}")
            return None
        finally:
            try:
                pythoncom.CoUninitialize()
            except:
                pass

    def _init_gpu_info(self):
        """Initialize GPU information for both GPUs"""
        try:
            if not self.wmi:
                try:
                    self.wmi = wmi.WMI()
                except Exception as e:
                    logger.error(f"Failed to initialize WMI in _init_gpu_info: {e}")
                    return
                
            for gpu in self.wmi.Win32_VideoController():
                if "AMD" in gpu.Name:
                    gpu_data = {
                        'name': gpu.Name,
                        'driver_version': gpu.DriverVersion,
                        'memory': gpu.AdapterRAM if gpu.AdapterRAM else 0,
                        'resolution': f"{gpu.CurrentHorizontalResolution}x{gpu.CurrentVerticalResolution}",
                        'device_id': gpu.DeviceID
                    }
                    # Use DeviceID as key to distinguish between GPUs
                    self.gpu_info[gpu.DeviceID] = gpu_data
                    logger.info(f"AMD GPU detected: {gpu_data['name']}")
        except Exception as e:
            logger.error(f"Error initializing GPU info: {e}")

    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            pythoncom.CoUninitialize()
        except:
            pass

class UpdateWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        # Window setup
        self.title("Driver Updates")
        self.geometry("450x750")  # Slightly reduced height
        self.minsize(450, 750)    # Adjusted minimum size
        
        # Set dark theme
        self.configure(fg_color="#1A1A1A")
        
        # Colors
        self.button_color = "#FF7F5C"
        self.hover_color = "#FF9B80"
        self.bg_color = "#242424"
        self.text_color = "#E0E0E0"
        
        # Get current AMD driver info
        self.current_drivers = self.get_current_driver_versions()
        
        # Create widgets
        self.create_widgets()
        
        # Center window
        self.center_window()
        
    def create_widgets(self):
        frame_style = {"fg_color": self.bg_color, "corner_radius": 10}
        
        # Main container with padding
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Title with icon
        title_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 25))
        
        # Framework logo/icon would go here
        title_label = ctk.CTkLabel(
            title_frame,
            text="Driver Updates",
            text_color=self.text_color,
            font=("Arial", 20, "bold")
        )
        title_label.pack()
        
        # System info frame
        system_frame = ctk.CTkFrame(main_container, **frame_style)
        system_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            system_frame,
            text="System Information:",
            text_color=self.text_color,
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Get Windows version
        try:
            win_ver = platform.win32_ver()[0]
            win_build = platform.win32_ver()[2]
            os_info = f"Windows {win_ver} (Build {win_build})"
        except:
            os_info = "Windows (version unknown)"
            
        ctk.CTkLabel(
            system_frame,
            text=f"Operating System: {os_info}",
            text_color=self.text_color,
            justify="left",
            font=("Arial", 12)
        ).pack(anchor="w", padx=15, pady=(0, 10))
        
        # Current version info
        version_frame = ctk.CTkFrame(main_container, **frame_style)
        version_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            version_frame,
            text="Currently Installed Drivers:",
            text_color=self.text_color,
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        for gpu, info in self.current_drivers.items():
            driver_text = f"{info['name']}\nDriver Version: {info['version']}"
            ctk.CTkLabel(
                version_frame,
                text=driver_text,
                text_color=self.text_color,
                justify="left",
                font=("Arial", 12)
            ).pack(anchor="w", padx=15, pady=(0, 10))
        
        # Info text frame
        info_frame = ctk.CTkFrame(main_container, **frame_style)
        info_frame.pack(fill="x", pady=(0, 25))
        
        info_text = """To update your drivers, please visit the official websites:

• AMD website for the latest GPU and chipset drivers
• Framework website for specific laptop drivers and BIOS updates

Important Updates:
• GPU and Chipset Drivers (AMD Website)
• BIOS Updates (Framework Website)
• Firmware Updates (Framework Website)
• Other System Drivers (Framework Website)

Note: It's recommended to regularly check for driver updates to ensure optimal performance and compatibility."""
        
        info_label = ctk.CTkLabel(
            info_frame,
            text=info_text,
            text_color=self.text_color,
            justify="left",
            font=("Arial", 12),
            wraplength=400
        )
        info_label.pack(padx=15, pady=15)
        
        # Buttons frame
        button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 0))
        
        # AMD Drivers button
        amd_button = ctk.CTkButton(
            button_frame,
            text="AMD Drivers",
            command=lambda: webbrowser.open("https://www.amd.com/en/support"),
            fg_color=self.button_color,
            hover_color=self.hover_color,
            text_color="black",
            height=40,
            width=420,
            corner_radius=5,
            font=("Arial", 12, "bold")
        )
        amd_button.pack(pady=(0, 10))
        
        # Framework Drivers button
        framework_button = ctk.CTkButton(
            button_frame,
            text="Framework Drivers",
            command=lambda: webbrowser.open("https://knowledgebase.frame.work/en_us/bios-and-drivers-downloads-rJ3PaCexh"),
            fg_color=self.button_color,
            hover_color=self.hover_color,
            text_color="black",
            height=40,
            width=420,
            corner_radius=5,
            font=("Arial", 12, "bold")
        )
        framework_button.pack()
    
    def get_current_driver_versions(self):
        """Get current AMD driver versions"""
        drivers = {}
        try:
            wmi_instance = wmi.WMI()
            for gpu in wmi_instance.Win32_VideoController():
                if "AMD" in gpu.Name:
                    drivers[gpu.DeviceID] = {
                        'name': gpu.Name,
                        'version': gpu.DriverVersion
                    }
        except Exception as e:
            logger.error(f"Error getting driver versions: {str(e)}")
        return drivers
    
    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

if __name__ == "__main__":
    try:
        logger.info("Starting application")
        if not ctypes.windll.shell32.IsUserAnAdmin():
            logger.info("Requesting admin privileges")
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{__file__}"', None, 1
            )
        else:
            logger.info("Running with admin privileges")
            app = MiniFrameworkHub()
            app.mainloop()
    except Exception as e:
        logger.error(f"Critical error: {str(e)}", exc_info=True)
        import tkinter.messagebox as messagebox
        messagebox.showerror(
            "Error",
            f"An error occurred during startup:\n{str(e)}\n\nPlease check mini_hub.log for details."
        )