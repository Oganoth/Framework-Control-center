from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collecter tous les sous-modules de customtkinter
hiddenimports = collect_submodules('customtkinter')

# Ajouter les sous-modules PIL nécessaires
hiddenimports += [
    'PIL._tkinter_finder',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL.ImageDraw',
    'PIL.ImageFont'
]

# Ajouter les modules système nécessaires
hiddenimports += [
    'distutils.util',
    'distutils.version',
    'pkg_resources.py31compat',
    'cffi.verifier'
]

# Collecter les fichiers de données
datas = collect_data_files('customtkinter')
datas += collect_data_files('PIL') 