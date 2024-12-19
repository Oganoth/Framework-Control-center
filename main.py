import tkinter as tk

# Création de la fenêtre principale
root = tk.Tk()
root.wm_attributes('-topmost', 1)
root.focus_force()  # Force le focus
root.wm_attributes('-toolwindow', True)
root.wm_attributes('-disabled', False)

# Le reste de votre code...