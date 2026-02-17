"""
UNIFIED GAME DEVELOPMENT DASHBOARD - MAIN ENTRY POINT

This is a small, focused entry point that launches the complete
`UnifiedDashboard` GUI from `unified_dashboard.py`.

Usage:
    python main.py

Environment variables:
    OPENAI_API_KEY    (optional) - required for AI features
"""

import os
import sys
import traceback

# Load environment variables from .env when available
try:
    from dotenv import load_dotenv
    import os as _os
    _env_path = _os.path.join(_os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path=_env_path)
except Exception:
    # If python-dotenv isn't installed, the user can set env vars in their shell.
    pass

# Ensure current directory is on sys.path so local modules can be imported
APP_DIR = os.path.abspath(os.path.dirname(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


def main():
    try:
        from unified_dashboard import UnifiedDashboard

        print("=== UNIFIED GAME DEVELOPMENT DASHBOARD ===")
        print("All Tools • One Interface • Real-time AI")
        print()

        # Check for available AI providers
        import os
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        hf_key = os.getenv("HUGGINGFACE_API_KEY")
        
        providers = []
        if gemini_key:
            providers.append("Google Gemini")
        if openai_key:
            providers.append("OpenAI")
        if hf_key:
            providers.append("HuggingFace")
        
        if providers:
            print(f"Available AI Providers: {', '.join(providers)}")
            print()
        else:
            print("Warning: No AI providers configured!")
            print("  Set API keys in .env: GEMINI_API_KEY, OPENAI_API_KEY, or HUGGINGFACE_API_KEY")
            print()

        print("Launching Unified Dashboard...\n")
        app = UnifiedDashboard()
        app.mainloop()

    except ImportError as e:
        print(f"Error: Could not import unified_dashboard: {e}")
        print("Make sure unified_dashboard.py exists in the same directory.")
        sys.exit(1)
    except Exception:
        print("Error launching dashboard:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
