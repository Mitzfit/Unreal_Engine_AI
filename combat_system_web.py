"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     COMBAT SYSTEM WEB INTERFACE & REST API                                  ║
║  FastAPI server with dashboard, real-time updates, combat simulation       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
import json
import uuid
from datetime import datetime
import logging

from combat_system import (
    CombatSystem, CombatEntity, DamageType, StatusEffectType, ComboChainType,
    DamageFormula, StatusEffect, ComboMove, ComboChain, SkillTreeNodeType
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════ MODELS ══════════════════════════════════════════

class CreateDamageFormulaRequest(BaseModel):
    name: str
    description: str
    base_damage: float = 10.0
    damage_type: str = "physical"

class CreateStatusEffectRequest(BaseModel):
    name: str
    description: str
    effect_type: str
    duration: int = 5

class CreateComboMoveRequest(BaseModel):
    name: str
    description: str
    formula_id: str
    damage_multiplier: float = 1.0

class CreateComboChainRequest(BaseModel):
    name: str
    description: str
    moves: List[str]
    chain_type: str = "linear"

class CreateEntityRequest(BaseModel):
    name: str
    level: int = 1
    health: float = 100
    attack_power: float = 10

class PerformAttackRequest(BaseModel):
    attacker_id: str
    target_id: str
    formula_id: str
    weapon_damage: float = 0.0

class AddStatusEffectRequest(BaseModel):
    effect_id: str

class ValidateComboRequest(BaseModel):
    chain_id: str
    executed_moves: List[str]
    time_between_moves: List[float]

# ═══════════════════════════ FASTAPI APP ════════════════════════════════════

app = FastAPI(title="Combat System Designer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global system instance
combat_system = CombatSystem()
active_entities: Dict[str, CombatEntity] = {}
active_connections: Dict[str, List[WebSocket]] = {}

# ═══════════════════════════ WEBSOCKET ═══════════════════════════════════════

@app.websocket("/ws/combat/{player_id}")
async def websocket_combat(websocket: WebSocket, player_id: str):
    """WebSocket for real-time combat updates."""
    await websocket.accept()
    
    if player_id not in active_connections:
        active_connections[player_id] = []
    active_connections[player_id].append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            command = json.loads(data)
            
            if command.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif command.get("type") == "get_status":
                if player_id in active_entities:
                    entity = active_entities[player_id]
                    await websocket.send_json({
                        "type": "status",
                        "data": entity.to_dict()
                    })
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_connections[player_id].remove(websocket)


async def broadcast_combat_update(player_id: str, message: Dict):
    """Broadcast combat update."""
    if player_id in active_connections:
        for connection in active_connections[player_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")

# ═══════════════════════════ DAMAGE FORMULA ENDPOINTS ═════════════════════════

@app.post("/api/formulas/create", response_model=Dict)
def create_damage_formula(request: CreateDamageFormulaRequest):
    """Create damage formula."""
    try:
        damage_type = DamageType[request.damage_type.upper()]
        formula = combat_system.create_damage_formula(
            request.name,
            request.description,
            request.base_damage,
            damage_type
        )
        return {
            "status": "success",
            "formula": formula.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/formulas", response_model=Dict)
def list_damage_formulas():
    """List all damage formulas."""
    return {
        "count": len(combat_system.damage_formulas),
        "formulas": [f.to_dict() for f in combat_system.damage_formulas.values()]
    }


@app.get("/api/formulas/{formula_id}", response_model=Dict)
def get_damage_formula(formula_id: str):
    """Get specific damage formula."""
    if formula_id not in combat_system.damage_formulas:
        raise HTTPException(status_code=404, detail="Formula not found")
    formula = combat_system.damage_formulas[formula_id]
    return formula.to_dict()


# ═══════════════════════════ STATUS EFFECT ENDPOINTS ═════════════════════════

@app.post("/api/effects/create", response_model=Dict)
def create_status_effect(request: CreateStatusEffectRequest):
    """Create status effect."""
    try:
        effect_type = StatusEffectType[request.effect_type.upper()]
        effect = combat_system.create_status_effect(
            request.name,
            request.description,
            effect_type,
            request.duration
        )
        return {
            "status": "success",
            "effect": effect.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/effects", response_model=Dict)
def list_status_effects():
    """List all status effects."""
    return {
        "count": len(combat_system.status_effects),
        "effects": [e.to_dict() for e in combat_system.status_effects.values()]
    }


# ═══════════════════════════ COMBO ENDPOINTS ═════════════════════════════════

@app.post("/api/combos/moves/create", response_model=Dict)
def create_combo_move(request: CreateComboMoveRequest):
    """Create combo move."""
    if request.formula_id not in combat_system.damage_formulas:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    move = combat_system.create_combo_move(
        request.name,
        request.description,
        request.formula_id,
        request.damage_multiplier
    )
    return {
        "status": "success",
        "move": move.to_dict()
    }


@app.get("/api/combos/moves", response_model=Dict)
def list_combo_moves():
    """List all combo moves."""
    return {
        "count": len(combat_system.combo_moves),
        "moves": [m.to_dict() for m in combat_system.combo_moves.values()]
    }


@app.post("/api/combos/chains/create", response_model=Dict)
def create_combo_chain(request: CreateComboChainRequest):
    """Create combo chain."""
    try:
        chain_type = ComboChainType[request.chain_type.upper()]
        chain = combat_system.create_combo_chain(
            request.name,
            request.description,
            request.moves,
            chain_type
        )
        return {
            "status": "success",
            "chain": chain.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/combos/chains", response_model=Dict)
def list_combo_chains():
    """List all combo chains."""
    return {
        "count": len(combat_system.combo_chains),
        "chains": [c.to_dict() for c in combat_system.combo_chains.values()]
    }


@app.post("/api/combos/validate")
def validate_combo(request: ValidateComboRequest):
    """Validate combo sequence."""
    is_valid, bonus = combat_system.validate_combo_sequence(
        request.chain_id,
        request.executed_moves,
        request.time_between_moves
    )
    return {
        "valid": is_valid,
        "damage_bonus": bonus
    }


# ═══════════════════════════ ENTITY ENDPOINTS ═════════════════════════════════

@app.post("/api/entities/create", response_model=Dict)
def create_entity(request: CreateEntityRequest):
    """Create combat entity."""
    entity = CombatEntity(
        entity_id=str(uuid.uuid4())[:8],
        name=request.name,
        level=request.level,
        health=request.health,
        max_health=request.health,
        stats={"attack_power": request.attack_power}
    )
    active_entities[entity.entity_id] = entity
    return {
        "status": "success",
        "entity": entity.to_dict()
    }


@app.get("/api/entities/{entity_id}", response_model=Dict)
def get_entity(entity_id: str):
    """Get entity."""
    if entity_id not in active_entities:
        raise HTTPException(status_code=404, detail="Entity not found")
    return active_entities[entity_id].to_dict()


@app.post("/api/entities/{entity_id}/damage")
def apply_damage(entity_id: str, damage: float, damage_type: str = "physical"):
    """Apply damage to entity."""
    if entity_id not in active_entities:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    entity = active_entities[entity_id]
    dt = DamageType[damage_type.upper()]
    actual_damage = entity.take_damage(damage, dt)
    
    return {
        "status": "success",
        "damage_taken": actual_damage,
        "health": entity.health,
        "is_alive": entity.is_alive
    }


@app.post("/api/entities/{entity_id}/heal")
def heal_entity(entity_id: str, amount: float):
    """Heal entity."""
    if entity_id not in active_entities:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    entity = active_entities[entity_id]
    entity.heal(amount)
    
    return {
        "status": "success",
        "health": entity.health,
        "health_pct": entity.health_pct
    }


@app.post("/api/entities/{entity_id}/add-effect")
def add_effect_to_entity(entity_id: str, request: AddStatusEffectRequest):
    """Add status effect to entity."""
    if entity_id not in active_entities:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    if request.effect_id not in combat_system.status_effects:
        raise HTTPException(status_code=404, detail="Effect not found")
    
    entity = active_entities[entity_id]
    effect = combat_system.status_effects[request.effect_id]
    success = entity.add_effect(effect)
    
    return {
        "status": "success" if success else "effect_blocked",
        "entity": entity.to_dict()
    }


# ═══════════════════════════ COMBAT ENDPOINTS ═════════════════════════════════

@app.post("/api/combat/attack")
def perform_attack(request: PerformAttackRequest, background_tasks: BackgroundTasks):
    """Perform attack."""
    if request.attacker_id not in active_entities:
        raise HTTPException(status_code=404, detail="Attacker not found")
    if request.target_id not in active_entities:
        raise HTTPException(status_code=404, detail="Target not found")
    if request.formula_id not in combat_system.damage_formulas:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    attacker = active_entities[request.attacker_id]
    target = active_entities[request.target_id]
    
    # Calculate damage
    result = combat_system.calculate_damage(
        request.formula_id,
        attacker,
        target,
        request.weapon_damage
    )
    
    # Apply damage if hit
    if result.did_hit:
        target.take_damage(result.damage)
    
    # Broadcast update
    background_tasks.add_task(
        broadcast_combat_update,
        request.target_id,
        {
            "type": "combat_update",
            "entity": target.to_dict()
        }
    )
    
    return {
        "status": "success",
        "hit_result": result.to_dict(),
        "target": target.to_dict()
    }


@app.get("/api/combat/critical-chance")
def get_critical_chance(
    attacker_level: int,
    attacker_dex: float,
    target_level: int,
    target_armor: float = 0
):
    """Get critical chance calculation."""
    chance = combat_system.crit_calculator.calculate_crit_chance(
        attacker_level, attacker_dex, 0,
        target_level, target_armor, 0
    )
    return {
        "crit_chance": chance,
        "is_critical": combat_system.crit_calculator.is_critical(
            attacker_level, attacker_dex, 0,
            target_level, target_armor, 0
        )
    }


# ═══════════════════════════ SKILL TREE ENDPOINTS ═════════════════════════════

@app.post("/api/skilltrees/create", response_model=Dict)
def create_skill_tree(name: str, description: str):
    """Create skill tree."""
    tree = combat_system.create_skill_tree(name, description)
    return {
        "status": "success",
        "tree": tree.to_dict()
    }


@app.get("/api/skilltrees/{tree_id}", response_model=Dict)
def get_skill_tree(tree_id: str):
    """Get skill tree."""
    if tree_id not in combat_system.skill_trees:
        raise HTTPException(status_code=404, detail="Skill tree not found")
    return combat_system.skill_trees[tree_id].to_dict()


@app.post("/api/skilltrees/{tree_id}/nodes/add")
def add_skill_tree_node(
    tree_id: str,
    name: str,
    description: str,
    node_type: str,
    x: int = 0,
    y: int = 0
):
    """Add node to skill tree."""
    try:
        nt = SkillTreeNodeType[node_type.upper()]
        node = combat_system.add_skill_node(
            tree_id, name, description, nt, x, y
        )
        return {
            "status": "success",
            "node": node.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════ SYSTEM ENDPOINTS ═════════════════════════════════

@app.get("/api/system/stats", response_model=Dict)
def get_system_stats():
    """Get system statistics."""
    return combat_system.to_dict()


@app.post("/api/system/export")
def export_system(filepath: str = "combat_export.json"):
    """Export combat system."""
    try:
        data = {
            "formulas": [f.to_dict() for f in combat_system.damage_formulas.values()],
            "effects": [e.to_dict() for e in combat_system.status_effects.values()],
            "combo_moves": [m.to_dict() for m in combat_system.combo_moves.values()],
            "combo_chains": [c.to_dict() for c in combat_system.combo_chains.values()],
            "skill_trees": [t.to_dict() for t in combat_system.skill_trees.values()],
        }
        Path(filepath).write_text(json.dumps(data, indent=2))
        return {"status": "success", "filepath": filepath}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    """Health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


# ═══════════════════════════ HTML DASHBOARD ══════════════════════════════════

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Combat System Designer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Arial', sans-serif;
            background: #1a1a2e;
            color: #e0e0e0;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 2px solid #0f3460;
            margin-bottom: 30px;
        }
        
        h1 {
            font-size: 2.5em;
            color: #ff6b6b;
            text-shadow: 0 0 20px rgba(255, 107, 107, 0.5);
            margin-bottom: 10px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .panel {
            background: rgba(15, 52, 96, 0.6);
            border: 1px solid #ff6b6b;
            border-radius: 8px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }
        
        .panel h2 {
            color: #ff6b6b;
            margin-bottom: 15px;
            font-size: 1.5em;
            border-bottom: 1px solid #ff6b6b;
            padding-bottom: 10px;
        }
        
        .stat-box {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #0f3460;
        }
        
        .stat-label {
            font-weight: 500;
            color: #b0b0b0;
        }
        
        .stat-value {
            color: #ff6b6b;
            font-weight: bold;
            font-size: 1.2em;
        }
        
        .entity-display {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid #ff6b6b;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
        }
        
        .health-bar {
            width: 100%;
            height: 20px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .health-fill {
            height: 100%;
            background: linear-gradient(90deg, #ff6b6b, #ff8787);
            width: 100%;
            transition: width 0.3s;
        }
        
        .tab-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .tab-btn {
            padding: 8px 16px;
            background: rgba(15, 52, 96, 0.6);
            border: 1px solid #ff6b6b;
            color: #b0b0b0;
            cursor: pointer;
            border-radius: 4px;
            transition: all 0.3s;
        }
        
        .tab-btn.active {
            background: #ff6b6b;
            color: #1a1a2e;
            border-color: #ff6b6b;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        button {
            background: #ff6b6b;
            color: #1a1a2e;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
            margin: 5px;
            transition: all 0.3s;
        }
        
        button:hover {
            background: #ff8787;
            box-shadow: 0 0 20px rgba(255, 107, 107, 0.5);
        }
        
        input, select {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid #ff6b6b;
            color: #e0e0e0;
            padding: 8px 12px;
            border-radius: 4px;
            margin: 5px;
            font-family: inherit;
        }
        
        .combat-sim {
            background: rgba(0, 0, 0, 0.3);
            border: 2px solid #ff6b6b;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .combo-list {
            list-style: none;
        }
        
        .combo-item {
            background: rgba(255, 107, 107, 0.1);
            border-left: 3px solid #ff6b6b;
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⚔️ Combat System Designer</h1>
            <p>Design damage formulas, combos, and combat mechanics</p>
        </header>
        
        <div class="tab-buttons">
            <button class="tab-btn active" onclick="switchTab('formulas', this)">Formulas</button>
            <button class="tab-btn" onclick="switchTab('effects', this)">Effects</button>
            <button class="tab-btn" onclick="switchTab('combos', this)">Combos</button>
            <button class="tab-btn" onclick="switchTab('entities', this)">Entities</button>
            <button class="tab-btn" onclick="switchTab('simulator', this)">Simulator</button>
            <button class="tab-btn" onclick="switchTab('skilltrees', this)">Skill Trees</button>
        </div>
        
        <!-- FORMULAS TAB -->
        <div id="formulas" class="tab-content active">
            <div class="grid">
                <div class="panel">
                    <h2>Create Damage Formula</h2>
                    <input type="text" id="formula-name" placeholder="Formula name">
                    <input type="text" id="formula-desc" placeholder="Description">
                    <input type="number" id="formula-base" placeholder="Base damage" value="10">
                    <select id="formula-type">
                        <option>Physical</option>
                        <option>Fire</option>
                        <option>Ice</option>
                        <option>Lightning</option>
                        <option>Poison</option>
                    </select>
                    <button onclick="createFormula()">Create Formula</button>
                </div>
                <div class="panel">
                    <h2>Formulas</h2>
                    <div id="formulas-list"></div>
                </div>
            </div>
        </div>
        
        <!-- EFFECTS TAB -->
        <div id="effects" class="tab-content">
            <div class="grid">
                <div class="panel">
                    <h2>Create Status Effect</h2>
                    <input type="text" id="effect-name" placeholder="Effect name">
                    <input type="text" id="effect-desc" placeholder="Description">
                    <select id="effect-type">
                        <option>Burn</option>
                        <option>Poison</option>
                        <option>Stun</option>
                        <option>Slow</option>
                        <option>Weakness</option>
                    </select>
                    <input type="number" id="effect-duration" placeholder="Duration (seconds)" value="5">
                    <button onclick="createEffect()">Create Effect</button>
                </div>
                <div class="panel">
                    <h2>Status Effects</h2>
                    <div id="effects-list"></div>
                </div>
            </div>
        </div>
        
        <!-- COMBOS TAB -->
        <div id="combos" class="tab-content">
            <div class="grid">
                <div class="panel">
                    <h2>Combo Moves</h2>
                    <div id="moves-list"></div>
                </div>
                <div class="panel">
                    <h2>Combo Chains</h2>
                    <div id="chains-list"></div>
                </div>
            </div>
        </div>
        
        <!-- ENTITIES TAB -->
        <div id="entities" class="tab-content">
            <div class="panel">
                <h2>Create Entity</h2>
                <input type="text" id="entity-name" placeholder="Entity name">
                <input type="number" id="entity-level" placeholder="Level" value="1">
                <input type="number" id="entity-health" placeholder="Health" value="100">
                <input type="number" id="entity-attack" placeholder="Attack Power" value="10">
                <button onclick="createEntity()">Create Entity</button>
            </div>
            <div class="panel">
                <h2>Active Entities</h2>
                <div id="entities-list"></div>
            </div>
        </div>
        
        <!-- SIMULATOR TAB -->
        <div id="simulator" class="tab-content">
            <div class="combat-sim">
                <h2>Combat Simulator</h2>
                <div class="grid">
                    <div class="panel">
                        <h3>Attacker</h3>
                        <select id="attacker-select"></select>
                        <div id="attacker-display"></div>
                    </div>
                    <div class="panel">
                        <h3>Defender</h3>
                        <select id="defender-select"></select>
                        <div id="defender-display"></div>
                    </div>
                </div>
                <div class="panel">
                    <select id="formula-select"></select>
                    <button onclick="simulateAttack()">Attack</button>
                    <div id="attack-result"></div>
                </div>
            </div>
        </div>
        
        <!-- SKILL TREES TAB -->
        <div id="skilltrees" class="tab-content">
            <div class="panel">
                <h2>Skill Trees</h2>
                <input type="text" id="tree-name" placeholder="Skill tree name">
                <input type="text" id="tree-desc" placeholder="Description">
                <button onclick="createSkillTree()">Create Skill Tree</button>
                <div id="skilltrees-list"></div>
            </div>
        </div>
    </div>
    
    <script>
        const API_BASE = "http://localhost:8000/api";
        
        function switchTab(tabName, buttonElement) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
            if (buttonElement) buttonElement.classList.add('active');
        }
        
        async function createFormula() {
            const name = document.getElementById('formula-name').value;
            const desc = document.getElementById('formula-desc').value;
            const base = parseFloat(document.getElementById('formula-base').value);
            const type = document.getElementById('formula-type').value;
            
            try {
                const res = await fetch(`${API_BASE}/formulas/create`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        name, description: desc, base_damage: base, damage_type: type
                    })
                });
                await loadFormulas();
                alert('Formula created!');
            } catch (e) {
                alert('Error: ' + e);
            }
        }
        
        async function loadFormulas() {
            try {
                const res = await fetch(`${API_BASE}/formulas`, {signal: AbortSignal.timeout(5000)});
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();
                const list = document.getElementById('formulas-list');
                list.innerHTML = data.formulas.map(f => `
                    <div style="padding: 10px; background: rgba(255, 107, 107, 0.1); margin: 5px 0; border-radius: 4px;">
                        <strong>${f.name}</strong><br>
                        Base: ${f.base_damage} | Type: ${f.damage_type}
                    </div>
                `).join('');
                
                // Update formula selects
                const select = document.getElementById('formula-select');
                if (select) {
                    select.innerHTML = data.formulas.map(f => 
                        `<option value="${f.id}">${f.name}</option>`
                    ).join('');
                }
            } catch (e) {
                console.warn('Error loading formulas:', e);
                document.getElementById('formulas-list').innerHTML = '<p style="color: #f57f17;">Failed to load formulas</p>';
            }
        }
        
        async function createEffect() {
            const name = document.getElementById('effect-name').value;
            const desc = document.getElementById('effect-desc').value;
            const type = document.getElementById('effect-type').value;
            const duration = parseInt(document.getElementById('effect-duration').value);
            
            try {
                await fetch(`${API_BASE}/effects/create`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        name, description: desc, effect_type: type, duration
                    })
                });
                await loadEffects();
                alert('Effect created!');
            } catch (e) {
                alert('Error: ' + e);
            }
        }
        
        async function loadEffects() {
            try {
                const res = await fetch(`${API_BASE}/effects`, {signal: AbortSignal.timeout(5000)});
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();
                const list = document.getElementById('effects-list');
                list.innerHTML = data.effects.map(e => `
                    <div style="padding: 10px; background: rgba(255, 107, 107, 0.1); margin: 5px 0;">
                        <strong>${e.name}</strong> (${e.type})<br>
                        Duration: ${e.duration}s
                    </div>
                `).join('');
            } catch (e) {
                console.warn('Error loading effects:', e);
                document.getElementById('effects-list').innerHTML = '<p style="color: #f57f17;">Failed to load effects</p>';
            }
        }
        
        async function createEntity() {
            const name = document.getElementById('entity-name').value;
            const level = parseInt(document.getElementById('entity-level').value);
            const health = parseFloat(document.getElementById('entity-health').value);
            const attack = parseFloat(document.getElementById('entity-attack').value);
            
            try {
                const res = await fetch(`${API_BASE}/entities/create`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        name, level, health, attack_power: attack
                    })
                });
                await loadEntities();
                alert('Entity created!');
            } catch (e) {
                alert('Error: ' + e);
            }
        }
        
        async function loadEntities() {
            // Would load from API
        }
        
        async function simulateAttack() {
            alert('Combat simulation coming soon!');
        }
        
        async function createSkillTree() {
            const name = document.getElementById('tree-name').value;
            const desc = document.getElementById('tree-desc').value;
            
            try {
                await fetch(`${API_BASE}/skilltrees/create?name=${name}&description=${desc}`, {
                    method: 'POST'
                });
                alert('Skill tree created!');
            } catch (e) {
                alert('Error: ' + e);
            }
        }
        
        // Load on page load
        window.addEventListener('load', () => {
            loadFormulas();
            loadEffects();
        });
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    """Get dashboard."""
    return DASHBOARD_HTML


@app.get("/health")
async def health():
    """Health check for Combat Web service."""
    try:
        entity_count = len(active_entities)
    except Exception:
        entity_count = 0
    return {"status": "healthy", "service": "Combat Web", "entities": entity_count}


if __name__ == "__main__":
    import uvicorn
    from pathlib import Path
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║  Combat System Designer Web Server                            ║
    ║  Starting at http://localhost:8000                            ║
    ║  Dashboard: http://localhost:8000/                            ║
    ║  API Docs: http://localhost:8000/docs                         ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=8000)


