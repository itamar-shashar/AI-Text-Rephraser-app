from cx_Freeze import setup, Executable
import os
import sys

build_exe_options = {
    "packages": ["os", "sys", "json", "tkinter", "keyboard", "pyperclip", "threading", 
                "time", "platform", "plyer", "google.genai", "ctypes", "subprocess", 
                "pystray", "PIL", "socket"],
    "include_files": [
        ("src/r_icon.ico", "r_icon.ico"), 
        ("src/config.json", "config.json"),
        ("src/system_prompt.txt", "system_prompt.txt")
    ],
    "excludes": []
}

base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="AI Text Rephraser",
    version="1.0.0",
    description="Rephrase text using Google Gemini AI",
    options={"build_exe": build_exe_options},
    executables=[Executable("src/rephrase_app.py", base=base, 
                           icon="src/r_icon.ico",
                           target_name="AI Text Rephraser.exe")]
)