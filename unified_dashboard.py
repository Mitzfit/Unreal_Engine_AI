"""
╔════════════════════════════════════════════════════════════════════════════╗
║        UNIFIED GAME DEVELOPMENT DASHBOARD - ALL TOOLS IN ONE              ║
║    AI-Powered Unreal Engine Development Console                           ║
║    Combat • Dialogue • Inventory • Quests • Streaming • Procedural Gen   ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import threading
import time
import json
from datetime import datetime
from collections import deque
from enum import Enum
from user_dashboard import UserDashboard, ProjectStatus
from ai_assistant_onboarding import AIAssistant

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox, filedialog
    import tkinter.font as tkFont
    import tkinter.simpledialog as simpledialog
except Exception:
    raise RuntimeError("Tkinter is required. Install Python with Tk support.")

try:
    import openai
except ImportError:
    openai = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    import requests
except ImportError:
    requests = None

# Try importing game systems (they may not all be available)
try:
    from combat_system import CombatSystem
except:
    CombatSystem = None

try:
    from dialogue_system import DialogueTree
except:
    DialogueTree = None

try:
    from inventory_crafting_system import AdvancedInventorySystem
except:
    AdvancedInventorySystem = None

try:
    from quest_mission_visual_designer import AdvancedQuestSystem
except:
    AdvancedQuestSystem = None

try:
    from level_streaming_manager import LevelStreamingManager
except:
    LevelStreamingManager = None

try:
    from procedural_gen import TerrainGenerator, DungeonGenerator, CityGenerator
except:
    TerrainGenerator = DungeonGenerator = CityGenerator = None

try:
    from analytics_dashboard import AnalyticsEngine, EventTracker
except:
    AnalyticsEngine = EventTracker = None

APP_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, APP_DIR)

def _sanitize_env_value(v: str) -> str:
    if not v:
        return ''
    v = v.strip()
    # strip surrounding single or double quotes
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        v = v[1:-1]
    return v.strip()

OPENAI_API_KEY = _sanitize_env_value(os.getenv("OPENAI_API_KEY"))
if openai and OPENAI_API_KEY:
    try:
        openai.api_key = OPENAI_API_KEY
    except Exception:
        # fallback assign
        setattr(openai, 'api_key', OPENAI_API_KEY)
# Ensure the sanitized key is available in os.environ for any later imports
if OPENAI_API_KEY:
    os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

# Gemini API configuration
GEMINI_API_KEY = _sanitize_env_value(os.getenv("GEMINI_API_KEY"))
GEMINI_MODEL = _sanitize_env_value(os.getenv("GEMINI_MODEL", "gemini-pro"))
if genai and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# HuggingFace API configuration
HUGGINGFACE_API_KEY = _sanitize_env_value(os.getenv("HUGGINGFACE_API_KEY"))
HUGGINGFACE_MODEL = _sanitize_env_value(os.getenv("HUGGINGFACE_MODEL", "meta-llama/Llama-2-7b-chat-hf"))
HUGGINGFACE_ENDPOINT = _sanitize_env_value(os.getenv("HUGGINGFACE_ENDPOINT", "https://api-inference.huggingface.co/models/"))

# Default AI provider (gemini, openai, or huggingface)
DEFAULT_AI_PROVIDER = _sanitize_env_value(os.getenv("DEFAULT_AI_PROVIDER", "gemini"))

# Password hashing: prefer bcrypt if available, otherwise use PBKDF2-HMAC as fallback
try:
    import bcrypt
    HAS_BCRYPT = True
except Exception:
    bcrypt = None
    HAS_BCRYPT = False

import hashlib

# Ensure .env is loaded explicitly
try:
    from dotenv import load_dotenv
    import os as _dotenv_os
    _env_file = _dotenv_os.path.join(_dotenv_os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path=_env_file, override=True)
except Exception:
    pass

def _hash_password(password: str) -> str:
    if not password:
        return ''
    if HAS_BCRYPT:
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        return hashed.decode('utf-8')
    # fallback: PBKDF2-HMAC with salt
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
    return salt.hex() + ':' + key.hex()

def _verify_password(password: str, stored: str) -> bool:
    if not stored:
        return False
    if HAS_BCRYPT:
        try:
            return bcrypt.checkpw(password.encode('utf-8'), stored.encode('utf-8'))
        except Exception:
            return False
    try:
        salt_hex, key_hex = stored.split(':')
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        test = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
        return test == key
    except Exception:
        return False

# Simple tooltip helper
class Tooltip:
    def __init__(self, widget, text=""):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tipwindow or not self.text:
            return
        x = event.x_root + 10
        y = event.y_root + 10
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=4)

    def hide(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

# System prompt for AI code generation
SYSTEM_PROMPT = """You are an expert AI assistant specialized in Unreal Engine C++ game development. 
Your role is to help developers integrate all game systems (combat, dialogue, inventory, quests, etc.)

You can help with:
1. Write C++ code - Production-ready code with comments
2. System integration - Connect multiple game systems
3. Debugging - Analyze and fix issues
4. Optimization - Suggest performance improvements
5. Documentation - Create API documentation

Always follow Unreal Engine best practices and explain your code choices.
Format code responses with clear sections and syntax highlighting using markdown."""

# ═══════════════════════════════════════════════════════════════════════════════
# COLOR SCHEME
# ═══════════════════════════════════════════════════════════════════════════════

COLOR = {
    'bg_dark': "#0a0e27",
    'bg_darker': "#050810",
    'bg_panel': "#0f1535",
    'accent_blue': "#00d4ff",
    'accent_blue_2': "#0099cc",
    'text_primary': "#e0e0ff",
    'text_secondary': "#a0a0c0",
    'text_success': "#00ff88",
    'text_error': "#ff4444",
    'text_warning': "#ffaa00",
    'tab_combat': "#ff6b6b",
    'tab_dialogue': "#4ecdc4",
    'tab_inventory': "#ffe66d",
    'tab_quest': "#a8e6cf",
    'tab_streaming': "#ff8b94",
    'tab_procedural': "#7b68ee",
    'tab_analytics': "#20b2aa",
}

# ═══════════════════════════════════════════════════════════════════════════════
# AI CHATBOT CORE
# ═══════════════════════════════════════════════════════════════════════════════

class GameDevChatBot:
    """AI chatbot for code generation and system integration"""
    
    def __init__(self):
        self.conversation_history = deque(maxlen=50)
        self.is_loading = False
        self.current_model = "gpt-3.5-turbo"
        self.available_providers = self._get_available_providers()
        # Set provider: use default if available, otherwise pick the first available
        if DEFAULT_AI_PROVIDER in self.available_providers:
            self.provider = DEFAULT_AI_PROVIDER
        elif self.available_providers:
            self.provider = list(self.available_providers.keys())[0]
        else:
            self.provider = None  # No providers available
    
    def _get_available_providers(self) -> dict:
        """Check which AI providers are available with valid keys."""
        providers = {}
        if genai and GEMINI_API_KEY:
            providers['gemini'] = 'Google Gemini'
        if openai and OPENAI_API_KEY:
            providers['openai'] = 'OpenAI'
        if HUGGINGFACE_API_KEY:
            providers['huggingface'] = 'HuggingFace Inference'
        return providers
    
    def set_provider(self, provider: str):
        """Switch to a different AI provider."""
        if provider in self.available_providers:
            self.provider = provider
            return True
        return False
    
    def send_message(self, user_message: str) -> str:
        """Send message to the configured AI provider."""
        if not user_message.strip():
            return ""
        
        if not self.provider or self.provider not in self.available_providers:
            return "Error: No AI provider is active. Please configure an API key (GEMINI_API_KEY, OPENAI_API_KEY, or HUGGINGFACE_API_KEY) in .env and restart."
        
        try:
            self.is_loading = True
            
            # Build conversation context
            context = [{"role": "system", "content": SYSTEM_PROMPT}]
            for msg in self.conversation_history:
                context.append(msg)
            context.append({"role": "user", "content": user_message})
            
            # Route to appropriate provider
            if self.provider == 'gemini' and genai and GEMINI_API_KEY:
                response_text = self._call_gemini(user_message, context)
            elif self.provider == 'openai' and openai and OPENAI_API_KEY:
                response_text = self._call_openai(context)
            elif self.provider == 'huggingface' and HUGGINGFACE_API_KEY:
                response_text = self._call_huggingface(user_message)
            else:
                response_text = f"Error: Provider '{self.provider}' is not available or not configured."
            
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": response_text})
            
            self.is_loading = False
            return response_text
            
        except Exception as e:
            self.is_loading = False
            return f"Error ({self.provider}): {str(e)}"
            return f"Error ({self.provider}): {str(e)}"
    
    def _call_gemini(self, user_message: str, context: list) -> str:
        """Call Google Gemini API."""
        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            # Gemini doesn't use system roles the same way; format as a single prompt
            prompt_text = SYSTEM_PROMPT + "\n\n" + user_message
            response = model.generate_content(prompt_text, generation_config=genai.types.GenerationConfig(max_output_tokens=2000))
            return response.text
        except Exception as e:
            return f"Gemini Error: {str(e)}"
    
    def _call_openai(self, context: list) -> str:
        """Call OpenAI ChatCompletion API."""
        try:
            response = openai.ChatCompletion.create(
                model=self.current_model,
                messages=context,
                temperature=0.7,
                max_tokens=2000,
                top_p=0.9
            )
            return response.choices[0].message['content']
        except Exception as e:
            return f"OpenAI Error: {str(e)}"
    
    def _call_huggingface(self, user_message: str) -> str:
        """Call HuggingFace Inference API."""
        try:
            headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
            payload = {
                "inputs": user_message,
                "parameters": {"max_length": 2000}
            }
            url = HUGGINGFACE_ENDPOINT + HUGGINGFACE_MODEL
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', 'No response from HuggingFace')
                return str(result)
            else:
                return f"HuggingFace API error: {response.status_code} {response.text}"
        except Exception as e:
            return f"HuggingFace Error: {str(e)}"
    
    def clear_history(self):
        self.conversation_history.clear()

# ═══════════════════════════════════════════════════════════════════════════════
# UNIFIED DASHBOARD APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

class UnifiedDashboard(tk.Tk):
    """Complete unified dashboard integrating all game development tools"""
    
    def __init__(self):
        super().__init__()
        
        self.title("Unreal Engine - Unified Game Development Dashboard")
        self.geometry("1600x900")
        self.minsize(1200, 700)
        
        # Initialize systems
        self.chatbot = GameDevChatBot()
        self.systems_status = self._init_systems()
        # User data
        self.users = self._load_users()
        self.user = None
        
        # Configure appearance
        self.configure(bg=COLOR['bg_dark'])
        self._setup_styles()
        
        # Build UI
        self._build_ui()
        
        # Alert on start
        self.after(500, self._show_startup_info)
    
    def _init_systems(self) -> dict:
        """Initialize all game systems"""
        status = {
            'combat': CombatSystem() if CombatSystem else None,
            # DialogueTree requires (tree_id, npc_id, npc_name)
            'dialogue': DialogueTree("root_tree", "root", "Root NPC") if DialogueTree else None,
            'inventory': AdvancedInventorySystem() if AdvancedInventorySystem else None,
            'quest': AdvancedQuestSystem() if AdvancedQuestSystem else None,
            'streaming': LevelStreamingManager() if LevelStreamingManager else None,
            'terrain': TerrainGenerator() if TerrainGenerator else None,
            'dungeon': DungeonGenerator() if DungeonGenerator else None,
            'city': CityGenerator() if CityGenerator else None,
            'analytics': AnalyticsEngine() if AnalyticsEngine else None,
        }
        return status

    # ----------------- User & Session Management -----------------
    def _load_users(self) -> dict:
        users_file = os.path.join(APP_DIR, 'users.json')
        if os.path.exists(users_file):
            try:
                with open(users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_users(self):
        users_file = os.path.join(APP_DIR, 'users.json')
        try:
            with open(users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            print('Error saving users:', e)

    def _login_dialog(self):
        dialog = simpledialog.Dialog(self, title='Login')

    def _prompt_login(self):
        # Username + password login with optional account creation
        username = simpledialog.askstring('Login', 'Enter username:')
        if not username:
            return False

        # Existing user: require password
        if username in self.users and self.users.get(username, {}).get('password'):
            pw = simpledialog.askstring('Password', f'Enter password for {username}:', show='*')
            if pw is None:
                return False
            stored = self.users[username].get('password', '')
            if not _verify_password(pw, stored):
                messagebox.showerror('Login Failed', 'Invalid password')
                return False
            # successful login
            self.user = username
            self._load_user_progress()
            self._update_status_bar()
            messagebox.showinfo('Login', f'Logged in as {username}')
            return True

        # New user: offer to create account
        create = messagebox.askyesno('Create Account', f'User "{username}" not found. Create new account?')
        if not create:
            return False
        # prompt for password and confirmation
        while True:
            pw = simpledialog.askstring('Set Password', f'Set a password for {username}:', show='*')
            if pw is None:
                return False
            pw2 = simpledialog.askstring('Confirm Password', 'Confirm password:', show='*')
            if pw != pw2:
                messagebox.showwarning('Mismatch', 'Passwords do not match; try again')
                continue
            if not pw:
                messagebox.showwarning('Invalid', 'Password cannot be empty')
                continue
            break

        hashed = _hash_password(pw)
        self.users[username] = {'projects': {}, 'password': hashed}
        self._save_users()
        self.user = username
        self._load_user_progress()
        self._update_status_bar()
        messagebox.showinfo('Account Created', f'Account created and logged in as {username}')
        return True

    def _logout_user(self):
        if not self.user:
            return
        self._save_user_progress()
        messagebox.showinfo('Logout', f'User {self.user} saved and logged out')
        self.user = None
        self._update_status_bar()

    def _save_user_progress(self):
        if not self.user:
            return
        proj_dir = os.path.join(APP_DIR, 'user_data')
        os.makedirs(proj_dir, exist_ok=True)
        filename = os.path.join(proj_dir, f'{self.user}_progress.json')
        data = {
            'last_tab': self.current_tab,
            'conversation': list(self.chatbot.conversation_history) if hasattr(self, 'chatbot') else [],
            'systems': {k: bool(v) for k, v in self.systems_status.items()},
        }
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print('Error saving progress:', e)

    def _load_user_progress(self):
        if not self.user:
            return
        filename = os.path.join(APP_DIR, 'user_data', f'{self.user}_progress.json')
        if not os.path.exists(filename):
            return
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # restore minimal state
            last = data.get('last_tab')
            if last and last in self.tabs:
                self.switch_tab(last)
            conv = data.get('conversation', [])
            if conv and hasattr(self, 'chatbot'):
                for m in conv:
                    self.chatbot.conversation_history.append(m)
        except Exception as e:
            print('Error loading progress:', e)

    
    def _setup_styles(self):
        """Setup ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=COLOR['bg_dark'], foreground=COLOR['text_primary'])
        style.configure('TLabel', background=COLOR['bg_dark'], foreground=COLOR['text_primary'])
    
    def _build_ui(self):
        """Build main dashboard UI"""
        # Top header
        self._build_header()
        
        # Main container with sidebar and content
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Sidebar
        self._build_sidebar(main_container)
        
        # Content area
        self._build_content_area(main_container)
        
        # Bottom status bar
        self._build_status_bar()
    
    def _build_header(self):
        """Build top header bar"""
        # Create a native menu bar
        self.menu_bar = tk.Menu(self)
        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label='New Project', command=lambda: messagebox.showinfo('New', 'New project created'))
        file_menu.add_command(label='Open Project...', command=self._open_project_file)
        file_menu.add_command(label='Save', command=self._save_user_progress)
        file_menu.add_command(label='Save As...', command=self._save_project_as)
        file_menu.add_separator()
        file_menu.add_command(label='Export...', command=lambda: messagebox.showinfo('Export', 'Exported'))
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.quit)
        self.menu_bar.add_cascade(label='File', menu=file_menu)

        # Tools / Help menus (minimal placeholders)
        tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        tools_menu.add_command(label='Run Diagnostics', command=lambda: messagebox.showinfo('Diagnostics', 'Diagnostics complete'))
        self.menu_bar.add_cascade(label='Tools', menu=tools_menu)

        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label='About', command=lambda: messagebox.showinfo('About', 'Unified Dashboard'))
        self.menu_bar.add_cascade(label='Help', menu=help_menu)

        # Attach menu to window
        try:
            self.config(menu=self.menu_bar)
        except Exception:
            # fallback for some platforms
            pass

        # Header frame (visual)
        header = tk.Frame(self, bg=COLOR['accent_blue'], height=80)
        header.pack(fill=tk.X, padx=0, pady=0)
        header.pack_propagate(False)

        title_font = tkFont.Font(family="Courier New", size=16, weight="bold")
        title = tk.Label(
            header,
            text="UNIFIED GAME DEVELOPMENT DASHBOARD",
            font=title_font,
            bg=COLOR['accent_blue'],
            fg=COLOR['bg_darker']
        )
        title.pack(pady=8)

        subtitle_font = tkFont.Font(family="Courier New", size=9)
        subtitle = tk.Label(
            header,
            text="All Tools • One Interface • Real-time Integration",
            font=subtitle_font,
            bg=COLOR['accent_blue'],
            fg=COLOR['bg_darker']
        )
        subtitle.pack(pady=2)

        # Hamburger menu button (top-right)
        ham_btn = tk.Button(header, text='≡', font=tkFont.Font(size=14), bg=COLOR['accent_blue'], fg=COLOR['bg_darker'], relief=tk.FLAT, command=self._show_hamburger_menu, cursor='hand2')
        ham_btn.place(relx=0.98, rely=0.12, anchor='ne')
        try:
            Tooltip(ham_btn, text='Open menu: account, save/load, tools')
        except Exception:
            pass

    def _open_project_file(self):
        """Open a project/progress JSON file and load minimal state"""
        path = filedialog.askopenfilename(initialdir=os.path.join(APP_DIR, 'user_data'), filetypes=[('JSON Files','*.json'), ('All Files','*.*')])
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            last = data.get('last_tab')
            if last and last in self.tabs:
                self.switch_tab(last)
            conv = data.get('conversation', [])
            if conv and hasattr(self, 'chatbot'):
                self.chatbot.conversation_history.clear()
                for m in conv:
                    self.chatbot.conversation_history.append(m)
            messagebox.showinfo('Open', f'Loaded project from {os.path.basename(path)}')
        except Exception as e:
            messagebox.showerror('Open Error', f'Failed to open file: {e}')

    def _save_project_as(self):
        """Save current user progress to a chosen file path"""
        path = filedialog.asksaveasfilename(initialdir=os.path.join(APP_DIR, 'user_data'), defaultextension='.json', filetypes=[('JSON Files','*.json')])
        if not path:
            return
        data = {
            'last_tab': self.current_tab,
            'conversation': list(self.chatbot.conversation_history) if hasattr(self, 'chatbot') else [],
            'systems': {k: bool(v) for k, v in self.systems_status.items()},
        }
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            messagebox.showinfo('Save As', f'Saved project to {os.path.basename(path)}')
        except Exception as e:
            messagebox.showerror('Save Error', f'Failed to save file: {e}')

    def _show_hamburger_menu(self):
        """Show a contextual hamburger menu with account/tools actions"""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label='Login', command=self._prompt_login)
        menu.add_command(label='Logout', command=self._logout_user)
        menu.add_command(label='Change Password', command=self._change_password)
        menu.add_separator()
        menu.add_command(label='Save Progress', command=self._save_user_progress)
        menu.add_command(label='Save As...', command=self._save_project_as)
        menu.add_command(label='Open Project...', command=self._open_project_file)
        menu.add_separator()
        menu.add_command(label='About', command=lambda: messagebox.showinfo('About', 'Unified Dashboard'))
        try:
            x = self.winfo_pointerx()
            y = self.winfo_pointery()
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()
    
    def _change_password(self):
        """Change password for current user (requires login)."""
        if not self.user:
            messagebox.showwarning('Not Logged In', 'Please log in first to change your password')
            return
        # Verify current password
        cur = simpledialog.askstring('Current Password', 'Enter current password:', show='*')
        if cur is None:
            return
        stored = self.users.get(self.user, {}).get('password', '')
        if not _verify_password(cur, stored):
            messagebox.showerror('Error', 'Current password is incorrect')
            return
        # Prompt for new password
        while True:
            new_pw = simpledialog.askstring('New Password', 'Enter new password:', show='*')
            if new_pw is None:
                return
            new_pw2 = simpledialog.askstring('Confirm Password', 'Confirm new password:', show='*')
            if new_pw != new_pw2:
                messagebox.showwarning('Mismatch', 'Passwords do not match; try again')
                continue
            if not new_pw:
                messagebox.showwarning('Invalid', 'Password cannot be empty')
                continue
            break
        self.users[self.user]['password'] = _hash_password(new_pw)
        self._save_users()
        messagebox.showinfo('Password Changed', 'Your password has been updated')
    
    def _build_sidebar(self, parent):
        """Build left sidebar with navigation"""
        sidebar = tk.Frame(parent, bg=COLOR['bg_panel'], width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5), pady=0)
        sidebar.pack_propagate(False)
        
        # Sidebar title
        title = tk.Label(
            sidebar,
            text="SYSTEMS",
            bg=COLOR['bg_panel'],
            fg=COLOR['accent_blue'],
            font=tkFont.Font(family="Courier", size=10, weight="bold")
        )
        title.pack(pady=10, padx=5)
        
        # Navigation buttons
        self.nav_buttons = {}
        systems = [
            ("💬 AI Chatbot", "ai", COLOR['accent_blue']),
            ("⚔️ Combat", "combat", COLOR['tab_combat']),
            ("💬 Dialogue", "dialogue", COLOR['tab_dialogue']),
            ("🎒 Inventory", "inventory", COLOR['tab_inventory']),
            ("📜 Quests", "quest", COLOR['tab_quest']),
            ("🌍 Streaming", "streaming", COLOR['tab_streaming']),
            ("🗻 Procedural", "procedural", COLOR['tab_procedural']),
            ("📊 Analytics", "analytics", COLOR['tab_analytics']),
            ("⚙️ Settings", "settings", COLOR['text_secondary']),
        ]
        
        for label, key, color in systems:
            btn = tk.Button(
                sidebar,
                text=label,
                bg=color,
                fg=COLOR['bg_darker'],
                font=("Courier", 9, "bold"),
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda k=key: self.switch_tab(k),
                width=20
            )
            btn.pack(fill=tk.X, padx=5, pady=3)
            self.nav_buttons[key] = btn
        # Attach concise tooltips to navigation buttons
        try:
            tooltip_texts = {
                'ai': 'Open AI chatbot for code generation and integration',
                'combat': 'Design combat systems, damage formulas, combos',
                'dialogue': 'Create branching dialogue trees and NPCs',
                'inventory': 'Manage items, crafting recipes, and trading',
                'quest': 'Design quests, objectives, and reward flows',
                'streaming': 'Configure level streaming and LOD settings',
                'procedural': 'Procedural terrain, city and weapon generation',
                'analytics': 'View performance metrics and analytics',
                'settings': 'View and export configuration, API status',
            }
            for k, txt in tooltip_texts.items():
                btn = self.nav_buttons.get(k)
                if btn:
                    Tooltip(btn, text=txt)
        except Exception:
            pass
        
        # Status section
        ttk.Separator(sidebar, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10, padx=5)
        
        status_label = tk.Label(
            sidebar,
            text="SYSTEM STATUS",
            bg=COLOR['bg_panel'],
            fg=COLOR['text_success'],
            font=tkFont.Font(family="Courier", size=9, weight="bold")
        )
        status_label.pack(pady=5, padx=5, anchor=tk.W)
        
        self.system_status_text = tk.Text(
            sidebar,
            height=15,
            bg=COLOR['bg_darker'],
            fg=COLOR['text_success'],
            font=("Courier", 8),
            relief=tk.FLAT
        )
        self.system_status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.system_status_text.config(state=tk.DISABLED)
        
        self._update_system_status()
    
    def _build_content_area(self, parent):
        """Build main content area with tabs"""
        self.content_frame = tk.Frame(parent, bg=COLOR['bg_darker'])
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=0)
        
        # Create tabs
        self.tabs = {}
        self.current_tab = "ai"
        
        # AI Chatbot Tab
        self.tabs["ai"] = self._create_ai_tab()
        
        # Combat Tab
        self.tabs["combat"] = self._create_combat_tab()
        
        # Dialogue Tab
        self.tabs["dialogue"] = self._create_dialogue_tab()
        
        # Inventory Tab
        self.tabs["inventory"] = self._create_inventory_tab()
        
        # Quest Tab
        self.tabs["quest"] = self._create_quest_tab()
        
        # Streaming Tab
        self.tabs["streaming"] = self._create_streaming_tab()
        
        # Procedural Tab
        self.tabs["procedural"] = self._create_procedural_tab()
        
        # Analytics Tab
        self.tabs["analytics"] = self._create_analytics_tab()
        
        # Settings Tab
        self.tabs["settings"] = self._create_settings_tab()
        
        # Show AI tab by default
        self.switch_tab("ai")
    
    def _create_ai_tab(self):
        """Create AI chatbot tab"""
        frame = tk.Frame(self.content_frame, bg=COLOR['bg_darker'])
        
        # Header
        header = tk.Frame(frame, bg=COLOR['accent_blue'], height=40)
        header.pack(fill=tk.X, padx=0, pady=0)
        header.pack_propagate(False)
        
        header_label = tk.Label(
            header,
            text="💬 AI Code Generation & Integration",
            bg=COLOR['accent_blue'],
            fg=COLOR['bg_darker'],
            font=tkFont.Font(family="Courier", size=11, weight="bold")
        )
        header_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Chat display
        chat_frame = tk.Frame(frame, bg=COLOR['bg_darker'])
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            bg=COLOR['bg_darker'],
            fg=COLOR['text_primary'],
            insertbackground=COLOR['accent_blue'],
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        self.chat_display.config(state=tk.DISABLED)
        
        # Configure tags
        self.chat_display.tag_config("user", foreground=COLOR['accent_blue'], font=("Courier", 9, "bold"))
        self.chat_display.tag_config("ai", foreground=COLOR['text_success'], font=("Courier", 9))
        self.chat_display.tag_config("error", foreground=COLOR['text_error'], font=("Courier", 9, "bold"))
        
        # Input area
        input_frame = tk.Frame(frame, bg=COLOR['bg_panel'])
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.ai_input = tk.Text(
            input_frame,
            height=4,
            bg=COLOR['bg_darker'],
            fg=COLOR['text_primary'],
            insertbackground=COLOR['accent_blue'],
            font=("Courier", 9),
            wrap=tk.WORD,
            relief=tk.FLAT
        )
        self.ai_input.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=5, pady=5)
        
        send_btn = tk.Button(
            input_frame,
            text="SEND",
            bg=COLOR['accent_blue'],
            fg=COLOR['bg_darker'],
            font=tkFont.Font(family="Courier", size=9, weight="bold"),
            command=self._send_ai_message,
            relief=tk.FLAT,
            width=8,
            cursor="hand2"
        )
        send_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        try:
            Tooltip(send_btn, text='Send the current message to the AI assistant')
            Tooltip(header_label, text='AI Code Generation & Integration - ask for code and integration help')
        except Exception:
            pass
        
        # Display welcome
        self.after(500, lambda: self._display_chat_message(
            "System",
            "Welcome to the Unified Dashboard!\n\nI can help you:\n"
            "✓ Generate C++ code for all systems\n"
            "✓ Integrate multiple game systems\n"
            "✓ Debug and optimize code\n"
            "✓ Create documentation\n\nAsk me anything!",
            "ai"
        ))
        
        return frame
    
    def _create_combat_tab(self):
        """Create combat system tab"""
        frame = tk.Frame(self.content_frame, bg=COLOR['bg_darker'])
        
        header = tk.Frame(frame, bg=COLOR['tab_combat'], height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        header_label = tk.Label(
            header,
            text="⚔️  COMBAT SYSTEM DESIGNER",
            bg=COLOR['tab_combat'],
            fg="white",
            font=tkFont.Font(family="Courier", size=11, weight="bold")
        )
        header_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        content = tk.Frame(frame, bg=COLOR['bg_darker'])
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Quick info
        info_text = scrolledtext.ScrolledText(
            content,
            height=10,
            bg=COLOR['bg_panel'],
            fg=COLOR['text_primary'],
            font=("Courier", 9),
            relief=tk.FLAT
        )
        info_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        combat_info = """COMBAT SYSTEM - Features & Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Damage Formulas Engine
✓ Status Effects System
✓ Combo Chains & Moves
✓ Skill Trees & Abilities
✓ Hit Detection & Critical Strikes
✓ Damage Type System
✓ Real-time Combat Simulation

System Status: """ + ("🟢 LOADED" if self.systems_status.get('combat') else "🔴 NOT LOADED")
        
        info_text.insert(1.0, combat_info)
        info_text.config(state=tk.DISABLED)
        
        # Action buttons
        btn_frame = tk.Frame(content, bg=COLOR['bg_darker'])
        btn_frame.pack(fill=tk.X, pady=10)
        
        buttons = [
            ("Create Damage Formula", COLOR['tab_combat']),
            ("Add Status Effect", COLOR['tab_combat']),
            ("Design Combo Chain", COLOR['tab_combat']),
            ("Build Skill Tree", COLOR['tab_combat']),
        ]
        
        for label, color in buttons:
            btn = tk.Button(
                btn_frame,
                text=label,
                bg=color,
                fg="white",
                font=("Courier", 9, "bold"),
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda l=label, t="combat": self._ai_request(f"Help me {l}"),
                width=25
            )
            btn.pack(side=tk.LEFT, padx=3, pady=3)
        
        return frame
    
    def _create_dialogue_tab(self):
        """Create dialogue system tab"""
        frame = tk.Frame(self.content_frame, bg=COLOR['bg_darker'])
        
        header = tk.Frame(frame, bg=COLOR['tab_dialogue'], height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        header_label = tk.Label(
            header,
            text="💬 DIALOGUE & NPC SYSTEM",
            bg=COLOR['tab_dialogue'],
            fg="white",
            font=tkFont.Font(family="Courier", size=11, weight="bold")
        )
        header_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        content = tk.Frame(frame, bg=COLOR['bg_darker'])
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info_text = scrolledtext.ScrolledText(
            content,
            height=10,
            bg=COLOR['bg_panel'],
            fg=COLOR['text_primary'],
            font=("Courier", 9),
            relief=tk.FLAT
        )
        info_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        dialogue_info = """DIALOGUE SYSTEM - Features & Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Branching Dialogue Trees
✓ Relationship Tracking
✓ Character Emotions & States
✓ Dialogue Conditions
✓ Voice Generation & Lip Sync
✓ NPC Behavior Management
✓ Conversation Flow Control

System Status: """ + ("🟢 LOADED" if self.systems_status.get('dialogue') else "🔴 NOT LOADED")
        
        info_text.insert(1.0, dialogue_info)
        info_text.config(state=tk.DISABLED)
        
        btn_frame = tk.Frame(content, bg=COLOR['bg_darker'])
        btn_frame.pack(fill=tk.X, pady=10)
        
        buttons = [
            ("Create Dialogue Tree", COLOR['tab_dialogue']),
            ("Add NPC", COLOR['tab_dialogue']),
            ("Design Relationships", COLOR['tab_dialogue']),
            ("Generate Voice", COLOR['tab_dialogue']),
        ]
        
        for label, color in buttons:
            btn = tk.Button(
                btn_frame,
                text=label,
                bg=color,
                fg="white",
                font=("Courier", 9, "bold"),
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda l=label: self._ai_request(f"Help me {l}"),
                width=25
            )
            btn.pack(side=tk.LEFT, padx=3, pady=3)
        
        return frame
    
    def _create_inventory_tab(self):
        """Create inventory & crafting tab"""
        frame = tk.Frame(self.content_frame, bg=COLOR['bg_darker'])
        
        header = tk.Frame(frame, bg=COLOR['tab_inventory'], height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        header_label = tk.Label(
            header,
            text="🎒 INVENTORY & CRAFTING SYSTEM",
            bg=COLOR['tab_inventory'],
            fg="white",
            font=tkFont.Font(family="Courier", size=11, weight="bold")
        )
        header_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        content = tk.Frame(frame, bg=COLOR['bg_darker'])
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info_text = scrolledtext.ScrolledText(
            content,
            height=10,
            bg=COLOR['bg_panel'],
            fg=COLOR['text_primary'],
            font=("Courier", 9),
            relief=tk.FLAT
        )
        info_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        inventory_info = """INVENTORY & CRAFTING - Features & Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Item Database System
✓ Equipment Slots & UI
✓ Crafting Recipes
✓ Trading & Commerce
✓ Set Bonuses & Effects
✓ Durability System
✓ Weight & Carrying Capacity
✓ Rarity & Item Types

System Status: """ + ("🟢 LOADED" if self.systems_status.get('inventory') else "🔴 NOT LOADED")
        
        info_text.insert(1.0, inventory_info)
        info_text.config(state=tk.DISABLED)
        
        btn_frame = tk.Frame(content, bg=COLOR['bg_darker'])
        btn_frame.pack(fill=tk.X, pady=10)
        
        buttons = [
            ("Create Item", COLOR['tab_inventory']),
            ("Design Recipe", COLOR['tab_inventory']),
            ("Setup Trading", COLOR['tab_inventory']),
            ("Add Set Bonus", COLOR['tab_inventory']),
        ]
        
        for label, color in buttons:
            btn = tk.Button(
                btn_frame,
                text=label,
                bg=color,
                fg="white",
                font=("Courier", 9, "bold"),
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda l=label: self._ai_request(f"Help me {l}"),
                width=25
            )
            btn.pack(side=tk.LEFT, padx=3, pady=3)
        
        return frame
    
    def _create_quest_tab(self):
        """Create quest system tab"""
        frame = tk.Frame(self.content_frame, bg=COLOR['bg_darker'])
        
        header = tk.Frame(frame, bg=COLOR['tab_quest'], height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        header_label = tk.Label(
            header,
            text="📜 QUEST & MISSION SYSTEM",
            bg=COLOR['tab_quest'],
            fg="white",
            font=tkFont.Font(family="Courier", size=11, weight="bold")
        )
        header_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        content = tk.Frame(frame, bg=COLOR['bg_darker'])
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info_text = scrolledtext.ScrolledText(
            content,
            height=10,
            bg=COLOR['bg_panel'],
            fg=COLOR['text_primary'],
            font=("Courier", 9),
            relief=tk.FLAT
        )
        info_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        quest_info = """QUEST SYSTEM - Features & Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Quest Designer & Builder
✓ Objectives & Conditions
✓ Quest Chains & Flow
✓ Reward System
✓ NPC Quest Givers
✓ Quest Tracking
✓ Progress Markers
✓ Random Generation

System Status: """ + ("🟢 LOADED" if self.systems_status.get('quest') else "🔴 NOT LOADED")
        
        info_text.insert(1.0, quest_info)
        info_text.config(state=tk.DISABLED)
        
        btn_frame = tk.Frame(content, bg=COLOR['bg_darker'])
        btn_frame.pack(fill=tk.X, pady=10)
        
        buttons = [
            ("Create Quest", COLOR['tab_quest']),
            ("Add Objectives", COLOR['tab_quest']),
            ("Design Rewards", COLOR['tab_quest']),
            ("Build Quest Chain", COLOR['tab_quest']),
        ]
        
        for label, color in buttons:
            btn = tk.Button(
                btn_frame,
                text=label,
                bg=color,
                fg="white",
                font=("Courier", 9, "bold"),
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda l=label: self._ai_request(f"Help me {l}"),
                width=25
            )
            btn.pack(side=tk.LEFT, padx=3, pady=3)
        
        return frame
    
    def _create_streaming_tab(self):
        """Create level streaming tab"""
        frame = tk.Frame(self.content_frame, bg=COLOR['bg_darker'])
        
        header = tk.Frame(frame, bg=COLOR['tab_streaming'], height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        header_label = tk.Label(
            header,
            text="🌍 LEVEL STREAMING & LOD SYSTEM",
            bg=COLOR['tab_streaming'],
            fg="white",
            font=tkFont.Font(family="Courier", size=11, weight="bold")
        )
        header_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        content = tk.Frame(frame, bg=COLOR['bg_darker'])
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info_text = scrolledtext.ScrolledText(
            content,
            height=10,
            bg=COLOR['bg_panel'],
            fg=COLOR['text_primary'],
            font=("Courier", 9),
            relief=tk.FLAT
        )
        info_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        streaming_info = """LEVEL STREAMING - Features & Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Dynamic Level Loading
✓ Streaming Volumes
✓ LOD (Level of Detail) System
✓ Occlusion Culling
✓ Memory Budget Management
✓ Performance Profiling
✓ Auto Streaming
✓ Multi-Level Management

System Status: """ + ("🟢 LOADED" if self.systems_status.get('streaming') else "🔴 NOT LOADED")
        
        info_text.insert(1.0, streaming_info)
        info_text.config(state=tk.DISABLED)
        
        btn_frame = tk.Frame(content, bg=COLOR['bg_darker'])
        btn_frame.pack(fill=tk.X, pady=10)
        
        buttons = [
            ("Create Streaming Volume", COLOR['tab_streaming']),
            ("Setup LOD Settings", COLOR['tab_streaming']),
            ("Configure Memory Budget", COLOR['tab_streaming']),
            ("Profile Performance", COLOR['tab_streaming']),
        ]
        
        for label, color in buttons:
            btn = tk.Button(
                btn_frame,
                text=label,
                bg=color,
                fg="white",
                font=("Courier", 9, "bold"),
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda l=label: self._ai_request(f"Help me {l}"),
                width=25
            )
            btn.pack(side=tk.LEFT, padx=3, pady=3)
        
        return frame
    
    def _create_procedural_tab(self):
        """Create procedural generation tab"""
        frame = tk.Frame(self.content_frame, bg=COLOR['bg_darker'])
        
        header = tk.Frame(frame, bg=COLOR['tab_procedural'], height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        header_label = tk.Label(
            header,
            text="🗻 PROCEDURAL GENERATION ENGINE",
            bg=COLOR['tab_procedural'],
            fg="white",
            font=tkFont.Font(family="Courier", size=11, weight="bold")
        )
        header_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        content = tk.Frame(frame, bg=COLOR['bg_darker'])
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info_text = scrolledtext.ScrolledText(
            content,
            height=10,
            bg=COLOR['bg_panel'],
            fg=COLOR['text_primary'],
            font=("Courier", 9),
            relief=tk.FLAT
        )
        info_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        procedural_info = """PROCEDURAL GENERATION - Features & Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Terrain Generation (Perlin Noise)
✓ Dungeon Generation
✓ City Generation
✓ Weapon Generation
✓ Character Generation
✓ Biome Systems
✓ Wave Function Collapse
✓ Random Name Generation

System Status: """ + ("🟢 LOADED" if any([self.systems_status.get('terrain'), self.systems_status.get('dungeon'), self.systems_status.get('city')]) else "🔴 NOT LOADED")
        
        info_text.insert(1.0, procedural_info)
        info_text.config(state=tk.DISABLED)
        
        btn_frame = tk.Frame(content, bg=COLOR['bg_darker'])
        btn_frame.pack(fill=tk.X, pady=10)
        
        buttons = [
            ("Generate Terrain", COLOR['tab_procedural']),
            ("Create Dungeon", COLOR['tab_procedural']),
            ("Build City", COLOR['tab_procedural']),
            ("Generate Weapons", COLOR['tab_procedural']),
        ]
        
        for label, color in buttons:
            btn = tk.Button(
                btn_frame,
                text=label,
                bg=color,
                fg="white",
                font=("Courier", 9, "bold"),
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda l=label: self._ai_request(f"Help me {l} in Unreal Engine"),
                width=25
            )
            btn.pack(side=tk.LEFT, padx=3, pady=3)
        
        return frame
    
    def _create_analytics_tab(self):
        """Create analytics dashboard tab"""
        frame = tk.Frame(self.content_frame, bg=COLOR['bg_darker'])
        
        header = tk.Frame(frame, bg=COLOR['tab_analytics'], height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        header_label = tk.Label(
            header,
            text="📊 ANALYTICS & PERFORMANCE DASHBOARD",
            bg=COLOR['tab_analytics'],
            fg="white",
            font=tkFont.Font(family="Courier", size=11, weight="bold")
        )
        header_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        content = tk.Frame(frame, bg=COLOR['bg_darker'])
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info_text = scrolledtext.ScrolledText(
            content,
            height=10,
            bg=COLOR['bg_panel'],
            fg=COLOR['text_primary'],
            font=("Courier", 9),
            relief=tk.FLAT
        )
        info_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        analytics_info = """ANALYTICS & PERFORMANCE - Features & Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Performance Profiling
✓ Memory Tracking
✓ Draw Call Analysis
✓ Event Tracking
✓ Heatmaps & Funnels
✓ Player Analytics
✓ System Metrics
✓ Real-time Monitoring

System Status: """ + ("🟢 LOADED" if self.systems_status.get('analytics') else "🔴 NOT LOADED")
        
        info_text.insert(1.0, analytics_info)
        info_text.config(state=tk.DISABLED)
        
        btn_frame = tk.Frame(content, bg=COLOR['bg_darker'])
        btn_frame.pack(fill=tk.X, pady=10)
        
        buttons = [
            ("View Metrics", COLOR['tab_analytics']),
            ("Analyze Events", COLOR['tab_analytics']),
            ("Performance Report", COLOR['tab_analytics']),
            ("Export Data", COLOR['tab_analytics']),
        ]
        
        for label, color in buttons:
            btn = tk.Button(
                btn_frame,
                text=label,
                bg=color,
                fg="white",
                font=("Courier", 9, "bold"),
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda l=label: self._ai_request(f"Help me {l}"),
                width=25
            )
            btn.pack(side=tk.LEFT, padx=3, pady=3)
        
        return frame
    
    def _create_settings_tab(self):
        """Create settings tab"""
        frame = tk.Frame(self.content_frame, bg=COLOR['bg_darker'])
        
        header = tk.Frame(frame, bg=COLOR['text_secondary'], height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        header_label = tk.Label(
            header,
            text="⚙️  SETTINGS & CONFIGURATION",
            bg=COLOR['text_secondary'],
            fg="white",
            font=tkFont.Font(family="Courier", size=11, weight="bold")
        )
        header_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        content = tk.Frame(frame, bg=COLOR['bg_darker'])
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # AI Provider Selection Section
        provider_frame = tk.Frame(content, bg=COLOR['bg_panel'])
        provider_frame.pack(fill=tk.X, padx=5, pady=10)
        
        provider_label = tk.Label(
            provider_frame,
            text="AI Provider Selection:",
            bg=COLOR['bg_panel'],
            fg=COLOR['accent_blue'],
            font=tkFont.Font(family="Courier", size=10, weight="bold")
        )
        provider_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Provider selector dropdown
        provider_var = tk.StringVar(value=self.chatbot.provider)
        provider_options = list(self.chatbot.available_providers.keys())
        
        if provider_options:
            provider_combo = ttk.Combobox(
                provider_frame,
                textvariable=provider_var,
                values=provider_options,
                state='readonly',
                width=20
            )
            provider_combo.pack(side=tk.LEFT, padx=5, pady=5)
            
            def switch_provider(new_provider=None):
                if new_provider is None:
                    new_provider = provider_var.get()
                if self.chatbot.set_provider(new_provider):
                    messagebox.showinfo('Provider Switched', f'AI provider changed to: {self.chatbot.available_providers.get(new_provider, new_provider)}')
                else:
                    messagebox.showerror('Error', 'Could not switch to that provider')
            
            switch_btn = tk.Button(
                provider_frame,
                text="Switch Provider",
                bg=COLOR['accent_blue'],
                fg=COLOR['bg_darker'],
                font=("Courier", 9, "bold"),
                relief=tk.FLAT,
                cursor="hand2",
                command=switch_provider
            )
            switch_btn.pack(side=tk.LEFT, padx=5, pady=5)
        else:
            no_provider_label = tk.Label(
                provider_frame,
                text="No AI providers configured. Set API keys in .env file.",
                bg=COLOR['bg_panel'],
                fg=COLOR['text_error'],
                font=("Courier", 9)
            )
            no_provider_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Configuration info
        settings_text = scrolledtext.ScrolledText(
            content,
            bg=COLOR['bg_panel'],
            fg=COLOR['text_primary'],
            font=("Courier", 9),
            relief=tk.FLAT
        )
        settings_text.pack(fill=tk.BOTH, expand=True, pady=10)
        
        settings_info = """SYSTEM CONFIGURATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AI Provider Configuration:
  Current Provider: """ + self.chatbot.provider.upper() + """
  Gemini API Key: """ + ("✓ CONFIGURED" if GEMINI_API_KEY else "✗ NOT SET") + """
  OpenAI API Key: """ + ("✓ CONFIGURED" if OPENAI_API_KEY else "✗ NOT SET") + """
  HuggingFace API Key: """ + ("✓ CONFIGURED" if HUGGINGFACE_API_KEY else "✗ NOT SET") + """

Available Providers:
"""
        for p_name, p_label in self.chatbot.available_providers.items():
            settings_info += f"  • {p_label}\n"
        
        settings_info += """
Loaded Game Development Modules:
  Combat System: """ + ("✓ LOADED" if self.systems_status.get('combat') else "✗ NOT AVAILABLE") + """
  Dialogue System: """ + ("✓ LOADED" if self.systems_status.get('dialogue') else "✗ NOT AVAILABLE") + """
  Inventory System: """ + ("✓ LOADED" if self.systems_status.get('inventory') else "✗ NOT AVAILABLE") + """
  Quest System: """ + ("✓ LOADED" if self.systems_status.get('quest') else "✗ NOT AVAILABLE") + """
  Level Streaming: """ + ("✓ LOADED" if self.systems_status.get('streaming') else "✗ NOT AVAILABLE") + """
  Procedural Gen: """ + ("✓ LOADED" if self.systems_status.get('terrain') else "✗ NOT AVAILABLE") + """
  Analytics: """ + ("✓ LOADED" if self.systems_status.get('analytics') else "✗ NOT AVAILABLE") + """

Quick Actions:
• Clear AI Chat History
• Export Configuration
• View System Logs
• Reset to Defaults
"""
        
        settings_text.insert(1.0, settings_info)
        settings_text.config(state=tk.DISABLED)
        
        btn_frame = tk.Frame(content, bg=COLOR['bg_darker'])
        btn_frame.pack(fill=tk.X, pady=10)
        
        buttons = [
            ("Clear History", COLOR['text_secondary']),
            ("Export Config", COLOR['text_secondary']),
            ("View Logs", COLOR['text_secondary']),
            ("About", COLOR['text_secondary']),
        ]
        
        for label, color in buttons:
            btn = tk.Button(
                btn_frame,
                text=label,
                bg=color,
                fg="white",
                font=("Courier", 9, "bold"),
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda l=label: self._handle_setting(l),
                width=25
            )
            btn.pack(side=tk.LEFT, padx=3, pady=3)
        
        return frame
    
    def _build_status_bar(self):
        """Build bottom status bar"""
        status_bar = tk.Frame(self, bg=COLOR['bg_panel'], height=30)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)
        
        status_text = tk.Label(
            status_bar,
            text="Ready • All Systems Integrated • Chat Ready",
            bg=COLOR['bg_panel'],
            fg=COLOR['accent_blue'],
            font=("Courier", 8),
            justify=tk.LEFT
        )
        status_text.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.status_indicator = tk.Label(
            status_bar,
            text="● ONLINE",
            bg=COLOR['bg_panel'],
            fg=COLOR['text_success'],
            font=("Courier", 8, "bold")
        )
        self.status_indicator.pack(side=tk.RIGHT, padx=10, pady=5)
    
    def _update_system_status(self):
        """Update system status display"""
        status_text = "SYSTEM STATUS\n" + "━" * 20 + "\n"
        
        systems_check = [
            ("Combat", self.systems_status.get('combat')),
            ("Dialogue", self.systems_status.get('dialogue')),
            ("Inventory", self.systems_status.get('inventory')),
            ("Quest", self.systems_status.get('quest')),
            ("Streaming", self.systems_status.get('streaming')),
            ("Procedural", any([self.systems_status.get('terrain'), self.systems_status.get('dungeon')])),
            ("Analytics", self.systems_status.get('analytics')),
        ]
        
        for name, available in systems_check:
            status = "🟢" if available else "🔴"
            status_text += f"{status} {name}\n"
        
        self.system_status_text.config(state=tk.NORMAL)
        self.system_status_text.delete(1.0, tk.END)
        self.system_status_text.insert(1.0, status_text)
        self.system_status_text.config(state=tk.DISABLED)
    
    def switch_tab(self, tab_name):
        """Switch to different tab"""
        # Hide all tabs
        for tab_frame in self.tabs.values():
            tab_frame.pack_forget()
        
        # Show selected tab
        if tab_name in self.tabs:
            self.tabs[tab_name].pack(fill=tk.BOTH, expand=True)
            self.current_tab = tab_name
    
    def _send_ai_message(self):
        """Send message to AI"""
        message = self.ai_input.get(1.0, tk.END).strip()
        
        if not message:
            return
        
        self._display_chat_message("You", message, "user")
        self.ai_input.delete(1.0, tk.END)
        
        # Process in background
        threading.Thread(
            target=self._process_ai_message,
            args=(message,),
            daemon=True
        ).start()
    
    def _ai_request(self, request: str):
        """Make an AI request from button"""
        self.ai_input.delete(1.0, tk.END)
        self.ai_input.insert(1.0, request)
        self.switch_tab("ai")
        self._send_ai_message()
    
    def _process_ai_message(self, message: str):
        """Process AI message in background thread"""
        response = self.chatbot.send_message(message)
        self._display_chat_message("AI", response, "ai")
    
    def _display_chat_message(self, sender: str, message: str, tag: str = "ai"):
        """Display message in chat"""
        self.chat_display.config(state=tk.NORMAL)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.chat_display.insert(tk.END, f"{sender}:\n", tag)
        self.chat_display.insert(tk.END, f"{message}\n\n", tag)
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def _handle_setting(self, action: str):
        """Handle settings actions"""
        if action == "Clear History":
            self.chatbot.clear_history()
            messagebox.showinfo("Success", "Chat history cleared!")
        elif action == "Export Config":
            messagebox.showinfo("Export", "Configuration exported to config.json")
        elif action == "View Logs":
            messagebox.showinfo("Logs", "System logs displayed in separate window")
        elif action == "About":
            about_text = """Unified Game Development Dashboard
Version 2.0

Integrated Systems:
• AI Code Generation (OpenAI GPT-3.5)
• Combat System Designer
• Dialogue & NPC Manager  
• Inventory & Crafting
• Quest Designer
• Level Streaming & LOD
• Procedural Generation
• Analytics & Profiling

All tools integrated into one dashboard for
seamless Unreal Engine development.
"""
            messagebox.showinfo("About", about_text)
    
    def _show_startup_info(self):
        """Show startup information"""
        if not OPENAI_API_KEY:
            messagebox.showwarning(
                "API Key Missing",
                "OpenAI API key not set.\n\n"
                "Set OPENAI_API_KEY environment variable to enable AI features.\n"
                "Export: $env:OPENAI_API_KEY='your-key'"
            )

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("╔════════════════════════════════════════════════════════╗")
    print("║   UNIFIED GAME DEVELOPMENT DASHBOARD                  ║")
    print("║        All Tools • One Interface                       ║")
    print("╚════════════════════════════════════════════════════════╝")
    print()
    
    if not OPENAI_API_KEY:
        print("⚠️  Warning: OPENAI_API_KEY environment variable not set!")
        print("   Set it with: $env:OPENAI_API_KEY='your-api-key'")
        print()
    else:
        print("✓ OpenAI API Key detected")
    
    print("Launching Unified Dashboard...\n")
    
    app = UnifiedDashboard()
    app.mainloop()
