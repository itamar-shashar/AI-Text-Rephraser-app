import os
import sys
import json
import tkinter as tk
import keyboard
import pyperclip
import threading
import time
import platform
from tkinter import ttk
from plyer import notification
from google import genai
from google.genai import types
import ctypes
from ctypes import wintypes
import subprocess
import socket

# Debug mode flag - set to False for production (this is just for me)
DEBUG_MODE = False

def debug_print(*args, **kwargs):
    """Print only if DEBUG_MODE is enabled"""
    if DEBUG_MODE:
        print(*args, **kwargs)



# Hardcoded system prompt that defines the core purpose of this app
SYSTEM_PROMPT = open("system_prompt.txt", "r").read()

# Default configurations            
DEFAULT_CONFIG = {
    "enabled": True,
    "shortcut": "ctrl+shift+r",
    "user_system_prompt": "Improve this text by fixing grammer, spelling and making it more professional and clear while keeping the original meaning",
    "api_key": "",
    "model": "gemini-2.0-flash-lite",
    "creativity_level": 5
}

# Windows constants
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002


def is_another_instance_running():
    """Check if another instance of this application is already running"""
    try:
        # Use a socket as a simple lock mechanism
        global single_instance_socket
        single_instance_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        single_instance_socket.bind(('localhost', 52878))  # Using a specific port for this app
        return False  # No other instance is running
    except socket.error:
        return True  # Another instance is already running

class RephraseApp:
    def __init__(self):
        debug_print("Initializing RephraseApp...")
        
        # Try to load config from installation directory first, then fall back to default location
        exe_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
        self.config_paths = [
            os.path.join(exe_dir, "config.json"),  # First check installation directory
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")  # Then check script directory
        ]
        
        self.load_config()
        
        # Configure Gemini API once at initialization
        self.configure_api()
        
        self.recording_shortcut = False
        self.processing = False
        self.settings_open = False
        self.setup_tray()
        self.setup_keyboard_hook()
        
        debug_print(f"RephraseApp initialized with shortcut: {self.config['shortcut']}")
        debug_print(f"App enabled: {self.config['enabled']}")


    ##########################################################################################################
    #                                Section: General Setups and Configurations
    ##########################################################################################################    
    

    def load_config(self):
        """Load configuration from file or use defaults"""
        try:
            # Try each possible config path
            config_loaded = False
            for config_path in self.config_paths:
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        self.config = json.load(f)
                    debug_print(f"Configuration loaded from {config_path}")
                    self.config_path = config_path  # Save the path that worked
                    config_loaded = True
                    break
                    
            if not config_loaded:
                debug_print("No configuration file found, using defaults")
                self.config = DEFAULT_CONFIG.copy()
                self.config_path = self.config_paths[0]  # Use first path for saving
                self.save_config()
        except Exception as e:
            debug_print(f"Error loading configuration: {e}")
            self.config = DEFAULT_CONFIG.copy()
            self.config_path = self.config_paths[0]
            
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            debug_print(f"Configuration saved to {self.config_path}")
        except Exception as e:
            debug_print(f"Error saving configuration: {e}")
   
    def configure_api(self):
        """Configure the API with the current API key"""
        try:
            self.client = genai.Client(api_key=self.config["api_key"])
            debug_print("Gemini API client configured with saved API key")
        except Exception as e:
            debug_print(f"Error configuring Gemini API client: {e}")
            self.client = None
    
    def show_notification(self, title, message):
        """Show a notification to the user"""
        try:
            # Get the absolute path to the icon file
            exe_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
            icon_path = os.path.join(exe_dir, "r_icon.ico")
            
            notification.notify(
                title=title,
                message=message,
                app_name="AI Text Rephraser",
                timeout=5,
                app_icon=icon_path
            )
            debug_print(f"Notification shown: {title} - {message}")
        except Exception as e:
            debug_print(f"Error showing notification: {e}")   

    def setup_keyboard_hook(self):
        """Setup keyboard shortcut hook to trigger the rephrasing process"""
        try:
            # Unhook any existing keyboard hooks
            keyboard.unhook_all()
            
            # Only set up the hook if the app is enabled
            if self.config["enabled"]:
                # Use a combination of suppress=True to prevent event propagation to other applications
                keyboard.add_hotkey(
                    self.config["shortcut"], 
                    self.process_clipboard,
                    suppress=True  # This prevents Windows from processing the hotkey
                )
                debug_print(f"Keyboard hook set up for shortcut: {self.config['shortcut']} with suppression")
            else:
                debug_print("Keyboard hook not set up because app is disabled")
        except Exception as e:
            debug_print(f"Error setting up keyboard hook: {e}")


    ##########################################################################################################
    #                                Section: Different Clipboard Access Methods 
    ##########################################################################################################    
    def simulate_copy(self):
        """Simulate copy operation using keyboard"""
        try:
            # First, simulate copy operation (Ctrl+C)
            debug_print("Simulating Ctrl+C...")
            # Try first sequence
            keyboard.press('ctrl')
            time.sleep(0.2)
            keyboard.press('c')
            time.sleep(0.2)
            keyboard.release('c')
            keyboard.release('ctrl')
            time.sleep(0.5)  # Wait for clipboard to update
            return True
        except Exception as e:
            debug_print(f"Keyboard simulation error: {e}")
            return False

    def simulate_alternative_copy(self):
        """Try alternative copy key sequence"""
        try:
            debug_print("Trying alternative key sequence...")
            # Release any possibly stuck keys
            keyboard.release('ctrl')
            time.sleep(0.1)
            
            # Try with press_and_release for better compatibility
            keyboard.press_and_release('ctrl+c')
            time.sleep(0.7)
            return True
        except Exception as e:
            debug_print(f"Alternative key sequence error: {e}")
            return False

    def get_clipboard_pyperclip(self, original_content):
        """Get clipboard content using pyperclip library"""
        try:
            text = pyperclip.paste()
            if text and text != '':
                if not original_content or text != original_content:
                    debug_print(f"Got new clipboard text using pyperclip: {text[:30]}...")
                    return text
                else:
                    debug_print("Pyperclip returned same content as initial state")
            else:
                debug_print("Pyperclip returned empty text")
        except Exception as e:
            debug_print(f"Pyperclip method failed: {e}")
        return None

    def get_clipboard_win32(self):
        """Get clipboard content using Win32 API"""
        if platform.system() != 'Windows':
            return None
            
        try:
            debug_print("Trying Win32 API with unicode text...")
            ctypes.windll.user32.OpenClipboard(0)
            if ctypes.windll.user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
                handle = ctypes.windll.user32.GetClipboardData(CF_UNICODETEXT)
                data = ctypes.windll.kernel32.GlobalLock(handle)
                text = ctypes.wintypes.LPWSTR(data).value
                ctypes.windll.kernel32.GlobalUnlock(handle)
                ctypes.windll.user32.CloseClipboard()
                if text and text != '':
                    debug_print(f"Got clipboard text using Win32 API (unicode): {text[:30]}...")
                    return text
            else:
                debug_print("No Unicode text in clipboard")
                ctypes.windll.user32.CloseClipboard()
        except Exception as e:
            debug_print(f"Win32 API unicode method failed: {e}")
            try:
                ctypes.windll.user32.CloseClipboard()
            except:
                pass
        return None

    def get_clipboard_powershell(self):
        """Get clipboard content using PowerShell"""
        if platform.system() != 'Windows':
            return None
            
        try:
            debug_print("Trying PowerShell Get-Clipboard -Raw...")
            process = subprocess.Popen(
                ['powershell.exe', '-command', 'Get-Clipboard -Raw'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            stdout, stderr = process.communicate()
            text = stdout.decode('utf-8', errors='replace').strip()
            if text and text != '':
                debug_print(f"Got clipboard text using PowerShell: {text[:30]}...")
                return text
            else:
                debug_print("PowerShell returned empty text")
        except Exception as e:
            debug_print(f"PowerShell method failed: {e}")
        return None

    def set_clipboard_pyperclip(self, text):
        """Set clipboard content using pyperclip"""
        try:
            pyperclip.copy(text)
            debug_print("Text set to clipboard using pyperclip")
            return True
        except Exception as e:
            debug_print(f"Pyperclip set method failed: {e}")
            return False

    def set_clipboard_win32(self, text):
        """Set clipboard content using Win32 API"""
        if platform.system() != 'Windows':
            return False
            
        try:
            ctypes.windll.user32.OpenClipboard(0)
            ctypes.windll.user32.EmptyClipboard()
            
            # Convert text to UTF-16LE (required for UNICODETEXT)
            text_encoded = text.encode('utf-16le')
            # Add null terminator
            text_encoded += b'\x00\x00'
            
            # Allocate and set clipboard data
            h_mem = ctypes.windll.kernel32.GlobalAlloc(GMEM_MOVEABLE, len(text_encoded))
            ptr = ctypes.windll.kernel32.GlobalLock(h_mem)
            ctypes.memmove(ptr, text_encoded, len(text_encoded))
            ctypes.windll.kernel32.GlobalUnlock(h_mem)
            ctypes.windll.user32.SetClipboardData(CF_UNICODETEXT, h_mem)
            ctypes.windll.user32.CloseClipboard()
            
            debug_print("Text set to clipboard using Win32 API (unicode)")
            return True
        except Exception as e:
            debug_print(f"Win32 API set method failed: {e}")
            try:
                ctypes.windll.user32.CloseClipboard()
            except:
                pass
            return False

    def set_clipboard_powershell(self, text):
        """Set clipboard content using PowerShell"""
        if platform.system() != 'Windows':
            return False
            
        try:
            # Escape quotes for PowerShell
            text_escaped = text.replace('"', '`"')
            
            process = subprocess.Popen(
                ['powershell.exe', '-command', f'Set-Clipboard -Value "{text_escaped}"'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            process.communicate()
            
            if process.returncode == 0:
                debug_print("Text set to clipboard using PowerShell")
                return True
            return False
        except Exception as e:
            debug_print(f"PowerShell set method failed: {e}")
            return False
    
    
    ##########################################################################################################
    #                                Section: Rephrasing Clipboard Text
    ##########################################################################################################
    def clear_clipboard(self):
            """Clear clipboard using multiple methods"""
            try:
                # Clear clipboard using multiple methods
                pyperclip.copy('')
                if platform.system() == 'Windows':
                    try:
                        ctypes.windll.user32.OpenClipboard(0)
                        ctypes.windll.user32.EmptyClipboard()
                        ctypes.windll.user32.CloseClipboard()
                    except:
                        try:
                            ctypes.windll.user32.CloseClipboard()
                        except:
                            pass
                    try:
                        subprocess.run(['powershell.exe', '-command', 'Set-Clipboard -Value ""'], 
                                    check=False, capture_output=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
                    except:
                        pass
                debug_print("Clipboard cleared")
                time.sleep(0.2)  # Small delay after clearing
            except Exception as e:
                debug_print(f"Error clearing clipboard: {e}")
    
    def get_clipboard_text_multi_approach(self):
        """Robust clipboard access using multiple methods"""
        debug_print("Trying to get clipboard text...")
        
        # First, clear the clipboard to avoid capturing old content
        self.clear_clipboard()
        
        # Store original clipboard content (I want it be empty after clearing)
        original_content = None
        try:
            original_content = pyperclip.paste()
            debug_print(f"Initial clipboard state: '{original_content[:30]}...' if present")
        except:
            pass
        
        # Simulate text copy using keyboard
        self.simulate_copy()
        
        # Method 1: Using pyperclip
        text = self.get_clipboard_pyperclip(original_content)
        if text:
            return text
        
        # Method 2: Using Win32 API with UNICODETEXT format
        text = self.get_clipboard_win32()
        if text:
            return text
        
        # Method 3: Using PowerShell with Raw parameter
        text = self.get_clipboard_powershell()
        if text:
            return text
        
        # Try all methods one more time with different text copy simulation
        if self.simulate_alternative_copy():
            
            # Method 1: Pyperclip again
            text = self.get_clipboard_pyperclip(original_content)
            if text:
                return text
                
            # Method 2: Win32 again
            text = self.get_clipboard_win32()
            if text:
                return text
        
        debug_print("All clipboard access methods failed")
        return None  # Return None instead of original content
        
    def set_clipboard_text_multi_approach(self, text):
        """Robust clipboard setting using multiple methods"""
        debug_print(f"Trying to set clipboard text: {text[:30]}...")
        
        # Method 1: Using pyperclip
        if self.set_clipboard_pyperclip(text):
            return True
        
        # Method 2: Using Win32 API
        if self.set_clipboard_win32(text):
            return True
        
        # Method 3: Using PowerShell
        if self.set_clipboard_powershell(text):
            return True
            
        debug_print("All clipboard set methods failed")
        return False
    
    def process_clipboard(self):
        """Process the text from clipboard with Google Generative AI"""
        if self.processing:
            debug_print("Already processing clipboard text, skipping...")
            return
            
        self.processing = True
        
        def process_thread():
            try:
                debug_print(f"Processing clipboard with shortcut: {self.config['shortcut']}")
                
                # Get text from clipboard
                text = self.get_clipboard_text_multi_approach()
                if not text:
                    self.show_notification("Error", "Failed to get text from clipboard")
                    self.processing = False
                    return

                # Show notification that rephrasing is in progress
                self.show_notification("Processing", "Rephrasing text with AI...")

                debug_print(f"Text captured from clipboard: {text[:50]}...")
                
                # Send text to Google Generative AI
                rephrased_text = self.rephrase_with_google_generative_ai(text)
                if not rephrased_text:
                    self.show_notification("Error", "Failed to rephrase text")
                    self.processing = False
                    return
                    
                debug_print(f"Rephrased text received: {rephrased_text[:50]}...")
                
                # Set rephrased text to clipboard
                if self.set_clipboard_text_multi_approach(rephrased_text):
                    # Wait a moment before pasting
                    time.sleep(0.2)
                    
                    # Use paste instead of direct writing to avoid triggering auto-send in chat apps
                    try:
                        # Use a more controlled paste sequence
                        keyboard.press('ctrl')
                        time.sleep(0.1)
                        keyboard.press('v')
                        time.sleep(0.1)
                        keyboard.release('v')
                        keyboard.release('ctrl')
                    except Exception as paste_error:
                        debug_print(f"Paste failed: {paste_error}")
                        self.show_notification("Error", "Failed to paste rephrased text")
                    
                    # Clear clipboard after operation complete
                    time.sleep(0.5)  # Small delay after paste
                    try:
                        pyperclip.copy('')
                        debug_print("Clipboard cleared after operation")
                    except:
                        pass
                else:
                    self.show_notification("Error", "Failed to set rephrased text to clipboard")
            except Exception as e:
                debug_print(f"Error processing clipboard: {e}")
                self.show_notification("Error", f"Error processing: {str(e)}")
            finally:
                self.processing = False
                
        # Run in a separate thread to avoid blocking
        threading.Thread(target=process_thread).start()
        
    def rephrase_with_google_generative_ai(self, text):
        """Send text to Google Generative AI for rephrasing"""
        try:
            debug_print("Sending text to Google Generative AI...")
            
            # Check if client is initialized
            if not self.client:
                self.configure_api()
                if not self.client:
                    raise Exception("Failed to initialize Gemini client")
            
            # Convert creativity level (0-10) to temperature (0-1)
            temperature = self.config.get("creativity_level", 5) / 10
            debug_print(f"Using temperature: {temperature}")
            
            user_system_prompt = self.config["user_system_prompt"]
            if user_system_prompt.endswith(':'):
                user_system_prompt = user_system_prompt[:-1]
            
            # Create prompt for rephrasing task
            prompt = f"""
Your System Prompt:
{SYSTEM_PROMPT}

User's instructions:
{user_system_prompt}:

Text for the task:
{text}
"""
            
            # Generate the response 
            response = self.client.models.generate_content(
                model=self.config["model"],
                contents=[prompt],
                config=types.GenerateContentConfig(
                    temperature=temperature,   
                )
            )
            
            # Extract and return rephrased text
            if response and hasattr(response, "text"):
                rephrased_text = response.text
                debug_print("Successfully received response from Google Generative AI")
                return rephrased_text
            else:
                debug_print("Empty response received from Google Generative AI")
                return None
        except Exception as e:
            debug_print(f"Error in Google Generative AI request: {e}")
            if "api_key" in str(e).lower():
                self.show_notification("API Key Error", "Please check your Google Generative AI API key")
            return None
                      
    
    ##########################################################################################################
    #                                Section: User Tray Icon and Menu Settings
    ##########################################################################################################
    def setup_tray(self):
        """Setup system tray icon and menu"""
        try:
            import pystray
            from PIL import Image, ImageDraw
            
            # Get the absolute path to the icon file
            exe_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
            icon_path = os.path.join(exe_dir, "r_icon.ico")
            
            # Load icon
            try:
                # Use absolute path to ensure icon loads after system restart
                icon_image = Image.open(icon_path)
                debug_print(f"Loaded icon from file: {icon_path}")
            except Exception as e:
                # Create a simple icon if file is not found
                debug_print(f"Icon file not found ({e}), creating a simple icon")
                icon_image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
                draw = ImageDraw.Draw(icon_image)
                draw.ellipse((4, 4, 60, 60), fill='blue')
                draw.text((20, 20), "R", fill='white')
                
            def on_clicked(icon, item):
                if str(item) == "Settings":
                    if not self.settings_open:
                        self.create_settings_window()
                elif str(item) == "Enable App":
                    self.config["enabled"] = not self.config["enabled"]
                    self.save_config()
                    self.setup_keyboard_hook()
                    if self.config["enabled"]:
                        self.show_notification("App Enabled", "Text rephrasing is now enabled")
                    else:
                        self.show_notification("App Disabled", "Text rephrasing is now disabled")
                elif str(item) == "Exit":
                    icon.stop()
                    os._exit(0)
                    
            # Create menu
            menu = pystray.Menu(
                pystray.MenuItem("Enable App", on_clicked, checked=lambda item: self.config["enabled"]),
                pystray.MenuItem("Settings", on_clicked),
                pystray.MenuItem("Exit", on_clicked)
            )
            
            # Create and run tray icon
            self.icon = pystray.Icon("AI Text Rephraser", icon_image, "AI Text Rephraser", menu)
            
            # Run the icon in a separate thread
            threading.Thread(target=self.icon.run, daemon=True).start()
            debug_print("System tray icon set up")
        except Exception as e:
            debug_print(f"Error setting up tray icon: {e}")
            
    def record_shortcut(self, shortcut_label, shortcut_button):
        """Start recording a new shortcut"""
        if self.recording_shortcut:
            return
            
        self.recording_shortcut = True
        shortcut_button.config(text="Recording... Press keys")
        
        # Function to handle key events
        def on_hotkey(event):
            if not self.recording_shortcut:
                return
                
            # Get the key combination
            key_name = event.name
            modifiers = []
            
            if keyboard.is_pressed('ctrl'):
                modifiers.append('ctrl')
            if keyboard.is_pressed('alt'):
                modifiers.append('alt')
            if keyboard.is_pressed('shift'):
                modifiers.append('shift')
            
            # If it's just a modifier key press, ignore it
            if key_name in ['ctrl', 'alt', 'shift']:
                return
            
            # Create the hotkey string
            if modifiers:
                hotkey = '+'.join(modifiers) + f"+{key_name}"
            else:
                hotkey = key_name
            
            # Update the shortcut in the UI
            self.shortcut_var.set(hotkey)
            shortcut_label.config(text=f"Current shortcut: {hotkey}")
            shortcut_button.config(text="Record New Shortcut")
            
            # Stop recording
            self.recording_shortcut = False
            
            try:
                keyboard.unhook_all()
                # Re-setup the main keyboard hook
                if self.config["enabled"]:
                    keyboard.add_hotkey(self.config["shortcut"], self.process_clipboard)
            except Exception as e:
                debug_print(f"Error resetting keyboard hook: {e}")
        
        try:
            # Hook the keyboard globally
            keyboard.unhook_all()
            keyboard.on_press(on_hotkey)
        except Exception as e:
            debug_print(f"Error setting up shortcut recording: {e}")
            self.recording_shortcut = False
            shortcut_button.config(text="Record New Shortcut")
    
    def list_available_models(self):
        """List all available Gemini models and their capabilities"""
        # # Here i tried to list all the models but it was too many models of the same type - too confusing for the user

        # wanted_models_names = ['gemini-2.0-flash','gemini-2.0-flash-lite', 'gemini-1.5-flash','gemini-1.5-flash-8b']
        # try:
        #     # Get models
        #     models = genai.list_models()
        #     available_models = []
            
        #     # Filter for chat-capable models
        #     for model in models:
        #         if any(wanted_model_name in model.name for wanted_model_name in wanted_models_names):
        #             model_name = model.name.split('/')[-1]
        #             available_models.append(model_name)
            
        #     return available_models
        # except Exception as e:
        #     debug_print(f"Error listing models: {e}")
        #     return ['gemini-2.0-flash', 'gemini-1.5-flash']

        # hardcoded list of models
        return ['gemini-2.0-flash','gemini-2.0-flash-lite', 'gemini-1.5-flash','gemini-1.5-flash-8b']
    
    def create_settings_window(self):
        """Create and show settings window"""
        if self.settings_open:
            debug_print("Settings window already open")
            if hasattr(self, 'root') and self.root:
                try:
                    self.root.focus_force()  # Bring to front if it exists
                except:
                    pass
            return
            
        self.settings_open = True
        debug_print("Opening settings window")
        
        try:
            # Create a new Tkinter window
            self.root = tk.Tk()
            self.root.title("Rephrase App Settings")
            self.root.geometry("500x450")
            self.root.resizable(False, False)
            
            # Create instance variables for settings
            self.enabled_var = tk.BooleanVar(value=self.config["enabled"])
            self.shortcut_var = tk.StringVar(value=self.config["shortcut"])
            self.user_system_prompt_var = tk.StringVar(value=self.config["user_system_prompt"])
            
            # For API key, store the actual value but display masked version
            self.api_key_var = tk.StringVar(value=self.config["api_key"])
            displayed_api_key = self.mask_api_key(self.config["api_key"])
            self.displayed_api_key_var = tk.StringVar(value=displayed_api_key)
            
            self.model_var = tk.StringVar(value=self.config["model"])
            
            # Add creativity level variable (0-10 scale)
            self.creativity_level_var = tk.IntVar(value=self.config.get("creativity_level", 5))
            
            # Create a notebook with tabs
            notebook = ttk.Notebook(self.root)
            
            # Shortcut Configuration tab
            shortcut_frame = ttk.Frame(notebook)
            notebook.add(shortcut_frame, text="Edit Shortcut")
            
            # Shortcut configuration
            shortcut_config_frame = ttk.LabelFrame(shortcut_frame, text="Shortcut Configuration")
            shortcut_config_frame.pack(fill=tk.X, padx=10, pady=10)
            
            shortcut_label = ttk.Label(shortcut_config_frame, text=f"Current shortcut: {self.config['shortcut']}")
            shortcut_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
            
            shortcut_button = ttk.Button(shortcut_config_frame, text="Record New Shortcut")
            shortcut_button.config(command=lambda: self.record_shortcut(shortcut_label, shortcut_button))
            shortcut_button.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
            
            # Instructions for shortcut
            instruction_label = ttk.Label(shortcut_frame, text="Press the 'Record New Shortcut' button and then press the key combination you want to use.")
            instruction_label.pack(pady=10, padx=10, anchor=tk.W)
            
            # API Configuration tab
            api_frame = ttk.Frame(notebook)
            notebook.add(api_frame, text="API Settings")
            
            # API configuration
            api_config_frame = ttk.LabelFrame(api_frame, text="Google Generative AI Configuration")
            api_config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            ttk.Label(api_config_frame, text="API Key:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
            api_key_entry = ttk.Entry(api_config_frame, textvariable=self.displayed_api_key_var, width=40)
            api_key_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
            
            # Add show/hide button for API key
            def toggle_api_key_visibility():
                # If currently showing masked version
                if self.displayed_api_key_var.get() == self.mask_api_key(self.api_key_var.get()):
                    # Show full key
                    self.displayed_api_key_var.set(self.api_key_var.get())
                    show_hide_button.config(text="Hide Key")
                else:
                    # Show masked version
                    self.displayed_api_key_var.set(self.mask_api_key(self.api_key_var.get()))
                    show_hide_button.config(text="Show Key")
                    
            show_hide_button = ttk.Button(api_config_frame, text="Show Key", command=toggle_api_key_visibility)
            show_hide_button.grid(row=0, column=2, padx=5, pady=5)
            
            # API key instructions
            ttk.Label(api_config_frame, text="Enter new key to update").grid(row=1, column=1, padx=5, pady=0, sticky=tk.W)
            
            ttk.Label(api_config_frame, text="Model:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
            
            # Create a combobox for model selection
            models_list = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]  # Default models
            try:
                # Try to get actual models if possible
                if self.config["api_key"]:
                    available_models = self.list_available_models()
                    if available_models:
                        models_list = available_models
            except:
                pass
                
            model_combobox = ttk.Combobox(api_config_frame, textvariable=self.model_var, values=models_list, width=38)
            model_combobox.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
            
            # Model refresh button
            def refresh_models():
                try:
                    status_var.set("Fetching available models...")
                    self.root.update_idletasks()
                    
                    # Only try to get models if API key is set
                    if self.api_key_var.get():
                        # Only reconfigure if using a different API key than current
                        current_key_changed = self.api_key_var.get() != self.config["api_key"]
                        if current_key_changed:
                            # Create a temporary client with the new key
                            temp_client = genai.Client(api_key=self.api_key_var.get())
                            debug_print("Temporarily created client with new key for fetching models")
                        
                        available_models = self.list_available_models()
                        
                        if available_models:
                            model_combobox['values'] = available_models
                            status_var.set(f"Found {len(available_models)} available models")
                            status_bar.config(foreground="green")
                        else:
                            status_var.set("No models found")
                            status_bar.config(foreground="red")
                    else:
                        status_var.set("API Key required to fetch models")
                        status_bar.config(foreground="red")
                except Exception as e:
                    status_var.set(f"Error fetching models...")
                    status_bar.config(foreground="red")
                    debug_print(f"Error fetching models: {e}")
            
            refresh_button = ttk.Button(api_config_frame, text="Refresh Models", command=refresh_models)
            refresh_button.grid(row=2, column=2, padx=5, pady=5)
            
            # Monitor API key changes
            def on_api_key_change(*args):
                # Only update the actual key if the displayed version changed and is not masked
                current_display = self.displayed_api_key_var.get()
                if not current_display.startswith('*'):
                    self.api_key_var.set(current_display)
                    
            self.displayed_api_key_var.trace_add("write", on_api_key_change)
            
            # Prompt Configuration tab
            prompt_frame = ttk.Frame(notebook)
            notebook.add(prompt_frame, text="Prompt Settings")
            
            prompt_config_frame = ttk.LabelFrame(prompt_frame, text="Your Rephrasing Instructions")
            prompt_config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            ttk.Label(prompt_config_frame, text="Tell the AI how you want your text processed:").pack(anchor=tk.W, padx=5, pady=5)
            
            system_prompt_text = tk.Text(prompt_config_frame, height=8, width=50)
            system_prompt_text.insert(tk.END, self.config["user_system_prompt"])
            system_prompt_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
            
            # Add creativity level slider
            creativity_frame = ttk.LabelFrame(prompt_frame, text="Creativity Level")
            creativity_frame.pack(fill=tk.X, padx=10, pady=10)
            
            # Configure the grid to have proper weights for centering
            creativity_frame.columnconfigure(0, weight=1)
            creativity_frame.columnconfigure(1, weight=3)
            creativity_frame.columnconfigure(2, weight=1)
            
            ttk.Label(creativity_frame, text="Precise").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
            ttk.Label(creativity_frame, text="Creative").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
            
            creativity_slider = ttk.Scale(
                creativity_frame, 
                from_=0, 
                to=10, 
                orient=tk.HORIZONTAL, 
                variable=self.creativity_level_var,
                length=250
            )
            creativity_slider.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
            
            # Show current value label
            creativity_value_label = ttk.Label(creativity_frame, text=f"Current: {self.creativity_level_var.get()}")
            creativity_value_label.grid(row=1, column=1, padx=5, pady=5, sticky=tk.N)
            
            # Update label when slider changes
            def update_creativity_label(*args):
                creativity_value_label.config(text=f"Current: {self.creativity_level_var.get()}")
                
            self.creativity_level_var.trace_add("write", update_creativity_label)
            
            # Add the notebook to the window
            notebook.pack(expand=1, fill="both", padx=10, pady=10)
            
            # Status bar
            status_var = tk.StringVar(value="Ready")
            status_bar = ttk.Label(self.root, textvariable=status_var, relief=tk.SUNKEN, anchor=tk.W)
            status_bar.pack(side=tk.BOTTOM, fill=tk.X)
            
            # Reset status timer
            def reset_status_after_delay():
                def reset_status():
                    if self.root and self.root.winfo_exists():
                        status_var.set("Ready")
                        status_bar.config(foreground="black")
                
                status_reset_timer = threading.Timer(5.0, reset_status)
                status_reset_timer.daemon = True
                status_reset_timer.start()
                
            # Monitor status changes and reset after delay
            def on_status_change(*args):
                if status_var.get() != "Ready":
                    reset_status_after_delay()
                    
            status_var.trace_add("write", on_status_change)
            
            # Button frame
            button_frame = ttk.Frame(self.root)
            button_frame.pack(pady=10, padx=10, fill=tk.X)
            
            # Test connection button
            def test_connection():
                try:
                    status_var.set("Testing connection...")
                    status_bar.config(foreground="black")  # Reset color
                    self.root.update_idletasks()
                    
                    # Create a test client with current settings in UI
                    test_client = genai.Client(api_key=self.api_key_var.get())
                    
                    # Simple test request
                    response = test_client.models.generate_content(
                        model=self.model_var.get(),
                        contents=["Hello"],
                        config=types.GenerateContentConfig(
                            temperature=0.2,
                            max_output_tokens=10
                        )
                    )
                    
                    if response and hasattr(response, 'text'):
                        status_var.set("Connection successful! API settings are valid.")
                        status_bar.config(foreground="green")  # Green for success
                    else:
                        status_var.set("Connection test returned empty response.")
                        status_bar.config(foreground="red")  # Red for failure
                        
                except Exception as e:
                    error_msg = str(e)
                    if "api_key" in error_msg.lower() or "key" in error_msg.lower() and "invalid" in error_msg.lower():
                        status_var.set(f"Connection test failed: Invalid API key..")
                        status_bar.config(foreground="red")  # Red for failure
                        debug_print(f"API connection test failed: {e}")
                    
            test_button = ttk.Button(button_frame, text="Test API Connection", command=test_connection)
            test_button.pack(side=tk.LEFT, padx=5)
            
            # Save button
            def save_settings():
                try:
                    # Update system prompt from text widget
                    self.user_system_prompt_var.set(system_prompt_text.get("1.0", tk.END).strip())
                    
                    # Get current API key before updating
                    old_api_key = self.config["api_key"]
                    new_api_key = self.api_key_var.get()
                    
                    # Update config with all settings
                    self.config["enabled"] = self.enabled_var.get()
                    self.config["shortcut"] = self.shortcut_var.get()
                    self.config["user_system_prompt"] = self.user_system_prompt_var.get()
                    self.config["api_key"] = new_api_key  # Use actual API key
                    self.config["model"] = self.model_var.get()
                    self.config["creativity_level"] = self.creativity_level_var.get()
                    
                    # Only reconfigure API if the key has changed
                    if old_api_key != new_api_key or not self.client:
                        try:
                            self.client = genai.Client(api_key=new_api_key)
                            debug_print("Gemini API client reconfigured with new API key")
                        except Exception as e:
                            debug_print(f"Error reconfiguring Gemini API client: {e}")
                    
                    # Save to file and update keyboard hook
                    self.save_config()
                    self.setup_keyboard_hook()
                    
                    # Show success notification and update status bar
                    self.show_notification("Settings Saved", "Your settings have been updated")
                    status_var.set("Settings saved successfully!")
                    status_bar.config(foreground="green")
                    self.root.update_idletasks()
                except Exception as e:
                    status_var.set(f"Error saving settings.. please try again.")
                    status_bar.config(foreground="red")
                    debug_print(f"Error saving settings: {e}")
            
            save_button = ttk.Button(button_frame, text="Save Settings", command=save_settings)
            save_button.pack(side=tk.RIGHT, padx=5)
            
            # Handle window close event
            def on_close():
                self.close_settings_window()
                
            self.root.protocol("WM_DELETE_WINDOW", on_close)
            
            # Make sure the window is on top and request focus
            self.root.attributes('-topmost', True)
            self.root.attributes('-topmost', False)
            self.root.focus_force()
            
            # Run the Tkinter event loop in the main thread
            self.root.mainloop()
        except Exception as e:
            debug_print(f"Error creating settings window: {e}")
            self.settings_open = False
            
    def mask_api_key(self, api_key):
        """Mask the API key to show only the last 3 characters"""
        if not api_key or len(api_key) <= 3:
            return api_key
        
        masked_part = '*' * (len(api_key) - 3)
        visible_part = api_key[-3:]
        return masked_part + visible_part
    
    def close_settings_window(self):
        """Safely close the settings window and reset state"""
        try:
            debug_print("Closing settings window")
            # Reset recording state if needed
            if self.recording_shortcut:
                self.recording_shortcut = False
                keyboard.unhook_all()
                self.setup_keyboard_hook()
                
            # Destroy the window if it exists
            if hasattr(self, 'root') and self.root:
                self.root.destroy()
                
        except Exception as e:
            debug_print(f"Error closing settings window: {e}")
        finally:
            # Ensure this flag is reset
            self.settings_open = False
            # Re-setup keyboard hook to ensure it's working
            self.setup_keyboard_hook()

if __name__ == "__main__":
    # Check if another instance is already running
    if is_another_instance_running():
        debug_print("Another instance is already running. Exiting.")
        sys.exit(0)
    
    # If not, start the app
    app = RephraseApp()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        debug_print("Exiting...")
        if hasattr(app, 'icon'):
            app.icon.stop()
        sys.exit(0) 
        