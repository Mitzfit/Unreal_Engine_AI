# Advanced Quest & Mission Designer System

## 📋 Overview

A complete quest and mission system with visual editor, reward calculator, quest chains, random generation, NPC assignment, and location mapping.

## 🎯 Features

### 1. **Visual Editor**
- Web-based drag-and-drop interface
- Real-time quest node visualization
- Auto-layout algorithms
- Connection management between quests
- Properties panel for quest details

### 2. **Objective Tracking**
- Multiple objective types (kill, collect, deliver, reach, etc.)
- Progress tracking with percentages
- Optional and hidden objectives
- Time-limited objectives
- Callback system for completion events

### 3. **Reward Calculator**
- Difficulty-based scaling
- Complexity multipliers by objective type
- Player level-based scaling
- Support for multiple reward types (gold, XP, items, skills)
- Rarity system (common to legendary)

### 4. **Quest Chains**
- Linked quest sequences
- Progressive difficulty
- Chain completion tracking
- Faction-based rewards

### 5. **Random Generation**
- Template-based quest creation
- Multiple objective types per quest
- Randomized quantities and targets
- Automatic reward calculation

### 6. **NPC Assignment**
- Role-based NPC system (quest giver, target, escort, etc.)
- Location assignment
- Quest giver management
- Faction system
- Time-based schedules

### 7. **Location Mapping**
- 3D world coordinate system
- Distance calculations
- Pathfinding between locations
- Location types (city, dungeon, wilderness, etc.)
- Connection management

## 📦 Installation

### Prerequisites
```bash
pip install fastapi uvicorn pydantic
```

### Setup
```bash
# Copy the files to your project
cp quest_mission_visual_designer.py your_project/
cp quest_visual_editor_web.py your_project/
```

## 🚀 Quick Start

### 1. Using the Web Interface

Start the visual editor:
```bash
python quest_visual_editor_web.py
```

Open in browser: `http://localhost:8000`

**Features:**
- Create quests with name, description, difficulty
- Generate random quests automatically
- Drag-and-drop quest nodes on canvas
- View quest properties and objectives
- Auto-arrange quest layout
- Export quest system as JSON

### 2. Using Python API

```python
from quest_mission_visual_designer import AdvancedQuestSystem, Difficulty, ObjectiveType

# Initialize system
system = AdvancedQuestSystem()

# Create a location
city = system.location_mapper.create_location(
    name="Brighthaven",
    location_type=LocationType.CITY,
    x=0, y=0, z=0,
    difficulty=Difficulty.EASY
)

# Create an NPC
npc = system.npc_system.create_npc(
    name="Geralt the Wise",
    role=NPCRole.QUEST_GIVER,
    location_id=city.location_id,
    level=5
)

# Create a quest
quest = system.create_quest(
    name="Defeat the Dragons",
    description="Slay the dragons threatening the realm",
    difficulty=Difficulty.EPIC,
    giver_npc_id=npc.npc_id,
    giver_location_id=city.location_id
)

# Add objectives
system.add_objective_to_quest(
    quest.quest_id,
    ObjectiveType.KILL,
    "Defeat 3 Dragons",
    target_id="dragon",
    required_qty=3
)

# Calculate rewards
quest.rewards = RewardCalculator.calculate_quest_rewards(quest)

print(f"Quest: {quest.name}")
print(f"Total Rewards: {quest.calculate_total_reward(RewardType.GOLD)} gold")
```

## 🔧 API Reference

### Quest Management

#### Create Quest
```http
POST /api/quests
Content-Type: application/json

{
  "name": "Rescue the Princess",
  "description": "Save the princess from the tower",
  "difficulty": "HARD",
  "giver_npc_id": "npc_123",
  "giver_location_id": "loc_456"
}
```

#### Get All Quests
```http
GET /api/quests
```

#### Get Specific Quest
```http
GET /api/quests/{quest_id}
```

#### Add Objective to Quest
```http
POST /api/quests/{quest_id}/objectives
Content-Type: application/json

{
  "obj_type": "KILL",
  "description": "Defeat 5 goblins",
  "target_id": "goblin",
  "required_qty": 5,
  "optional": false
}
```

#### Calculate Quest Rewards
```http
POST /api/quests/{quest_id}/calculate-rewards
```

### Locations

#### Create Location
```http
POST /api/locations
Content-Type: application/json

{
  "name": "Ancient Ruins",
  "location_type": "RUIN",
  "x": 100.5,
  "y": 50.0,
  "z": -75.3,
  "difficulty": "EPIC",
  "description": "Mysterious ruins of an ancient civilization"
}
```

#### Get Nearest Locations
```http
GET /api/locations/{location_id}/nearest?count=5
```

#### Connect Locations
```http
POST /api/locations/{loc1_id}/connect/{loc2_id}
```

### NPCs

#### Create NPC
```http
POST /api/npcs
Content-Type: application/json

{
  "name": "Aldric the Knight",
  "role": "QUEST_GIVER",
  "location_id": "loc_123",
  "faction": "Order of the Light",
  "level": 10
}
```

#### Assign Quest to NPC
```http
POST /api/npcs/{npc_id}/assign-quest/{quest_id}
```

#### Get NPCs by Role
```http
GET /api/npcs/role/{role}
```

### Quest Chains

#### Create Quest Chain
```http
POST /api/chains
Content-Type: application/json

{
  "name": "Dragon Slayer Arc",
  "description": "A series of quests leading to the final dragon battle",
  "quest_ids": ["quest_1", "quest_2", "quest_3"],
  "faction": "Dragonslayers Guild"
}
```

#### Get Chain Progress
```http
GET /api/chains/{chain_id}/progress?completed_quests=quest_1,quest_2
```

### Random Generation

#### Generate Single Random Quest
```http
POST /api/quests/random/generate
```

#### Generate Multiple Random Quests
```http
POST /api/quests/random/batch?count=10
```

### Visualization

#### Get Visualization Data
```http
GET /api/visualization
```

Response:
```json
{
  "nodes": [
    {
      "id": "node_quest_1",
      "quest_id": "quest_1",
      "label": "Defeat the Goblin King",
      "x": 100,
      "y": 150,
      "color": "#FF8C00"
    }
  ],
  "edges": [
    {"from": "node_quest_1", "to": "node_quest_2"}
  ]
}
```

#### Auto-Layout Quests
```http
POST /api/visualization/auto-layout
```

#### Update Node Position
```http
PUT /api/visualization/nodes/{node_id}
Content-Type: application/json

{
  "x": 250,
  "y": 300
}
```

### System

#### Get System Statistics
```http
GET /api/system/stats
```

Response:
```json
{
  "total_quests": 42,
  "total_chains": 3,
  "total_locations": 15,
  "total_npcs": 28,
  "total_objectives": 156,
  "total_rewards": 89
}
```

#### Export System
```http
POST /api/system/export?filepath=quest_data.json
```

#### Download Export
```http
GET /api/system/export/download
```

## 🎓 Examples

### Example 1: Create a Dungeon Quest

```python
from quest_mission_visual_designer import *

system = AdvancedQuestSystem()

# Create dungeon location
dungeon = system.location_mapper.create_location(
    name="Shadow Crypt",
    location_type=LocationType.DUNGEON,
    x=500, y=-100, z=-200,
    difficulty=Difficulty.HARD
)

# Create quest giver
npc = system.npc_system.create_npc(
    name="Brother Marcus",
    role=NPCRole.QUEST_GIVER,
    location_id=dungeon.location_id,
    description="A monk seeking to reclaim holy artifacts"
)

# Create main quest
quest = system.create_quest(
    name="Reclaim the Holy Chalice",
    description="Enter the Shadow Crypt and retrieve the sacred chalice",
    difficulty=Difficulty.HARD,
    giver_npc_id=npc.npc_id,
    giver_location_id=dungeon.location_id,
    tags=["dungeon", "holy_artifact"]
)

# Add multiple objectives
system.add_objective_to_quest(
    quest.quest_id,
    ObjectiveType.REACH,
    "Enter the Shadow Crypt",
    target_id=dungeon.location_id
)

system.add_objective_to_quest(
    quest.quest_id,
    ObjectiveType.KILL,
    "Defeat the Shadow Guardians",
    target_id="shadow_guardian",
    required_qty=3
)

system.add_objective_to_quest(
    quest.quest_id,
    ObjectiveType.COLLECT,
    "Find the Holy Chalice",
    target_id="holy_chalice",
    required_qty=1
)

# Calculate and apply rewards
quest.rewards = RewardCalculator.calculate_quest_rewards(quest)

print(f"Quest Created: {quest.name}")
print(f"Objectives: {len(quest.objectives)}")
print(f"Gold Reward: {quest.calculate_total_reward(RewardType.GOLD)}")
```

### Example 2: Create a Quest Chain

```python
from quest_mission_visual_designer import *

system = AdvancedQuestSystem()

# Create multiple quests
quest1 = system.create_quest(
    name="Find the Lost Map",
    description="Locate the pirate map",
    difficulty=Difficulty.EASY
)

quest2 = system.create_quest(
    name="Gather Supplies",
    description="Prepare for the voyage",
    difficulty=Difficulty.NORMAL
)

quest3 = system.create_quest(
    name="Find the Treasure",
    description="Follow the map to the treasure",
    difficulty=Difficulty.HARD
)

# Create chain
chain = system.chains.create_chain(
    name="Pirate Treasure Hunt",
    description="A series of quests to find legendary pirate treasure",
    faction="Pirate Collective"
)

# Add quests to chain in order
quest1.next_quest_id = quest2.quest_id
quest2.next_quest_id = quest3.quest_id

system.chains.add_quest_to_chain(chain.chain_id, quest1)
system.chains.add_quest_to_chain(chain.chain_id, quest2)
system.chains.add_quest_to_chain(chain.chain_id, quest3)

print(f"Chain Created: {chain.name}")
print(f"Quests in Chain: {len(chain.quest_ids)}")
```

### Example 3: Generate Random Quest System

```python
from quest_mission_visual_designer import *

system = AdvancedQuestSystem()

# Generate 5 locations
for i in range(5):
    system.location_mapper.create_location(
        name=f"Location {i+1}",
        location_type=random.choice(list(LocationType)),
        x=random.uniform(-500, 500),
        y=random.uniform(-500, 500),
        z=random.uniform(-500, 500),
        difficulty=random.choice(list(Difficulty))
    )

# Generate 20 NPCs
for i in range(20):
    location_ids = list(system.location_mapper.locations.keys())
    system.npc_system.create_npc(
        name=f"NPC {i+1}",
        role=random.choice(list(NPCRole)),
        location_id=random.choice(location_ids)
    )

# Generate 50 random quests
for _ in range(50):
    quest = QuestRandomGenerator.generate_quest()
    system.quests[quest.quest_id] = quest
    system.visual_editor.add_quest_node(quest)

# Auto-arrange
system.visual_editor.auto_layout()

# Get statistics
stats = system.get_system_stats()
print(f"Generated System:")
print(f"  Quests: {stats['total_quests']}")
print(f"  Locations: {stats['total_locations']}")
print(f"  NPCs: {stats['total_npcs']}")
print(f"  Objectives: {stats['total_objectives']}")
```

## 📊 Data Models

### Quest
```python
@dataclass
class Quest:
    quest_id: str
    name: str
    description: str
    difficulty: Difficulty
    giver_npc_id: str
    objectives: List[Objective]
    rewards: List[Reward]
    quest_chain_id: Optional[str]
    next_quest_id: Optional[str]
    prerequisite_quests: List[str]
    time_limit: Optional[int]
    is_repeatable: bool
    is_hidden: bool
```

### Objective
```python
@dataclass
class Objective:
    objective_id: str
    quest_id: str
    obj_type: ObjectiveType
    description: str
    target_id: str
    required_qty: int
    current_qty: int
    is_optional: bool
    time_limit: Optional[int]
    location_id: Optional[str]
```

### Location
```python
@dataclass
class Location:
    location_id: str
    name: str
    location_type: LocationType
    x: float
    y: float
    z: float
    difficulty: Difficulty
    npcs: List[str]
    objectives: List[str]
    connections: List[str]
```

### NPC
```python
@dataclass
class NPC:
    npc_id: str
    name: str
    role: NPCRole
    location_id: str
    faction: str
    level: int
    available_quests: List[str]
    relationships: Dict[str, int]
```

## 🎨 Difficulty System

| Level | Multiplier | XP | Gold | Use Case |
|-------|-----------|----|----|----------|
| Trivial | 0.5x | 125 | 50 | Tutorial/Warmup |
| Easy | 0.8x | 200 | 80 | New players |
| Normal | 1.0x | 250 | 100 | Standard quests |
| Hard | 1.5x | 375 | 150 | Challenging |
| Epic | 2.5x | 625 | 250 | Major questline |
| Legendary | 4.0x | 1000 | 400 | Raid/Boss quests |
| Mythic | 6.0x | 1500 | 600 | Ultimate challenges |

## 📈 Reward Scaling

Rewards are calculated based on:

1. **Difficulty Multiplier** - Base multiplier from difficulty level
2. **Complexity Multiplier** - Average of objective type multipliers
3. **Objective Types** - Each objective type has different reward value
4. **Player Level Scaling** - Adjusted for player vs quest level difference

```
Final Reward = Base Value × Difficulty Multiplier × Complexity Multiplier × Player Level Scale
```

## 🔗 Pathfinding

Find shortest route between locations:

```python
path = system.location_mapper.get_path_between(location1_id, location2_id)
# Returns list of location IDs representing the path
```

## 💾 Persistence

### Export System
```python
system.export_system_state("my_quests.json")
```

### Import System
```python
system.import_system_state("my_quests.json")
```

## 🎬 Web Interface Features

### Dashboard
- Real-time quest statistics
- Visual quest chain editor
- NPC and location browser

### Quest Creator
- Form-based quest creation
- Objective builder
- Reward calculator
- Template system

### Visual Editor
- Drag-and-drop quest nodes
- Connection drawing
- Auto-layout algorithm
- Real-time property editing

### Export/Import
- JSON export of entire system
- Quest template library
- Batch quest import

## ⚙️ Configuration

### Server Settings
```python
app = FastAPI(title="Quest Designer", version="1.0.0")
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Database
```python
system = AdvancedQuestSystem("quest_system.db")
```

### Canvas Size
```python
system.visual_editor.canvas_width = 2560
system.visual_editor.canvas_height = 1440
```

## 🐛 Troubleshooting

### Quest rewards too low
- Check difficulty setting
- Verify objective types are set correctly
- Use `calculate_quest_rewards()` to recalculate

### NPCs not appearing at locations
- Verify location_id is valid
- Check NPC role is QUEST_GIVER for quest givers
- Use `get_npcs_at_location()` to verify

### Pathfinding not working
- Ensure locations are connected with `connect_locations()`
- Check location IDs are correct
- Try `find_nearest_location()` as alternative

## 📝 Best Practices

1. **Organization**
   - Group related quests into chains
   - Use faction system for organization
   - Tag quests for categorization

2. **Balance**
   - Use difficulty multipliers consistently
   - Scale rewards based on objective count
   - Test player progression

3. **Performance**
   - Use auto-layout for large quest systems (100+)
   - Cache nearest location lookups
   - Batch objective updates

4. **Design**
   - Create quest chains for narrative flow
   - Use optional objectives for replayability
   - Hide advanced objectives for discovery

## 🚀 Advanced Features

### Custom Objective Types
Extend `ObjectiveType` enum:
```python
class ObjectiveType(Enum):
    CUSTOM_TYPE = "custom_type"
```

### Custom Reward Types
Add to `RewardType` enum:
```python
class RewardType(Enum):
    CUSTOM_REWARD = "custom_reward"
```

### Custom NPC Roles
Extend `NPCRole` enum for specialized roles

### Custom Location Types
Add to `LocationType` for world-specific locations

## 📞 Support

For issues or questions:
1. Check the example code
2. Review API reference
3. Test with web interface first
4. Check database for data integrity

---

**Version:** 1.0.0  
**Last Updated:** February 17, 2026  
**Status:** Production Ready ✅
