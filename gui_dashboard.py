"""
Modern GUI Dashboard for Unreal Engine AI
Integrates user dashboard, projects, and AI chat
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import tkinter.font as tkFont
from datetime import datetime
import threading
import json
import os
import sys
from ai_code_generator import AICodeGenerator

# Add current directory to path
APP_DIR = os.path.abspath(os.path.dirname(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# Import AI Assistant
from ai_assistant_onboarding import AIAssistant

# Update the __init__ method to include the code generator

def __init__(self, root, user_id: int, ai_assistant):
    # ... existing code ...
    
    # Add AI code generator
    self.code_gen = AICodeGenerator(
        api_key=os.getenv("OPENAI_API_KEY", "")
    )
    
    # ... rest of init ...