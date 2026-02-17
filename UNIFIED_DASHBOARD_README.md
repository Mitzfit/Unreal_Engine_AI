# 🎮 Unified Game Development Dashboard

## Overview

The **Unified Game Development Dashboard** is an all-in-one application that consolidates all game development tools into a single, integrated interface. It combines:

- 🤖 **AI Code Generation** - OpenAI-powered C++ code generation for Unreal Engine
- ⚔️ **Combat System** - Damage formulas, status effects, combo chains, skill trees
- 💬 **Dialogue & NPCs** - Branching dialogue trees, relationships, voice generation
- 🎒 **Inventory & Crafting** - Items, equipment, recipes, trading systems
- 📜 **Quest System** - Quest designer, objectives, rewards, quest chains
- 🌍 **Level Streaming** - Dynamic level loading, LOD systems, memory management
- 🗻 **Procedural Generation** - Terrain, dungeons, cities, weapons
- 📊 **Analytics** - Performance tracking, event analysis, metrics

## Features

### Integrated Dashboard
- **Single Window Interface**: All tools accessible from one dashboard
- **Navigation Sidebar**: Quick access to all systems
- **Real-time System Status**: Monitor which systems are loaded
- **Dark Theme with Blue Accents**: Professional gaming-oriented UI
- **Responsive Layout**: 1600x900 minimum, scales up to full screen

### AI Integration
- **OpenAI GPT-3.5 Support**: Generate production-ready C++ code
- **Conversation History**: Maintains context across 50+ messages
- **System-Aware Prompts**: Each system has specialized AI assistance
- **Non-blocking Interface**: AI processing runs in background threads

### Multi-System Support
- **Modular Design**: Systems load gracefully if modules aren't available
- **Status Indicators**: Visual feedback on system availability
- **Cross-System Integration**: Generate code that integrates multiple systems
- **Quick Command Buttons**: Pre-built requests for common tasks

## System Requirements

### Python
- Python 3.8+
- tkinter (usually included with Python)

### Python Packages
```bash
pip install openai
```

### Environment Variables
```powershell
$env:OPENAI_API_KEY='your-openai-api-key'
```

## Installation

1. **Navigate to the project directory**
   ```powershell
   cd C:\Unreal_Engine_AI
   ```

2. **Activate virtual environment** (if available)
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. **Launch the dashboard**
   ```powershell
   python main.py
   ```
   
   Or directly:
   ```powershell
   python unified_dashboard.py
   ```

## Usage Guide

### Main Interface

The dashboard is divided into:

1. **Top Header** - Application title and status
2. **Left Sidebar** - Navigation buttons and system status
3. **Main Content Area** - Tab-based interface for each system
4. **Bottom Status Bar** - Quick status information

### Navigation

Click any system button in the left sidebar to switch to that system's interface:

- 💬 **AI Chatbot** - Chat interface for code generation
- ⚔️ **Combat** - Combat system designer
- 💬 **Dialogue** - NPC and dialogue management
- 🎒 **Inventory** - Item and crafting system
- 📜 **Quests** - Quest designer
- 🌍 **Streaming** - Level streaming manager
- 🗻 **Procedural** - Procedural generation tools
- 📊 **Analytics** - Dashboard and metrics
- ⚙️ **Settings** - Configuration and status

### AI Code Generation

1. Click the **💬 AI Chatbot** tab
2. Type your request in the input box (supports multi-line)
3. Press **SEND** or Ctrl+Return
4. AI response appears in chat history
5. Use quick command buttons for common requests:
   - Write Actor
   - Create Component
   - Async Load
   - Debug Tips

### System-Specific Tools

Each system tab has:

- **Info Panel** - System features and status
- **Quick Action Buttons** - Pre-built AI requests
- **Status Indicators** - System availability (🟢 LOADED / 🔴 NOT AVAILABLE)

## Architecture

### File Structure

```
Unified_Dashboard/
├── main.py                    # Entry point
├── unified_dashboard.py       # Main dashboard application
├── combat_system.py           # Combat mechanics
├── dialogue_system.py         # NPC dialogue
├── inventory_crafting_system.py # Items & recipes
├── quest_mission_visual_designer.py # Quests
├── level_streaming_manager.py # Level streaming
├── procedural_gen.py          # Procedural generation
├── analytics_dashboard.py     # Analytics engine
└── .env                       # Configuration file
```

### Dashboard Class Structure

- **UnifiedDashboard** (tk.Tk)
  - `_build_ui()` - Main UI construction
  - `_create_*_tab()` - Individual system tabs
  - `switch_tab()` - Tab switching logic
  - `_send_ai_message()` - AI integration
  - `_update_system_status()` - Status monitoring

## Configuration

### Environment Variables

**.env file** or system environment:

```bash
OPENAI_API_KEY=sk-...          # OpenAI API key
OPENAI_MODEL=gpt-3.5-turbo     # Model selection
DEBUG=true                      # Debug mode
```

### Settings Tab

Access configuration in the **⚙️ Settings** tab:
- Check API status
- View loaded modules
- Clear chat history
- Export configuration
- View system logs

## Color Scheme

The dashboard uses a dark theme with blue accents:

| Element | Color | Usage |
|---------|-------|-------|
| Background | #0a0e27 | Main bg |
| Panels | #0f1535 | Content areas |
| Accent Blue | #00d4ff | Primary color |
| Text Primary | #e0e0ff | Main text |
| Success | #00ff88 | Positive status |
| Error | #ff4444 | Error messages |
| Warning | #ffaa00 | Warnings |

Each system has its own tab color for visual distinction.

## AI Features

### System Prompts

The AI is configured with specialized prompts for Unreal Engine C++ development:

- **Code Generation** - Production-ready, best practices
- **System Integration** - Multi-system connection
- **Debugging** - Issue analysis and fixes
- **Optimization** - Performance improvements
- **Documentation** - API and architecture docs

### Conversation Context

- Maintains last 50 messages
- References previous discussions
- Understands cross-system requests
- Provides continuity across sessions

## Troubleshooting

### Dashboard won't launch
```powershell
# Check Python/tkinter
python -c "import tkinter; print('✓ Tkinter OK')"

# Check syntax
python -m py_compile unified_dashboard.py
```

### AI features not working
```powershell
# Set API key
$env:OPENAI_API_KEY='your-key'

# Verify
python -c "import os; print(os.getenv('OPENAI_API_KEY'))"
```

### Module import errors
```powershell
# Ensure dependencies are installed
pip install -r requirements.txt
```

### UI scaling issues
- Resize window to 1600x900 or larger
- Minimum size: 1200x700

## Performance Tips

1. **AI Requests** - Takes 2-5 seconds depending on complexity
2. **System Status** - Updates on tab switch
3. **Chat Display** - Smooth scrolling even with large histories
4. **Memory** - Conversation history limited to last 50 messages

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+Return | Send chat message |
| Alt+C | Open Combat tab |
| Alt+D | Open Dialogue tab |
| Alt+I | Open Inventory tab |
| Alt+Q | Open Quest tab |

## Future Enhancements

- [ ] Keyboard shortcuts for all tabs
- [ ] Export/import project configurations
- [ ] Real-time system visualization
- [ ] Integration with Unreal Engine via WebSocket
- [ ] Team collaboration features
- [ ] Code templates library
- [ ] Asset preview panels
- [ ] Plugin system for custom tools

## Support & Resources

- **OpenAI Documentation**: https://platform.openai.com/docs
- **Unreal Engine Docs**: https://docs.unrealengine.com
- **System Modules**: See individual system design files

## License

This unified dashboard integrates multiple game development systems for use with Unreal Engine.

## Version

**Dashboard Version**: 2.0
**Release Date**: February 2026
**Status**: Production Ready

---

**Enjoy integrated game development with the Unified Dashboard! 🎮**
