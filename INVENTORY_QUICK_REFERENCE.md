# Inventory & Crafting System - Quick Reference

## Quick Start

### 1. Create System
```python
from inventory_crafting_system import AdvancedInventorySystem, ItemType, ItemRarity, Stat

system = AdvancedInventorySystem()
```

### 2. Create Items
```python
# Basic item
potion = system.item_db.create_item(
    "Health Potion", "Restores 50 HP", 
    ItemType.CONSUMABLE, ItemRarity.COMMON, 20, 0.5
)

# Equipment
sword = system.item_db.create_equipment(
    "Iron Sword", "A sturdy sword",
    EquipmentSlot.MAIN_HAND, ItemRarity.RARE,
    weapon_type=WeaponType.SWORD
)

# Add stats
system.item_db.add_stat_to_item(sword.item_id, Stat.ATTACK_POWER, 15.0)
```

### 3. Create Inventory
```python
inv = system.create_player_inventory("player_1", max_slots=24)
inv.add_item(potion, 5)  # Add 5 potions
inv.add_gold(500)        # Add gold
```

### 4. Equipment
```python
inv.equip_item(sword.item_id)           # Equip sword
stats = inv.get_equipped_stats()         # Get stat bonuses
inv.unequip_item(EquipmentSlot.MAIN_HAND)  # Unequip
```

### 5. Crafting
```python
# Create recipe
recipe = system.crafting_system.create_recipe(
    "Iron Sword", "Craft an iron sword",
    CraftingCategory.WEAPON, sword.item_id
)

# Add ingredient
system.crafting_system.add_ingredient(
    recipe.recipe_id, "iron_ore", "Iron Ore", 5
)

# Start crafting
job = system.crafting_system.start_crafting("player_1", recipe.recipe_id, inv)

# Complete crafting
result = system.crafting_system.complete_crafting(job.job_id, inv, system.item_db)
```

### 6. Trading
```python
# Create offer
offer = system.trading_system.create_offer(
    "seller_id",
    items_offered={"sword_1": 1},
    items_wanted={"shield_1": 1},
    price_gold=0
)

# Execute trade
success = system.trading_system.execute_trade(
    offer.offer_id, buyer_inv, seller_inv
)
```

---

## Item Types

```python
ItemType.WEAPON      # Swords, axes, bows, etc.
ItemType.ARMOR       # Helmets, chest, legs, etc.
ItemType.ACCESSORY   # Rings, amulets, cloaks
ItemType.CONSUMABLE  # Potions, food, buffs
ItemType.MATERIAL    # Crafting materials
ItemType.QUEST       # Quest items
ItemType.MISC        # Misc items
```

## Rarities

```python
ItemRarity.COMMON      # 1x value multiplier
ItemRarity.UNCOMMON    # 1.5x value multiplier
ItemRarity.RARE        # 2x value multiplier
ItemRarity.EPIC        # 2.5x value multiplier
ItemRarity.LEGENDARY   # 3x value multiplier
ItemRarity.MYTHIC      # 4x value multiplier
```

## Equipment Slots

```python
EquipmentSlot.HEAD           # Helmets
EquipmentSlot.NECK           # Amulets, necklaces
EquipmentSlot.CHEST          # Armor
EquipmentSlot.BACK           # Cloaks, backpacks
EquipmentSlot.HANDS          # Gloves, gauntlets
EquipmentSlot.WAIST          # Belts
EquipmentSlot.LEGS           # Leg armor
EquipmentSlot.FEET           # Boots
EquipmentSlot.FINGER_LEFT    # Left ring
EquipmentSlot.FINGER_RIGHT   # Right ring
EquipmentSlot.MAIN_HAND      # Main hand weapon
EquipmentSlot.OFF_HAND       # Off-hand weapon
EquipmentSlot.TWO_HAND       # Two-handed weapon
```

## Stats

```python
Stat.HEALTH               # Hit points
Stat.MANA                 # Magic points
Stat.STAMINA              # Stamina/energy
Stat.STRENGTH             # Physical power
Stat.DEXTERITY            # Agility
Stat.INTELLIGENCE         # Magic power
Stat.WISDOM               # Mental defense
Stat.CONSTITUTION         # Endurance
Stat.ATTACK_POWER         # Physical damage
Stat.DEFENSE              # Physical defense
Stat.MAGIC_POWER          # Magic damage
Stat.MAGIC_DEFENSE        # Magic defense
Stat.FIRE_RES             # Fire resistance
Stat.ICE_RES              # Ice resistance
Stat.LIGHTNING_RES        # Lightning resistance
Stat.POISON_RES           # Poison resistance
```

---

## REST API Quick Reference

### Items
```bash
# Create item
POST /api/items/create

# Get item
GET /api/items/{item_id}

# List items
GET /api/items?item_type=weapon&rarity=rare

# Add stat
POST /api/items/{item_id}/add-stat?stat=attack_power&value=10
```

### Inventory
```bash
# Create inventory
POST /api/inventory/{player_id}/create

# Get inventory
GET /api/inventory/{player_id}

# Add item
POST /api/inventory/{player_id}/add-item

# Remove item
POST /api/inventory/{player_id}/remove-item

# Equip
POST /api/inventory/{player_id}/equip

# Unequip
POST /api/inventory/{player_id}/unequip

# Get stats
GET /api/inventory/{player_id}/stats

# Add gold
POST /api/inventory/{player_id}/add-gold

# Remove gold
POST /api/inventory/{player_id}/remove-gold
```

### Crafting
```bash
# Create recipe
POST /api/recipes/create

# Add ingredient
POST /api/recipes/{recipe_id}/add-ingredient

# Start crafting
POST /api/crafting/{player_id}/start

# Complete crafting
POST /api/crafting/{player_id}/complete/{job_id}

# Get available recipes
GET /api/crafting/{player_id}/available
```

### Trading
```bash
# Create offer
POST /api/trades/offer/create

# List offers
GET /api/trades/offers

# Execute trade
POST /api/trades/execute
```

---

## WebSocket Events (Unreal)

```cpp
// Inventory Events
EInventoryEventType::InventoryOpened
EInventoryEventType::ItemAdded
EInventoryEventType::ItemRemoved
EInventoryEventType::ItemEquipped
EInventoryEventType::ItemUnequipped
EInventoryEventType::InventoryFull
EInventoryEventType::DurabilityLow

// Crafting Events
EInventoryEventType::CraftingStarted
EInventoryEventType::CraftingCompleted
EInventoryEventType::CraftingFailed

// Trading Events
EInventoryEventType::TradeCompleted
```

---

## Common Patterns

### Pattern 1: Check for Item
```python
def has_item(inventory, item_id, quantity=1):
    for inv_item in inventory.items:
        if inv_item.item_id == item_id and inv_item.quantity >= quantity:
            return True
    return False
```

### Pattern 2: Get Total Stat
```python
def get_total_stat(inventory, stat):
    stats = inventory.get_equipped_stats()
    return stats.get(stat, 0)
```

### Pattern 3: Repair Equipment
```python
def repair_all(inventory):
    for item in inventory.equipment.values():
        item.repair_durability()
```

### Pattern 4: Get Item Value
```python
def calculate_inventory_worth(inventory):
    total = inventory.gold
    for inv_item in inventory.items:
        total += inv_item.item.total_value * inv_item.quantity
    return total
```

### Pattern 5: Get Required Level
```python
def can_use_item(player_level, item):
    return player_level >= item.level_required
```

---

## Debugging

### Check Inventory Status
```python
inv = system.get_player_inventory("player_1")
print(f"Slots: {inv.used_slots}/{inv.max_slots}")
print(f"Weight: {inv.total_weight}/{inv.max_weight}")
print(f"Items: {[i.item.name for i in inv.items]}")
```

### Check Item Stats
```python
item = system.item_db.get_item("sword_1")
print(f"Name: {item.name}")
print(f"Rarity: {item.rarity.label}")
print(f"Stats: {item.stats}")
print(f"Durability: {item.durability_pct}%")
```

### Check Recipe
```python
recipe = system.crafting_system.recipes["recipe_1"]
print(f"Name: {recipe.name}")
print(f"Ingredients: {[(i.item_name, i.quantity) for i in recipe.ingredients]}")
print(f"Result: {recipe.result_item_id} x{recipe.result_quantity}")
```

### Check Trade Status
```python
offer = system.trading_system.offers["offer_1"]
print(f"Offering: {offer.items_offered}")
print(f"Wanting: {offer.items_wanted}")
print(f"Gold: {offer.price_gold}")
print(f"Available: {offer.is_available}")
```

---

## Performance Tips

1. **Batch Operations**: Group multiple add_item calls
2. **Lazy Loading**: Load items on demand, not all at startup
3. **Caching**: Cache calculated stats, invalidate on equip/unequip
4. **Indexing**: Use item_id lookups instead of name searches
5. **Connection Pooling**: Use connection pool for WebSocket/HTTP

---

## Common Issues

**Q: Inventory full error**
- A: Check `inventory.inventory_full` property
- Solution: Remove items or increase max_slots

**Q: Crafting fails silently**
- A: Check ingredient availability and level requirements
- Solution: Use `get_available_recipes()` first

**Q: Stat calculations wrong**
- A: Equipment slot conflicts or stack override issues
- Solution: Check `get_equipped_stats()` directly

**Q: Trade not executing**
- A: Missing items or insufficient gold
- Solution: Validate inventories before executing trade

---

## File Structure

```
inventory_crafting_system.py    - Core system (1,500 lines)
inventory_crafting_web.py       - REST API & Web UI (1,000 lines)
inventory_unreal_integration.py - Unreal integration (900 lines)
inventory_crafting_db.py        - Database layer (to be created)
```

## Next Steps

1. Run the web server: `python inventory_crafting_web.py`
2. Visit http://localhost:8000 for the dashboard
3. Check /docs for interactive API documentation
4. Review INVENTORY_CRAFTING_GUIDE.md for detailed info
5. Integrate with Unreal Engine using C++ headers

