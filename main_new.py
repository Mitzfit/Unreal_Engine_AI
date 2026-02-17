"""
╔════════════════════════════════════════════════════════════════════════════╗
║     UNIFIED GAME DEVELOPMENT DASHBOARD - MAIN ENTRY POINT                  ║
║    Integrated with All Game Development Tools & AI Code Generation         ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys

# Add current directory to path
APP_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, APP_DIR)

# Import and launch the unified dashboard
try:
    from unified_dashboard import UnifiedDashboard
    
    print("╔════════════════════════════════════════════════════════╗")
    print("║   UNIFIED GAME DEVELOPMENT DASHBOARD                  ║")
    print("║        All Tools • One Interface • Real-time           ║")
    print("╚════════════════════════════════════════════════════════╝")
    print()
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        print("⚠️  Warning: OPENAI_API_KEY environment variable not set!")
        print("   Set it with: $env:OPENAI_API_KEY='your-api-key'")
        print("   AI features will be limited without an API key.")
        print()
    else:
        print("✓ OpenAI API Key detected - AI features enabled")
        print()
    
    print("Launching Unified Dashboard...\n")
    
    app = UnifiedDashboard()
    app.mainloop()
    
except ImportError as e:
    print(f"Error: Could not import unified_dashboard: {e}")
    print("Make sure unified_dashboard.py exists in the same directory.")
    sys.exit(1)
except Exception as e:
    print(f"Error launching dashboard: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
