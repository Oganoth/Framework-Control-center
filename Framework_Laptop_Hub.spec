# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\johnd\\Documents\\TEST\\app\\framework_laptop_hub.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\johnd\\Documents\\TEST\\app/assets', 'assets'), ('C:\\Users\\johnd\\Documents\\TEST\\app/fonts', 'fonts'), ('C:\\Users\\johnd\\Documents\\TEST\\app/ryzenadj', 'ryzenadj'), ('C:\\Users\\johnd\\Documents\\TEST\\app/translations.py', '.'), ('C:\\Users\\johnd\\Documents\\TEST\\app/language_manager.py', '.'), ('C:\\Users\\johnd\\Documents\\TEST\\app/settings.json', '.')],
    hiddenimports=['PIL._tkinter_finder', 'queue', 'urllib.parse', 'http.client', 'urllib.request', 'json'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Framework_Laptop_Hub',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    icon=['C:\\Users\\johnd\\Documents\\TEST\\app\\assets\\logo.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Framework_Laptop_Hub',
)
