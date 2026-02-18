"""
Quick test script for the GUI dashboard
"""

import tkinter as tk
from gui_dashboard import ModernGUIDashboard
from ai_assistant_onboarding import AIAssistant
import os
from dotenv import load_dotenv

# Load env
load_dotenv()

print("Initializing test dashboard...")

# Create AI assistant
ai = AIAssistant(
    openai_key=os.getenv("OPENAI_API_KEY", ""),
    db_path="assistant.db"
)

# Create test user
result = ai.register_user("testuser", "test@example.com", "password123")
if not result[0]:
    result = ai.login_user("test@example.com", "password123")

if result[0]:
    user_id = result[1]["user_id"]
    print(f"✓ User created/logged in (ID: {user_id})")
    print("✓ Launching GUI...")
    
    # Create GUI
    root = tk.Tk()
    dashboard = ModernGUIDashboard(root, user_id, ai)
    root.mainloop()
else:
    print(f"❌ Failed: {result[1]}")