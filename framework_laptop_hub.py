import sys
import ctypes
import os
from pathlib import Path
import requests
import zipfile
import subprocess
import psutil
import wmi
import json
import webbrowser
from threading import Thread
import time
import customtkinter as ctk
from PIL import Image
from language_manager import LanguageManager
from laptop_models import LAPTOP_MODELS, POWER_PROFILES
import pythoncom
import tkinter.font as tkfont
import logging

# Font configuration
class FontManager:
    def __init__(self):
        self.fonts_dir = Path("fonts")
        self.load_fonts()
        
    def load_fonts(self):
        """Load Ubuntu fonts from the fonts directory"""
        self.fonts = {
            "regular": self.load_font("Ubuntu-Regular.ttf"),
            "medium": self.load_font("Ubuntu-Medium.ttf"),
            "bold": self.load_font("Ubuntu-Bold.ttf"),
            "light": self.load_font("Ubuntu-Light.ttf"),
            "italic": self.load_font("Ubuntu-Italic.ttf"),
            "medium_italic": self.load_font("Ubuntu-MediumItalic.ttf"),
            "bold_italic": self.load_font("Ubuntu-BoldItalic.ttf"),
            "light_italic": self.load_font("Ubuntu-LightItalic.ttf")
        }
    
    def load_font(self, font_file):
        """Load a single font file"""
        try:
            font_path = self.fonts_dir / font_file
            if font_path.exists():
                return str(font_path)
            return None
        except Exception as e:
            print(f"Error loading font {font_file}: {e}")
            return None
    
    def get_font(self, style="regular", size=11):
        """Get a CTkFont object with the specified style and size"""
        try:
            font_path = self.fonts.get(style)
            if font_path:
                # Map style to valid weight values
                weight = "bold" if style in ["bold", "medium"] else "normal"
                return ctk.CTkFont(family="Ubuntu", size=size, weight=weight)
            return ctk.CTkFont(size=size)  # Fallback to system font
        except Exception as e:
            print(f"Error creating font: {e}")
            return ctk.CTkFont(size=size)  # Fallback to system font

class SystemInfo:
    def __init__(self, settings):
        self._wmi = None
        self.settings = settings
        self.update_system_info()
    
    @property
    def wmi(self):
        if self._wmi is None:
            self._wmi = wmi.WMI()
        return self._wmi
    
    def update_system_info(self):
        try:
            # CPU Info
            cpu_info = self.wmi.Win32_Processor()[0]
            self.cpu_name = cpu_info.Name
            self.cpu_cores = psutil.cpu_count(logical=False)
            self.cpu_threads = psutil.cpu_count(logical=True)
            
            # GPU Info
            gpu_info = self.wmi.Win32_VideoController()
            self.gpu_names = [gpu.Name for gpu in gpu_info]
            
            # RAM Info
            ram = psutil.virtual_memory()
            self.total_ram = round(ram.total / (1024**3))  # Convert to GB
            
            # Framework specific info
            self.is_framework = any("Framework" in gpu.Name for gpu in gpu_info)
            
            # Get model info from settings
            model_key = self.settings.get_setting("laptop_model", "model_13_amd")
            model_info = LAPTOP_MODELS.get(model_key, LAPTOP_MODELS["model_13_amd"])
            self.model_name = model_info["name"]
            
            # Additional model-specific info
            self.display_info = model_info["display"]
            self.ram_info = model_info["ram"]
            self.storage_info = model_info["storage"]
            self.expansion_ports = model_info["expansion_ports"]
            self.battery_capacity = model_info["battery"]
            self.tdp_range = model_info["tdp"]
            self.has_dgpu = model_info["has_dgpu"]
            self.gpu_model = model_info.get("gpu", None)
            
        except Exception as e:
            print(f"Error updating system info: {e}")
            self.cpu_name = "Unknown CPU"
            self.gpu_names = ["Unknown GPU"]
            self.total_ram = 0
            self.model_name = "Unknown System"
            self.display_info = {}
            self.ram_info = {}
            self.storage_info = {}
            self.expansion_ports = 0
            self.battery_capacity = 0
            self.tdp_range = {"min": 0, "max": 0}
            self.has_dgpu = False
            self.gpu_model = None

class Settings:
    def __init__(self):
        self.settings_file = Path("settings.json")
        self.load_settings()
    
    def load_settings(self):
        default_settings = {
            "language": "en",
            "ryzenadj_profile": "Balanced",
            "laptop_model": "model_13_amd",  # Default to AMD 13" model
            "theme": "light",  # Default to light theme
            "ryzenadj_custom_values": {},
            "admin_granted": False
        }
        
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
                    # Ensure new settings are added
                    for key, value in default_settings.items():
                        if key not in self.settings:
                            self.settings[key] = value
            except:
                self.settings = default_settings
        else:
            self.settings = default_settings
    
    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)
    
    def get_setting(self, key, default=None):
        return self.settings.get(key, default)
    
    def set_setting(self, key, value):
        self.settings[key] = value
        self.save_settings()

class RyzenADJ:
    def __init__(self, settings):
        self.settings = settings
        self.ryzenadj_path = self.ensure_ryzenadj()
        self.current_profile = self.settings.get_setting("ryzenadj_profile", "Balanced")
        self.laptop_model = self.settings.get_setting("laptop_model", "model_13_amd")
        
        # Get the model-specific power profiles
        self.update_profiles()
    
    def update_profiles(self):
        """Update power profiles based on the selected laptop model"""
        model_profiles = POWER_PROFILES.get(self.laptop_model, POWER_PROFILES["model_13_amd"])
        
        # Convert the power profiles to RyzenADJ format
        self.profiles = {
            "Silent": {
                "stapm-limit": str(model_profiles["silent"]["tdp"] * 1000),
                "fast-limit": str(model_profiles["silent"]["tdp"] * 1000),
                "slow-limit": str(model_profiles["silent"]["tdp"] * 1000),
                "tctl-temp": "95"
            },
            "Balanced": {
                "stapm-limit": str(model_profiles["balanced"]["tdp"] * 1000),
                "fast-limit": str(model_profiles["balanced"]["tdp"] * 1000),
                "slow-limit": str(model_profiles["balanced"]["tdp"] * 1000),
                "tctl-temp": "95"
            },
            "Performance": {
                "stapm-limit": str(model_profiles["performance"]["tdp"] * 1000),
                "fast-limit": str(model_profiles["performance"]["tdp"] * 1000),
                "slow-limit": str(model_profiles["performance"]["tdp"] * 1000),
                "tctl-temp": "100"
            }
        }
    
    def set_laptop_model(self, model):
        """Update the laptop model and refresh power profiles"""
        self.laptop_model = model
        self.settings.set_setting("laptop_model", model)
        self.update_profiles()
    
    def apply_profile(self, profile_name):
        try:
            if profile_name not in self.profiles:
                print(f"Error: Profile {profile_name} not found")
                return False
            
            profile = self.profiles[profile_name]
            self.current_profile = profile_name
            
            # Build RyzenADJ command
            ryzenadj_path = str(self.ryzenadj_path)
            ryzenadj_args = []
            for param, value in profile.items():
                ryzenadj_args.append(f"--{param}")
                ryzenadj_args.append(value)
            
            # Create a temporary batch file to run RyzenADJ with admin rights
            batch_content = f'''@echo off
echo Applying {profile_name} profile...
cd /d "%~dp0"
"{ryzenadj_path}" {" ".join(ryzenadj_args)}
if %ERRORLEVEL% EQU 0 (
    echo Profile applied successfully
    exit /b 0
) else (
    echo Failed to apply profile
    exit /b 1
)
'''
            batch_path = Path("ryzenadj") / "apply_profile.bat"
            with open(batch_path, "w", encoding='utf-8') as f:
                f.write(batch_content)
            
            print(f"Executing RyzenADJ with profile {profile_name}")
            
            # Run the batch file with admin rights using PowerShell
            powershell_command = f'Start-Process -FilePath "{batch_path}" -Verb RunAs -Wait -WindowStyle Hidden -PassThru'
            
            try:
                result = subprocess.run(
                    ["powershell.exe", "-Command", powershell_command],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    print(f"Profile {profile_name} applied successfully")
                    return True
                else:
                    print(f"Failed to apply profile: {result.stderr}")
                    return False
                    
            except Exception as e:
                print(f"Error executing RyzenADJ: {str(e)}")
                return False
            
        except Exception as e:
            print(f"Error applying profile: {str(e)}")
            return False
    
    def ensure_ryzenadj(self):
        ryzenadj_dir = Path("ryzenadj")
        ryzenadj_exe = ryzenadj_dir / "ryzenadj.exe"
        
        if not ryzenadj_exe.exists():
            print("Downloading RyzenADJ...")
            ryzenadj_dir.mkdir(exist_ok=True)
            
            url = "https://github.com/FlyGoat/RyzenAdj/releases/download/v0.8.2/ryzenadj-win64.zip"
            zip_path = Path("ryzenadj.zip")
            
            try:
                response = requests.get(url)
                response.raise_for_status()
                
                with open(zip_path, 'wb') as f:
                    f.write(response.content)
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(ryzenadj_dir)
                
                zip_path.unlink()
                
                # Verify the executable exists after extraction
                if not ryzenadj_exe.exists():
                    raise FileNotFoundError("RyzenADJ executable not found after extraction")
                    
            except Exception as e:
                print(f"Error downloading/extracting RyzenADJ: {str(e)}")
                return None
        
        # Convert to absolute path
        return ryzenadj_exe.absolute()

class CollapsibleFrame(ctk.CTkFrame):
    def __init__(self, *args, title="", subtitle="", **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get language manager from master if available
        try:
            if "master" in kwargs and hasattr(kwargs["master"], "app"):
                self.language_manager = kwargs["master"].app.language_manager
            elif "master" in kwargs and hasattr(kwargs["master"], "language_manager"):
                self.language_manager = kwargs["master"].language_manager
            else:
                self.language_manager = None
        except:
            self.language_manager = None
        
        # Header
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=15, pady=(15,5))
        
        # Default fonts
        title_font = ctk.CTkFont(family="Ubuntu", size=13, weight="bold")
        subtitle_font = ctk.CTkFont(family="Ubuntu", size=11)
        
        # Try to get fonts from master if available
        try:
            if "master" in kwargs and hasattr(kwargs["master"], "font_manager"):
                title_font = kwargs["master"].font_manager.get_font("bold", 13)
                subtitle_font = kwargs["master"].font_manager.get_font("light", 11)
            elif "master" in kwargs and hasattr(kwargs["master"], "app"):
                title_font = kwargs["master"].app.font_manager.get_font("bold", 13)
                subtitle_font = kwargs["master"].app.font_manager.get_font("light", 11)
        except Exception as e:
            print(f"Warning: Could not access font_manager: {e}")
        
        # If title/subtitle are translation keys and we have language_manager, translate them
        if self.language_manager:
            try:
                title = self.language_manager.get_text(title)
                subtitle = self.language_manager.get_text(subtitle)
            except:
                pass  # Keep original strings if translation fails
        
        self.title_label = ctk.CTkLabel(
            self.header, 
            text=title,
            font=title_font,
            anchor="w"
        )
        self.title_label.pack(fill="x")
        
        self.subtitle_label = ctk.CTkLabel(
            self.header,
            text=subtitle,
            font=subtitle_font,
            text_color="gray",
            anchor="w"
        )
        self.subtitle_label.pack(fill="x")
        
        # Content
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="x", padx=15, pady=(5,15))
        
    def update_text(self):
        """Update frame text when language changes"""
        if self.language_manager:
            try:
                current_title = self.title_label.cget("text")
                current_subtitle = self.subtitle_label.cget("text")
                
                # Try to translate current text
                new_title = self.language_manager.get_text(current_title)
                new_subtitle = self.language_manager.get_text(current_subtitle)
                
                self.title_label.configure(text=new_title)
                self.subtitle_label.configure(text=new_subtitle)
            except:
                pass  # Keep current text if translation fails

class CustomSlider(ctk.CTkFrame):
    def __init__(self, *args, title="", value=0, unit="", min_val=0, max_val=100, show_button=True, **kwargs):
        super().__init__(*args, fg_color="transparent", **kwargs)
        
        # Get language manager from master if available
        try:
            if "master" in kwargs and hasattr(kwargs["master"], "app"):
                self.language_manager = kwargs["master"].app.language_manager
            elif "master" in kwargs and hasattr(kwargs["master"], "language_manager"):
                self.language_manager = kwargs["master"].language_manager
            else:
                self.language_manager = None
        except:
            self.language_manager = None
        
        # Get the root window to access font manager
        try:
            if "master" in kwargs and hasattr(kwargs["master"], "app"):
                font_manager = kwargs["master"].app.font_manager
            elif "master" in kwargs and hasattr(kwargs["master"], "font_manager"):
                font_manager = kwargs["master"].font_manager
            else:
                font_manager = None
        except:
            font_manager = None
        
        # Store values
        self.min_val = min_val
        self.max_val = max_val
        self.current_val = value
        self.unit = unit
        self.show_button = show_button
        self.callback = None
        
        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0,5))
        
        # Title with value display
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", fill="x", expand=True)
        
        # Title with fallback font
        title_font = (
            font_manager.get_font("regular", 11) if font_manager 
            else ctk.CTkFont(family="Ubuntu", size=11)
        )
        
        # If title is a translation key and we have language_manager, translate it
        if self.language_manager:
            try:
                title = self.language_manager.get_text(title)
            except:
                pass  # Keep original string if translation fails
        
        self.title_label = ctk.CTkLabel(
            title_frame,
            text=title,
            font=title_font,
            anchor="w"
        )
        self.title_label.pack(side="left")
        
        # Value with fallback font
        value_font = (
            font_manager.get_font("bold", 11) if font_manager 
            else ctk.CTkFont(family="Ubuntu", size=11, weight="bold")
        )
        
        # If unit is a translation key and we have language_manager, translate it
        if self.language_manager:
            try:
                unit = self.language_manager.get_text(unit)
            except:
                pass  # Keep original string if translation fails
        
        self.value_label = ctk.CTkLabel(
            header,
            text=f"{value}{unit}",
            font=value_font,
            anchor="e"
        )
        self.value_label.pack(side="right")
        
        # Store original title and unit for language updates
        self.original_title = title
        self.original_unit = unit
        
        # Slider
        if show_button:
            self.slider = ctk.CTkSlider(
                self,
                from_=min_val,
                to=max_val,
                number_of_steps=int(max_val-min_val),
                progress_color="#ff4400",
                button_color="#ff4400",
                button_hover_color="#ff5500",
                command=self._on_slider_change
            )
            self.slider.bind("<Button-1>", self._on_click)
            self.slider.bind("<B1-Motion>", self._on_drag)
            self.slider.bind("<ButtonRelease-1>", self._on_release)
        else:
            self.slider = ctk.CTkProgressBar(
                self,
                progress_color="#ff4400",
                fg_color="#f0f0f0",
                height=6,
                corner_radius=2
            )
        
        self.slider.pack(fill="x")
        self.set(value)
    
    def _on_click(self, event):
        # Store initial click position
        self._drag_start = event.x
        self._initial_value = self.current_val
    
    def _on_drag(self, event):
        if hasattr(self, '_drag_start'):
            # Calculate value change based on drag distance
            width = self.slider.winfo_width()
            delta = (event.x - self._drag_start) / width * (self.max_val - self.min_val)
            new_val = max(self.min_val, min(self.max_val, self._initial_value + delta))
            self.set(new_val)
            if self.callback:
                self.callback(new_val)
    
    def _on_release(self, event):
        if hasattr(self, '_drag_start'):
            del self._drag_start
            del self._initial_value
    
    def _on_slider_change(self, normalized_value):
        """Convert normalized slider value (0-1) back to actual value"""
        if self.show_button:
            # Convert normalized value back to actual value
            actual_value = self.min_val + (normalized_value * (self.max_val - self.min_val))
            self.current_val = actual_value
            self.update_value(actual_value)
            if self.callback:
                self.callback(actual_value)
    
    def update_value(self, value):
        """Update the displayed value"""
        self.value_label.configure(text=f"{int(value)}{self.unit}")
        self.current_val = value
    
    def set(self, value):
        """Set slider value and position"""
        try:
            if not self.winfo_exists():
                return
                
            self.current_val = value
            if self.show_button:
                # Calculate normalized value (0 to 1) for slider position
                normalized = (value - self.min_val) / (self.max_val - self.min_val)
                self.slider.set(normalized)
            else:
                self.slider.set(value / 100)
            
            if hasattr(self, 'value_label') and self.value_label.winfo_exists():
                self.value_label.configure(text=f"{int(value)}{self.unit}")
                
        except Exception as e:
            print(f"Error setting slider value: {e}")
    
    def configure(self, **kwargs):
        """Configure slider parameters"""
        if "command" in kwargs:
            self.callback = kwargs.pop("command")
        if "max_val" in kwargs:
            self.max_val = kwargs.pop("max_val")
            if self.show_button:
                self.slider.configure(to=self.max_val)
        super().configure(**kwargs)
    
    def update_text(self):
        """Update slider text when language changes"""
        if self.language_manager:
            try:
                # Update title
                new_title = self.language_manager.get_text(self.original_title)
                self.title_label.configure(text=new_title)
                
                # Update value label with translated unit
                new_unit = self.language_manager.get_text(self.original_unit)
                self.value_label.configure(text=f"{int(self.current_val)}{new_unit}")
            except:
                pass  # Keep current text if translation fails

class PerformanceFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.app = master  # Store reference to main app
        self.language_manager = self.app.language_manager
        self._wmi = wmi.WMI()
        
        # Initialize monitoring flag
        self.monitoring = False
        
        # Create and configure the frame
        self.configure(fg_color="transparent")
        
        # Create tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs with translated names
        self.system_tab = self.tabview.add(self.language_manager.get_text("system"))
        
        # Configure tab grids
        self.system_tab.grid_columnconfigure(0, weight=1)
        
        self.create_widgets()
        
        # Start monitoring thread
        self.start_monitoring()
    
    def create_widgets(self):
        # System Tab - Combined CPU, GPU, RAM, Storage
        system_frame = CollapsibleFrame(
            master=self.system_tab, 
            title=self.language_manager.get_text("system_info"),
            subtitle=self.language_manager.get_text("system_info_subtitle"),
            fg_color="white",
            corner_radius=8
        )
        system_frame.pack(fill="x", pady=5, padx=5)
        
        # CPU Usage
        self.cpu_usage = CustomSlider(
            master=system_frame.content,
            title=self.language_manager.get_text("cpu_usage"),
            value=0,
            unit="%",
            min_val=0,
            max_val=100,
            show_button=False
        )
        self.cpu_usage.pack(fill="x", pady=5)
        
        # GPU Usage for each GPU
        self.gpu_frames = []
        for gpu_name in self.app.system_info.gpu_names:
            gpu_usage = CustomSlider(
                master=system_frame.content,
                title=f"{gpu_name} {self.language_manager.get_text('gpu_usage')}",
                value=0,
                unit="%",
                min_val=0,
                max_val=100,
                show_button=False
            )
            gpu_usage.pack(fill="x", pady=5)
            self.gpu_frames.append({
                'name': gpu_name,
                'usage': gpu_usage
            })
        
        # RAM Usage
        self.ram_usage = CustomSlider(
            master=system_frame.content,
            title=self.language_manager.get_text("memory_usage"),
            value=0,
            unit="%",
            min_val=0,
            max_val=100,
            show_button=False
        )
        self.ram_usage.pack(fill="x", pady=5)
        
        # Storage Usage
        self.ssd_usage = CustomSlider(
            master=system_frame.content,
            title=self.language_manager.get_text("storage_usage"),
            value=0,
            unit="%",
            min_val=0,
            max_val=100,
            show_button=False
        )
        self.ssd_usage.pack(fill="x", pady=5)
    
    def start_monitoring(self):
        self.monitoring = True
        Thread(target=self.update_stats, daemon=True).start()
    
    def stop_monitoring(self):
        self.monitoring = False
    
    def update_stats(self):
        # Initialize COM for this thread
        pythoncom.CoInitialize()
        
        # Initialize performance counters
        try:
            import win32pdh
            self.gpu_counters = {}
            for gpu_info in self.gpu_frames:
                gpu_name = gpu_info['name']
                try:
                    # Create query for GPU usage based on vendor
                    counter_paths = []
                    if 'NVIDIA' in gpu_name.upper():
                        counter_paths.append(r"\GPU Engine(*engtype_3D)\Utilization Percentage")
                    elif 'AMD' in gpu_name.upper():
                        counter_paths.append(r"\GPU Engine(*)\Utilization Percentage")
                    else:
                        counter_paths.append(r"\GPU Engine(*)\Utilization Percentage")
                    
                    # Initialize counters for this GPU
                    counters = []
                    for path in counter_paths:
                        try:
                            hq = win32pdh.OpenQuery()
                            hc = win32pdh.AddCounter(hq, path)
                            counters.append((hq, hc))
                            # First collection to establish baseline
                            win32pdh.CollectQueryData(hq)
                        except:
                            continue
                    
                    if counters:
                        self.gpu_counters[gpu_name] = counters
                except Exception as e:
                    print(f"Error initializing GPU counters for {gpu_name}: {e}")
        except Exception as e:
            print(f"Error initializing performance counters: {e}")
            self.gpu_counters = {}
        
        update_interval = 0.25  # Update every 250ms for smoother monitoring
        last_storage_update = 0
        storage_update_interval = 5  # Update storage every 5 seconds
        
        while self.monitoring:
            try:
                current_time = time.time()
                
                # CPU stats - Non-blocking for faster updates
                try:
                    if hasattr(self, 'cpu_usage') and self.cpu_usage.winfo_exists():
                        cpu_percent = psutil.cpu_percent(interval=None)
                        self.cpu_usage.set(cpu_percent)
                except Exception as e:
                    print(f"Error updating CPU stats: {e}")
                
                # GPU stats - Optimized for faster updates
                try:
                    for gpu_info in self.gpu_frames:
                        gpu_name = gpu_info['name']
                        try:
                            if gpu_name in self.gpu_counters:
                                total_usage = 0
                                samples = 0
                                
                                for hq, hc in self.gpu_counters[gpu_name]:
                                    try:
                                        win32pdh.CollectQueryData(hq)
                                        usage = win32pdh.GetFormattedCounterValue(hc, win32pdh.PDH_FMT_LONG)[1]
                                        
                                        if usage > 0:
                                            total_usage += usage
                                            samples += 1
                                    except:
                                        continue
                                
                                if samples > 0:
                                    gpu_info['usage'].set(min(100, total_usage / samples))
                            else:
                                # Fast process-based estimation
                                total_usage = 0
                                gpu_processes = {
                                    'NVIDIA': ['nvwgf2umx.exe', 'nvidia-smi.exe'],
                                    'AMD': ['amdow.exe', 'amddvr.exe', 'amdow64.exe'],
                                    'INTEL': ['igfxext.exe', 'igfxsrvc.exe']
                                }
                                
                                vendor = next((v for v in gpu_processes.keys() if v in gpu_name.upper()), None)
                                default_processes = ['dwm.exe', 'explorer.exe']
                                processes_to_monitor = gpu_processes.get(vendor or '', []) + default_processes
                                
                                for proc in psutil.process_iter(['name', 'cpu_percent']):
                                    try:
                                        if proc.info['name'].lower() in [p.lower() for p in processes_to_monitor]:
                                            total_usage += proc.info['cpu_percent'] / psutil.cpu_count()
                                    except:
                                        pass
                                
                                gpu_info['usage'].set(min(100, total_usage))
                                
                        except Exception as e:
                            print(f"Error getting GPU stats for {gpu_name}: {e}")
                except Exception as e:
                    print(f"Error updating GPU stats: {e}")
                
                # RAM stats - Fast update
                try:
                    if hasattr(self, 'ram_usage') and self.ram_usage.winfo_exists():
                        ram = psutil.virtual_memory()
                        self.ram_usage.set(ram.percent)
                except Exception as e:
                    print(f"Error updating RAM stats: {e}")
                
                # Storage stats - Less frequent updates
                if current_time - last_storage_update >= storage_update_interval:
                    try:
                        total_usage = 0
                        drive_count = 0
                        
                        for partition in psutil.disk_partitions():
                            if 'fixed' in partition.opts:
                                try:
                                    usage = psutil.disk_usage(partition.mountpoint)
                                    total_usage += usage.percent
                                    drive_count += 1
                                except:
                                    pass
                        
                        if drive_count > 0 and hasattr(self, 'ssd_usage') and self.ssd_usage.winfo_exists():
                            self.ssd_usage.set(total_usage / drive_count)
                            
                        last_storage_update = current_time
                            
                    except Exception as e:
                        print(f"Error updating storage stats: {e}")
                
            except Exception as e:
                print(f"Error updating stats: {e}")
            
            time.sleep(update_interval)
        
        # Cleanup
        try:
            for counters in self.gpu_counters.values():
                for hq, _ in counters:
                    try:
                        win32pdh.CloseQuery(hq)
                    except:
                        pass
        except:
            pass
        
        pythoncom.CoUninitialize()

class FrameworkApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Set application icon
        try:
            icon_path = Path("assets") / "logo.ico"
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
            else:
                print("Warning: logo.ico not found in assets folder")
        except Exception as e:
            print(f"Error setting application icon: {e}")
        
        # Initialize font manager
        self.font_manager = FontManager()
        
        # Initialize system info and settings
        self.settings = Settings()
        self.system_info = SystemInfo(self.settings)
        self.language_manager = LanguageManager(self.settings)
        self.ryzenadj = RyzenADJ(self.settings)
        
        # Initialize performance monitoring
        self.perf_frame = None
        
        # Initialize mode buttons dictionary
        self.mode_buttons = {}
        
        # Window setup
        self.title("Framework Hub PY Edition")
        self.geometry("1200x800")
        self.minsize(800, 600)  # Set minimum window size
        
        # Set theme from settings
        theme = self.settings.get_setting("theme", "light")
        if theme == "dark":
            ctk.set_appearance_mode("dark")
            self.configure(fg_color="#1a1a1a")
        else:
            ctk.set_appearance_mode("light")
            self.configure(fg_color="white")
        
        # Configure grid weights for proper scaling
        self.grid_columnconfigure(1, weight=1)  # Main content area expands
        self.grid_rowconfigure(0, weight=1)
        
        # Create main sections
        self.create_sidebar()
        self.show_home()
        
        # Add resize grip
        self.resize_grip = ctk.CTkButton(
            self,
            text="⟊",  # Fixed resize grip character
            width=20,
            height=20,
            fg_color="transparent",
            text_color="gray",
            hover_color="#f0f0f0",
            corner_radius=0
        )
        self.resize_grip.grid(row=1, column=1, sticky="se", padx=2, pady=2)
        self.resize_grip.bind("<B1-Motion>", self.on_resize_drag)
    
    def on_resize_drag(self, event):
        # Get minimum window size
        min_width = 800
        min_height = 600
        
        # Calculate new window size based on mouse position
        new_width = max(event.x_root - self.winfo_x(), min_width)
        new_height = max(event.y_root - self.winfo_y(), min_height)
        
        # Update window size
        self.geometry(f"{new_width}x{new_height}")
    
    def create_sidebar(self):
        # Create sidebar container that scales with window height
        sidebar_container = ctk.CTkFrame(self, fg_color="#fafafa", corner_radius=0, width=120)
        sidebar_container.grid(row=0, column=0, rowspan=2, sticky="nsew")
        sidebar_container.grid_rowconfigure(1, weight=1)
        sidebar_container.grid_propagate(False)
        
        # Create button frame
        button_frame = ctk.CTkFrame(sidebar_container, fg_color="transparent")
        button_frame.grid(row=0, column=0, sticky="new", padx=5, pady=5)
        
        # Load icons from assets directory
        try:
            assets_dir = Path("assets")
            home_icon = ctk.CTkImage(Image.open(assets_dir / "home.png"), size=(24, 24))
            tasks_icon = ctk.CTkImage(Image.open(assets_dir / "tasks.png"), size=(24, 24))
            keyboard_icon = ctk.CTkImage(Image.open(assets_dir / "keyboard.png"), size=(24, 24))
            settings_icon = ctk.CTkImage(Image.open(assets_dir / "setting.png"), size=(24, 24))
            print("Icons loaded successfully from assets directory")
        except Exception as e:
            print(f"Error loading icons from assets directory: {e}")
            home_icon = tasks_icon = keyboard_icon = settings_icon = None
        
        # Sidebar buttons with icons
        self.sidebar_buttons = {}
        buttons = [
            ("home", home_icon or "🏠", self.show_home),
            ("performance", tasks_icon or "📊", self.show_performance),
            ("keyboard", keyboard_icon or "⌨️", self.show_keyboard),
            ("settings", settings_icon or "⚙️", self.show_settings)
        ]
        
        for i, (key, icon, command) in enumerate(buttons):
            btn = ctk.CTkButton(
                button_frame,
                text=self.language_manager.get_text(key),
                font=self.font_manager.get_font("medium", 11),
                fg_color="transparent",
                text_color="gray",
                hover_color="#f0f0f0",
                anchor="center",
                height=70,
                width=110,
                image=icon if isinstance(icon, ctk.CTkImage) else None,
                compound="top",
                command=lambda k=key, c=command: self.on_sidebar_button_click(k, c)
            )
            btn.pack(pady=2, fill="x")
            self.sidebar_buttons[key] = btn
        
        # Set initial active button
        self.set_active_button("home")
    
    def on_sidebar_button_click(self, key, command):
        """Handle sidebar button clicks"""
        self.set_active_button(key)
        command()
    
    def set_active_button(self, active_key):
        """Set the active state of sidebar buttons"""
        for key, btn in self.sidebar_buttons.items():
            if key == active_key:
                btn.configure(
                    fg_color="#ff4400",
                    text_color="white",
                    hover_color="#ff5500"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color="gray",
                    hover_color="#f0f0f0"
                )
    
    def show_home(self):
        self.set_active_button("home")
        # Clear main content
        for widget in self.grid_slaves():
            if widget != self.grid_slaves(row=0, column=0)[0]:  # Keep sidebar
                widget.destroy()
        
        if self.perf_frame:
            self.perf_frame.stop_monitoring()
        
        self.create_main_content()
    
    def show_performance(self):
        self.set_active_button("performance")
        # Clear main content and controls
        for widget in self.grid_slaves():
            if widget != self.grid_slaves(row=0, column=0)[0]:  # Keep sidebar
                widget.destroy()
        
        self.perf_frame = PerformanceFrame(self)
        self.perf_frame.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        self.perf_frame.start_monitoring()
    
    def show_keyboard(self):
        self.set_active_button("keyboard")
        webbrowser.open("https://keyboard.frame.work/")
    
    def show_settings(self):
        """Show the settings page with language options"""
        try:
            self.set_active_button("settings")
            
            # Clear main content and controls
            for widget in self.grid_slaves():
                if widget != self.grid_slaves(row=0, column=0)[0]:  # Keep sidebar
                    widget.destroy()
            
            if self.perf_frame:
                self.perf_frame.stop_monitoring()
                self.perf_frame = None
            
            # Create main settings frame
            settings_frame = ctk.CTkFrame(master=self)
            settings_frame.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
            
            # Language settings section
            lang_frame = CollapsibleFrame(
                master=settings_frame,
                title=self.language_manager.get_text("language_settings"),
                subtitle=self.language_manager.get_text("choose_language"),
                fg_color="white",
                corner_radius=8
            )
            lang_frame.pack(fill="x", pady=5)
            
            # Create language buttons container
            buttons_frame = ctk.CTkFrame(master=lang_frame.content, fg_color="transparent")
            buttons_frame.pack(fill="x", pady=5)
            
            # Create language buttons
            for lang_code in self.language_manager.get_available_languages():
                try:
                    is_current = lang_code == self.language_manager.current_language
                    
                    btn = ctk.CTkButton(
                        master=buttons_frame,
                        text=self.language_manager.get_language_name(lang_code),
                        font=self.font_manager.get_font("bold" if is_current else "regular", 11),
                        fg_color="#ff4400" if is_current else "transparent",
                        text_color="white" if is_current else "black",
                        hover_color="#ff5500",
                        command=lambda l=lang_code: self.change_language(l)
                    )
                    btn.pack(pady=2, padx=10, fill="x")
                except Exception as e:
                    print(f"Error creating language button for {lang_code}: {e}")
            
            # Theme settings section
            theme_frame = CollapsibleFrame(
                master=settings_frame,
                title=self.language_manager.get_text("theme_settings"),
                subtitle="",
                fg_color="white",
                corner_radius=8
            )
            theme_frame.pack(fill="x", pady=5)
            
            # Create theme buttons container
            theme_buttons_frame = ctk.CTkFrame(master=theme_frame.content, fg_color="transparent")
            theme_buttons_frame.pack(fill="x", pady=5)
            
            # Create theme buttons
            theme_options = {
                "light": self.language_manager.get_text("theme_light"),
                "dark": self.language_manager.get_text("theme_dark")
            }
            
            current_theme = self.settings.get_setting("theme", "light")
            
            for theme_code, theme_name in theme_options.items():
                try:
                    is_current = theme_code == current_theme
                    
                    btn = ctk.CTkButton(
                        master=theme_buttons_frame,
                        text=theme_name,
                        font=self.font_manager.get_font("bold" if is_current else "regular", 11),
                        fg_color="#ff4400" if is_current else "transparent",
                        text_color="white" if is_current else "black",
                        hover_color="#ff5500",
                        command=lambda t=theme_code: self.change_theme(t)
                    )
                    btn.pack(pady=2, padx=10, fill="x")
                except Exception as e:
                    print(f"Error creating theme button for {theme_code}: {e}")
            
        except Exception as e:
            print(f"Error showing settings: {e}")
            import traceback
            traceback.print_exc()
    
    def change_language(self, lang_code):
        """Change the application language and update all UI elements"""
        print(f"Changing language to: {lang_code}")  # Debug log
        
        if self.language_manager.set_language(lang_code):
            print("Language changed successfully")  # Debug log
            
            try:
                # Update window title
                self.title(self.language_manager.get_text("title"))
                
                # Safely update sidebar buttons
                for key, btn in list(self.sidebar_buttons.items()):
                    try:
                        if btn.winfo_exists():
                            btn.configure(text=self.language_manager.get_text(key))
                    except Exception as e:
                        print(f"Error updating sidebar button {key}: {e}")
                
                # Safely update mode buttons
                for mode, btn in list(self.mode_buttons.items()):
                    try:
                        if btn.winfo_exists():
                            btn.configure(text=self.language_manager.get_text(mode))
                    except Exception as e:
                        print(f"Error updating mode button {mode}: {e}")
                
                # Get current page before refreshing
                try:
                    current_page = next(
                        (key for key, btn in self.sidebar_buttons.items() 
                         if btn.winfo_exists() and btn.cget("fg_color") == "#ff4400"),
                        "home"
                    )
                except Exception as e:
                    print(f"Error getting current page: {e}")
                    current_page = "home"
                
                print(f"Refreshing current page: {current_page}")  # Debug log
                
                # Refresh the current page
                if current_page == "home":
                    self.show_home()
                elif current_page == "performance":
                    self.show_performance()
                elif current_page == "settings":
                    self.show_settings()
                
                print("UI refresh complete")  # Debug log
                
            except Exception as e:
                print(f"Error updating UI: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"Failed to change language to: {lang_code}")  # Debug log
    
    def switch_profile(self, profile):
        """Switch to the specified power profile"""
        try:
            # Convert profile names to match the RyzenADJ profiles
            profile_mapping = {
                self.language_manager.get_text("silent"): "Silent",
                self.language_manager.get_text("balanced"): "Balanced",
                self.language_manager.get_text("performance_profile"): "Performance"
            }
            
            ryzenadj_profile = profile_mapping.get(profile)
            if not ryzenadj_profile:
                print(f"Error: Unknown profile {profile}")
                return
            
            print(f"Switching to profile: {ryzenadj_profile}")  # Debug log
            
            # Update button colors - Orange for active profile
            for mode, btn in list(self.mode_buttons.items()):
                try:
                    if btn.winfo_exists():
                        is_active = self.language_manager.get_text(mode) == profile
                        btn.configure(
                            fg_color="#ff8800" if is_active else "transparent",
                            text_color="white" if is_active else "black",
                            hover_color="#ff9900" if is_active else "#f0f0f0",
                            border_color="#ff8800" if is_active else "#e0e0e0",
                            font=self.font_manager.get_font("bold" if is_active else "regular", 11)
                        )
                except Exception as e:
                    print(f"Error updating button for mode {mode}: {e}")
            
            # Apply profile using the mapped name
            if self.ryzenadj.apply_profile(ryzenadj_profile):
                # Save the current profile to settings only if successfully applied
                self.settings.set_setting("ryzenadj_profile", ryzenadj_profile)
                print(f"Successfully applied and saved profile: {ryzenadj_profile}")
            else:
                print(f"Failed to apply profile: {ryzenadj_profile}")
            
            # Refresh the main content to update profile explanations
            self.show_home()
            
        except Exception as e:
            print(f"Error switching profile: {e}")
            import traceback
            traceback.print_exc()
    
    def create_main_content(self):
        # Create scrollable main content area
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(1, weight=1)
        
        # Header section (fixed)
        header = ctk.CTkFrame(main_container, fg_color="transparent")
        header.grid(row=0, column=0, sticky="new")
        header.grid_columnconfigure(0, weight=1)
        
        # Title with Ubuntu font
        title_label = ctk.CTkLabel(
            header,
            text="Framework Hub",
            font=self.font_manager.get_font("bold", 24),
            anchor="w"
        )
        title_label.pack(fill="x")
        
        specs = ctk.CTkLabel(
            header,
            text=f"- {self.system_info.cpu_name}\n"
                 f"- {', '.join(self.system_info.gpu_names)}\n"
                 f"- {self.system_info.total_ram}GB RAM",
            font=self.font_manager.get_font("light", 11),
            text_color="gray",
            anchor="w",
            justify="left"
        )
        specs.pack(fill="x", pady=(5,20))
        
        # Create main content area with two columns
        content = ctk.CTkFrame(main_container, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(1, weight=1)  # Make right column expandable
        
        # Left column for image and buttons
        left_column = ctk.CTkFrame(content, fg_color="transparent")
        left_column.grid(row=0, column=0, sticky="n", padx=(0, 20))
        
        # Main image in left column
        try:
            # Create assets directory if it doesn't exist
            assets_dir = Path("assets")
            assets_dir.mkdir(exist_ok=True)
            
            # Load main image
            main_image_path = assets_dir / "main.png"
            if main_image_path.exists():
                image = Image.open(main_image_path)
                window_width = 500  # Reduced width for better layout
                aspect_ratio = image.height / image.width
                new_width = window_width
                new_height = int(new_width * aspect_ratio)
                
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                ctk_image = ctk.CTkImage(
                    light_image=image,
                    dark_image=image,
                    size=(new_width, new_height)
                )
                
                image_label = ctk.CTkLabel(
                    left_column,
                    image=ctk_image,
                    text=""
                )
                image_label.pack(pady=20)
            else:
                # Create placeholder if image doesn't exist
                placeholder = ctk.CTkFrame(left_column, fg_color="#f5f5f5", height=300)
                placeholder.pack(pady=20)
                
                error_label = ctk.CTkLabel(
                    placeholder,
                    text="Framework Laptop Hub",
                    font=("Segoe UI", 24, "bold"),
                    text_color="gray"
                )
                error_label.place(relx=0.5, rely=0.5, anchor="center")
            
        except Exception as e:
            print(f"Error handling image: {e}")
            placeholder = ctk.CTkFrame(left_column, fg_color="#f5f5f5", height=300)
            placeholder.pack(pady=20)
            
            error_label = ctk.CTkLabel(
                placeholder,
                text="Framework Laptop Hub",
                font=("Segoe UI", 24, "bold"),
                text_color="gray"
            )
            error_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Profile buttons in left column
        button_frame = ctk.CTkFrame(left_column, fg_color="transparent")
        button_frame.pack(pady=20)
        
        # Mode buttons
        self.mode_buttons.clear()  # Clear existing buttons
        for mode in ["silent", "balanced", "performance_profile"]:
            display_name = self.language_manager.get_text(mode)
            mapped_name = {
                self.language_manager.get_text("silent"): "Silent",
                self.language_manager.get_text("balanced"): "Balanced",
                self.language_manager.get_text("performance_profile"): "Performance"
            }.get(display_name)
            
            is_active = mapped_name == self.ryzenadj.current_profile
            
            btn = ctk.CTkButton(
                button_frame,
                text=display_name,
                font=self.font_manager.get_font("bold" if is_active else "regular", 11),
                fg_color="#ff4400" if is_active else "transparent",
                text_color="white" if is_active else "black",
                hover_color="#ff5500" if is_active else "#f0f0f0",
                border_color="#ff4400" if is_active else "#e0e0e0",
                border_width=1,
                width=120,
                command=lambda m=mode: self.switch_profile(self.language_manager.get_text(m))
            )
            btn.pack(side="left", padx=5)
            self.mode_buttons[mode] = btn
        
        # Right column for profile explanations
        right_column = ctk.CTkFrame(content, fg_color="transparent")
        right_column.grid(row=0, column=1, sticky="nsew")
        right_column.grid_columnconfigure(0, weight=1)
        
        # Profile explanations in right column
        explanations = {
            self.language_manager.get_text("silent"): {
                "description": self.language_manager.get_text("silent_description"),
                "values": {
                    self.language_manager.get_text("power_limit"): "30W",
                    self.language_manager.get_text("current_limit"): "80A"
                }
            },
            self.language_manager.get_text("balanced"): {
                "description": self.language_manager.get_text("balanced_description"),
                "values": {
                    self.language_manager.get_text("power_limit"): "45W",
                    self.language_manager.get_text("current_limit"): "100A"
                }
            },
            self.language_manager.get_text("performance_profile"): {
                "description": self.language_manager.get_text("performance_description"),
                "values": {
                    self.language_manager.get_text("power_limit"): "65W",
                    self.language_manager.get_text("current_limit"): "120A"
                }
            }
        }
        
        for profile, info in explanations.items():
            frame = CollapsibleFrame(
                master=right_column,
                title=profile,
                subtitle=info["description"],
                fg_color="white",
                corner_radius=8
            )
            frame.pack(fill="x", pady=5)
            
            for setting, value in info["values"].items():
                value_frame = ctk.CTkFrame(frame.content, fg_color="transparent")
                value_frame.pack(fill="x", pady=2)
                
                # Default fonts
                label_font = ctk.CTkFont(family="Ubuntu", size=11)
                value_font = ctk.CTkFont(family="Ubuntu", size=11, weight="bold")
                
                # Try to get fonts from master if available
                try:
                    if hasattr(self, "font_manager"):
                        label_font = self.font_manager.get_font("regular", 11)
                        value_font = self.font_manager.get_font("bold", 11)
                except Exception as e:
                    print(f"Warning: Could not access font_manager: {e}")
                
                ctk.CTkLabel(
                    master=value_frame,
                    text=setting,
                    font=label_font,
                    anchor="w"
                ).pack(side="left")
                
                ctk.CTkLabel(
                    master=value_frame,
                    text=value,
                    font=value_font,
                    text_color="#ff4400",
                    anchor="e"
                ).pack(side="right")

    def set_theme(self, theme):
        """Set the application theme"""
        if theme == "dark":
            ctk.set_appearance_mode("dark")
            self.configure(fg_color="#1a1a1a")
            for widget in self.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    widget.configure(fg_color="#1a1a1a")
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkFrame):
                            child.configure(fg_color="#1a1a1a")
        else:
            ctk.set_appearance_mode("light")
            self.configure(fg_color="white")
            for widget in self.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    widget.configure(fg_color="white")
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkFrame):
                            child.configure(fg_color="white")
        
        self.settings.set_setting("theme", theme)
        
        # Update UI elements
        self.show_home()  # Refresh the current page to apply theme changes

if __name__ == "__main__":
    try:
        # Enable debug logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('app.log'),
                logging.StreamHandler()
            ]
        )
        logger = logging.getLogger(__name__)
        logger.debug("Starting application...")
        
        # Check if running with admin rights
        if not ctypes.windll.shell32.IsUserAnAdmin():
            logger.info("Restarting with admin rights...")
            # Re-run the program with admin rights
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable, 
                f'"{__file__}"',
                None, 
                1
            )
        else:
            # We have admin rights, start the app
            logger.info("Starting app with admin rights...")
            try:
                app = FrameworkApp()
                logger.info("App instance created successfully")
                app.mainloop()
            except Exception as e:
                logger.error(f"Error in main app: {str(e)}", exc_info=True)
                import traceback
                traceback.print_exc()
                # Show error message to user
                import tkinter.messagebox as messagebox
                messagebox.showerror(
                    "Error",
                    f"An error occurred while starting the application:\n{str(e)}\n\nCheck app.log for details."
                )
                
    except Exception as e:
        print(f"Critical error: {str(e)}")
        import traceback
        traceback.print_exc()
        # Show error message to user
        import tkinter.messagebox as messagebox
        messagebox.showerror(
            "Critical Error",
            f"A critical error occurred:\n{str(e)}\n\nCheck app.log for details."
        )