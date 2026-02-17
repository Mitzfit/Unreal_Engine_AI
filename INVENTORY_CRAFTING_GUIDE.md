# Inventory & Crafting System - Complete Guide

## Table of Contents
1. [Overview](#overview)
2. [Core Features](#core-features)
3. [System Architecture](#system-architecture)
4. [Getting Started](#getting-started)
5. [API Reference](#api-reference)
6. [Unreal Integration](#unreal-integration)
7. [Code Examples](#code-examples)
8. [Advanced Topics](#advanced-topics)

---

## Overview

The **Advanced Inventory & Crafting System** is a production-ready Python module providing complete inventory management, crafting, equipment, trading, and set bonus systems for game development.

### Key Features
- **Item Management**: Create, store, and manage thousands of items with rarity, durability, and stat systems
- **Inventory System**: Player inventories with weight/slot limitations, equipment slots, and stat bonuses
- **Crafting Engine**: Recipe-based crafting with quality tiers, success rates, and experience rewards
- **Equipment System**: Full equipment slot management with stat calculation from equipped items
- **Trading System**: Player-to-player trading with gold and item exchange
- **Set Bonuses**: Equipment sets that grant bonuses when multiple pieces are equipped
- **Web Dashboard**: Interactive HTML5 interface for inventory management
- **REST API**: 40+ endpoints for integration with game engines
- **WebSocket Support**: Real-time updates and streaming
- **Unreal Integration**: C++ bindings and event system for Unreal Engine 5+

---

## Core Features

### 1. Item System

Items have multiple properties:
- **Basic**: ID, name, description, type (weapon, armor, consumable, material, etc.)
- **Rarity**: Common, Uncommon, Rare, Epic, Legendary, Mythic (affects value multiplier)
- **Durability**: Weapons and armor degrade with use (optional)
- **Weight**: Inventory management
- **Stats**: Items grant stat bonuses (health, damage, defense, resistances, etc.)
- **Effects**: Special effects (on-hit, passive, on-use)
- **Equipment Slots**: Where items can be worn
- **Set Bonuses**: Belonging to item sets

### 2. Inventory System

Player inventory features:
- **Slot-based**: Limited inventory slots
- **Weight-based**: Maximum carrying capacity
- **Equipment slots**: Head, chest, hands, legs, feet, rings, weapons
- **Stacking**: Consumables and materials can stack
- **Gold tracking**: In-game currency storage
- **Real-time stats**: Automatic stat calculation from equipped items

### 3. Crafting System

Crafting system includes:
- **Recipes**: Define what can be crafted
- **Ingredients**: Required items and quantities
- **Crafting time**: How long crafting takes
- **Quality tiers**: Results vary in quality
- **Yield chance**: Success percentage
- **Experience rewards**: Crafting skill progression
- **Tools required**: Optional crafting tools

### 4. Equipment System

Equipment management:
- **13 equipment slots**: Head, neck, chest, back, hands, waist, legs, feet, 2 rings, main hand, off-hand
- **Two-handed weapons**: Special handling
- **Armor types**: Light, medium, heavy
- **Weapon types**: Swords, axes, hammers, bows, staffs, etc.
- **Stat stacking**: Bonuses from multiple equipped items stack
- **Set detection**: Automatic set bonus activation

### 5. Trading System

Trading features:
- **Trade offers**: Create buy/sell/swap offers
- **Gold trading**: Include gold in trades
- **Item trading**: Exchange items between players
- **Offer expiration**: Optional expiration dates
- **Trade history**: Track completed trades

### 6. Set Bonus System

Set bonuses provide:
- **Multi-piece bonuses**: Require 2+ items from same set
- **Stat bonuses**: Additional stats from set completion
- **Special effects**: Unique effects when set is complete
- **Automatic activation**: Applied when items are equipped

---

## System Architecture

### Module Structure

```
inventory_crafting_system.py
├── Enums (ItemRarity, ItemType, EquipmentSlot, etc.)
├── Item Management
│   ├── Item (core item definition)
│   ├── ItemStat (stat modifiers)
│   ├── ItemEffect (special effects)
│   ├── ItemSetBonus (set system)
│   └── ItemDatabase (item storage)
├── Inventory System
│   ├── InventoryItem (stacking wrapper)
│   └── PlayerInventory (player inventory)
├── Crafting System
│   ├── Recipe (recipe definition)
│   ├── RecipeIngredient (ingredient spec)
│   ├── CraftingJob (active crafting)
│   └── CraftingSystem (recipe manager)
├── Trading System
│   ├── TradeOffer (trade definition)
│   └── TradingSystem (trade manager)
└── AdvancedInventorySystem (orchestrator)

inventory_crafting_web.py
├── FastAPI Application
├── REST Endpoints (40+)
├── WebSocket Support
└── HTML5 Dashboard

inventory_unreal_integration.py
├── UnrealInventoryBridge
├── Event System
├── WebSocket Server
├── C++ Headers
└── UnrealInventoryAdapter
```

### Data Flow

```
Unreal Engine
    ↓
WebSocket/HTTP API
    ↓
FastAPI Server
    ↓
AdvancedInventorySystem
    ├── ItemDatabase
    ├── PlayerInventory (per player)
    ├── CraftingSystem
    ├── TradingSystem
    └── SQLite Storage
```

---

## Getting Started

### 1. Installation

```bash
# Install dependencies
pip install fastapi uvicorn websockets pydantic

# Or use the provided requirements.txt
pip install -r requirements.txt
```

### 2. Basic Usage

```python
from inventory_crafting_system import AdvancedInventorySystem, ItemType, ItemRarity, Stat

# Create system
system = AdvancedInventorySystem()

# Create items
sword = system.item_db.create_item(
    name="Iron Sword",
    description="A sturdy iron sword",
    item_type=ItemType.WEAPON,
    rarity=ItemRarity.COMMON,
    value=100,
    weight=5.0
)

# Add stats to item
system.item_db.add_stat_to_item(sword.item_id, Stat.ATTACK_POWER, 10.0)

# Create player inventory
inv = system.create_player_inventory("player_1", max_slots=24)

# Add item to inventory
inv.add_item(sword)
inv.add_gold(500)

print(f"Gold: {inv.gold}")
print(f"Items: {inv.used_slots}/{inv.max_slots}")
```

### 3. Running Web Server

```bash
# Start the web server
python inventory_crafting_web.py

# Access at:
# - Dashboard: http://localhost:8000
# - API: http://localhost:8000/docs
# - Health: http://localhost:8000/health
```

### 4. Unreal Integration

```python
from inventory_unreal_integration import UnrealInventoryBridge

bridge = UnrealInventoryBridge(system)

# Generate C++ headers
bridge.generate_cpp_headers("./Source/YourProject")

# Start WebSocket server
await bridge.start_websocket_server("0.0.0.0", 8765)

# Register event listeners
bridge.register_event_listener(
    "item_added",
    lambda event: print(f"Item added: {event}")
)
```

---

## API Reference

### Item Endpoints

#### Create Item
```
POST /api/items/create
{
    "name": "Iron Sword",
    "description": "A sturdy iron sword",
    "item_type": "weapon",
    "rarity": "common",
    "value": 100,
    "weight": 5.0
}
```

#### Get Item
```
GET /api/items/{item_id}
```

#### List Items
```
GET /api/items?item_type=weapon&rarity=rare&limit=50
```

#### Add Stat
```
POST /api/items/{item_id}/add-stat?stat=attack_power&value=10.0
```

### Inventory Endpoints

#### Create Inventory
```
POST /api/inventory/{player_id}/create?max_slots=24
```

#### Get Inventory
```
GET /api/inventory/{player_id}
```

#### Add Item
```
POST /api/inventory/{player_id}/add-item
{
    "item_id": "sword_1",
    "quantity": 1
}
```

#### Equip Item
```
POST /api/inventory/{player_id}/equip
{
    "item_id": "sword_1"
}
```

#### Unequip Item
```
POST /api/inventory/{player_id}/unequip
{
    "slot": "main_hand"
}
```

#### Get Stats
```
GET /api/inventory/{player_id}/stats
```

### Crafting Endpoints

#### Create Recipe
```
POST /api/recipes/create
{
    "name": "Iron Sword Recipe",
    "description": "Craft an iron sword",
    "category": "weapon",
    "result_item_id": "sword_1",
    "result_quantity": 1,
    "crafting_time": 10,
    "level_required": 1
}
```

#### Add Ingredient
```
POST /api/recipes/{recipe_id}/add-ingredient
{
    "item_id": "iron_ore",
    "item_name": "Iron Ore",
    "quantity": 5
}
```

#### Start Crafting
```
POST /api/crafting/{player_id}/start
{
    "recipe_id": "recipe_1"
}
```

#### Complete Crafting
```
POST /api/crafting/{player_id}/complete/{job_id}
```

#### Get Available Recipes
```
GET /api/crafting/{player_id}/available?player_level=10&player_skill=50
```

### Trading Endpoints

#### Create Offer
```
POST /api/trades/offer/create
{
    "items_offered": {"sword_1": 1},
    "items_wanted": {"shield_1": 1},
    "price_gold": 0,
    "description": "Sword for Shield trade"
}
```

#### List Offers
```
GET /api/trades/offers
```

#### Execute Trade
```
POST /api/trades/execute
{
    "offer_id": "offer_1",
    "buyer_id": "player_1",
    "seller_id": "player_2"
}
```

### System Endpoints

#### Get Stats
```
GET /api/system/stats
```

#### Export System
```
POST /api/system/export?filepath=export.json
```

---

## Unreal Integration

### C++ Usage

#### 1. Include Headers

```cpp
#include "InventoryBridge.h"
#include "InventoryItem.h"
```

#### 2. Connect to System

```cpp
void AMyCharacter::BeginPlay() {
    Super::BeginPlay();
    
    AInventoryBridge* Bridge = GetWorld()->SpawnActor<AInventoryBridge>();
    Bridge->ConnectToSystem(FString("ue_player_1"));
    
    Bridge->OnInventoryEvent.AddDynamic(this, &AMyCharacter::OnInventoryEvent);
}

void AMyCharacter::OnInventoryEvent(EInventoryEventType EventType, const FString& EventData) {
    switch (EventType) {
        case EInventoryEventType::ItemAdded:
            ShowNotification("Item added!");
            break;
        case EInventoryEventType::ItemEquipped:
            UpdateCharacterMesh();
            break;
        case EInventoryEventType::CraftingCompleted:
            PlayCraftingCompleteAnimation();
            break;
        default:
            break;
    }
}
```

#### 3. Use Inventory

```cpp
// Get inventory
Bridge->GetInventory();

// Add item
FGameItem NewItem;
NewItem.ItemId = "sword_1";
NewItem.ItemName = "Iron Sword";
NewItem.Value = 100;
Inventory->AddItem(NewItem, 1);

// Equip item
Inventory->EquipItem("sword_1", EEquipmentSlot::MainHand);

// Start crafting
Bridge->StartCrafting("recipe_1");
```

### WebSocket Connection

```cpp
void AInventoryBridge::ConnectToSystem(const FString& PlayerId) {
    CurrentPlayerId = PlayerId;
    
    FString URL = FString::Printf(TEXT("ws://localhost:8765"));
    WebSocket = FWebSocketsModule::Get().CreateWebSocket(URL);
    
    WebSocket->OnConnected().AddDynamic(this, &AInventoryBridge::OnWebSocketConnected);
    WebSocket->OnClosed().AddDynamic(this, &AInventoryBridge::OnWebSocketClosed);
    WebSocket->OnMessage().AddDynamic(this, &AInventoryBridge::OnWebSocketMessage);
    
    WebSocket->Connect();
}

void AInventoryBridge::OnWebSocketConnected() {
    FString ConnectMsg = FString::Printf(
        TEXT("{"command":"connect","player_id":"%s"}"),
        *CurrentPlayerId
    );
    WebSocket->Send(ConnectMsg);
}
```

---

## Code Examples

### Example 1: Create Complete Item Set

```python
from inventory_crafting_system import *

system = AdvancedInventorySystem()

# Create item set
plate_set = system.item_db.create_set("Plate Armor Set", required_count=4)

# Create items in set
helmet = system.item_db.create_equipment(
    "Plate Helmet",
    "Heavy protection for the head",
    EquipmentSlot.HEAD,
    ItemRarity.EPIC,
    armor_type=ArmorType.HEAVY
)
helmet.set_id = plate_set.set_id

# Add stat to set
plate_set.bonus_stats[Stat.DEFENSE] = 50.0
plate_set.bonus_stats[Stat.HEALTH] = 100.0

# Add effect to set
defense_effect = ItemEffect(
    effect_id="plate_defense",
    name="Plate Defense",
    description="10% damage reduction",
    effect_type="passive",
    value=10.0
)
plate_set.bonus_effects.append(defense_effect)

print(f"Set created: {plate_set.set_name}")
print(f"Bonuses: {plate_set.to_dict()}")
```

### Example 2: Crafting Workflow

```python
from inventory_crafting_system import *

system = AdvancedInventorySystem()

# Create recipe
sword_recipe = system.crafting_system.create_recipe(
    name="Iron Sword",
    description="Craft an iron sword",
    category=CraftingCategory.WEAPON,
    result_item_id="iron_sword",
    result_quantity=1,
    crafting_time=10,
    level_required=1
)

# Add ingredients
system.crafting_system.add_ingredient(
    sword_recipe.recipe_id,
    "iron_ore",
    "Iron Ore",
    5
)
system.crafting_system.add_ingredient(
    sword_recipe.recipe_id,
    "wood",
    "Wood",
    2
)

# Create player and start crafting
inv = system.create_player_inventory("crafter_1")
inv.add_item(system.item_db.get_item("iron_ore"), 5)
inv.add_item(system.item_db.get_item("wood"), 2)

job = system.crafting_system.start_crafting(
    "crafter_1",
    sword_recipe.recipe_id,
    inv
)

print(f"Crafting started: {job.job_id}")
print(f"Progress: {job.progress_pct}%")

# Later... complete crafting
result = system.crafting_system.complete_crafting(
    job.job_id,
    inv,
    system.item_db
)

print(f"Crafting complete! Quality: {job.quality_tier}")
```

### Example 3: Trading System

```python
from inventory_crafting_system import *

system = AdvancedInventorySystem()

# Create player inventories
player1_inv = system.create_player_inventory("player_1")
player2_inv = system.create_player_inventory("player_2")

# Add items
sword = system.item_db.create_item(
    "Iron Sword", "A sword", ItemType.WEAPON, ItemRarity.COMMON, 100
)
shield = system.item_db.create_item(
    "Iron Shield", "A shield", ItemType.ARMOR, ItemRarity.COMMON, 80
)

player1_inv.add_item(sword, 1)
player2_inv.add_item(shield, 1)

# Create trade offer
offer = system.trading_system.create_offer(
    trader_id="player_2",
    items_offered={"shield_id": 1},
    items_wanted={"sword_id": 1},
    description="Sword for Shield"
)

# Execute trade
success = system.trading_system.execute_trade(
    offer.offer_id,
    player1_inv,
    player2_inv
)

if success:
    print("Trade completed!")
    print(f"Player 1 has: {player1_inv.items}")
    print(f"Player 2 has: {player2_inv.items}")
```

---

## Advanced Topics

### 1. Custom Item Effects

```python
# Create custom effect
critical_strike = ItemEffect(
    effect_id="crit_strike",
    name="Critical Strike",
    description="20% chance to deal 2x damage",
    effect_type="on_hit",
    value=20.0
)

# Add to item
system.item_db.add_effect_to_item("sword_1", critical_strike)
```

### 2. Durability Management

```python
# Take damage
inventory.equipment[EquipmentSlot.MAIN_HAND].damage_durability(10)

# Repair item
inventory.equipment[EquipmentSlot.MAIN_HAND].repair_durability(20)

# Full repair
inventory.equipment[EquipmentSlot.MAIN_HAND].repair_durability()
```

### 3. Database Persistence

```python
# Export system state
system.export_system("inventory_save.json")

# Save to SQLite
import sqlite3
conn = sqlite3.connect("inventory.db")
# Custom persistence logic here
conn.close()
```

### 4. Performance Optimization

For large inventories:
```python
# Use indexed lookups
item = system.item_db.get_item(item_id)  # O(1)

# Batch operations
for item_data in large_item_list:
    inv.add_item(item_data["item"], item_data["quantity"])
```

### 5. Event Listeners

```python
# Register listener
def on_crafting_complete(data):
    print(f"Crafting complete: {data['job_id']}")
    send_notification_to_player(data['player_id'])

# In Unreal bridge
bridge.register_event_listener(
    UnrealCraftingEvent.CRAFTING_COMPLETED.value,
    on_crafting_complete
)
```

---

## Conclusion

The Inventory & Crafting System provides a complete, production-ready solution for managing complex game inventory systems. With support for items, crafting, trading, equipment sets, and full Unreal Engine integration, it's designed to scale from indie games to large MMOs.

For questions or issues, refer to the API documentation or the code examples provided in the modules.
