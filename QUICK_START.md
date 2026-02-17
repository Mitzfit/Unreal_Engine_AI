# 🚀 Quick Start Guide - Unified Dashboard

## 30 Second Setup

### 1. Set API Key
```powershell
$env:OPENAI_API_KEY='your-openai-api-key-here'
```

### 2. Launch Dashboard
```powershell
cd C:\Unreal_Engine_AI
python main.py
```

### 3. Start Using!
- Click any system button in the sidebar
- Use the AI chatbot to generate code
- Explore each system's features

---

## Main Features at a Glance

### 🤖 AI Code Generation
- Click **💬 AI Chatbot** tab
- Ask anything about Unreal Engine C++
- Get production-ready code

### ⚔️ Combat System
- Create damage formulas
- Design status effects
- Build combo chains
- Setup skill trees

### 💬 Dialogue & NPCs
- Create branching dialogue trees
- Manage NPC relationships
- Generate voice lines
- Track emotions and states

### 🎒 Inventory & Crafting
- Design items and equipment
- Create recipes
- Setup trading system
- Add set bonuses

### 📜 Quest System
- Create quests and missions
- Design objectives
- Setup rewards
- Build quest chains

### 🌍 Level Streaming
- Create streaming volumes
- Configure LOD settings
- Manage memory budgets
- Profile performance

### 🗻 Procedural Generation
- Generate terrain
- Create dungeons
- Build cities
- Generate weapons

### 📊 Analytics
- View performance metrics
- Track events
- Analyze player data
- Export reports

---

## Common Tasks

### Generate a Combat Actor
1. Open **💬 AI Chatbot** tab
2. Type: "Create an Unreal Engine Actor for a combat character with health, damage types, and attack animations"
3. AI generates complete C++ code

### Design a Dialogue Tree
1. Open **💬 Dialogue & NPC System** tab
2. Click "Create Dialogue Tree"
3. Or ask AI: "Design a dialogue tree for a merchant NPC with 5 conversation branches"

### Create an Item
1. Open **🎒 Inventory & Crafting** tab
2. Click "Create Item"
3. Or ask AI: "Create a legendary sword item with fire damage and critical strike bonus"

### Build a Quest
1. Open **📜 Quest & Mission System** tab
2. Click "Create Quest"
3. Or ask AI: "Design a fetch quest that requires players to collect 5 crystals"

---

## System Status

The **Left Sidebar** shows:

🟢 **LOADED** - System is ready to use
🔴 **NOT LOADED** - System module not available

You can still request AI help even if a system isn't loaded!

---

## Tips & Tricks

### ✨ Quick Commands
Each system tab has quick command buttons:
- Combat: "Create Damage Formula", "Add Status Effect", etc.
- Dialogue: "Create Dialogue Tree", "Add NPC", etc.
- Inventory: "Create Item", "Design Recipe", etc.

### 💬 AI Context
The AI remembers your conversation history, so you can:
- Ask follow-up questions
- Reference previous code
- Request modifications

### 🎨 Dark Theme
The dark blue interface:
- Reduces eye strain
- Professional gaming aesthetic
- Optimized for code viewing

### 📱 Responsive UI
- Resize window to any size (min 1200x700)
- All panels adjust automatically
- Sidebar can be scrolled if truncated

---

## Troubleshooting

### "API not configured" message
```powershell
# Set your API key:
$env:OPENAI_API_KEY='sk-...'

# Verify it's set:
echo $env:OPENAI_API_KEY
```

### Dashboard starts slowly
- First launch takes longer
- System initialization in background
- Subsequent launches are faster

### Chat isn't responding
1. Check API key is set correctly
2. Ensure OpenAI account has credits
3. Check internet connection
4. Verify OpenAI APIs aren't down

### Module not loading
- Some systems require additional dependencies
- Dashboard still works without them
- Check UNIFIED_DASHBOARD_README.md for details

---

## What's Included

| System | Status | Files |
|--------|--------|-------|
| Combat | ✓ | combat_system.py |
| Dialogue | ✓ | dialogue_system.py |
| Inventory | ✓ | inventory_crafting_system.py |
| Quests | ✓ | quest_mission_visual_designer.py |
| Level Streaming | ✓ | level_streaming_manager.py |
| Procedural Gen | ✓ | procedural_gen.py |
| Analytics | ✓ | analytics_dashboard.py |
| AI Integration | ✓ | OpenAI API (requires key) |

---

## Next Steps

1. **Read Full Documentation**
   - Open UNIFIED_DASHBOARD_README.md

2. **Explore Each System**
   - Click through each tab
   - Read the info panels
   - Try the quick commands

3. **Start Coding**
   - Ask AI to generate code
   - Copy it to your Unreal Engine project
   - Customize and integrate

4. **Integrate Multiple Systems**
   - Use AI to combine systems
   - Ask for cross-system integration code
   - Build complete game features

---

## Need Help?

### Inside Dashboard
- Use **⚙️ Settings** tab for configuration
- Click **About** for version info
- Check system status in sidebar

### AI Chatbot
Ask anything like:
- "How do I integrate combat with inventory?"
- "Generate a complete NPC with dialogue and trading"
- "Create a quest system that uses items"

### Documentation
- UNIFIED_DASHBOARD_README.md - Full manual
- COMBAT_SYSTEM_GUIDE.md - Combat details
- DIALOGUE_SYSTEM_GUIDE.md - Dialogue details
- INVENTORY_QUICK_REFERENCE.md - Inventory reference
- QUEST_SYSTEM_GUIDE.md - Quest details

---

## Dashboard Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Ctrl+Return | Send chat message |
| Escape | Close any modal |
| Tab | Navigate between systems |

---

## Platform Support

✓ **Windows 10/11** (Primary)
✓ **macOS** (Python 3.8+)
✓ **Linux** (Python 3.8+)

---

**Ready to start? Launch the dashboard and explore all the tools!** 🎮

```powershell
python main.py
```

---

*Unified Game Development Dashboard v2.0*
*All Tools • One Interface • Real-time Integration*
