import customtkinter as ctk
from PIL import Image
from pathlib import Path
import logging
from typing import Dict, Any, Optional, Callable, Union
import win32gui

logger = logging.getLogger(__name__)

class UIManager:
    def __init__(self, parent: Any, settings: Dict[str, Any], translations: Dict[str, str]):
        self.parent = parent
        self.settings = settings
        self.translations = translations
        self.buttons: Dict[str, ctk.CTkButton] = {}
        self.labels: Dict[str, ctk.CTkLabel] = {}
        self.frames: Dict[str, ctk.CTkFrame] = {}
        
        # Couleurs
        self.colors = {
            'button': "#FF7F5C",      # Orange Framework
            'hover': "#FF9B80",       # Orange plus clair
            'active': "#E85D3A",      # Orange plus foncé
            'bg': "#242424",          # Gris foncé
            'progress_bg': "#2D2D2D", # Gris plus clair
            'text': "#E0E0E0"         # Gris clair
        }
        
    def setup_window(self, title: str, geometry: str) -> None:
        """Configure la fenêtre principale"""
        self.parent.title(title)
        self.parent.geometry("300x650")
        self.parent.minsize(300, 650)
        
        # Thème sombre
        ctk.set_appearance_mode("dark")
        self.parent.configure(fg_color="#1A1A1A")
        
        # Icône
        self._set_window_icon()
        
        # Barre de titre personnalisée
        self._create_title_bar()
        
        # Position de la fenêtre
        self._position_window()
        
    def _set_window_icon(self) -> None:
        """Configure l'icône de la fenêtre"""
        try:
            icon_path = Path("assets") / "logo.ico"
            if icon_path.exists():
                self.parent.iconbitmap(str(icon_path))
        except Exception as e:
            logger.error(f"Erreur lors du chargement de l'icône: {e}")
            
    def _create_title_bar(self) -> None:
        """Crée une barre de titre personnalisée"""
        title_bar = ctk.CTkFrame(self.parent, fg_color="#1A1A1A", height=30)
        title_bar.pack(fill="x", pady=0)
        
        # Titre
        title_label = ctk.CTkLabel(
            title_bar,
            text="Framework Mini Hub",
            text_color=self.colors['text'],
            anchor="w"
        )
        title_label.pack(side="left", padx=10)
        
        # Bouton fermer
        close_button = ctk.CTkButton(
            title_bar,
            text="×",
            width=30,
            height=30,
            command=self.parent.withdraw,
            fg_color="#1A1A1A",
            hover_color="#FF4B1F",
            text_color=self.colors['text']
        )
        close_button.pack(side="right", padx=0)
        
        # Bouton réduire
        minimize_button = ctk.CTkButton(
            title_bar,
            text="−",
            width=30,
            height=30,
            command=self.parent.withdraw,
            fg_color="#1A1A1A",
            hover_color="#FF7F5C",
            text_color=self.colors['text']
        )
        minimize_button.pack(side="right", padx=0)
        
        # Rendre la fenêtre déplaçable
        title_bar.bind("<Button-1>", self.parent.start_move)
        title_bar.bind("<B1-Motion>", self.parent.on_move)
        title_label.bind("<Button-1>", self.parent.start_move)
        title_label.bind("<B1-Motion>", self.parent.on_move)
        
    def _position_window(self) -> None:
        """Positionne la fenêtre"""
        try:
            saved_position = self.settings.get("window_position")
            
            if saved_position:
                x = saved_position["x"]
                y = saved_position["y"]
                self.parent.geometry(f"300x650+{x}+{y}")
            else:
                # Position par défaut (coin inférieur droit)
                screen_width = self.parent.winfo_screenwidth()
                screen_height = self.parent.winfo_screenheight()
                
                # Hauteur de la barre des tâches
                taskbar = win32gui.FindWindow("Shell_TrayWnd", None)
                taskbar_height = (taskbar_rect := win32gui.GetWindowRect(taskbar))[3] - taskbar_rect[1] if taskbar else 40
                
                # Calcul de la position
                x = screen_width - 315
                y = screen_height - 650 - taskbar_height - 5
                
                # Sauvegarde et utilisation
                self.settings["window_position"] = {"x": x, "y": y}
                self.parent.geometry(f"300x650+{x}+{y}")
            
            # Suppression des décorations de fenêtre et toujours au premier plan
            self.parent.overrideredirect(True)
            self.parent.attributes('-topmost', True)
            self.parent.after(100, lambda: self.parent.attributes('-topmost', False))
            
        except Exception as e:
            logger.error(f"Erreur lors du positionnement de la fenêtre: {e}")
            
    def create_frame(self, name: str, **kwargs) -> ctk.CTkFrame:
        """Crée un frame avec le style par défaut"""
        frame = ctk.CTkFrame(
            self.parent,
            fg_color=self.colors['bg'],
            corner_radius=10,
            **kwargs
        )
        self.frames[name] = frame
        return frame
        
    def create_button(self, parent: Any, text: str, command: Callable, **kwargs) -> ctk.CTkButton:
        """Crée un bouton avec le style par défaut"""
        # Valeurs par défaut
        default_kwargs = {
            "fg_color": self.colors['button'],
            "hover_color": self.colors['hover'],
            "text_color": "black",
            "corner_radius": 8,
            "height": 35  # Hauteur par défaut
        }
        
        # Mettre à jour avec les kwargs fournis
        default_kwargs.update(kwargs)
        
        button = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            **default_kwargs
        )
        self.buttons[text] = button
        return button
        
    def create_label(self, parent: Any, text: str, **kwargs) -> ctk.CTkLabel:
        """Crée un label avec le style par défaut"""
        label = ctk.CTkLabel(
            parent,
            text=text,
            text_color=self.colors['text'],
            **kwargs
        )
        self.labels[text] = label
        return label
        
    def create_progress_bar(self, parent: Any, **kwargs) -> ctk.CTkProgressBar:
        """Crée une barre de progression avec le style par défaut"""
        return ctk.CTkProgressBar(
            parent,
            progress_color=self.colors['button'],
            fg_color=self.colors['progress_bg'],
            height=6,
            corner_radius=3,
            border_width=0,
            **kwargs
        )
        
    def update_ui_language(self, translations: Dict[str, str]) -> None:
        """Met à jour la langue de l'interface"""
        self.translations = translations
        
        # Mise à jour des textes
        for widget in self.parent.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                text = widget.cget("text")
                if text in self.translations:
                    widget.configure(text=self.translations[text])
            elif isinstance(widget, ctk.CTkButton):
                text = widget.cget("text")
                if text in self.translations:
                    widget.configure(text=self.translations[text])
            elif isinstance(widget, (ctk.CTkFrame, ctk.CTkScrollableFrame)):
                self._update_frame_language(widget)
                    
    def _update_frame_language(self, frame: Union[ctk.CTkFrame, ctk.CTkScrollableFrame]) -> None:
        """Met à jour la langue des widgets dans un frame"""
        for widget in frame.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                text = widget.cget("text")
                if text in self.translations:
                    widget.configure(text=self.translations[text])
            elif isinstance(widget, ctk.CTkButton):
                text = widget.cget("text")
                if text in self.translations:
                    widget.configure(text=self.translations[text])
            elif isinstance(widget, (ctk.CTkFrame, ctk.CTkScrollableFrame)):
                self._update_frame_language(widget)
        
    def create_monitoring_widgets(self, parent: ctk.CTkFrame) -> Dict[str, Any]:
        """Crée les widgets de monitoring système"""
        # Nettoyer les widgets existants
        for widget in parent.winfo_children():
            widget.destroy()
        
        # Créer le groupe de monitoring
        monitor_group = ctk.CTkFrame(parent, fg_color="transparent")
        monitor_group.pack(fill="x", pady=2, padx=5)
        
        widgets = {}
        
        # CPU
        widgets['cpu_label'] = ctk.CTkLabel(monitor_group, text="CPU: 0%", font=("Arial", 12))
        widgets['cpu_label'].grid(row=0, column=0, padx=3, pady=1, sticky="w")
        
        widgets['cpu_progress'] = self.create_progress_bar(monitor_group)
        widgets['cpu_progress'].grid(row=0, column=1, padx=3, pady=1, sticky="ew")
        widgets['cpu_progress'].set(0)
        
        # Température CPU
        widgets['temp_label'] = ctk.CTkLabel(monitor_group, text="CPU Temp: 0°C", font=("Arial", 12))
        widgets['temp_label'].grid(row=1, column=0, padx=3, pady=1, sticky="w")
        
        widgets['temp_progress'] = self.create_progress_bar(monitor_group)
        widgets['temp_progress'].grid(row=1, column=1, padx=3, pady=1, sticky="ew")
        widgets['temp_progress'].set(0)
        
        # RAM
        widgets['ram_label'] = ctk.CTkLabel(monitor_group, text="RAM: 0%", font=("Arial", 12))
        widgets['ram_label'].grid(row=2, column=0, padx=3, pady=1, sticky="w")
        
        widgets['ram_progress'] = self.create_progress_bar(monitor_group)
        widgets['ram_progress'].grid(row=2, column=1, padx=3, pady=1, sticky="ew")
        widgets['ram_progress'].set(0)
        
        # GPU intégré (780M)
        widgets['igpu_label'] = ctk.CTkLabel(monitor_group, text="iGPU (780M): 0%", font=("Arial", 12))
        widgets['igpu_label'].grid(row=3, column=0, padx=3, pady=1, sticky="w")
        
        widgets['igpu_progress'] = self.create_progress_bar(monitor_group)
        widgets['igpu_progress'].grid(row=3, column=1, padx=3, pady=1, sticky="ew")
        widgets['igpu_progress'].set(0)
        
        # Température iGPU
        widgets['igpu_temp_label'] = ctk.CTkLabel(monitor_group, text="GPU VR SoC: 0°C", font=("Arial", 12))
        widgets['igpu_temp_label'].grid(row=4, column=0, padx=3, pady=1, sticky="w")
        
        widgets['igpu_temp_progress'] = self.create_progress_bar(monitor_group)
        widgets['igpu_temp_progress'].grid(row=4, column=1, padx=3, pady=1, sticky="ew")
        widgets['igpu_temp_progress'].set(0)
        
        # GPU dédié (7700S)
        widgets['dgpu_label'] = ctk.CTkLabel(monitor_group, text="dGPU (7700S): 0%", font=("Arial", 12))
        widgets['dgpu_label'].grid(row=5, column=0, padx=3, pady=1, sticky="w")
        
        widgets['dgpu_progress'] = self.create_progress_bar(monitor_group)
        widgets['dgpu_progress'].grid(row=5, column=1, padx=3, pady=1, sticky="ew")
        widgets['dgpu_progress'].set(0)
        
        # Température dGPU
        widgets['dgpu_temp_label'] = ctk.CTkLabel(monitor_group, text="GPU Core: 0°C", font=("Arial", 12))
        widgets['dgpu_temp_label'].grid(row=6, column=0, padx=3, pady=1, sticky="w")
        
        widgets['dgpu_temp_progress'] = self.create_progress_bar(monitor_group)
        widgets['dgpu_temp_progress'].grid(row=6, column=1, padx=3, pady=1, sticky="ew")
        widgets['dgpu_temp_progress'].set(0)
        
        # Configurer la colonne pour qu'elle s'étende
        monitor_group.grid_columnconfigure(1, weight=1)
        
        return widgets