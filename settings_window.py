import customtkinter as ctk
from typing import Dict, Any
import logging
import json
from translations import TRANSLATIONS
from constants import RYZENADJ_LIMITS

logger = logging.getLogger(__name__)

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.sliders = {}
        self.current_model = self.parent.settings.get("laptop_model", "model_13_amd")
        
        # Ajouter un callback pour le changement de modèle
        self.parent.model_var.trace_add("write", self.on_model_change)
        
        # Window setup
        self.title(self.tr("settings"))
        self.geometry("600x800")
        self.minsize(600, 800)
        
        # Forcer la fenêtre au premier plan
        self.attributes('-topmost', True)
        
        # Set dark theme
        self.configure(fg_color="#1A1A1A")
        
        # Colors
        self.button_color = "#FF7F5C"
        self.hover_color = "#FF9B80"
        self.bg_color = "#242424"
        self.text_color = "#E0E0E0"
        
        # Variables for theme settings
        self.theme_change_vars = {}
        self.dark_theme_vars = {}
        self.dark_theme_checks = {}
        
        # Load current settings
        self.current_model = self.parent.model_var.get()
        self.current_profile = self.parent.settings.get("ryzenadj_profile", "Balanced")
        self.profiles = self.parent.settings.get("power_profiles", {})
        
        if not self.profiles:  # If no saved profiles, get defaults
            self.profiles = {
                profile: self.parent.power_manager.get_profile_settings(profile, self.current_model)
                for profile in ["Silent", "Balanced", "Boost"]
            }
        
        # Create main scrollable frame
        self.main_frame = ctk.CTkScrollableFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create widgets
        self.create_widgets()
        
        # Center window
        self.center_window()
        
        # Initialiser les variables de contrôle
        self.default_profile_var = ctk.StringVar(value=self.parent.settings.get("default_profile", "Balanced"))
        self.minimize_var = ctk.BooleanVar(value=self.parent.settings.get("minimize_to_tray", True))
        self.notifications_var = ctk.BooleanVar(value=self.parent.settings.get("show_notifications", True))
        self.startup_profile_var = ctk.StringVar(value=self.parent.settings.get("startup_profile", "Last Used"))
        self.hotkey_var = ctk.StringVar(value=self.parent.settings.get("hotkey", "F12"))
        self.theme_var = ctk.StringVar(value=self.parent.settings.get("theme", "dark"))
        self.charge_limit_var = ctk.IntVar(value=self.parent.settings.get("battery_charge_limit", 80))
        self.auto_switch_var = ctk.BooleanVar(value=self.parent.settings.get("auto_switch_profile", True))
        self.battery_profile_var = ctk.StringVar(value=self.parent.settings.get("on_battery_profile", "Silent"))
        self.ac_profile_var = ctk.StringVar(value=self.parent.settings.get("on_ac_profile", "Balanced"))
        
    def tr(self, key):
        """Get translation for key"""
        return self.parent.translations.get(key, key)
        
    def create_widgets(self):
        frame_style = {"fg_color": self.bg_color, "corner_radius": 10}
        
        # Title
        title_label = ctk.CTkLabel(
            self.main_frame,
            text=self.tr("advanced_settings"),
            text_color=self.text_color,
            font=("Arial", 20, "bold")
        )
        title_label.pack(pady=10)
        
        # Language Selection
        language_frame = ctk.CTkFrame(self.main_frame, **frame_style)
        language_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            language_frame,
            text=self.tr("language"),
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
        
        # Reverse mapping for getting language code from display name
        self.language_codes = {v: k for k, v in self.language_display.items()}
        
        # Get current language display name
        current_lang = self.parent.settings.get("language", "en")
        current_display = self.language_display.get(current_lang, "English")
        
        self.language_menu = ctk.CTkOptionMenu(
            language_frame,
            values=list(self.language_display.values()),
            command=self.on_language_change,
            variable=ctk.StringVar(value=current_display),
            fg_color=self.button_color,
            button_color=self.button_color,
            button_hover_color=self.hover_color,
            text_color="black"
        )
        self.language_menu.pack(fill="x", padx=10, pady=5)
        
        # Model Selection
        model_frame = ctk.CTkFrame(self.main_frame, **frame_style)
        model_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            model_frame,
            text=self.tr("laptop_model"),
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
        
        # Profile Customization
        self.create_profile_settings("Silent", self.tr("silent_profile"))
        self.create_profile_settings("Balanced", self.tr("balanced_profile"))
        self.create_profile_settings("Boost", self.tr("boost_profile"))
        
        # Other Settings
        other_frame = ctk.CTkFrame(self.main_frame, **frame_style)
        other_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            other_frame,
            text=self.tr("other_settings"),
            text_color=self.text_color,
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        # Startup option
        self.startup_var = ctk.BooleanVar(value=self.parent.settings.get("start_with_windows", False))
        startup_check = ctk.CTkCheckBox(
            other_frame,
            text=self.tr("start_with_windows"),
            variable=self.startup_var,
            text_color=self.text_color,
            fg_color=self.button_color,
            hover_color=self.hover_color
        )
        startup_check.pack(anchor="w", padx=10, pady=5)
        
        # Auto-update option
        self.update_var = ctk.BooleanVar(value=self.parent.settings.get("auto_update", True))
        update_check = ctk.CTkCheckBox(
            other_frame,
            text=self.tr("auto_update"),
            variable=self.update_var,
            text_color=self.text_color,
            fg_color=self.button_color,
            hover_color=self.hover_color
        )
        update_check.pack(anchor="w", padx=10, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        save_btn = ctk.CTkButton(
            button_frame,
            text=self.tr("save"),
            command=self.save_settings,
            fg_color=self.button_color,
            hover_color=self.hover_color,
            text_color="black"
        )
        save_btn.pack(side="left", padx=5, expand=True)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text=self.tr("cancel"),
            command=self.destroy,
            fg_color="#808080",
            hover_color="#A0A0A0",
            text_color=self.text_color
        )
        cancel_btn.pack(side="right", padx=5, expand=True)
        
    def create_profile_settings(self, profile_name: str, title: str):
        """Create settings for a power profile"""
        profile = self.profiles.get(profile_name, {})
        
        # Profile frame
        profile_frame = ctk.CTkFrame(self.main_frame, fg_color=self.bg_color)
        profile_frame.pack(fill="x", pady=5, padx=10)
        
        # Title
        ctk.CTkLabel(
            profile_frame,
            text=title,
            text_color=self.text_color,
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        # TDP settings
        self.create_slider(
            profile_frame,
            f"{profile_name}_tdp",
            self.tr("tdp"),
            profile.get("tdp", 15),
            0,
            120 if "16" in self.current_model else 60
        )
        
        # Fast Boost settings
        self.create_slider(
            profile_frame,
            f"{profile_name}_fast",
            self.tr("fast_limit"),
            profile.get("fast_limit", 20),
            0,
            140 if "16" in self.current_model else 70
        )
        
        # Slow Boost settings
        self.create_slider(
            profile_frame,
            f"{profile_name}_slow",
            self.tr("slow_limit"),
            profile.get("slow_limit", 15),
            0,
            120 if "16" in self.current_model else 60
        )
        
        # Temperature limit
        self.create_slider(
            profile_frame,
            f"{profile_name}_temp",
            self.tr("temp_limit"),
            profile.get("temp_limit", 85),
            60,
            100
        )
        
        # Current limit
        self.create_slider(
            profile_frame,
            f"{profile_name}_current",
            self.tr("current_limit"),
            profile.get("current_limit", 180),
            100,
            200
        )
        
        # Skin temperature
        self.create_slider(
            profile_frame,
            f"{profile_name}_skin",
            self.tr("skin_temp"),
            profile.get("skin_temp", 45),
            35,
            50
        )
        
        # Screen timeout
        self.create_slider(
            profile_frame,
            f"{profile_name}_screen",
            self.tr("screen_timeout"),
            profile.get("screen_timeout", 15),
            1,
            60
        )
        
        # Sleep timeout
        self.create_slider(
            profile_frame,
            f"{profile_name}_sleep",
            self.tr("sleep_timeout"),
            profile.get("sleep_timeout", 30),
            1,
            120
        )
        
        # Theme change settings
        theme_frame = ctk.CTkFrame(profile_frame, fg_color="transparent")
        theme_frame.pack(fill="x", padx=10, pady=5)
        
        self.theme_change_vars[profile_name] = ctk.BooleanVar(value=profile.get("change_theme", False))
        self.dark_theme_vars[profile_name] = ctk.BooleanVar(value=profile.get("dark_theme", False))
        
        theme_check = ctk.CTkCheckBox(
            theme_frame,
            text=self.tr("theme_change"),
            variable=self.theme_change_vars[profile_name],
            command=lambda: self.on_theme_change(profile_name),
            text_color=self.text_color,
            fg_color=self.button_color,
            hover_color=self.hover_color
        )
        theme_check.pack(side="left", padx=5)
        
        self.dark_theme_checks[profile_name] = ctk.CTkCheckBox(
            theme_frame,
            text=self.tr("dark_theme"),
            variable=self.dark_theme_vars[profile_name],
            state="normal" if profile.get("change_theme", False) else "disabled",
            text_color=self.text_color,
            fg_color=self.button_color,
            hover_color=self.hover_color
        )
        self.dark_theme_checks[profile_name].pack(side="left", padx=5)
        
    def create_slider(self, parent, name: str, label: str, default: float, min_val: float, max_val: float):
        """Create a labeled slider"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=2)
        
        # Label with current value
        label_frame = ctk.CTkFrame(frame, fg_color="transparent")
        label_frame.pack(fill="x")
        
        ctk.CTkLabel(
            label_frame,
            text=label,
            text_color=self.text_color
        ).pack(side="left")
        
        value_label = ctk.CTkLabel(
            label_frame,
            text=f"{int(default)}",
            text_color=self.text_color
        )
        value_label.pack(side="right")
        
        # Slider
        slider = ctk.CTkSlider(
            frame,
            from_=int(min_val),
            to=int(max_val),
            number_of_steps=int(max_val - min_val),
            command=lambda v: value_label.configure(text=f"{int(v)}"),
            button_color=self.button_color,
            button_hover_color=self.hover_color,
            progress_color=self.button_color,
            fg_color=self.bg_color
        )
        slider.pack(fill="x", pady=2)
        slider.set(int(default))
        
        # Store reference
        setattr(self, f"slider_{name}", slider)
        return slider
        
    def on_language_change(self, display_name: str):
        """Handle language change"""
        try:
            # Get language code from display name
            language_code = self.language_codes.get(display_name, "en")
            
            # Save language code in settings and update current language
            self.parent.settings["language"] = language_code
            self.parent.current_language = language_code
            self.parent.translations = TRANSLATIONS[language_code]
            
            # Save settings immediately
            self.parent.save_settings()
            
            # Force update ALL UI elements
            self.parent.update_ui_language()  # Main window
            self.parent.update_profile_buttons()  # Profile buttons
            self.parent.update_status_labels()  # Status labels
            self.parent.update_menu()  # Menu items
            
            # Recreate ALL windows to ensure complete UI update
            if hasattr(self.parent, 'settings_window') and self.parent.settings_window:
                self.parent.settings_window.destroy()
                self.parent.settings_window = None
                
            if hasattr(self.parent, 'update_window') and self.parent.update_window:
                self.parent.update_window.destroy()
                self.parent.update_window = None
                
            # Create new settings window with updated language
            new_settings = SettingsWindow(self.parent)
            
            logger.info(f"Language changed to {language_code} ({display_name})")
            
            # Show success notification in new language
            success_text = TRANSLATIONS[language_code].get("language_changed", "Language changed successfully")
            title_text = TRANSLATIONS[language_code].get("success", "Success")
            self.parent.show_notification(title_text, success_text)
            
        except Exception as e:
            logger.error(f"Error changing language: {e}")
            error_text = "Could not change language" if display_name == "English" else TRANSLATIONS.get(language_code, {}).get("language_error", "Impossible de changer la langue")
            title_text = "Error" if display_name == "English" else TRANSLATIONS.get(language_code, {}).get("error", "Erreur")
            self.parent.show_notification(title_text, error_text, error=True)
        
    def update_ui_language(self):
        """Update UI text based on selected language"""
        try:
            # Update window title
            self.title(self.tr("settings"))
            
            # Update all widgets in main frame
            for widget in self.main_frame.winfo_children():
                if isinstance(widget, ctk.CTkLabel):
                    # Update main labels
                    if widget.cget("text") == "Advanced Settings":
                        widget.configure(text=self.tr("advanced_settings"))
                elif isinstance(widget, ctk.CTkFrame):
                    # Update frame contents
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkLabel):
                            # Update section titles
                            text = child.cget("text")
                            if text in ["Language", "Laptop Model", "Other Settings"]:
                                child.configure(text=self.tr(text.lower().replace(" ", "_")))
                        elif isinstance(child, ctk.CTkCheckBox):
                            # Update checkboxes
                            text = child.cget("text")
                            if text in ["Start with Windows", "Auto Update"]:
                                child.configure(text=self.tr(text.lower().replace(" ", "_")))
                                
            # Update buttons
            for widget in self.winfo_children():
                if isinstance(widget, ctk.CTkButton):
                    text = widget.cget("text")
                    if text in ["Save", "Cancel"]:
                        widget.configure(text=self.tr(text.lower()))
                        
            logger.info("Settings window UI updated to new language")
            
        except Exception as e:
            logger.error(f"Error updating settings window UI: {e}")
        
    def on_model_change(self, *args):
        """Appelé quand le modèle de laptop change"""
        try:
            new_model = self.parent.model_var.get()
            if new_model != self.current_model:
                self.current_model = new_model
                # Recharger les sliders avec les nouvelles valeurs
                self.update_all_sliders()
                logger.info(f"Settings window updated for model: {new_model}")
        except Exception as e:
            logger.error(f"Erreur mise à jour modèle: {e}")

    def update_all_sliders(self):
        """Met à jour tous les sliders avec les valeurs du modèle actuel"""
        try:
            # Obtenir les profils pour le modèle actuel
            profiles = self.parent.settings["power_profiles"].get(self.current_model, {})
            
            # Pour chaque profil
            for profile_name in ["Silent", "Balanced", "Boost"]:
                if profile_name in profiles:
                    profile_values = profiles[profile_name]
                    
                    # Pour chaque paramètre du profil
                    for param, value in profile_values.items():
                        slider_key = f"{profile_name}_{param}"
                        if slider_key in self.sliders:
                            # Mettre à jour le slider et son label
                            slider = self.sliders[slider_key]
                            slider.set(value)
                            
                            # Mettre à jour le label
                            slider_frame = slider.master
                            label = slider_frame.winfo_children()[0]
                            label.configure(text=f"{param}: {value}")
                            
            logger.info(f"Sliders updated for model: {self.current_model}")
        except Exception as e:
            logger.error(f"Erreur mise à jour sliders: {e}")

    def center_window(self):
        """Centre la fenêtre en haut de l'écran"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        
        # Calculer la position x pour centrer horizontalement
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        
        # Positionner en haut avec un petit décalage de 50 pixels
        y = 50
        
        # Appliquer la position
        self.geometry(f"{width}x{height}+{x}+{y}")
        
    def save_settings(self):
        """Save all settings"""
        try:
            # Save language and model
            self.parent.settings["language"] = self.parent.current_language
            self.parent.settings["laptop_model"] = "model_16" if "16" in self.current_model else "model_13_amd"
            
            # Save profile settings for each profile
            profiles_settings = {}
            for profile in ["Silent", "Balanced", "Boost"]:
                profile_settings = {
                    # Paramètres existants
                    "tdp": int(getattr(self, f"slider_{profile}_tdp").get()),
                    "fast_limit": int(getattr(self, f"slider_{profile}_fast").get()),
                    "slow_limit": int(getattr(self, f"slider_{profile}_slow").get()),
                    "temp_limit": int(getattr(self, f"slider_{profile}_temp").get()),
                    "change_theme": self.theme_change_vars[profile].get(),
                    "dark_theme": self.dark_theme_vars[profile].get(),
                    "boost_enabled": profile != "Silent",
                    
                    # Nouveaux paramètres à sauvegarder
                    "current_limit": getattr(self, f"slider_{profile}_current").get() if hasattr(self, f"slider_{profile}_current") else 180,
                    "skin_temp": getattr(self, f"slider_{profile}_skin").get() if hasattr(self, f"slider_{profile}_skin") else 45,
                    "power_plan": getattr(self, f"power_plan_{profile}") if hasattr(self, f"power_plan_{profile}") else "Balanced",
                    "refresh_rate": getattr(self, f"refresh_rate_{profile}") if hasattr(self, f"refresh_rate_{profile}") else "Auto",
                    "brightness": getattr(self, f"slider_{profile}_brightness").get() if hasattr(self, f"slider_{profile}_brightness") else 100,
                    "background_apps": getattr(self, f"background_apps_{profile}") if hasattr(self, f"background_apps_{profile}") else True,
                    "location": getattr(self, f"location_{profile}") if hasattr(self, f"location_{profile}") else True,
                    "bluetooth": getattr(self, f"bluetooth_{profile}") if hasattr(self, f"bluetooth_{profile}") else True,
                    "screen_timeout": getattr(self, f"slider_{profile}_screen").get() if hasattr(self, f"slider_{profile}_screen") else 15,
                    "sleep_timeout": getattr(self, f"slider_{profile}_sleep").get() if hasattr(self, f"slider_{profile}_sleep") else 30
                }
                profiles_settings[profile] = profile_settings
                
            # Save all profiles
            self.parent.settings["power_profiles"] = profiles_settings
            
            # Save other settings
            self.parent.settings.update({
                "start_with_windows": self.startup_var.get(),
                "auto_update": self.update_var.get(),
                "default_profile": self.default_profile_var.get() if hasattr(self, 'default_profile_var') else "Balanced",
                "minimize_to_tray": self.minimize_var.get() if hasattr(self, 'minimize_var') else True,
                "show_notifications": self.notifications_var.get() if hasattr(self, 'notifications_var') else True,
                "startup_profile": self.startup_profile_var.get() if hasattr(self, 'startup_profile_var') else "Last Used",
                "hotkey": self.hotkey_var.get() if hasattr(self, 'hotkey_var') else "F12",
                "theme": self.theme_var.get() if hasattr(self, 'theme_var') else "dark",
                "battery_charge_limit": int(self.charge_limit_var.get()) if hasattr(self, 'charge_limit_var') else 80,
                "auto_switch_profile": self.auto_switch_var.get() if hasattr(self, 'auto_switch_var') else True,
                "on_battery_profile": self.battery_profile_var.get() if hasattr(self, 'battery_profile_var') else "Silent",
                "on_ac_profile": self.ac_profile_var.get() if hasattr(self, 'ac_profile_var') else "Balanced"
            })
            
            # Save to file
            self.parent.save_settings()
            
            # Apply changes
            self.parent.power_manager.load_profiles(profiles_settings)
            self.parent.power_manager.apply_power_profile(self.current_profile, self.current_model)
            
            # Update UI
            self.parent.update_ui_language()
            
            # Show success notification
            self.parent.show_notification(
                self.tr("success"),
                self.tr("settings_saved")
            )
            
            # Close window
            self.destroy()
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des paramètres: {e}")
            self.parent.show_notification(
                self.tr("error"),
                self.tr("settings_save_error"),
                error=True
            )
        
    def on_theme_change(self, profile_name: str) -> None:
        """Handle theme change checkbox toggle"""
        enabled = self.theme_change_vars[profile_name].get()
        if profile_name in self.dark_theme_checks:
            self.dark_theme_checks[profile_name].configure(
                state="normal" if enabled else "disabled"
            )
        
    def create_ryzenadj_frame(self) -> None:
        """Crée le frame des paramètres RyzenADJ"""
        try:
            frame = ctk.CTkFrame(self)
            frame.pack(fill="x", padx=10, pady=5)
            
            # Obtenir le modèle actuel
            current_model = self.parent.settings.get("laptop_model", "model_13_amd")
            custom_values = self.parent.settings["ryzenadj_custom_values"].get(current_model, {})
            
            # Créer les sliders avec les valeurs spécifiques au modèle
            self.create_ryzenadj_sliders(frame, custom_values)
            
        except Exception as e:
            logger.error(f"Erreur création frame RyzenADJ: {e}")
            
    def create_ryzenadj_sliders(self, parent: ctk.CTkFrame, custom_values: Dict[str, Any]) -> None:
        """Crée les sliders pour les paramètres RyzenADJ"""
        try:
            # Définir les limites selon le modèle
            limits = RYZENADJ_LIMITS[self.current_model]
            
            # Créer un frame pour chaque profil
            for profile_name in ["Silent", "Balanced", "Boost"]:
                profile_frame = ctk.CTkFrame(parent)
                profile_frame.pack(fill="x", padx=5, pady=5)
                
                # Titre du profil
                label = ctk.CTkLabel(profile_frame, text=profile_name, font=("Arial", 14, "bold"))
                label.pack(fill="x", padx=5, pady=5)
                
                # Récupérer les valeurs du profil
                profile_values = self.parent.settings["power_profiles"][self.current_model][profile_name]
                
                # Créer les sliders pour chaque paramètre
                for param, (min_val, max_val) in limits.items():
                    if param in profile_values:
                        param_frame = ctk.CTkFrame(profile_frame)
                        param_frame.pack(fill="x", padx=5, pady=2)
                        
                        # Label avec la valeur actuelle
                        label_text = f"{param}: {profile_values[param]}"
                        label = ctk.CTkLabel(param_frame, text=label_text)
                        label.pack(side="left", padx=5)
                        
                        # Slider
                        slider = ctk.CTkSlider(
                            param_frame,
                            from_=min_val,
                            to=max_val,
                            number_of_steps=100,
                            command=lambda v, p=param, pn=profile_name: self.update_profile_value(pn, p, v)
                        )
                        slider.set(profile_values[param])
                        slider.pack(side="right", expand=True, fill="x", padx=5)
                        
                        # Stocker la référence du slider
                        self.sliders[f"{profile_name}_{param}"] = slider
                        
        except Exception as e:
            logger.error(f"Erreur création sliders RyzenADJ: {e}")
        
    def update_profile_value(self, profile_name: str, param: str, value: float) -> None:
        """Met à jour la valeur d'un paramètre dans un profil"""
        try:
            current_model = self.parent.settings.get("laptop_model", "model_13_amd")
            if current_model in self.parent.settings["power_profiles"]:
                # Mettre à jour la valeur
                self.parent.settings["power_profiles"][current_model][profile_name][param] = value
                
                # Mettre à jour le label
                slider_key = f"{profile_name}_{param}"
                if slider_key in self.sliders:
                    slider_frame = self.sliders[slider_key].master
                    label = slider_frame.winfo_children()[0]  # Le premier enfant est le label
                    label.configure(text=f"{param}: {value}")
                
                # Sauvegarder les paramètres
                self.parent.save_settings()
                
                # Si c'est le profil actuel, appliquer les changements
                if self.parent.settings["ryzenadj_profile"] == profile_name:
                    self.parent.apply_profile(profile_name)
                    
                logger.info(f"Paramètre {param} du profil {profile_name} mis à jour: {value}")
                
        except Exception as e:
            logger.error(f"Erreur mise à jour paramètre du profil: {e}")
  