# 📊 Dashboard Layout & Navigation Map

## Visual Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🎮 UNIFIED GAME DEVELOPMENT DASHBOARD 🎮 (1600x900 min)                    │
├──────┬──────────────────────────────────────────────────────────────────────┤
│      │                                                                       │
│ LEFT │                     MAIN CONTENT AREA (TABS)                        │
│      │                          (Active Tab Shown)                          │
│      │                                                                       │
│ SIDE │  ┌─ AI CHATBOT ────────────────────────────────────────────────┐   │
│ BAR  │  │                                                             │   │
│      │  │  [Chat Display - Full Height]                              │   │
│ 200  │  │  ══════════════════════════════════════════════════════    │   │
│ px   │  │  [System]: Welcome to dashboard...                         │   │
│      │  │  [User]:   Tell me about combat systems                    │   │
│ FIXED│  │  [AI]:     Combat system offers damage formulas...         │   │
│ NAVY │  │  ══════════════════════════════════════════════════════    │   │
│      │  │                                                             │   │
│      │  │  Input:  [                                      ] [SEND]   │   │
│      │  □                                                             │   │
│      │  │ [💬 AI Chatbot]      ← ACTIVE (blue)                       │   │
│      │  │ [⚔️ Combat]          ← Available (red)                     │   │
│NAVI- │  │ [💬 Dialogue]        ← Available (teal)                    │   │
│GATION│  │ [🎒 Inventory]       ← Available (yellow)                  │   │
│BUTTONS│  │ [📜 Quests]         ← Available (green)                   │   │
│      │  │ [🌍 Streaming]      ← Available (pink)                    │   │
│      │  │ [🗻 Procedural]     ← Available (purple)                  │   │
│ 9    │  │ [📊 Analytics]      ← Available (teal)                    │   │
│TOTAL │  │ [⚙️ Settings]       ← Configuration                       │   │
│      │  │                                                             │   │
│SYSTEM│  │ ══════════════════════════════════════════════════════    │   │
│STATUS│  │ SYSTEM STATUS:                                             │   │
│      │  │ 🟢 Combat                                                  │   │
│ 15   │  │ 🟢 Dialogue                                                │   │
│LINES │  │ 🟢 Inventory                                               │   │
│SCROLL│  │ 🟢 Quest                                                   │   │
│      │  │ 🟢 Streaming                                               │   │
│      │  │ 🟢 Procedural                                              │   │
│      │  │ 🟢 Analytics                                               │   │
│      │  └─────────────────────────────────────────────────────────────┘   │
│      │                                                                       │
├──────┼──────────────────────────────────────────────────────────────────────┤
│      Ready • All Systems Integrated • Chat Ready       ● ONLINE              │
└──────┴──────────────────────────────────────────────────────────────────────┘
```

## Tab Switching Flow

```
Legend:
🟢 = Currently Active
⬜ = Available to Click
❌ = Not Loaded (if module missing)

Start
  ↓
Main Dashboard
  ├─→ 💬 AI Chatbot (🟢 DEFAULT)
  │     └─ Generate C++ code
  │     └─ Ask integration questions
  │     └─ Debug assistance
  │
  ├─→ ⚔️ Combat System (⬜ Click to switch)
  │     ├─ Info Panel (features & status)
  │     ├─ Quick Buttons:
  │     │   • Create Damage Formula
  │     │   • Add Status Effect
  │     │   • Design Combo Chain
  │     │   • Build Skill Tree
  │     └─ All AI-powered
  │
  ├─→ 💬 Dialogue & NPCs (⬜ Click to switch)
  │     ├─ Info Panel
  │     ├─ Quick Buttons:
  │     │   • Create Dialogue Tree
  │     │   • Add NPC
  │     │   • Design Relationships
  │     │   • Generate Voice
  │     └─ NPC Management
  │
  ├─→ 🎒 Inventory & Crafting (⬜ Click to switch)
  │     ├─ Info Panel
  │     ├─ Quick Buttons:
  │     │   • Create Item
  │     │   • Design Recipe
  │     │   • Setup Trading
  │     │   • Add Set Bonus
  │     └─ Item System
  │
  ├─→ 📜 Quest & Mission System (⬜ Click to switch)
  │     ├─ Info Panel
  │     ├─ Quick Buttons:
  │     │   • Create Quest
  │     │   • Add Objectives
  │     │   • Design Rewards
  │     │   • Build Quest Chain
  │     └─ Quest Designer
  │
  ├─→ 🌍 Level Streaming (⬜ Click to switch)
  │     ├─ Info Panel
  │     ├─ Quick Buttons:
  │     │   • Create Streaming Volume
  │     │   • Setup LOD Settings
  │     │   • Configure Memory Budget
  │     │   • Profile Performance
  │     └─ Level Management
  │
  ├─→ 🗻 Procedural Generation (⬜ Click to switch)
  │     ├─ Info Panel
  │     ├─ Quick Buttons:
  │     │   • Generate Terrain
  │     │   • Create Dungeon
  │     │   • Build City
  │     │   • Generate Weapons
  │     └─ Content Generation
  │
  ├─→ 📊 Analytics Dashboard (⬜ Click to switch)
  │     ├─ Info Panel
  │     ├─ Quick Buttons:
  │     │   • View Metrics
  │     │   • Analyze Events
  │     │   • Performance Report
  │     │   • Export Data
  │     └─ Analytics & Profiling
  │
  └─→ ⚙️ Settings (⬜ Click to switch)
        ├─ Info Panel
        ├─ Configuration Options
        ├─ System Status Display
        ├─ Quick Buttons:
        │   • Clear History
        │   • Export Config
        │   • View Logs
        │   • About
        └─ Settings & Config
```

## Color Codes

### Navigation Colors
```
🔵 #00d4ff  - AI Chatbot (Primary Accent)
🔴 #ff6b6b  - Combat System
🔵 #4ecdc4  - Dialogue & NPCs
🟡 #ffe66d  - Inventory & Crafting
🟢 #a8e6cf  - Quest System
🔵 #ff8b94  - Level Streaming
🟣 #7b68ee  - Procedural Generation
🔵 #20b2aa  - Analytics
⚙️ #a0a0c0  - Settings
```

### Status Indicators
```
🟢 LOADED        - System ready to use
🔴 NOT LOADED    - Module not available (graceful degrade)
🟡 LOADING       - System initializing
⚫ ERROR         - System encountered error
```

### Background Colors
```
Background:      #0a0e27  (Dark navy)
Panels:          #0f1535  (Darker navy)
Sidebar:         #0f1535  (Matching panels)
Text Primary:    #e0e0ff  (Light purple)
Text Secondary:  #a0a0c0  (Gray purple)
```

## Workflow Examples

### Example 1: AI Code Generation
```
1. Start on AI Chatbot tab (default)
2. Type request: "Create a weapon inventory item class"
3. AI generates C++ code
4. Copy code to Unreal Engine project
5. Modify as needed
DONE in 5 seconds
```

### Example 2: Combat System Design
```
1. Click ⚔️ Combat button
2. View features: Damage, effects, combos, skills
3. Click "Create Damage Formula" button
4. Pre-filled with common request
5. Switches to AI tab automatically
6. AI generates formula code
7. Back to Combat tab to view results
DONE via AI assistance
```

### Example 3: Dialogue Integration
```
1. Click 💬 Dialogue button
2. Review dialogue system capabilities
3. Click "Create Dialogue Tree"
4. AI generates complete dialogue structure
5. Click "Add NPC"
6. AI creates NPC with relationships
7. Full system ready to integrate
DONE with AI help
```

### Example 4: Multi-System Quest
```
1. Click 📜 Quest button
2. Click "Create Quest"
3. AI starts in quest context
4. Ask: "Create a quest that uses inventory items and triggers dialogue"
5. AI generates integrated quest code
6. Use Combat tab to add combat encounters
7. Complete game feature designed
DONE in single workflow
```

## Quick Command Buttons

Every system has quick command buttons that:

```
User clicks button
        ↓
AI request pre-filled in chatbot
        ↓
Switches to AI Chatbot tab
        ↓
Chat input populated with command
        ↓
Message sent immediately
        ↓
AI response appears in chat
        ↓
User can continue conversation or modify result
```

## Sidebar Functions

### Top Section (Navigation)
- 9 clickable system buttons
- Each switches to relevant tab
- Current tab highlighted
- Visual color coding

### Middle Section (Separator)
- ttk.Separator line
- Visual division

### Bottom Section (System Status)
- 15-line scrollable text display
- Shows loaded systems
- Green dot = 🟢 LOADED
- Red dot = 🔴 NOT LOADED
- Real-time updates on tab switch

## Status Bar Functions

### Left Side
- "Ready" indicator
- System integration status
- Chat availability

### Right Side
- "● ONLINE" indicator
- Green dot for active status
- Pulsing when processing

## Tab Content Structure

Each system tab (except AI) has:

```
┌─────────────────────────────────────────────┐
│ System Header (Colored Bar)                 │
│ System Name • System Icon                   │
├─────────────────────────────────────────────┤
│ Info Panel                                  │
│ • Features list                             │
│ • System status 🟢/🔴                      │
│ • Description                               │
├─────────────────────────────────────────────┤
│ Action Buttons (4 quick commands)           │
│ [Button 1]  [Button 2]  [Button 3]  [4]    │
│ All trigger AI requests                     │
└─────────────────────────────────────────────┘
```

## AI Chat Tab Structure

```
┌─────────────────────────────────────────────┐
│ Chat Header (Blue Bar)                      │
│ 💬 AI Code Generation & Integration         │
├─────────────────────────────────────────────┤
│ Chat Display Area                           │
│ [Scrolled Text Widget - Full Height]        │
│ Showing conversation history                │
│ User messages in cyan                       │
│ AI responses in green                       │
├─────────────────────────────────────────────┤
│ Input Area                                  │
│ [Text Widget        ] [SEND Button]         │
│ 4 lines for typing                          │
│ Ctrl+Return = Send                          │
└─────────────────────────────────────────────┘
```

## System Integration Map

```
           ┌─────────────────────┐
           │   AI Chatbot Core   │
           │  (GPT-3.5 Turbo)    │
           └──────────┬──────────┘
                      │
                 ┌────┴────┐
                 │ Provides │
                 │   Code   │
                 │ for All  │
                 │ Systems  │
                 └────┬────┘
                      ↓
        ┌─────────────────────────────────┐
        │    Game Systems Integration     │
        │                                 │
        │ ⚔️  Combat        📜 Quests    │
        │ 💬 Dialogue       🌍 Streaming │
        │ 🎒 Inventory      🗻 Procedural │
        │                                 │
        └─────────────────────────────────┘
        
All systems:
✓ Generate standalone code
✓ Generate integrated code
✓ Generate cross-system code
✓ Debugging & optimization
```

## Navigation Summary

- **9 Total Systems** in sidebar
- **1 Primary AI System** always available
- **8 Game Systems** + Settings
- **Quick Buttons** in each tab (4 per system)
- **Status Display** always visible
- **One-Click Switching** between any tab
- **Instant Context** switching in AI

---

## Ready to Navigate!

1. 🎮 **Launch Dashboard**: `python main.py`
2. 🧭 **Click Any System** in sidebar to explore
3. 🤖 **Use AI** from any tab with quick buttons
4. 💬 **Chat Directly** in AI Chatbot tab
5. 📊 **Check Status** in left sidebar anytime

*All Tools • One Interface • Real-time Integration*
