# Quest & Mission System - Quick Reference

## 🎯 Start in 30 Seconds

### Launch Web Interface
```bash
python quest_visual_editor_web.py
```
Then open: **http://localhost:8000**

### Use Programmatically
```python
from quest_mission_visual_designer import AdvancedQuestSystem, Difficulty, ObjectiveType

system = AdvancedQuestSystem()

# Create quest
q = system.create_quest("Kill 5 Goblins", "...", Difficulty.EASY)

# Add objective
system.add_objective_to_quest(q.quest_id, ObjectiveType.KILL, 
                              "Defeat Goblins", target_id="goblin", required_qty=5)

# Calculate rewards
from quest_mission_visual_designer import RewardCalculator
q.rewards = RewardCalculator.calculate_quest_rewards(q)

print(f"Rewards: {q.calculate_total_reward(RewardType.GOLD)} gold")
```

---

## 📚 Files Overview

| File | Purpose | Lines |
|------|---------|-------|
| `quest_mission_visual_designer.py` | Core system | 1,200+ |
| `quest_visual_editor_web.py` | Web interface | 700+ |
| `quest_unreal_integration.py` | Unreal engine bridge | 400+ |
| `QUEST_SYSTEM_GUIDE.md` | Full documentation | 500+ |
| `QUEST_SYSTEM_IMPLEMENTATION.md` | This guide | - |

---

## 🔧 Main Classes

### Core System
```python
AdvancedQuestSystem()          # Main system manager
QuestVisualEditor()            # Node-based visualization
ObjectiveTracker()             # Progress tracking
RewardCalculator()             # Reward computation
QuestChainSystem()             # Chain management
NPCAssignmentSystem()          # NPC assignment
LocationMapper()               # World mapping
QuestRandomGenerator()         # Procedural generation
```

### Data Models
```python
Quest                          # Quest definition
Objective                      # Quest objective
Reward                         # Reward definition
Location                       # World location
NPC                            # Non-player character
QuestChain                     # Linked quests
```

### Integration
```python
UnrealQuestBridge()            # Unreal communication
QuestEventData()               # Event information
QuestEvent(Enum)               # Event types
```

---

## 🎓 Common Tasks

### Create a Location
```python
loc = system.location_mapper.create_location(
    name="Dragon's Lair",
    location_type=LocationType.DUNGEON,
    x=100, y=50, z=-200,
    difficulty=Difficulty.EPIC
)
```

### Create an NPC
```python
npc = system.npc_system.create_npc(
    name="Aldric the Brave",
    role=NPCRole.QUEST_GIVER,
    location_id=loc.location_id,
    level=10
)
```

### Create Quest
```python
quest = system.create_quest(
    name="Slay the Dragon",
    description="Defeat the dragon",
    difficulty=Difficulty.EPIC,
    giver_npc_id=npc.npc_id,
    giver_location_id=loc.location_id
)
```

### Add Objective
```python
system.add_objective_to_quest(
    quest.quest_id,
    ObjectiveType.KILL,
    "Defeat the Dragon",
    target_id="red_dragon",
    required_qty=1
)
```

### Generate Random Quest
```python
q = QuestRandomGenerator.generate_quest(
    difficulty=Difficulty.HARD,
    location=loc,
    quest_giver=npc
)
```

### Create Quest Chain
```python
chain = system.chains.create_chain(
    "Dragon Slayer Arc",
    "Multi-part dragon hunting",
    faction="Dragon Hunters"
)

system.chains.add_quest_to_chain(chain.chain_id, quest1)
system.chains.add_quest_to_chain(chain.chain_id, quest2)
system.chains.add_quest_to_chain(chain.chain_id, quest3)
```

### Export System
```python
system.export_system_state("my_quests.json")
```

### Get Statistics
```python
stats = system.get_system_stats()
# Returns: total_quests, total_chains, total_locations, 
#          total_npcs, total_objectives, total_rewards
```

---

## 🌐 API Endpoints

### Quests
```
POST   /api/quests                    Create quest
GET    /api/quests                    Get all quests
GET    /api/quests/{quest_id}         Get specific quest
PUT    /api/quests/{quest_id}         Update quest
DELETE /api/quests/{quest_id}         Delete quest
POST   /api/quests/{quest_id}/objectives    Add objective
POST   /api/quests/{quest_id}/calculate-rewards  Calculate rewards
```

### Locations
```
POST   /api/locations                 Create location
GET    /api/locations                 Get all locations
GET    /api/locations/{location_id}   Get location
POST   /api/locations/{loc1}/connect/{loc2}   Connect locations
GET    /api/locations/{location_id}/nearest   Find nearest
GET    /api/locations/{location_id}/npcs      Get location NPCs
```

### NPCs
```
POST   /api/npcs                      Create NPC
GET    /api/npcs                      Get all NPCs
GET    /api/npcs/{npc_id}             Get NPC
POST   /api/npcs/{npc_id}/assign-quest/{quest_id}  Assign quest
GET    /api/npcs/role/{role}          Get NPCs by role
```

### Chains
```
POST   /api/chains                    Create chain
GET    /api/chains                    Get all chains
GET    /api/chains/{chain_id}         Get chain
GET    /api/chains/{chain_id}/progress   Get progress
```

### Generation
```
POST   /api/quests/random/generate    Generate 1 quest
POST   /api/quests/random/batch?count=10  Generate 10 quests
```

### System
```
GET    /api/system/stats              Get statistics
POST   /api/system/export             Export system
GET    /api/system/export/download    Download export
POST   /api/system/import             Import system
GET    /api/health                    Health check
```

---

## 🎨 Enums Reference

### Objective Types (17)
`KILL, COLLECT, DELIVER, REACH, INTERACT, PROTECT, ESCORT, SURVIVE, CRAFT, TALK_TO, DISCOVER, SOLVE_PUZZLE, STEALTH, TIMED, DEFEND, RESCUE, INVESTIGATE`

### Difficulty (7)
`TRIVIAL(0.5x), EASY(0.8x), NORMAL(1.0x), HARD(1.5x), EPIC(2.5x), LEGENDARY(4.0x), MYTHIC(6.0x)`

### Reward Types (11)
`GOLD, XP, ITEM, SKILL_POINT, REPUTATION, UNLOCK, TITLE, COMPANION, SPELL, ABILITY, RECIPE`

### NPC Roles (6)
`QUEST_GIVER, QUEST_TARGET, ESCORT, GUARDIAN, VENDOR, ALLY`

### Location Types (10)
`CITY, DUNGEON, WILDERNESS, CAVE, CAMP, FORTRESS, SHRINE, RUIN, TAVERN, MARKETPLACE`

### Quest Status (6)
`LOCKED, AVAILABLE, ACTIVE, COMPLETED, FAILED, ABANDONED`

---

## 💾 Database

Automatically created tables:
- `quests` - Quest data
- `objectives` - Objectives
- `chains` - Quest chains
- `locations` - World locations
- `npcs` - Characters

Access via: `quest_system.py` file (path set in `AdvancedQuestSystem()`)

---

## 🔗 Integration Examples

### With Dialogue System
```python
# Link NPC quest giver to dialogue tree
npc.dialogue_tree_id = "npc_dialogue_001"

# Quest trigger from dialogue
dialogue_system.on_dialogue_complete(
    lambda: bridge.assign_quest_to_player("player1", "quest123")
)
```

### With Game Environment
```python
# Create quest at procedurally generated location
location = system.location_mapper.create_location(
    "Procedural City",
    LocationType.CITY,
    x=env.center.x,
    y=env.center.y,
    z=env.center.z
)

quest = system.create_quest(
    "Explore City",
    giver_location_id=location.location_id
)
```

### With Audio System
```python
# Generate quest NPC voice
voice = audio_system.generate_speech(
    npc.name + ": " + quest.description,
    speaker=npc.name
)

# Link to quest event
quest_event.audio_file = voice.file_path
```

### With Unreal Engine
```python
# Initialize bridge
bridge = UnrealQuestBridge(system)

# Subscribe to events
bridge.subscribe_to_event(
    QuestEvent.QUEST_COMPLETED,
    on_unreal_quest_complete
)

# Assign quest to player
await bridge.assign_quest_to_player("unreal_player_123", quest_id)

# Update objective from Unreal
await bridge.update_objective(
    player_id="unreal_player_123",
    objective_id="obj_456",
    amount=1
)
```

---

## 📊 Reward Examples

### Easy Quest
```
Base: 80 gold, 200 XP
Math: 100 × 0.8 = 80 gold
      250 × 0.8 = 200 XP
```

### Normal Quest with Complex Objectives
```
Base: 130 gold, 325 XP (with 1.3x complexity multiplier)
Math: 100 × 1.0 × 1.3 = 130 gold
      250 × 1.0 × 1.3 = 325 XP
+ 10 reputation
```

### Epic Quest
```
Base: 250 gold, 625 XP
Math: 100 × 2.5 = 250 gold
      250 × 2.5 = 625 XP
+ 1 skill point
+ 25 reputation
```

---

## 🐛 Debugging

### Check Quest Progress
```python
quest = system.quests[quest_id]
print(f"Progress: {quest.progress_pct}%")
print(f"Objectives: {len(quest.objectives)}")
for obj in quest.objectives:
    print(f"  {obj.description}: {obj.current_qty}/{obj.required_qty}")
```

### Verify Connections
```python
loc1 = system.location_mapper.locations[loc1_id]
loc2 = system.location_mapper.locations[loc2_id]
distance = loc1.distance_to(loc2)
path = system.location_mapper.get_path_between(loc1_id, loc2_id)
print(f"Distance: {distance}, Path: {path}")
```

### Check NPC Assignments
```python
npc = system.npc_system.npcs[npc_id]
print(f"NPC: {npc.name}")
print(f"Quests: {npc.available_quests}")
print(f"Location: {npc.location_id}")
```

### Export for Analysis
```python
system.export_system_state("debug.json")
# Open debug.json in editor for full data inspection
```

---

## ⚡ Performance Tips

1. **Use auto-layout for 100+ quests**
   ```python
   system.visual_editor.auto_layout()
   ```

2. **Cache nearest locations**
   ```python
   nearest = system.location_mapper.find_nearest_location(loc, count=10)
   ```

3. **Batch generate quests**
   ```python
   quests = [QuestRandomGenerator.generate_quest() for _ in range(100)]
   ```

4. **Use quest chains for organization**
   ```python
   # Instead of 100 separate quests, use 10 chains of 10 quests
   ```

---

## 🎮 Web Interface Usage

### Create Quest
1. Enter name and description
2. Select difficulty
3. Click "Create Quest"
4. Drag node to arrange

### Generate Random
1. Click "Random Quest" button
2. Node appears on canvas
3. Adjust properties in sidebar

### Auto-Layout
1. Create multiple quests
2. Click "Auto Layout"
3. Quests arrange hierarchically

### Export System
1. Click "Export" button
2. Downloads `quest_system_export.json`
3. Can be imported later

---

## 📱 Mobile/Client Integration

### Python Client Example
```python
import requests

base_url = "http://localhost:8000/api"

# Get all quests
quests = requests.get(f"{base_url}/quests").json()

# Create quest
new_quest = requests.post(f"{base_url}/quests", json={
    "name": "New Quest",
    "description": "...",
    "difficulty": "HARD"
}).json()

# Update objective
requests.post(f"{base_url}/objectives/{obj_id}/update", json={
    "amount": 1
})
```

### JavaScript Client Example
```javascript
const API = "http://localhost:8000/api";

// Get quests
const quests = await fetch(`${API}/quests`).then(r => r.json());

// Create quest
const newQuest = await fetch(`${API}/quests`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({name: "New", description: "...", difficulty: "NORMAL"})
}).then(r => r.json());

// Update objective
await fetch(`${API}/objectives/${objId}/update`, {
    method: "POST",
    body: JSON.stringify({amount: 1})
});
```

---

## ✅ Checklist

- [ ] Created quest system files
- [ ] Reviewed API reference
- [ ] Launched web interface
- [ ] Created test quest
- [ ] Added objectives
- [ ] Generated random quests
- [ ] Created quest chain
- [ ] Exported system
- [ ] Reviewed reward calculations
- [ ] Read full documentation

---

**Quick Reference Guide v1.0**  
Updated: February 17, 2026
