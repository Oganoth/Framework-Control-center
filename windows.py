import tkinter as tk

class BatteryWindow:
    def __init__(self):
        self.window = tk.Toplevel()
        self.window.wm_attributes('-topmost', 1)
        self.window.focus_force()
        self.window.wm_attributes('-toolwindow', True)
        self.window.wm_attributes('-disabled', False)
        # reste du code...

class SettingsWindow:
    def __init__(self):
        self.window = tk.Toplevel()
        self.window.wm_attributes('-topmost', 1)
        self.window.focus_force()
        self.window.wm_attributes('-toolwindow', True)
        self.window.wm_attributes('-disabled', False)
        # reste du code...