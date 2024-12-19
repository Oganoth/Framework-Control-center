# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['mini.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('LICENSE', '.'),
        ('README.md', '.'),
        ('RELEASE_NOTES.md', '.'),
        ('assets/*', 'assets/'),
        ('battery_config.json', '.'),
        ('config.json', '.'),
        ('libs/*', 'libs/'),
        ('ryzenadj/*', 'ryzenadj/'),
    ],
    hiddenimports=[
        'customtkinter',
        'PIL',
        'PIL._tkinter_finder',
        'PIL.Image',
        'psutil',
        'keyboard',
        'pystray',
        'pystray._win32',
        'requests',
        'charset_normalizer',
        'idna',
        'certifi',
        'urllib3',
        'wmi',
        'win32api',
        'win32con', 
        'win32gui',
        'pythoncom',
        'platform',
        'json',
        'logging',
        'threading',
        'subprocess',
        'webbrowser',
        'shutil',
        'ctypes',
        'time',
        'os',
        'sys'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Framework Hub',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/logo.ico',
    version='file_version_info.txt',
    uac_admin=True
)