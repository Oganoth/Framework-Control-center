import json
from pathlib import Path
import customtkinter as ctk
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from .adlx_wrapper import (
    ADLXWrapper,
    ADLXError,
    ADLXValidationError,
    QualityMode,
    TuningMode,
    DisplaySettings,
    ThreeDSettings,
    AutoTuningSettings,
    ProfileSettings
)

logger = logging.getLogger(__name__)

class AMDSettingsWindow:
    """AMD Settings configuration window."""
    
    def __init__(self, parent):
        """Initialize AMD Settings window."""
        self.parent = parent
        logger.info("Initializing AMD Settings window")
        
        # Create window first
        self.window = ctk.CTkToplevel(parent)
        self.window.title("AMD Settings")
        self.window.geometry("800x600")
        self.window.resizable(False, False)
        logger.debug("Created top level window")
        
        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()
        
        # Configure window style
        self.window.configure(fg_color=parent.colors.background.main)
        
        try:
            import sys
            if sys.platform.startswith('win'):
                self.window.after(200, lambda: self.window.iconbitmap(str(Path("assets/logo.ico").absolute())))
            else:
                self.window.iconbitmap(str(Path("assets/logo.ico")))
        except Exception as e:
            logger.error(f"Failed to set window icon: {e}")
        
        # Create main container
        self.container = ctk.CTkFrame(
            self.window,
            fg_color=parent.colors.background.main
        )
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        logger.debug("Created main container")
        
        try:
            # Initialize ADLX wrapper
            logger.info("Initializing ADLX wrapper")
            self.adlx = ADLXWrapper()
            # Create profile tabs
            logger.info("Creating profile tabs")
            self._create_profile_tabs()
            logger.info("Profile tabs created successfully")
        except ADLXError as e:
            logger.error(f"ADLX initialization error: {e}")
            self._show_error_message(f"AMD Display Library initialization failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error initializing AMD Settings window: {e}")
            self._show_error_message(f"Failed to initialize AMD Settings: {str(e)}")
        
        # Center window on parent
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (height // 2)
        self.window.geometry(f"+{x}+{y}")
        
        # Bind window close event
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Wait for window to be ready before showing
        self.window.after(100, self._show_window)
        logger.info("AMD Settings window initialization complete")
        
    def _show_window(self):
        """Show the window after it's fully initialized."""
        try:
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
        except Exception as e:
            logger.error(f"Error showing AMD Settings window: {e}")
            
    def _on_close(self):
        """Handle window close event."""
        try:
            # Release modal state
            self.window.grab_release()
            # Clean up ADLX resources if initialized
            if hasattr(self, 'adlx'):
                self.adlx.cleanup()
            # Destroy window
            self.window.destroy()
        except Exception as e:
            logger.error(f"Error closing AMD Settings window: {e}")
            try:
                self.window.destroy()
            except Exception:
                pass
        
    def _create_profile_tabs(self):
        """Create tabs for each power profile."""
        # Create tabview
        self.tabview = ctk.CTkTabview(
            self.container,
            fg_color=self.parent.colors.background.secondary,
            segmented_button_fg_color=self.parent.colors.button.primary,
            segmented_button_selected_color=self.parent.colors.hover,
            segmented_button_selected_hover_color=self.parent.colors.hover,
            segmented_button_unselected_color=self.parent.colors.button.primary,
            segmented_button_unselected_hover_color=self.parent.colors.hover,
            text_color=self.parent.colors.text.primary
        )
        self.tabview.pack(fill="both", expand=True)
        
        # Add tabs for each profile
        for profile in ["Silent", "Balanced", "Boost"]:
            tab = self.tabview.add(profile)
            self._create_profile_settings(tab, profile)
            
        # Select current profile tab if any
        current_profile = self.adlx.get_current_profile()
        if current_profile:
            self.tabview.set(current_profile)
            
    def _create_profile_settings(self, tab: ctk.CTkFrame, profile: str):
        """Create settings controls for a profile tab."""
        # Create scrollable frame for settings
        settings_frame = ctk.CTkScrollableFrame(
            tab,
            fg_color="transparent",
            label_text=f"{profile} Profile Settings",
            label_text_color=self.parent.colors.text.primary
        )
        settings_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Get current profile settings
        profile_settings = self.adlx.get_profile_settings(profile)
        if not profile_settings:
            logger.warning(f"No settings found for profile {profile}, using defaults")
            profile_settings = ProfileSettings(
                display=DisplaySettings(
                    brightness=50,
                    contrast=50,
                    saturation=50,
                    refresh_rate=60
                ),
                three_d=ThreeDSettings(
                    anti_aliasing=QualityMode.OFF,
                    anisotropic_filtering=QualityMode.OFF,
                    image_sharpening=0,
                    radeon_boost=False,
                    radeon_chill=False,
                    frame_rate_target=60
                ),
                auto_tuning=AutoTuningSettings(
                    gpu_tuning=TuningMode.AUTO,
                    memory_tuning=TuningMode.AUTO,
                    fan_tuning=TuningMode.AUTO,
                    power_tuning=TuningMode.AUTO
                )
            )
        
        # Display Settings section
        self._create_section_label(settings_frame, "Display Settings")
        self._create_slider(settings_frame, profile, "display", "brightness", "Brightness", 0, 100,
                          profile_settings.display.brightness)
        self._create_slider(settings_frame, profile, "display", "contrast", "Contrast", 0, 100,
                          profile_settings.display.contrast)
        self._create_slider(settings_frame, profile, "display", "saturation", "Saturation", 0, 100,
                          profile_settings.display.saturation)
        self._create_option_menu(settings_frame, profile, "display", "refresh_rate", "Refresh Rate",
                               ["60", "120", "165"], str(profile_settings.display.refresh_rate))
        
        # Performance Settings section
        self._create_section_label(settings_frame, "Performance Settings")
        self._create_option_menu(settings_frame, profile, "auto_tuning", "gpu_tuning", "GPU Tuning",
                               [mode.name for mode in TuningMode],
                               profile_settings.auto_tuning.gpu_tuning.name)
        self._create_option_menu(settings_frame, profile, "auto_tuning", "memory_tuning", "Memory Tuning",
                               [mode.name for mode in TuningMode],
                               profile_settings.auto_tuning.memory_tuning.name)
        self._create_option_menu(settings_frame, profile, "auto_tuning", "fan_tuning", "Fan Tuning",
                               [mode.name for mode in TuningMode],
                               profile_settings.auto_tuning.fan_tuning.name)
        self._create_option_menu(settings_frame, profile, "auto_tuning", "power_tuning", "Power Tuning",
                               [mode.name for mode in TuningMode],
                               profile_settings.auto_tuning.power_tuning.name)
        
        # 3D Settings section
        self._create_section_label(settings_frame, "3D Settings")
        self._create_option_menu(settings_frame, profile, "3d", "anti_aliasing", "Anti-Aliasing",
                               [mode.name for mode in QualityMode],
                               profile_settings.three_d.anti_aliasing.name)
        self._create_option_menu(settings_frame, profile, "3d", "anisotropic_filtering", "Anisotropic Filtering",
                               [mode.name for mode in QualityMode],
                               profile_settings.three_d.anisotropic_filtering.name)
        self._create_slider(settings_frame, profile, "3d", "image_sharpening", "Image Sharpening", 0, 100,
                          profile_settings.three_d.image_sharpening)
        self._create_switch(settings_frame, profile, "3d", "radeon_boost", "Radeon Boost",
                          profile_settings.three_d.radeon_boost)
        self._create_switch(settings_frame, profile, "3d", "radeon_chill", "Radeon Chill",
                          profile_settings.three_d.radeon_chill)
        self._create_slider(settings_frame, profile, "3d", "frame_rate_target", "Frame Rate Target", 30, 165,
                          profile_settings.three_d.frame_rate_target)
        
        # Last applied time
        if profile_settings.last_applied:
            last_applied = profile_settings.last_applied.strftime("%Y-%m-%d %H:%M:%S")
            last_applied_label = ctk.CTkLabel(
                settings_frame,
                text=f"Last Applied: {last_applied}",
                text_color=self.parent.colors.text.secondary,
                font=("Roboto", 10)
            )
            last_applied_label.pack(pady=(10, 0))
        
        # Save and Apply buttons
        buttons_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        buttons_frame.pack(pady=20)
        
        save_btn = ctk.CTkButton(
            buttons_frame,
            text="Save Settings",
            command=lambda p=profile: self._save_profile_settings(p),
            fg_color=self.parent.colors.button.primary,
            hover_color=self.parent.colors.hover,
            text_color=self.parent.colors.text.primary,
            width=120
        )
        save_btn.pack(side="left", padx=5)
        
        apply_btn = ctk.CTkButton(
            buttons_frame,
            text="Apply Now",
            command=lambda p=profile: self._apply_profile_settings(p),
            fg_color=self.parent.colors.button.primary,
            hover_color=self.parent.colors.hover,
            text_color=self.parent.colors.text.primary,
            width=120
        )
        apply_btn.pack(side="left", padx=5)
        
    def _create_section_label(self, parent: ctk.CTkFrame, text: str):
        """Create a section label."""
        label = ctk.CTkLabel(
            parent,
            text=text,
            text_color=self.parent.colors.text.primary,
            font=("Roboto", 12, "bold")
        )
        label.pack(anchor="w", pady=(20, 10))
        
    def _create_slider(self, parent: ctk.CTkFrame, profile: str, section: str, setting: str,
                      label: str, min_val: int, max_val: int, initial_value: int = 0):
        """Create a slider control."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        
        label = ctk.CTkLabel(
            frame,
            text=label,
            text_color=self.parent.colors.text.primary
        )
        label.pack(side="left")
        
        value_label = ctk.CTkLabel(
            frame,
            text=str(initial_value),
            text_color=self.parent.colors.text.primary
        )
        value_label.pack(side="right")
        
        slider = ctk.CTkSlider(
            frame,
            from_=min_val,
            to=max_val,
            command=lambda val: self._update_slider_value(profile, section, setting, val, value_label),
            fg_color=self.parent.colors.background.secondary,
            progress_color=self.parent.colors.button.primary,
            button_color=self.parent.colors.button.primary,
            button_hover_color=self.parent.colors.hover
        )
        slider.pack(fill="x", padx=10)
        slider.set(initial_value)
        
    def _create_option_menu(self, parent: ctk.CTkFrame, profile: str, section: str, setting: str,
                          label: str, values: list, initial_value: str = None):
        """Create an option menu control."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        
        label = ctk.CTkLabel(
            frame,
            text=label,
            text_color=self.parent.colors.text.primary
        )
        label.pack(side="left")
        
        menu = ctk.CTkOptionMenu(
            frame,
            values=values,
            command=lambda val: self._update_option_value(profile, section, setting, val),
            fg_color=self.parent.colors.button.primary,
            button_color=self.parent.colors.button.primary,
            button_hover_color=self.parent.colors.hover,
            text_color=self.parent.colors.text.primary
        )
        menu.pack(side="right")
        if initial_value:
            menu.set(initial_value)
        
    def _create_switch(self, parent: ctk.CTkFrame, profile: str, section: str, setting: str,
                      label: str, initial_value: bool = False):
        """Create a switch control."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        
        label = ctk.CTkLabel(
            frame,
            text=label,
            text_color=self.parent.colors.text.primary
        )
        label.pack(side="left")
        
        switch = ctk.CTkSwitch(
            frame,
            text="",
            command=lambda: self._update_switch_value(profile, section, setting, switch.get()),
            fg_color=self.parent.colors.background.secondary,
            progress_color=self.parent.colors.button.primary,
            button_color=self.parent.colors.button.primary,
            button_hover_color=self.parent.colors.hover
        )
        switch.pack(side="right")
        if initial_value:
            switch.select()
        else:
            switch.deselect()
        
    def _update_slider_value(self, profile: str, section: str, setting: str, value: float,
                           label: ctk.CTkLabel):
        """Update slider value."""
        try:
            # Update label
            label.configure(text=str(int(value)))
            
            # Get current profile settings
            settings = self.adlx.get_profile_settings(profile)
            if not settings:
                return
            
            # Update the specific setting
            if section == "display":
                settings.display.__dict__[setting] = int(value)
            elif section == "3d":
                settings.three_d.__dict__[setting] = int(value)
            
        except Exception as e:
            logger.error(f"Error updating slider value: {e}")
        
    def _update_option_value(self, profile: str, section: str, setting: str, value: str):
        """Update option menu value."""
        try:
            # Get current profile settings
            settings = self.adlx.get_profile_settings(profile)
            if not settings:
                return
            
            # Convert string value to enum if needed
            if section == "auto_tuning":
                value = TuningMode[value]
            elif section == "3d" and setting in ["anti_aliasing", "anisotropic_filtering"]:
                value = QualityMode[value]
            
            # Update the specific setting
            if section == "display":
                settings.display.__dict__[setting] = value
            elif section == "3d":
                settings.three_d.__dict__[setting] = value
            elif section == "auto_tuning":
                settings.auto_tuning.__dict__[setting] = value
            
        except Exception as e:
            logger.error(f"Error updating option value: {e}")
        
    def _update_switch_value(self, profile: str, section: str, setting: str, value: bool):
        """Update switch value."""
        try:
            # Get current profile settings
            settings = self.adlx.get_profile_settings(profile)
            if not settings:
                return
            
            # Update the specific setting
            if section == "3d":
                settings.three_d.__dict__[setting] = value
            
        except Exception as e:
            logger.error(f"Error updating switch value: {e}")
        
    def _save_profile_settings(self, profile: str):
        """Save settings for a profile."""
        try:
            # Get current profile settings
            settings = self.adlx.get_profile_settings(profile)
            if not settings:
                return
            
            # Update profile settings
            success = self.adlx.update_profile_settings(profile, {
                "display": settings.display.__dict__,
                "3d": settings.three_d.__dict__,
                "auto_tuning": settings.auto_tuning.__dict__
            })
            
            if success:
                logger.info(f"Saved settings for {profile} profile")
            else:
                logger.error(f"Failed to save settings for {profile} profile")
            
        except Exception as e:
            logger.error(f"Error saving profile settings: {e}")
            
    def _apply_profile_settings(self, profile: str):
        """Apply settings for a profile."""
        try:
            # Switch to the profile
            success = self.adlx.switch_profile(profile)
            
            if success:
                logger.info(f"Applied settings for {profile} profile")
                # Refresh the window to update last applied time
                self._create_profile_tabs()
            else:
                logger.error(f"Failed to apply settings for {profile} profile")
            
        except Exception as e:
            logger.error(f"Error applying profile settings: {e}")
        
    def _show_error_message(self, message: str):
        """Show error message in the window."""
        logger.info(f"Showing error message: {message}")
        
        # Clear container
        for widget in self.container.winfo_children():
            widget.destroy()
            
        # Create error message
        error_frame = ctk.CTkFrame(
            self.container,
            fg_color=self.parent.colors.background.secondary
        )
        error_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Error icon or symbol
        error_symbol = ctk.CTkLabel(
            error_frame,
            text="⚠",  # Unicode warning symbol
            font=("Segoe UI", 48),
            text_color="#FF6B6B"  # Red color for error
        )
        error_symbol.pack(pady=(40, 20))
        
        # Error title
        error_title = ctk.CTkLabel(
            error_frame,
            text="AMD Settings Unavailable",
            font=("Segoe UI", 24, "bold"),
            text_color="#FF6B6B"  # Red color for error
        )
        error_title.pack(pady=(0, 20))
        
        # Error message
        error_message = ctk.CTkLabel(
            error_frame,
            text=message,
            font=("Segoe UI", 12),
            text_color=self.parent.colors.text.primary,
            wraplength=500  # Ensure text wraps properly
        )
        error_message.pack(pady=(0, 20))
        
        # Additional help text
        help_text = ctk.CTkLabel(
            error_frame,
            text="This error occurs when the AMD Display Library DLLs are not properly initialized.\n\n"
                 "Possible solutions:\n"
                 "1. Verify that AMD drivers are installed correctly\n"
                 "2. Try reinstalling the AMD drivers\n"
                 "3. Check if your GPU supports the AMD Display Library",
            font=("Segoe UI", 12),
            text_color=self.parent.colors.text.secondary,
            wraplength=500,
            justify="left"
        )
        help_text.pack(pady=(0, 40))
        
        # Close button
        close_btn = ctk.CTkButton(
            error_frame,
            text="Close",
            command=self._on_close,
            fg_color=self.parent.colors.button.primary,
            hover_color=self.parent.colors.hover,
            text_color=self.parent.colors.text.primary,
            width=120
        )
        close_btn.pack(pady=20)
        
        logger.info("Error message displayed successfully") 