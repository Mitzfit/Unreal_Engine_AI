"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          WEB-BASED VISUAL QUEST & MISSION EDITOR                            ║
║  Real-time Visual Editing · Drag-and-drop · Live Preview                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import json
import asyncio
from pathlib import Path
import uvicorn

from quest_mission_visual_designer import (
    AdvancedQuestSystem, Quest, Objective, Location, NPC,
    ObjectiveType, LocationType, NPCRole, Difficulty, RewardType,
    QuestChainSystem, RewardCalculator, QuestRandomGenerator
)


# ═══════════════════════════ PYDANTIC MODELS ═══════════════════════════════════

class ObjectiveCreate(BaseModel):
    obj_type: str
    description: str
    target_id: str = ""
    required_qty: int = 1
    optional: bool = False
    hidden: bool = False
    time_limit: Optional[int] = None

class RewardCreate(BaseModel):
    reward_type: str
    value: Any
    quantity: int = 1
    rarity: str = "common"

class QuestCreate(BaseModel):
    name: str
    description: str
    difficulty: str = "NORMAL"
    giver_npc_id: str = ""
    giver_location_id: str = ""
    tags: List[str] = []

class LocationCreate(BaseModel):
    name: str
    location_type: str
    x: float
    y: float
    z: float
    difficulty: str = "NORMAL"
    description: str = ""

class NPCCreate(BaseModel):
    name: str
    role: str
    location_id: str
    faction: str = ""
    level: int = 1
    description: str = ""

class NodePosition(BaseModel):
    node_id: str
    x: float
    y: float

class ConnectionCreate(BaseModel):
    from_quest_id: str
    to_quest_id: str

class QuestChainCreate(BaseModel):
    name: str
    description: str
    quest_ids: List[str]
    faction: str = ""


# ═══════════════════════════ FASTAPI APP ═══════════════════════════════════════

app = FastAPI(title="Quest & Mission Visual Designer", version="1.0.0")

# Initialize quest system
quest_system = AdvancedQuestSystem("quest_system_web.db")


# ─────────────────────────── QUEST ENDPOINTS ──────────────────────────────

@app.get("/api/quests")
async def get_all_quests():
    """Get all quests."""
    return {
        "quests": [q.to_dict() for q in quest_system.quests.values()]
    }

@app.get("/api/quests/{quest_id}")
async def get_quest(quest_id: str):
    """Get specific quest."""
    if quest_id not in quest_system.quests:
        raise HTTPException(status_code=404, detail="Quest not found")
    
    quest = quest_system.quests[quest_id]
    return quest.to_dict()

@app.post("/api/quests")
async def create_quest(data: QuestCreate):
    """Create new quest."""
    try:
        difficulty = Difficulty[data.difficulty]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid difficulty")

    quest = quest_system.create_quest(
        name=data.name,
        description=data.description,
        difficulty=difficulty,
        giver_npc_id=data.giver_npc_id,
        giver_location_id=data.giver_location_id,
        tags=data.tags,
    )
    return quest.to_dict()

@app.put("/api/quests/{quest_id}")
async def update_quest(quest_id: str, data: QuestCreate):
    """Update quest."""
    if quest_id not in quest_system.quests:
        raise HTTPException(status_code=404, detail="Quest not found")

    quest = quest_system.quests[quest_id]
    quest.name = data.name
    quest.description = data.description
    quest.giver_npc_id = data.giver_npc_id
    quest.giver_location_id = data.giver_location_id
    quest.tags = data.tags
    
    try:
        quest.difficulty = Difficulty[data.difficulty]
    except KeyError:
        pass

    return quest.to_dict()

@app.delete("/api/quests/{quest_id}")
async def delete_quest(quest_id: str):
    """Delete quest."""
    if quest_id not in quest_system.quests:
        raise HTTPException(status_code=404, detail="Quest not found")
    
    del quest_system.quests[quest_id]
    return {"status": "deleted"}

@app.post("/api/quests/{quest_id}/objectives")
async def add_objective(quest_id: str, data: ObjectiveCreate):
    """Add objective to quest."""
    if quest_id not in quest_system.quests:
        raise HTTPException(status_code=404, detail="Quest not found")

    try:
        obj_type = ObjectiveType[data.obj_type]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid objective type")

    obj = quest_system.add_objective_to_quest(
        quest_id,
        obj_type,
        data.description,
        data.target_id,
        data.required_qty,
        data.optional
    )
    
    if obj is None:
        raise HTTPException(status_code=400, detail="Could not add objective")

    return obj.to_dict()

@app.post("/api/quests/{quest_id}/calculate-rewards")
async def calculate_rewards(quest_id: str):
    """Calculate rewards for quest."""
    if quest_id not in quest_system.quests:
        raise HTTPException(status_code=404, detail="Quest not found")

    quest = quest_system.quests[quest_id]
    rewards = RewardCalculator.calculate_quest_rewards(quest)
    quest.rewards = rewards

    return {
        "rewards": [r.to_dict() for r in rewards]
    }


# ─────────────────────────── OBJECTIVE ENDPOINTS ──────────────────────────

@app.post("/api/objectives/{objective_id}/update")
async def update_objective_progress(objective_id: str, amount: int = 1):
    """Update objective progress."""
    # Find the objective
    for quest in quest_system.quests.values():
        for obj in quest.objectives:
            if obj.objective_id == objective_id:
                obj.update(amount)
                return obj.to_dict()

    raise HTTPException(status_code=404, detail="Objective not found")


# ─────────────────────────── LOCATION ENDPOINTS ──────────────────────────

@app.get("/api/locations")
async def get_all_locations():
    """Get all locations."""
    return {
        "locations": [loc.to_dict() for loc in quest_system.location_mapper.locations.values()]
    }

@app.get("/api/locations/{location_id}")
async def get_location(location_id: str):
    """Get specific location."""
    if location_id not in quest_system.location_mapper.locations:
        raise HTTPException(status_code=404, detail="Location not found")
    
    loc = quest_system.location_mapper.locations[location_id]
    return loc.to_dict()

@app.post("/api/locations")
async def create_location(data: LocationCreate):
    """Create new location."""
    try:
        location_type = LocationType[data.location_type]
        difficulty = Difficulty[data.difficulty]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid type or difficulty")

    loc = quest_system.location_mapper.create_location(
        name=data.name,
        location_type=location_type,
        x=data.x,
        y=data.y,
        z=data.z,
        difficulty=difficulty,
        description=data.description,
    )
    return loc.to_dict()

@app.get("/api/locations/{location_id}/npcs")
async def get_location_npcs(location_id: str):
    """Get NPCs at location."""
    if location_id not in quest_system.location_mapper.locations:
        raise HTTPException(status_code=404, detail="Location not found")

    npcs = quest_system.npc_system.get_npcs_at_location(location_id)
    return {"npcs": [n.to_dict() for n in npcs]}

@app.post("/api/locations/{loc1_id}/connect/{loc2_id}")
async def connect_locations(loc1_id: str, loc2_id: str):
    """Connect two locations."""
    if loc1_id not in quest_system.location_mapper.locations:
        raise HTTPException(status_code=404, detail="Location 1 not found")
    if loc2_id not in quest_system.location_mapper.locations:
        raise HTTPException(status_code=404, detail="Location 2 not found")

    quest_system.location_mapper.connect_locations(loc1_id, loc2_id)
    return {"status": "connected"}

@app.get("/api/locations/{location_id}/nearest")
async def get_nearest_locations(location_id: str, count: int = 5):
    """Get nearest locations."""
    if location_id not in quest_system.location_mapper.locations:
        raise HTTPException(status_code=404, detail="Location not found")

    loc = quest_system.location_mapper.locations[location_id]
    nearest = quest_system.location_mapper.find_nearest_location(loc, count)
    
    return {
        "locations": [
            {**n.to_dict(), "distance": loc.distance_to(n)}
            for n in nearest
        ]
    }

@app.get("/api/locations/map/export")
async def export_location_map():
    """Export all locations as map data."""
    return quest_system.location_mapper.to_dict()


# ─────────────────────────── NPC ENDPOINTS ────────────────────────────────

@app.get("/api/npcs")
async def get_all_npcs():
    """Get all NPCs."""
    return {
        "npcs": [n.to_dict() for n in quest_system.npc_system.npcs.values()]
    }

@app.get("/api/npcs/{npc_id}")
async def get_npc(npc_id: str):
    """Get specific NPC."""
    if npc_id not in quest_system.npc_system.npcs:
        raise HTTPException(status_code=404, detail="NPC not found")
    
    npc = quest_system.npc_system.npcs[npc_id]
    return npc.to_dict()

@app.post("/api/npcs")
async def create_npc(data: NPCCreate):
    """Create new NPC."""
    try:
        role = NPCRole[data.role]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid NPC role")

    if data.location_id not in quest_system.location_mapper.locations:
        raise HTTPException(status_code=400, detail="Location not found")

    npc = quest_system.npc_system.create_npc(
        name=data.name,
        role=role,
        location_id=data.location_id,
        faction=data.faction,
        level=data.level,
        description=data.description,
    )
    return npc.to_dict()

@app.post("/api/npcs/{npc_id}/assign-quest/{quest_id}")
async def assign_quest_to_npc(npc_id: str, quest_id: str):
    """Assign quest to NPC."""
    if npc_id not in quest_system.npc_system.npcs:
        raise HTTPException(status_code=404, detail="NPC not found")
    if quest_id not in quest_system.quests:
        raise HTTPException(status_code=404, detail="Quest not found")

    success = quest_system.npc_system.assign_quest_to_npc(npc_id, quest_id)
    if not success:
        raise HTTPException(status_code=400, detail="NPC must be a quest giver")

    return {"status": "assigned"}

@app.get("/api/npcs/role/{role}")
async def get_npcs_by_role(role: str):
    """Get NPCs by role."""
    try:
        npc_role = NPCRole[role]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid role")

    npcs = quest_system.npc_system.find_suitable_npcs(npc_role, count=100)
    return {"npcs": [n.to_dict() for n in npcs]}


# ─────────────────────────── QUEST CHAIN ENDPOINTS ──────────────────────────

@app.get("/api/chains")
async def get_all_chains():
    """Get all quest chains."""
    return {
        "chains": [c.to_dict() for c in quest_system.chains.chains.values()]
    }

@app.post("/api/chains")
async def create_chain(data: QuestChainCreate):
    """Create quest chain."""
    # Verify all quests exist
    for qid in data.quest_ids:
        if qid not in quest_system.quests:
            raise HTTPException(status_code=404, detail=f"Quest {qid} not found")

    chain = quest_system.chains.create_chain(
        name=data.name,
        description=data.description,
        faction=data.faction
    )

    for qid in data.quest_ids:
        quest_system.chains.add_quest_to_chain(chain.chain_id, quest_system.quests[qid])

    return chain.to_dict()

@app.get("/api/chains/{chain_id}")
async def get_chain(chain_id: str):
    """Get specific chain."""
    if chain_id not in quest_system.chains.chains:
        raise HTTPException(status_code=404, detail="Chain not found")

    chain = quest_system.chains.chains[chain_id]
    return chain.to_dict()

@app.get("/api/chains/{chain_id}/progress")
async def get_chain_progress(chain_id: str, completed_quests: str = ""):
    """Get chain completion progress."""
    if chain_id not in quest_system.chains.chains:
        raise HTTPException(status_code=404, detail="Chain not found")

    completed = set(completed_quests.split(",")) if completed_quests else set()
    completed_count, total_count = quest_system.chains.get_chain_progress(chain_id, completed)

    return {
        "completed": completed_count,
        "total": total_count,
        "progress_pct": (completed_count / max(1, total_count)) * 100,
    }


# ─────────────────────────── VISUAL EDITOR ENDPOINTS ──────────────────────

@app.get("/api/visualization")
async def get_visualization():
    """Get current visualization."""
    return quest_system.visual_editor.export_visualization()

@app.post("/api/visualization/auto-layout")
async def auto_layout():
    """Auto-arrange quest nodes."""
    quest_system.visual_editor.auto_layout()
    return quest_system.visual_editor.export_visualization()

@app.put("/api/visualization/nodes/{node_id}")
async def update_node_position(node_id: str, data: NodePosition):
    """Update node position."""
    if node_id not in quest_system.visual_editor.nodes:
        raise HTTPException(status_code=404, detail="Node not found")

    node = quest_system.visual_editor.nodes[node_id]
    node.x = data.x
    node.y = data.y
    
    return node.to_dict()

@app.post("/api/visualization/connect")
async def create_connection(data: ConnectionCreate):
    """Create connection between quests."""
    success = quest_system.visual_editor.connect_quests(
        data.from_quest_id,
        data.to_quest_id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Could not connect quests")

    # Also set next_quest_id
    if data.from_quest_id in quest_system.quests:
        quest_system.quests[data.from_quest_id].next_quest_id = data.to_quest_id

    return {"status": "connected"}


# ─────────────────────────── RANDOM GENERATION ENDPOINTS ────────────────────

@app.post("/api/quests/random/generate")
async def generate_random_quest():
    """Generate a random quest."""
    quest = QuestRandomGenerator.generate_quest()
    quest_system.quests[quest.quest_id] = quest
    quest_system.visual_editor.add_quest_node(quest)
    return quest.to_dict()

@app.post("/api/quests/random/batch")
async def generate_random_quests(count: int = 5):
    """Generate multiple random quests."""
    generated = []
    for _ in range(count):
        quest = QuestRandomGenerator.generate_quest()
        quest_system.quests[quest.quest_id] = quest
        quest_system.visual_editor.add_quest_node(quest)
        generated.append(quest.to_dict())

    return {"quests": generated}


# ─────────────────────────── SYSTEM ENDPOINTS ────────────────────────────

@app.get("/api/system/stats")
async def get_system_stats():
    """Get system statistics."""
    return quest_system.get_system_stats()

@app.post("/api/system/export")
async def export_system(filepath: str = "quest_system_export.json"):
    """Export entire system."""
    quest_system.export_system_state(filepath)
    return {"filepath": filepath}

@app.get("/api/system/export/download")
async def download_export():
    """Download system export."""
    export_file = "quest_system_export.json"
    quest_system.export_system_state(export_file)
    return FileResponse(export_file, filename="quest_system_export.json")

@app.post("/api/system/import")
async def import_system(file: UploadFile = File(...)):
    """Import system state."""
    content = await file.read()
    data = json.loads(content)
    quest_system.import_system_state(json.dumps(data))
    return {"status": "imported"}


# ─────────────────────────── HEALTH CHECK ──────────────────────────────

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "system": quest_system.get_system_stats()
    }


# ═══════════════════════════ HTML INTERFACE ═════════════════════════════════════

HTML_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>Quest & Mission Visual Designer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            height: 100vh;
            overflow: hidden;
        }
        
        .container {
            display: flex;
            height: 100vh;
        }
        
        .sidebar {
            width: 300px;
            background: white;
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
            overflow-y: auto;
            padding: 20px;
        }
        
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        
        .toolbar {
            background: white;
            padding: 15px 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .canvas {
            flex: 1;
            background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%);
            position: relative;
            overflow: auto;
        }
        
        .quest-node {
            position: absolute;
            background: white;
            border: 2px solid #667eea;
            border-radius: 8px;
            padding: 10px;
            min-width: 150px;
            cursor: move;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            z-index: 10;
        }
        
        .quest-node.selected {
            border-color: #ff6b6b;
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
        }
        
        .quest-node h4 {
            font-size: 12px;
            margin-bottom: 5px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .quest-node .difficulty {
            font-size: 10px;
            padding: 3px 6px;
            border-radius: 3px;
            background: #f0f0f0;
            width: fit-content;
        }
        
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }
        
        button:hover {
            background: #764ba2;
        }
        
        .sidebar-section {
            margin-bottom: 25px;
        }
        
        .sidebar-section h3 {
            font-size: 14px;
            margin-bottom: 10px;
            color: #667eea;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .sidebar-section input,
        .sidebar-section select,
        .sidebar-section textarea {
            width: 100%;
            padding: 8px;
            margin-bottom: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-family: inherit;
        }
        
        .quest-list {
            background: #f9f9f9;
            border-radius: 5px;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .quest-item {
            padding: 10px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            font-size: 13px;
            transition: background 0.2s;
        }
        
        .quest-item:hover {
            background: #f0f0f0;
        }
        
        .stats {
            background: white;
            padding: 15px;
            border-radius: 5px;
            margin-top: auto;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .stat-row {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            margin-bottom: 8px;
        }
        
        .stat-value {
            font-weight: bold;
            color: #667eea;
        }
        
        .properties-panel {
            position: fixed;
            right: 0;
            top: 50px;
            width: 300px;
            background: white;
            box-shadow: -2px 0 10px rgba(0,0,0,0.1);
            overflow-y: auto;
            padding: 20px;
            display: none;
            max-height: calc(100vh - 50px);
        }
        
        .properties-panel.active {
            display: block;
        }
        
        .close-properties {
            position: absolute;
            right: 10px;
            top: 10px;
            background: none;
            border: none;
            font-size: 20px;
            cursor: pointer;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <h2 style="margin-bottom: 20px; color: #667eea;">Quest Designer</h2>
            
            <div class="sidebar-section">
                <h3>Create Quest</h3>
                <input id="questName" type="text" placeholder="Quest Name">
                <textarea id="questDesc" placeholder="Description" rows="3"></textarea>
                <select id="questDiff">
                    <option value="EASY">Easy</option>
                    <option value="NORMAL" selected>Normal</option>
                    <option value="HARD">Hard</option>
                    <option value="EPIC">Epic</option>
                </select>
                <button onclick="createNewQuest()">Create Quest</button>
                <button onclick="generateRandomQuest()">Random Quest</button>
            </div>
            
            <div class="sidebar-section">
                <h3>Actions</h3>
                <button onclick="autoLayout()" style="width: 100%;">Auto Layout</button>
                <button onclick="exportSystem()" style="width: 100%; margin-top: 10px;">Export</button>
                <button onclick="clearCanvas()" style="width: 100%; margin-top: 10px;">Clear All</button>
            </div>
            
            <div class="sidebar-section">
                <h3>Active Quests</h3>
                <div id="questList" class="quest-list"></div>
            </div>
            
            <div class="stats" id="stats">
                <div class="stat-row">
                    <span>Total Quests:</span>
                    <span class="stat-value" id="statQuests">0</span>
                </div>
                <div class="stat-row">
                    <span>Locations:</span>
                    <span class="stat-value" id="statLocations">0</span>
                </div>
                <div class="stat-row">
                    <span>NPCs:</span>
                    <span class="stat-value" id="statNPCs">0</span>
                </div>
                <div class="stat-row">
                    <span>Objectives:</span>
                    <span class="stat-value" id="statObjectives">0</span>
                </div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="toolbar">
                <span style="margin-right: auto;">Visual Quest Editor</span>
                <button onclick="toggleProperties()">Show Properties</button>
                <button onclick="help()">Help</button>
            </div>
            <div class="canvas" id="canvas"></div>
        </div>
        
        <div class="properties-panel" id="propertiesPanel">
            <button class="close-properties" onclick="toggleProperties()">✕</button>
            <h3 id="propTitle" style="margin-bottom: 15px;">Quest Properties</h3>
            <div id="propertiesContent"></div>
        </div>
    </div>

    <script>
        const API_BASE = '/api';
        let selectedQuest = null;
        let quests = {};
        
        async function createNewQuest() {
            const name = document.getElementById('questName').value;
            const desc = document.getElementById('questDesc').value;
            const diff = document.getElementById('questDiff').value;
            
            if (!name) {
                alert('Please enter a quest name');
                return;
            }
            
            try {
                const res = await fetch(`${API_BASE}/quests`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        name, description: desc, difficulty: diff
                    }),
                    signal: AbortSignal.timeout(5000)
                });
                
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const quest = await res.json();
                quests[quest.quest_id] = quest;
                addQuestNode(quest);
                updateStats();
                document.getElementById('questName').value = '';
                document.getElementById('questDesc').value = '';
            } catch (e) {
                alert('Error creating quest: ' + e.message);
                console.error(e);
            }
        }
        
        async function generateRandomQuest() {
            try {
                const res = await fetch(`${API_BASE}/quests/random/generate`, {method: 'POST', signal: AbortSignal.timeout(5000)});
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const quest = await res.json();
                quests[quest.quest_id] = quest;
                addQuestNode(quest);
                updateStats();
            } catch (e) {
                alert('Error generating random quest: ' + e.message);
            }
        }
        
        function addQuestNode(quest) {
            const canvas = document.getElementById('canvas');
            const node = document.createElement('div');
            node.className = 'quest-node';
            node.id = `node_${quest.quest_id}`;
            node.style.left = (Math.random() * (canvas.offsetWidth - 200)) + 'px';
            node.style.top = (Math.random() * (canvas.offsetHeight - 100)) + 'px';
            
            node.innerHTML = `
                <h4>${quest.name}</h4>
                <div class="difficulty">${quest.difficulty}</div>
            `;
            
            node.onclick = (e) => {
                e.stopPropagation();
                document.querySelectorAll('.quest-node').forEach(n => n.classList.remove('selected'));
                node.classList.add('selected');
                selectedQuest = quest;
                showProperties(quest);
            };
            
            // Make draggable
            let isDragging = false;
            let dragOffsetX, dragOffsetY;
            
            node.onmousedown = (e) => {
                isDragging = true;
                dragOffsetX = e.clientX - node.offsetLeft;
                dragOffsetY = e.clientY - node.offsetTop;
            };
            
            document.onmousemove = (e) => {
                if (isDragging && node.classList.contains('selected')) {
                    node.style.left = (e.clientX - dragOffsetX) + 'px';
                    node.style.top = (e.clientY - dragOffsetY) + 'px';
                }
            };
            
            document.onmouseup = () => {
                isDragging = false;
            };
            
            canvas.appendChild(node);
        }
        
        function showProperties(quest) {
            const content = document.getElementById('propertiesContent');
            content.innerHTML = `
                <div style="font-size: 13px;">
                    <p><strong>ID:</strong> ${quest.quest_id}</p>
                    <p><strong>Difficulty:</strong> ${quest.difficulty}</p>
                    <p><strong>Status:</strong> ${quest.status}</p>
                    <p><strong>Progress:</strong> ${quest.progress}%</p>
                    <p><strong>Objectives:</strong> ${quest.objectives.length}</p>
                    <p><strong>Total Rewards:</strong> ${quest.total_gold} gold, ${quest.total_xp} XP</p>
                </div>
            `;
            document.getElementById('propertiesPanel').classList.add('active');
        }
        
        async function autoLayout() {
            try {
                const res = await fetch(`${API_BASE}/visualization/auto-layout`, {method: 'POST', signal: AbortSignal.timeout(5000)});
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const viz = await res.json();
                const canvas = document.getElementById('canvas');
                canvas.innerHTML = '';
                viz.nodes.forEach(node => {
                    const quest = quests[node.quest_id];
                    if (quest) {
                        const element = document.createElement('div');
                        element.className = 'quest-node';
                        element.id = `node_${node.quest_id}`;
                        element.style.left = node.x + 'px';
                        element.style.top = node.y + 'px';
                        element.innerHTML = `<h4>${node.label}</h4>`;
                        canvas.appendChild(element);
                    }
                });
            } catch (e) {
                alert('Error during auto layout: ' + e.message);
            }
        }
        
        async function updateStats() {
            try {
                const res = await fetch(`${API_BASE}/system/stats`, {signal: AbortSignal.timeout(5000)});
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const stats = await res.json();
                document.getElementById('statQuests').textContent = stats.total_quests;
                document.getElementById('statLocations').textContent = stats.total_locations;
                document.getElementById('statNPCs').textContent = stats.total_npcs;
                document.getElementById('statObjectives').textContent = stats.total_objectives;
            } catch (e) {
                console.warn('Failed to update stats:', e);
            }
        }
        
        function toggleProperties() {
            document.getElementById('propertiesPanel').classList.toggle('active');
        }
        
        async function exportSystem() {
            try {
                const res = await fetch(`${API_BASE}/system/export/download`, {signal: AbortSignal.timeout(5000)});
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'quest_system_export.json';
                a.click();
                URL.revokeObjectURL(url);
            } catch (e) {
                alert('Error exporting system: ' + e.message);
            }
        }
        
        function clearCanvas() {
            if (confirm('Clear all quests?')) {
                document.getElementById('canvas').innerHTML = '';
                quests = {};
            }
        }
        
        function help() {
            alert('Quest & Mission Visual Designer\\n\\n' +
                  'Create Quests: Enter details and click Create Quest\\n' +
                  'Drag Nodes: Click and drag quest nodes to position\\n' +
                  'Properties: Select a quest to see details\\n' +
                  'Auto Layout: Automatically arrange all quests\\n' +
                  'Export: Download quest system data\\n' +
                  '\\nTip: Generate random quests to fill your world!');
        }
        
        // Initial load
        updateStats();
    </script>
</body>
</html>
"""

@app.get("/")
async def serve_interface():
    """Serve the web interface."""
    return HTMLResponse(content=HTML_INTERFACE)


@app.get("/health")
async def health_check():
    """Health check endpoint for Quest Visual Designer."""
    try:
        total_quests = len(quest_system.quests)
    except Exception:
        total_quests = 0
    return {"status": "healthy", "service": "Quest Visual Designer", "total_quests": total_quests}


if __name__ == "__main__":
    print("Starting Quest & Mission Visual Designer...")
    print("Open: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
