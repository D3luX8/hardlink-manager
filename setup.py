"""
setup.py — cx_Freeze build script per HardLink Manager
Uso: python setup.py build
"""

import sys
from cx_Freeze import setup, Executable
import customtkinter
import os

# Percorso della cartella customtkinter (necessario per includere assets/temi)
ctk_path = os.path.dirname(customtkinter.__file__)

build_exe_options = {
    "packages": [
        "customtkinter",
        "tkinter",
        "threading",
        "queue",
        "subprocess",
        "pathlib",
        "os",
        "sys",
    ],
    "include_files": [
        (ctk_path, "lib/customtkinter"),   # copia tutti i file di customtkinter (temi, immagini)
    ],
    "excludes": [
        "unittest", "email", "html", "http", "urllib",
        "xml", "pydoc", "doctest", "argparse", "difflib",
        "logging", "multiprocessing",
    ],
    "optimize": 2,
}

# Su Windows, "Win32GUI" nasconde la finestra CMD in background
base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="HardLink Manager",
    version="1.0",
    description="Crea hardlink NTFS con interfaccia grafica",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            script="hardlink_manager.py",
            base=base,
            target_name="HardLink Manager.exe",
            icon=None,   # metti qui il path di un .ico se vuoi un'icona personalizzata
        )
    ],
)
