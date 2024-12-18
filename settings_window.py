import customtkinter as ctk
from translations import TRANSLATIONS

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        # Window setup
        self.title(self.tr("settings"))
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
        
    def on_language_change(self, language_code):
        """Handle language change"""
        self.parent.settings["language"] = language_code
        self.parent.save_settings()
        self.parent.update_ui_language()
        self.update_ui_language()
        
    def update_ui_language(self):
        """Update UI text based on selected language"""
        # Update window title
        self.title(self.tr("settings"))
        
        # Update all labels in main frame
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                if widget.cget("text") == "Advanced Settings":
                    widget.configure(text=self.tr("advanced_settings"))
            elif isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkLabel):
                        text = child.cget("text")
                        if text == "Language":
                            child.configure(text=self.tr("language"))
                        elif text == "Laptop Model":
                            child.configure(text=self.tr("laptop_model"))
        
    def on_model_change(self, model):
        """Handle model change"""
        self.parent.change_laptop_model(model)
        
    def center_window(self):
        """Center the window on the screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}") 