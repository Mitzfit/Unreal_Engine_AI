"""
UNIFIED GAME DEVELOPMENT DASHBOARD - MAIN ENTRY POINT

Launches the modern tkinter GUI dashboard with AI integration.

Usage:
    python main.py

Environment variables:
    OPENAI_API_KEY    (optional) - required for AI features
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
import traceback
from datetime import datetime

# Ensure current directory is on sys.path
APP_DIR = os.path.abspath(os.path.dirname(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# Load environment variables from .env when available
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(APP_DIR, '.env')
    load_dotenv(dotenv_path=_env_path)
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")


def main():
    """Main application entry point"""
    try:
        print("=" * 60)
        print("UNREAL ENGINE AI — DASHBOARD".center(60))
        print("=" * 60)
        print()

        print("Importing modules...")
        
        # Import required modules
        from ai_assistant_onboarding import AIAssistant
        from gui_dashboard import ModernGUIDashboard 

        print("✓ Modules imported successfully")
        print()

        # Check for available AI providers
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        hf_key = os.getenv("HUGGINGFACE_API_KEY")
        
        providers = []
        if gemini_key:
            providers.append("✓ Google Gemini")
        if openai_key:
            providers.append("✓ OpenAI")
        if hf_key:
            providers.append("✓ HuggingFace")
        
        if providers:
            print("Available AI Providers:")
            for p in providers:
                print(f"  {p}")
            print()
        else:
            print("⚠️  Warning: No AI providers configured!")
            print("   Set API keys in .env file:")
            print("     - GEMINI_API_KEY")
            print("     - OPENAI_API_KEY")
            print("     - HUGGINGFACE_API_KEY")
            print()

        print("Initializing AI Assistant...")
        
        # Initialize AI Assistant
        ai_assistant = AIAssistant(
            openai_key=openai_key or "",
            db_path="assistant.db"
        )
        
        print("✓ AI Assistant initialized")
        print()

        # Create root Tk window
        root = tk.Tk()
        root.withdraw()  # Hide while initializing
        
        print("Creating/logging in user account...")
        
        # Create or login demo user
        user_email = "demo@unrealai.local"
        user_pass = "demo123"
        
        # Try to register
        success, response = ai_assistant.register_user(
            username="Demo User",
            email=user_email,
            password=user_pass
        )
        
        if not success:
            # Try to login if already exists
            success, response = ai_assistant.login_user(
                email=user_email,
                password=user_pass
            )
        
        if not success:
            raise Exception(f"Failed to create/login user: {response}")
        
        user_id = response["user_id"]
        print(f"✓ User logged in (ID: {user_id})")
        print()
        
        print("Launching GUI Dashboard...")
        print()
        
        # Show root window
        root.deiconify()
        
        # Create and show dashboard
        dashboard = ModernGUIDashboard(root, user_id, ai_assistant)
        
        # Run application
        root.mainloop()

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure all required files exist in the same directory:")
        print("  - ai_assistant_onboarding.py")
        print("  - gui_dashboard.py")
        print("  - user_dashboard.py")
        print()
        print("Traceback:")
        traceback.print_exc()
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error launching dashboard:")
        traceback.print_exc()
        
        # Show error dialog
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Dashboard Error",
                f"Failed to start dashboard:\n\n{str(e)}"
            )
            root.destroy()
        except:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()
