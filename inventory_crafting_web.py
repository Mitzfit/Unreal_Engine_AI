"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     INVENTORY & CRAFTING WEB INTERFACE & REST API                           ║
║  FastAPI server with HTML5 dashboard, REST endpoints, WebSocket support     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
import json
import uuid
from datetime import datetime
import logging

from inventory_crafting_system import (
    AdvancedInventorySystem, Item, Recipe, TradeOffer, ItemType, ItemRarity,
    Stat, EquipmentSlot, CraftingCategory, ItemEffect, ItemSetBonus
)

# ═══════════════════════════ LOGGING ═════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════ MODELS ══════════════════════════════════════════

class CreateItemRequest(BaseModel):
    name: str
    description: str
    item_type: str
    rarity: str = "common"
    value: int = 10
    weight: float = 1.0

class AddItemToInventoryRequest(BaseModel):
    item_id: str
    quantity: int = 1

class EquipItemRequest(BaseModel):
    item_id: str

class UnequipItemRequest(BaseModel):
    slot: str

class CreateRecipeRequest(BaseModel):
    name: str
    description: str
    category: str
    result_item_id: str
    result_quantity: int = 1
    crafting_time: int = 5
    level_required: int = 1

class AddRecipeIngredientRequest(BaseModel):
    recipe_id: str
    item_id: str
    item_name: str
    quantity: int

class StartCraftingRequest(BaseModel):
    recipe_id: str

class CreateTradeOfferRequest(BaseModel):
    items_offered: Dict[str, int]
    items_wanted: Dict[str, int] = {}
    price_gold: int = 0
    description: str = ""

class ExecuteTradeRequest(BaseModel):
    offer_id: str
    buyer_id: str
    seller_id: str

# ═══════════════════════════ FASTAPI APP ════════════════════════════════════

app = FastAPI(title="Inventory & Crafting System", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global system instance
inventory_system = AdvancedInventorySystem()
active_connections: Dict[str, List[WebSocket]] = {}

# ═══════════════════════════ WEBSOCKET HANDLERS ══════════════════════════════

@app.websocket("/ws/inventory/{player_id}")
async def websocket_inventory(websocket: WebSocket, player_id: str):
    """WebSocket connection for real-time inventory updates."""
    await websocket.accept()
    
    if player_id not in active_connections:
        active_connections[player_id] = []
    active_connections[player_id].append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            command = json.loads(data)
            
            # Handle commands
            if command.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
            elif command.get("type") == "get_inventory":
                inv = inventory_system.get_player_inventory(player_id)
                if inv:
                    await websocket.send_json({
                        "type": "inventory_update",
                        "data": inv.to_dict()
                    })
    except Exception as e:
        logger.error(f"WebSocket error for {player_id}: {e}")
    finally:
        active_connections[player_id].remove(websocket)


async def broadcast_to_player(player_id: str, message: Dict):
    """Send message to all WebSocket connections for player."""
    if player_id in active_connections:
        for connection in active_connections[player_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")

# ═══════════════════════════ ITEM ENDPOINTS ══════════════════════════════════

@app.post("/api/items/create", response_model=Dict)
def create_item(request: CreateItemRequest):
    """Create a new item."""
    try:
        item_type = ItemType[request.item_type.upper()]
        rarity = ItemRarity[request.rarity.upper()]
        
        item = inventory_system.item_db.create_item(
            name=request.name,
            description=request.description,
            item_type=item_type,
            rarity=rarity,
            value=request.value,
            weight=request.weight
        )
        return {
            "status": "success",
            "item": item.to_dict()
        }
    except Exception as e:
        logger.error(f"Error creating item: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/items/{item_id}", response_model=Dict)
def get_item(item_id: str):
    """Get item details."""
    item = inventory_system.item_db.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item.to_dict()


@app.get("/api/items", response_model=Dict)
def list_items(
    item_type: Optional[str] = None,
    rarity: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500)
):
    """List all items with optional filtering."""
    items = list(inventory_system.item_db.items.values())
    
    if item_type:
        items = [i for i in items if i.item_type.value == item_type]
    if rarity:
        items = [i for i in items if i.rarity.label == rarity]
    
    return {
        "count": len(items),
        "items": [item.to_dict() for item in items[:limit]]
    }


@app.post("/api/items/{item_id}/add-stat")
def add_stat_to_item(item_id: str, stat: str, value: float):
    """Add stat to item."""
    try:
        stat_enum = Stat[stat.upper()]
        inventory_system.item_db.add_stat_to_item(item_id, stat_enum, value)
        item = inventory_system.item_db.get_item(item_id)
        return {
            "status": "success",
            "item": item.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/items/database/stats", response_model=Dict)
def get_database_stats():
    """Get item database statistics."""
    return inventory_system.item_db.get_stats()


# ═══════════════════════════ INVENTORY ENDPOINTS ══════════════════════════════

@app.post("/api/inventory/{player_id}/create")
def create_inventory(player_id: str, max_slots: int = 24):
    """Create inventory for player."""
    if player_id in inventory_system.player_inventories:
        raise HTTPException(status_code=400, detail="Inventory already exists")
    
    inventory = inventory_system.create_player_inventory(player_id, max_slots)
    return {
        "status": "success",
        "player_id": player_id,
        "max_slots": max_slots
    }


@app.get("/api/inventory/{player_id}", response_model=Dict)
def get_inventory(player_id: str):
    """Get player inventory."""
    inventory = inventory_system.get_player_inventory(player_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return inventory.to_dict()


@app.post("/api/inventory/{player_id}/add-item")
def add_item_to_inventory(player_id: str, request: AddItemToInventoryRequest, background_tasks: BackgroundTasks):
    """Add item to player inventory."""
    inventory = inventory_system.get_player_inventory(player_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    
    item = inventory_system.item_db.get_item(request.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    success = inventory.add_item(item, request.quantity)
    if not success:
        raise HTTPException(status_code=400, detail="Inventory full or item constraints violated")
    
    # Broadcast update
    background_tasks.add_task(broadcast_to_player, player_id, {
        "type": "inventory_updated",
        "data": inventory.to_dict()
    })
    
    return {
        "status": "success",
        "inventory": inventory.to_dict()
    }


@app.post("/api/inventory/{player_id}/remove-item")
def remove_item_from_inventory(player_id: str, item_id: str, quantity: int = 1, background_tasks: BackgroundTasks = None):
    """Remove item from inventory."""
    inventory = inventory_system.get_player_inventory(player_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    
    success = inventory.remove_item(item_id, quantity)
    if not success:
        raise HTTPException(status_code=400, detail="Item not found or insufficient quantity")
    
    if background_tasks:
        background_tasks.add_task(broadcast_to_player, player_id, {
            "type": "inventory_updated",
            "data": inventory.to_dict()
        })
    
    return {"status": "success", "inventory": inventory.to_dict()}


@app.post("/api/inventory/{player_id}/equip")
def equip_item(player_id: str, request: EquipItemRequest, background_tasks: BackgroundTasks):
    """Equip item."""
    inventory = inventory_system.get_player_inventory(player_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    
    success = inventory.equip_item(request.item_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot equip this item")
    
    background_tasks.add_task(broadcast_to_player, player_id, {
        "type": "equipment_updated",
        "data": inventory.to_dict()
    })
    
    return {"status": "success", "inventory": inventory.to_dict()}


@app.post("/api/inventory/{player_id}/unequip")
def unequip_item(player_id: str, request: UnequipItemRequest, background_tasks: BackgroundTasks):
    """Unequip item."""
    inventory = inventory_system.get_player_inventory(player_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    
    try:
        slot = EquipmentSlot[request.slot.upper()]
        success = inventory.unequip_item(slot)
        if not success:
            raise HTTPException(status_code=400, detail="Cannot unequip from this slot")
        
        background_tasks.add_task(broadcast_to_player, player_id, {
            "type": "equipment_updated",
            "data": inventory.to_dict()
        })
        
        return {"status": "success", "inventory": inventory.to_dict()}
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid equipment slot")


@app.get("/api/inventory/{player_id}/stats")
def get_inventory_stats(player_id: str):
    """Get stats from equipped items."""
    inventory = inventory_system.get_player_inventory(player_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    
    stats = inventory.get_equipped_stats()
    return {
        "equipped_stats": {s.value: v for s, v in stats.items()},
        "set_bonuses": inventory.get_equipped_set_bonuses()
    }


@app.post("/api/inventory/{player_id}/add-gold")
def add_gold(player_id: str, amount: int):
    """Add gold to inventory."""
    inventory = inventory_system.get_player_inventory(player_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    
    inventory.add_gold(amount)
    return {"status": "success", "gold": inventory.gold}


@app.post("/api/inventory/{player_id}/remove-gold")
def remove_gold(player_id: str, amount: int):
    """Remove gold from inventory."""
    inventory = inventory_system.get_player_inventory(player_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    
    success = inventory.remove_gold(amount)
    if not success:
        raise HTTPException(status_code=400, detail="Insufficient gold")
    
    return {"status": "success", "gold": inventory.gold}


# ═══════════════════════════ CRAFTING ENDPOINTS ═══════════════════════════════

@app.post("/api/recipes/create", response_model=Dict)
def create_recipe(request: CreateRecipeRequest):
    """Create crafting recipe."""
    try:
        category = CraftingCategory[request.category.upper()]
        recipe = inventory_system.crafting_system.create_recipe(
            name=request.name,
            description=request.description,
            category=category,
            result_item_id=request.result_item_id,
            result_quantity=request.result_quantity,
            crafting_time=request.crafting_time,
            level_required=request.level_required
        )
        return {
            "status": "success",
            "recipe": recipe.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/recipes/{recipe_id}/add-ingredient")
def add_recipe_ingredient(recipe_id: str, request: AddRecipeIngredientRequest):
    """Add ingredient to recipe."""
    inventory_system.crafting_system.add_ingredient(
        recipe_id,
        request.item_id,
        request.item_name,
        request.quantity
    )
    recipe = inventory_system.crafting_system.recipes.get(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return {"status": "success", "recipe": recipe.to_dict()}


@app.get("/api/recipes", response_model=Dict)
def list_recipes(category: Optional[str] = None):
    """List all recipes."""
    recipes = list(inventory_system.crafting_system.recipes.values())
    if category:
        recipes = [r for r in recipes if r.category.value == category]
    return {
        "count": len(recipes),
        "recipes": [r.to_dict() for r in recipes]
    }


@app.post("/api/crafting/{player_id}/start")
def start_crafting(player_id: str, request: StartCraftingRequest, background_tasks: BackgroundTasks):
    """Start crafting job."""
    inventory = inventory_system.get_player_inventory(player_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    
    job = inventory_system.crafting_system.start_crafting(
        player_id,
        request.recipe_id,
        inventory
    )
    
    if not job:
        raise HTTPException(status_code=400, detail="Cannot start crafting")
    
    background_tasks.add_task(broadcast_to_player, player_id, {
        "type": "crafting_started",
        "job": job.to_dict()
    })
    
    return {
        "status": "success",
        "job": job.to_dict()
    }


@app.post("/api/crafting/{player_id}/complete/{job_id}")
def complete_crafting(player_id: str, job_id: str, background_tasks: BackgroundTasks):
    """Complete crafting job."""
    inventory = inventory_system.get_player_inventory(player_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    
    result = inventory_system.crafting_system.complete_crafting(
        job_id,
        inventory,
        inventory_system.item_db
    )
    
    if result is None:
        raise HTTPException(status_code=400, detail="Crafting failed or not complete")
    
    background_tasks.add_task(broadcast_to_player, player_id, {
        "type": "crafting_completed",
        "job_id": job_id,
        "result": result.to_dict()
    })
    
    return {
        "status": "success",
        "result": result.to_dict(),
        "inventory": inventory.to_dict()
    }


@app.get("/api/crafting/{player_id}/available")
def get_available_recipes(player_id: str, player_level: int = 1, player_skill: int = 1):
    """Get available recipes for player."""
    recipes = inventory_system.crafting_system.get_available_recipes(player_level, player_skill)
    return {
        "count": len(recipes),
        "recipes": [r.to_dict() for r in recipes]
    }


# ═══════════════════════════ TRADING ENDPOINTS ═══════════════════════════════

@app.post("/api/trades/offer/create")
def create_trade_offer(offer: CreateTradeOfferRequest, background_tasks: BackgroundTasks):
    """Create a trade offer."""
    trade_offer = inventory_system.trading_system.create_offer(
        trader_id=str(uuid.uuid4())[:8],
        items_offered=offer.items_offered,
        items_wanted=offer.items_wanted,
        price_gold=offer.price_gold,
        description=offer.description
    )
    return {
        "status": "success",
        "offer": trade_offer.to_dict()
    }


@app.get("/api/trades/offers", response_model=Dict)
def list_trade_offers():
    """List all active trade offers."""
    offers = [o for o in inventory_system.trading_system.offers.values() if o.is_available]
    return {
        "count": len(offers),
        "offers": [o.to_dict() for o in offers]
    }


@app.post("/api/trades/execute")
def execute_trade(request: ExecuteTradeRequest, background_tasks: BackgroundTasks):
    """Execute trade between two players."""
    buyer_inv = inventory_system.get_player_inventory(request.buyer_id)
    seller_inv = inventory_system.get_player_inventory(request.seller_id)
    
    if not buyer_inv or not seller_inv:
        raise HTTPException(status_code=404, detail="Player inventory not found")
    
    success = inventory_system.trading_system.execute_trade(
        request.offer_id,
        buyer_inv,
        seller_inv
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Trade execution failed")
    
    background_tasks.add_task(broadcast_to_player, request.buyer_id, {
        "type": "trade_completed",
        "data": buyer_inv.to_dict()
    })
    background_tasks.add_task(broadcast_to_player, request.seller_id, {
        "type": "trade_completed",
        "data": seller_inv.to_dict()
    })
    
    return {
        "status": "success",
        "message": "Trade executed successfully"
    }


# ═══════════════════════════ SYSTEM ENDPOINTS ═════════════════════════════════

@app.get("/api/system/stats", response_model=Dict)
def get_system_stats():
    """Get overall system statistics."""
    return inventory_system.get_system_stats()


@app.post("/api/system/export")
def export_system(filepath: str = "inventory_export.json"):
    """Export system state to JSON."""
    try:
        inventory_system.export_system(filepath)
        return {
            "status": "success",
            "filepath": filepath
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════ HTML DASHBOARD ══════════════════════════════════

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inventory & Crafting System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
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
            padding: 20px 0;
            border-bottom: 2px solid #0f3460;
            margin-bottom: 30px;
        }
        
        h1 {
            font-size: 2.5em;
            color: #00d4ff;
            text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
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
            border: 1px solid #0f3460;
            border-radius: 8px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }
        
        .panel h2 {
            color: #00d4ff;
            margin-bottom: 15px;
            font-size: 1.5em;
            border-bottom: 1px solid #0f3460;
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
            color: #00ff00;
            font-weight: bold;
            font-size: 1.2em;
        }
        
        .item-slot {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid #0f3460;
            border-radius: 4px;
            padding: 10px;
            margin: 5px 0;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .item-slot:hover {
            background: rgba(0, 212, 255, 0.1);
            border-color: #00d4ff;
        }
        
        .item-rarity {
            font-size: 0.8em;
            padding: 2px 6px;
            border-radius: 3px;
            display: inline-block;
            margin-left: 10px;
        }
        
        .rarity-common { background: #808080; color: white; }
        .rarity-uncommon { background: #1EFF00; color: black; }
        .rarity-rare { background: #0070DD; color: white; }
        .rarity-epic { background: #A335EE; color: white; }
        .rarity-legendary { background: #FF8000; color: white; }
        
        button {
            background: linear-gradient(135deg, #0f3460, #16213e);
            color: #00d4ff;
            border: 1px solid #00d4ff;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s;
            margin: 5px;
        }
        
        button:hover {
            background: #00d4ff;
            color: #1a1a2e;
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
        }
        
        input, select {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid #0f3460;
            color: #e0e0e0;
            padding: 8px 12px;
            border-radius: 4px;
            margin: 5px;
            font-family: inherit;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #0070DD, #00d4ff);
            width: 0%;
            transition: width 0.3s;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin: 15px 0;
        }
        
        .stat-card {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid #0f3460;
            border-radius: 4px;
            padding: 10px;
            text-align: center;
        }
        
        .stat-name {
            font-size: 0.8em;
            color: #b0b0b0;
        }
        
        .stat-num {
            font-size: 1.5em;
            color: #00ff00;
            font-weight: bold;
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
            border: 1px solid #0f3460;
            color: #b0b0b0;
            cursor: pointer;
            border-radius: 4px;
            transition: all 0.3s;
        }
        
        .tab-btn.active {
            background: #00d4ff;
            color: #1a1a2e;
            border-color: #00d4ff;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⚔️ Inventory & Crafting System</h1>
            <p>Manage inventory, craft items, and trade with other players</p>
        </header>
        
        <div class="tab-buttons">
            <button class="tab-btn active" onclick="switchTab('inventory', this)">Inventory</button>
            <button class="tab-btn" onclick="switchTab('equipment', this)">Equipment</button>
            <button class="tab-btn" onclick="switchTab('crafting', this)">Crafting</button>
            <button class="tab-btn" onclick="switchTab('trading', this)">Trading</button>
            <button class="tab-btn" onclick="switchTab('items', this)">Items DB</button>
        </div>
        
        <!-- INVENTORY TAB -->
        <div id="inventory" class="tab-content active">
            <div class="grid">
                <div class="panel">
                    <h2>Inventory Overview</h2>
                    <div class="stat-box">
                        <span class="stat-label">Slots Used</span>
                        <span class="stat-value" id="slots-used">0</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-label">Weight</span>
                        <span class="stat-value" id="weight">0 kg</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-label">Gold</span>
                        <span class="stat-value" id="gold">0</span>
                    </div>
                </div>
                <div class="panel">
                    <h2>Items</h2>
                    <div id="items-list"></div>
                </div>
            </div>
        </div>
        
        <!-- EQUIPMENT TAB -->
        <div id="equipment" class="tab-content">
            <div class="grid">
                <div class="panel">
                    <h2>Equipped Items</h2>
                    <div id="equipment-list"></div>
                </div>
                <div class="panel">
                    <h2>Character Stats</h2>
                    <div class="stats-grid" id="stats-grid"></div>
                </div>
            </div>
        </div>
        
        <!-- CRAFTING TAB -->
        <div id="crafting" class="tab-content">
            <div class="grid">
                <div class="panel">
                    <h2>Crafting Jobs</h2>
                    <div id="crafting-jobs"></div>
                </div>
                <div class="panel">
                    <h2>Available Recipes</h2>
                    <div id="recipes-list"></div>
                </div>
            </div>
        </div>
        
        <!-- TRADING TAB -->
        <div id="trading" class="tab-content">
            <div class="grid">
                <div class="panel">
                    <h2>Trade Offers</h2>
                    <div id="offers-list"></div>
                </div>
                <div class="panel">
                    <h2>Create Offer</h2>
                    <input type="text" id="offer-desc" placeholder="Description">
                    <button onclick="createOffer()">Create Offer</button>
                </div>
            </div>
        </div>
        
        <!-- ITEMS DATABASE TAB -->
        <div id="items" class="tab-content">
            <div class="grid">
                <div class="panel">
                    <h2>Database Stats</h2>
                    <div id="db-stats"></div>
                </div>
                <div class="panel">
                    <h2>Create Item</h2>
                    <input type="text" id="item-name" placeholder="Item name">
                    <input type="text" id="item-desc" placeholder="Description">
                    <select id="item-type">
                        <option>weapon</option>
                        <option>armor</option>
                        <option>consumable</option>
                        <option>material</option>
                    </select>
                    <button onclick="createItem()">Create Item</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const API_BASE = "http://localhost:8000/api";
        const PLAYER_ID = "player_demo";
        
        function switchTab(tabName, buttonElement) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
            if (buttonElement) buttonElement.classList.add('active');
        }
        
        async function fetchInventory() {
            try {
                const res = await fetch(`${API_BASE}/inventory/${PLAYER_ID}`);
                const data = await res.json();
                updateInventoryUI(data);
            } catch (e) {
                console.error('Error fetching inventory:', e);
            }
        }
        
        function updateInventoryUI(inv) {
            document.getElementById('slots-used').textContent = `${inv.slots.used}/${inv.slots.max}`;
            document.getElementById('weight').textContent = `${inv.weight.current.toFixed(1)}/${inv.weight.max} kg`;
            document.getElementById('gold').textContent = inv.gold;
            
            const itemsList = document.getElementById('items-list');
            itemsList.innerHTML = inv.items.map(item => `
                <div class="item-slot">
                    <strong>${item.name}</strong>
                    <span class="item-rarity rarity-${item.rarity}">${item.rarity}</span>
                    <div style="font-size: 0.9em; color: #b0b0b0;">
                        Qty: ${item.quantity} | Weight: ${item.total_weight.toFixed(1)} kg
                    </div>
                </div>
            `).join('');
            
            updateEquipmentUI(inv);
        }
        
        function updateEquipmentUI(inv) {
            const equipList = document.getElementById('equipment-list');
            equipList.innerHTML = Object.entries(inv.equipment || {}).map(([slot, item]) => `
                <div class="item-slot">
                    <strong>${item.name}</strong> (${slot})
                    <div style="color: #00ff00;">
                        Durability: ${item.durability.percentage.toFixed(1)}%
                    </div>
                </div>
            `).join('');
        }
        
        async function getStats() {
            try {
                const res = await fetch(`${API_BASE}/inventory/${PLAYER_ID}/stats`);
                const data = await res.json();
                const statsGrid = document.getElementById('stats-grid');
                statsGrid.innerHTML = Object.entries(data.equipped_stats || {}).map(([stat, value]) => `
                    <div class="stat-card">
                        <div class="stat-name">${stat}</div>
                        <div class="stat-num">${value.toFixed(1)}</div>
                    </div>
                `).join('');
            } catch (e) {
                console.error('Error fetching stats:', e);
            }
        }
        
        async function getSystemStats() {
            try {
                const res = await fetch(`${API_BASE}/system/stats`);
                const data = await res.json();
                const statsDiv = document.getElementById('db-stats');
                statsDiv.innerHTML = `
                    <div class="stat-box">
                        <span class="stat-label">Total Items</span>
                        <span class="stat-value">${data.items.total_items}</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-label">Recipes</span>
                        <span class="stat-value">${data.recipes}</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-label">Active Trades</span>
                        <span class="stat-value">${data.active_trades}</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-label">Players</span>
                        <span class="stat-value">${data.players}</span>
                    </div>
                `;
            } catch (e) {
                console.error('Error fetching system stats:', e);
            }
        }
        
        async function createItem() {
            const name = document.getElementById('item-name').value;
            const desc = document.getElementById('item-desc').value;
            const type = document.getElementById('item-type').value;
            
            try {
                const res = await fetch(`${API_BASE}/items/create`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        name, description: desc, item_type: type
                    })
                });
                alert('Item created successfully!');
                getSystemStats();
            } catch (e) {
                alert('Error creating item: ' + e);
            }
        }
        
        async function createOffer() {
            const desc = document.getElementById('offer-desc').value;
            try {
                const res = await fetch(`${API_BASE}/trades/offer/create`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        items_offered: {},
                        items_wanted: {},
                        description: desc
                    })
                });
                alert('Offer created!');
            } catch (e) {
                alert('Error: ' + e);
            }
        }
        
        // Initialize on page load
        window.addEventListener('load', () => {
            fetchInventory();
            getStats();
            getSystemStats();
            // Refresh every 5 seconds
            setInterval(() => {
                fetchInventory();
                getStats();
            }, 5000);
        });
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    """Get HTML dashboard."""
    return DASHBOARD_HTML


@app.get("/health", response_model=Dict)
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Inventory & Crafting System v1.0"
    }


if __name__ == "__main__":
    import uvicorn
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║  Inventory & Crafting System Web Server                       ║
    ║  Starting at http://localhost:8000                            ║
    ║  Dashboard: http://localhost:8000/                            ║
    ║  API Docs: http://localhost:8000/docs                         ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=8000)
