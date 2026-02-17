"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        ADVANCED INVENTORY & CRAFTING SYSTEM                                 ║
║  Item Database · Recipe Designer · Equipment System · Trading · Set Bonuses ║
║  Durability · Weight · Rarity · UI Generator                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import json
import sqlite3
import uuid
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any
import math


# ═══════════════════════════ ENUMS ═════════════════════════════════════════

class ItemRarity(Enum):
    COMMON      = ("common", 1.0, "#A0A0A0")
    UNCOMMON    = ("uncommon", 1.5, "#1EFF00")
    RARE        = ("rare", 2.0, "#0070DD")
    EPIC        = ("epic", 2.5, "#A335EE")
    LEGENDARY   = ("legendary", 3.0, "#FF8000")
    MYTHIC      = ("mythic", 4.0, "#E6CC80")
    
    def __init__(self, label, multiplier, color):
        self.label = label
        self.multiplier = multiplier
        self.color = color

class ItemType(Enum):
    WEAPON      = "weapon"
    ARMOR       = "armor"
    ACCESSORY   = "accessory"
    CONSUMABLE  = "consumable"
    MATERIAL    = "material"
    QUEST       = "quest"
    MISC        = "misc"

class EquipmentSlot(Enum):
    HEAD        = "head"
    NECK        = "neck"
    CHEST       = "chest"
    BACK        = "back"
    HANDS       = "hands"
    WAIST       = "waist"
    LEGS        = "legs"
    FEET        = "feet"
    FINGER_LEFT = "finger_left"
    FINGER_RIGHT= "finger_right"
    MAIN_HAND   = "main_hand"
    OFF_HAND    = "off_hand"
    TWO_HAND    = "two_hand"

class WeaponType(Enum):
    SWORD       = "sword"
    AXE         = "axe"
    HAMMER      = "hammer"
    MACE        = "mace"
    DAGGER      = "dagger"
    BOW         = "bow"
    STAFF       = "staff"
    WAND        = "wand"
    SPEAR       = "spear"

class ArmorType(Enum):
    LIGHT       = "light"
    MEDIUM      = "medium"
    HEAVY       = "heavy"

class Stat(Enum):
    HEALTH          = "health"
    MANA            = "mana"
    STAMINA         = "stamina"
    STRENGTH        = "strength"
    DEXTERITY       = "dexterity"
    INTELLIGENCE    = "intelligence"
    WISDOM          = "wisdom"
    CONSTITUTION    = "constitution"
    ATTACK_POWER    = "attack_power"
    DEFENSE         = "defense"
    MAGIC_POWER     = "magic_power"
    MAGIC_DEFENSE   = "magic_defense"
    FIRE_RES        = "fire_resistance"
    ICE_RES         = "ice_resistance"
    LIGHTNING_RES   = "lightning_resistance"
    POISON_RES      = "poison_resistance"

class CraftingCategory(Enum):
    WEAPON      = "weapon"
    ARMOR       = "armor"
    ACCESSORY   = "accessory"
    POTION      = "potion"
    FOOD        = "food"
    ENCHANTMENT = "enchantment"
    MISC        = "misc"


# ═══════════════════════════ DATA STRUCTURES ═════════════════════════════════

@dataclass
class ItemStat:
    """Stat modification for an item."""
    stat: Stat
    value: float
    percentage: bool = False  # If True, apply as percentage instead of flat value

    def to_dict(self) -> Dict:
        return {
            "stat": self.stat.value,
            "value": self.value,
            "percentage": self.percentage
        }


@dataclass
class ItemEffect:
    """Special effect triggered by item use or equipment."""
    effect_id: str
    name: str
    description: str
    effect_type: str  # "passive", "on_hit", "on_equip", "on_use"
    duration: Optional[int] = None  # seconds
    cooldown: Optional[int] = None  # seconds
    value: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "id": self.effect_id,
            "name": self.name,
            "description": self.description,
            "type": self.effect_type,
            "duration": self.duration,
            "cooldown": self.cooldown,
            "value": self.value
        }


@dataclass
class ItemSetBonus:
    """Bonus granted when all items in a set are equipped."""
    set_id: str
    set_name: str
    required_count: int  # Number of items needed for bonus
    bonus_stats: Dict[Stat, float] = field(default_factory=dict)
    bonus_effects: List[ItemEffect] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "set_id": self.set_id,
            "set_name": self.set_name,
            "required_count": self.required_count,
            "bonus_stats": {s.value: v for s, v in self.bonus_stats.items()},
            "bonus_effects": [e.to_dict() for e in self.bonus_effects]
        }


@dataclass
class Item:
    """Complete item definition."""
    item_id: str
    name: str
    description: str
    item_type: ItemType
    rarity: ItemRarity = ItemRarity.COMMON
    level_required: int = 1
    value: int = 10  # Base gold value
    weight: float = 1.0
    max_durability: float = 100.0
    current_durability: float = 100.0
    stackable: bool = False
    max_stack: int = 1
    
    # Equipment specific
    equipment_slot: Optional[EquipmentSlot] = None
    weapon_type: Optional[WeaponType] = None
    armor_type: Optional[ArmorType] = None
    
    # Stats
    stats: Dict[Stat, ItemStat] = field(default_factory=dict)
    
    # Effects
    effects: List[ItemEffect] = field(default_factory=list)
    
    # Set bonus
    set_bonus: Optional[ItemSetBonus] = None
    set_id: str = ""
    
    # Metadata
    flavor_text: str = ""
    icon_path: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Enchantments (socketed)
    enchantments: List[str] = field(default_factory=list)

    @property
    def durability_pct(self) -> float:
        if self.max_durability == 0:
            return 100.0
        return (self.current_durability / self.max_durability) * 100

    @property
    def total_value(self) -> int:
        """Calculate item value with rarity and durability"""
        base = self.value * self.rarity.multiplier
        if self.max_durability > 0:
            durability_modifier = self.durability_pct / 100.0
            base *= durability_modifier
        return int(base)

    def damage_durability(self, amount: float = 1.0):
        """Reduce durability by amount."""
        self.current_durability = max(0, self.current_durability - amount)

    def repair_durability(self, amount: float = None):
        """Repair durability (full or partial)."""
        if amount is None:
            self.current_durability = self.max_durability
        else:
            self.current_durability = min(self.max_durability, 
                                         self.current_durability + amount)

    def to_dict(self) -> Dict:
        return {
            "item_id": self.item_id,
            "name": self.name,
            "description": self.description,
            "type": self.item_type.value,
            "rarity": self.rarity.label,
            "level_required": self.level_required,
            "value": self.total_value,
            "weight": self.weight,
            "durability": {
                "current": self.current_durability,
                "max": self.max_durability,
                "percentage": self.durability_pct
            },
            "stackable": self.stackable,
            "max_stack": self.max_stack,
            "equipment_slot": self.equipment_slot.value if self.equipment_slot else None,
            "stats": {s.value: stat.to_dict() for s, stat in self.stats.items()},
            "effects": [e.to_dict() for e in self.effects],
            "set_bonus": self.set_bonus.to_dict() if self.set_bonus else None,
            "enchantments": self.enchantments
        }


@dataclass
class InventoryItem:
    """Item in player inventory with quantity tracking."""
    item: Item
    quantity: int = 1
    item_id: str = field(default="")

    def __post_init__(self):
        if not self.item_id:
            self.item_id = self.item.item_id

    @property
    def total_weight(self) -> float:
        return self.item.weight * self.quantity

    def to_dict(self) -> Dict:
        data = self.item.to_dict()
        data["quantity"] = self.quantity
        data["total_weight"] = self.total_weight
        return data


@dataclass
class RecipeIngredient:
    """Ingredient needed for crafting."""
    item_id: str
    item_name: str
    quantity: int
    
    def to_dict(self) -> Dict:
        return {
            "item_id": self.item_id,
            "item_name": self.item_name,
            "quantity": self.quantity
        }


@dataclass
class Recipe:
    """Crafting recipe definition."""
    recipe_id: str
    name: str
    description: str
    category: CraftingCategory
    crafting_time: int = 5  # seconds
    level_required: int = 1
    skill_required: int = 0  # 0-100
    
    ingredients: List[RecipeIngredient] = field(default_factory=list)
    result_item_id: str = ""
    result_quantity: int = 1
    
    yield_chance: float = 100.0  # Success percentage
    experience_reward: int = 10
    
    tool_required: Optional[str] = None  # Item ID of required tool
    
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict:
        return {
            "recipe_id": self.recipe_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "crafting_time": self.crafting_time,
            "level_required": self.level_required,
            "skill_required": self.skill_required,
            "ingredients": [i.to_dict() for i in self.ingredients],
            "result_item_id": self.result_item_id,
            "result_quantity": self.result_quantity,
            "yield_chance": self.yield_chance,
            "experience_reward": self.experience_reward,
            "tool_required": self.tool_required
        }


@dataclass
class CraftingJob:
    """Active crafting job."""
    job_id: str
    recipe_id: str
    player_id: str
    started_at: str
    duration: int  # seconds
    completed_at: Optional[str] = None
    was_successful: bool = False
    quality_tier: int = 1  # 1-5

    @property
    def is_complete(self) -> bool:
        if self.completed_at is None:
            return False
        completed_time = datetime.fromisoformat(self.completed_at)
        return datetime.utcnow() >= completed_time

    @property
    def progress_pct(self) -> float:
        if self.completed_at is None:
            return 0.0
        started = datetime.fromisoformat(self.started_at)
        completed = datetime.fromisoformat(self.completed_at)
        elapsed = (datetime.utcnow() - started).total_seconds()
        total = (completed - started).total_seconds()
        return min(100.0, (elapsed / total) * 100)

    def to_dict(self) -> Dict:
        return {
            "job_id": self.job_id,
            "recipe_id": self.recipe_id,
            "player_id": self.player_id,
            "progress": self.progress_pct,
            "complete": self.is_complete,
            "success": self.was_successful,
            "quality": self.quality_tier
        }


@dataclass
class TradeOffer:
    """Trading offer between players or NPC."""
    offer_id: str
    trader_id: str  # NPC or player ID
    items_offered: Dict[str, int] = field(default_factory=dict)  # item_id -> quantity
    items_wanted: Dict[str, int] = field(default_factory=dict)   # item_id -> quantity
    price_gold: int = 0
    description: str = ""
    expires_at: Optional[str] = None
    is_available: bool = True

    def to_dict(self) -> Dict:
        return {
            "offer_id": self.offer_id,
            "trader_id": self.trader_id,
            "items_offered": self.items_offered,
            "items_wanted": self.items_wanted,
            "price_gold": self.price_gold,
            "description": self.description,
            "available": self.is_available
        }


# ═══════════════════════════ ITEM DATABASE ═════════════════════════════════

class ItemDatabase:
    """Central item database with all game items."""

    def __init__(self):
        self.items: Dict[str, Item] = {}
        self.sets: Dict[str, ItemSetBonus] = {}
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect("item_database.db")
        c = conn.cursor()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS items(
            item_id TEXT PRIMARY KEY,
            name TEXT,
            item_type TEXT,
            rarity TEXT,
            value INT,
            weight REAL,
            max_durability REAL,
            data TEXT
        );
        CREATE TABLE IF NOT EXISTS sets(
            set_id TEXT PRIMARY KEY,
            set_name TEXT,
            required_count INT,
            data TEXT
        );
        """)
        conn.commit()
        conn.close()

    def create_item(
        self,
        name: str,
        description: str,
        item_type: ItemType,
        rarity: ItemRarity = ItemRarity.COMMON,
        value: int = 10,
        weight: float = 1.0,
        max_durability: float = 100.0,
    ) -> Item:
        """Create and register a new item."""
        item = Item(
            item_id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            item_type=item_type,
            rarity=rarity,
            value=value,
            weight=weight,
            max_durability=max_durability,
            current_durability=max_durability
        )
        self.items[item.item_id] = item
        return item

    def create_equipment(
        self,
        name: str,
        description: str,
        slot: EquipmentSlot,
        rarity: ItemRarity = ItemRarity.COMMON,
        armor_type: Optional[ArmorType] = None,
        weapon_type: Optional[WeaponType] = None,
    ) -> Item:
        """Create equipment item."""
        item_type = ItemType.ARMOR if armor_type else ItemType.WEAPON if weapon_type else ItemType.ACCESSORY
        
        item = Item(
            item_id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            item_type=item_type,
            rarity=rarity,
            equipment_slot=slot,
            armor_type=armor_type,
            weapon_type=weapon_type,
            weight=1.0 if weapon_type else 0.5 if armor_type else 0.1,
            max_durability=100.0 if (armor_type or weapon_type) else float('inf')
        )
        self.items[item.item_id] = item
        return item

    def add_stat_to_item(self, item_id: str, stat: Stat, value: float):
        """Add stat to item."""
        if item_id in self.items:
            item = self.items[item_id]
            item.stats[stat] = ItemStat(stat, value)

    def add_effect_to_item(self, item_id: str, effect: ItemEffect):
        """Add effect to item."""
        if item_id in self.items:
            self.items[item_id].effects.append(effect)

    def create_set(self, set_name: str, required_count: int) -> ItemSetBonus:
        """Create an item set."""
        set_bonus = ItemSetBonus(
            set_id=str(uuid.uuid4())[:6],
            set_name=set_name,
            required_count=required_count
        )
        self.sets[set_bonus.set_id] = set_bonus
        return set_bonus

    def get_item(self, item_id: str) -> Optional[Item]:
        """Get item from database."""
        return self.items.get(item_id)

    def export_database(self, filepath: str):
        """Export item database to JSON."""
        data = {
            "items": {iid: item.to_dict() for iid, item in self.items.items()},
            "sets": {sid: s.to_dict() for sid, s in self.sets.items()}
        }
        Path(filepath).write_text(json.dumps(data, indent=2))

    def get_stats(self) -> Dict:
        """Get database statistics."""
        return {
            "total_items": len(self.items),
            "total_sets": len(self.sets),
            "by_type": {t.value: len([i for i in self.items.values() if i.item_type == t])
                       for t in ItemType},
            "by_rarity": {r.label: len([i for i in self.items.values() if i.rarity == r])
                         for r in ItemRarity}
        }


# ═══════════════════════════ INVENTORY SYSTEM ═════════════════════════════

class PlayerInventory:
    """Player inventory management."""

    def __init__(self, player_id: str, max_slots: int = 24, max_weight: float = 100.0):
        self.player_id = player_id
        self.max_slots = max_slots
        self.max_weight = max_weight
        self.items: List[InventoryItem] = []
        self.equipment: Dict[EquipmentSlot, Item] = {}
        self.gold: int = 0
        self.total_carried_weight: float = 0.0

    @property
    def used_slots(self) -> int:
        return len(self.items)

    @property
    def available_slots(self) -> int:
        return self.max_slots - self.used_slots

    @property
    def total_weight(self) -> float:
        return sum(item.total_weight for item in self.items)

    @property
    def inventory_full(self) -> bool:
        return self.used_slots >= self.max_slots or self.total_weight >= self.max_weight

    def add_item(self, item: Item, quantity: int = 1) -> bool:
        """Add item to inventory."""
        if item.stackable:
            # Try to stack with existing
            for inv_item in self.items:
                if inv_item.item_id == item.item_id:
                    if inv_item.quantity + quantity <= item.max_stack:
                        inv_item.quantity += quantity
                        return True

        # Add as new item
        if self.used_slots < self.max_slots:
            if self.total_weight + (item.weight * quantity) <= self.max_weight:
                self.items.append(InventoryItem(item, quantity))
                return True

        return False

    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        """Remove item from inventory."""
        for inv_item in self.items:
            if inv_item.item_id == item_id:
                if inv_item.quantity > quantity:
                    inv_item.quantity -= quantity
                else:
                    self.items.remove(inv_item)
                return True
        return False

    def equip_item(self, item_id: str) -> bool:
        """Equip an item."""
        inv_item = None
        for item in self.items:
            if item.item_id == item_id:
                inv_item = item
                break

        if not inv_item or not inv_item.item.equipment_slot:
            return False

        slot = inv_item.item.equipment_slot
        if slot in self.equipment:
            # Unequip existing
            old_item = self.equipment[slot]
            self.add_item(old_item)

        # Equip new item
        self.equipment[slot] = inv_item.item
        self.remove_item(item_id, 1)
        return True

    def unequip_item(self, slot: EquipmentSlot) -> bool:
        """Unequip item from slot."""
        if slot in self.equipment:
            item = self.equipment[slot]
            del self.equipment[slot]
            return self.add_item(item)
        return False

    def get_equipped_stats(self) -> Dict[Stat, float]:
        """Calculate total stats from equipped items."""
        total_stats: Dict[Stat, float] = {}
        
        for item in self.equipment.values():
            for stat, item_stat in item.stats.items():
                if stat not in total_stats:
                    total_stats[stat] = 0.0
                if item_stat.percentage:
                    total_stats[stat] *= (1.0 + item_stat.value / 100.0)
                else:
                    total_stats[stat] += item_stat.value

        return total_stats

    def get_equipped_set_bonuses(self) -> List[ItemSetBonus]:
        """Get active set bonuses from equipped items."""
        set_counts: Dict[str, int] = {}
        
        for item in self.equipment.values():
            if item.set_id:
                set_counts[item.set_id] = set_counts.get(item.set_id, 0) + 1

        active_sets = []
        for set_id, count in set_counts.items():
            if count >= 2:  # At least 2 pieces
                active_sets.append(set_id)

        return active_sets

    def add_gold(self, amount: int):
        """Add gold to inventory."""
        self.gold += amount

    def remove_gold(self, amount: int) -> bool:
        """Remove gold from inventory."""
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False

    def to_dict(self) -> Dict:
        return {
            "player_id": self.player_id,
            "gold": self.gold,
            "items": [item.to_dict() for item in self.items],
            "equipment": {slot.value: item.to_dict() 
                         for slot, item in self.equipment.items()},
            "slots": {
                "used": self.used_slots,
                "max": self.max_slots,
                "available": self.available_slots
            },
            "weight": {
                "current": self.total_weight,
                "max": self.max_weight,
                "percentage": (self.total_weight / self.max_weight) * 100
            }
        }


# ═══════════════════════════ CRAFTING SYSTEM ═════════════════════════════

class CraftingSystem:
    """Recipe management and crafting."""

    def __init__(self, item_db: ItemDatabase):
        self.item_db = item_db
        self.recipes: Dict[str, Recipe] = {}
        self.crafting_jobs: Dict[str, CraftingJob] = {}

    def create_recipe(
        self,
        name: str,
        description: str,
        category: CraftingCategory,
        result_item_id: str,
        result_quantity: int = 1,
        crafting_time: int = 5,
        level_required: int = 1,
    ) -> Recipe:
        """Create a crafting recipe."""
        recipe = Recipe(
            recipe_id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            category=category,
            result_item_id=result_item_id,
            result_quantity=result_quantity,
            crafting_time=crafting_time,
            level_required=level_required
        )
        self.recipes[recipe.recipe_id] = recipe
        return recipe

    def add_ingredient(self, recipe_id: str, item_id: str, item_name: str, quantity: int):
        """Add ingredient to recipe."""
        if recipe_id in self.recipes:
            ingredient = RecipeIngredient(item_id, item_name, quantity)
            self.recipes[recipe_id].ingredients.append(ingredient)

    def start_crafting(self, player_id: str, recipe_id: str, inventory: PlayerInventory) -> Optional[CraftingJob]:
        """Start a crafting job."""
        if recipe_id not in self.recipes:
            return None

        recipe = self.recipes[recipe_id]

        # Check ingredients
        for ingredient in recipe.ingredients:
            item_found = False
            for inv_item in inventory.items:
                if inv_item.item_id == ingredient.item_id and inv_item.quantity >= ingredient.quantity:
                    item_found = True
                    break
            if not item_found:
                return None  # Missing ingredient

        # Remove ingredients from inventory
        for ingredient in recipe.ingredients:
            inventory.remove_item(ingredient.item_id, ingredient.quantity)

        # Create crafting job
        job = CraftingJob(
            job_id=str(uuid.uuid4())[:6],
            recipe_id=recipe_id,
            player_id=player_id,
            started_at=datetime.utcnow().isoformat(),
            duration=recipe.crafting_time,
            completed_at=(datetime.utcnow() + timedelta(seconds=recipe.crafting_time)).isoformat()
        )

        self.crafting_jobs[job.job_id] = job
        return job

    def complete_crafting(self, job_id: str, inventory: PlayerInventory, item_db: ItemDatabase) -> Optional[Item]:
        """Complete a crafting job."""
        if job_id not in self.crafting_jobs:
            return None

        job = self.crafting_jobs[job_id]
        if not job.is_complete:
            return None

        recipe = self.recipes[job.recipe_id]
        result_item = item_db.get_item(recipe.result_item_id)

        if not result_item:
            return None

        # Check success
        if random.random() * 100 > recipe.yield_chance:
            job.was_successful = False
            return None

        job.was_successful = True

        # Determine quality tier
        job.quality_tier = max(1, min(5, random.randint(1, 6)))

        # Add result to inventory
        for _ in range(recipe.result_quantity):
            inventory.add_item(result_item)

        return result_item

    def get_available_recipes(self, player_level: int, player_skill: int) -> List[Recipe]:
        """Get recipes available to player."""
        available = []
        for recipe in self.recipes.values():
            if recipe.level_required <= player_level and recipe.skill_required <= player_skill:
                available.append(recipe)
        return available

    def to_dict(self) -> Dict:
        return {
            "recipes": {rid: r.to_dict() for rid, r in self.recipes.items()},
            "jobs": {jid: j.to_dict() for jid, j in self.crafting_jobs.items()}
        }


# ═══════════════════════════ TRADING SYSTEM ═════════════════════════════

class TradingSystem:
    """Player-to-player and NPC trading."""

    def __init__(self):
        self.offers: Dict[str, TradeOffer] = {}
        self.completed_trades: List[Dict] = []

    def create_offer(
        self,
        trader_id: str,
        items_offered: Dict[str, int],
        items_wanted: Dict[str, int] = None,
        price_gold: int = 0,
        description: str = ""
    ) -> TradeOffer:
        """Create a trade offer."""
        offer = TradeOffer(
            offer_id=str(uuid.uuid4())[:8],
            trader_id=trader_id,
            items_offered=items_offered,
            items_wanted=items_wanted or {},
            price_gold=price_gold,
            description=description
        )
        self.offers[offer.offer_id] = offer
        return offer

    def execute_trade(
        self,
        offer_id: str,
        buyer_inventory: PlayerInventory,
        seller_inventory: PlayerInventory
    ) -> bool:
        """Execute a trade between two players."""
        if offer_id not in self.offers:
            return False

        offer = self.offers[offer_id]

        # Check buyer has gold/items wanted
        if offer.price_gold > 0 and buyer_inventory.gold < offer.price_gold:
            return False

        # Check buyer has items wanted
        for item_id, quantity in offer.items_wanted.items():
            found = False
            for inv_item in buyer_inventory.items:
                if inv_item.item_id == item_id and inv_item.quantity >= quantity:
                    found = True
                    break
            if not found:
                return False

        # Check seller has items offered
        for item_id, quantity in offer.items_offered.items():
            found = False
            for inv_item in seller_inventory.items:
                if inv_item.item_id == item_id and inv_item.quantity >= quantity:
                    found = True
                    break
            if not found:
                return False

        # Execute trade
        # Buyer pays gold
        if offer.price_gold > 0:
            buyer_inventory.remove_gold(offer.price_gold)
            seller_inventory.add_gold(offer.price_gold)

        # Buyer gives items wanted
        for item_id, quantity in offer.items_wanted.items():
            seller_inventory.remove_item(item_id, quantity)
            # Note: item already in seller's hands

        # Seller gives items offered
        for item_id, quantity in offer.items_offered.items():
            # Get item from seller's inventory
            for inv_item in seller_inventory.items:
                if inv_item.item_id == item_id:
                    for _ in range(quantity):
                        buyer_inventory.add_item(inv_item.item)
                    seller_inventory.remove_item(item_id, quantity)
                    break

        # Record trade
        self.completed_trades.append({
            "timestamp": datetime.utcnow().isoformat(),
            "offer_id": offer_id,
            "buyer": buyer_inventory.player_id,
            "seller": seller_inventory.player_id
        })

        # Close offer
        self.offers[offer_id].is_available = False

        return True

    def to_dict(self) -> Dict:
        return {
            "open_offers": {oid: o.to_dict() for oid, o in self.offers.items() if o.is_available},
            "completed_trades": len(self.completed_trades)
        }


# ═══════════════════════════ COMPLETE SYSTEM ═══════════════════════════

class AdvancedInventorySystem:
    """Complete inventory, crafting, and trading system."""

    def __init__(self, db_path: str = "inventory_system.db"):
        self.db_path = db_path
        self.item_db = ItemDatabase()
        self.crafting_system = CraftingSystem(self.item_db)
        self.trading_system = TradingSystem()
        self.player_inventories: Dict[str, PlayerInventory] = {}

    def create_player_inventory(self, player_id: str, max_slots: int = 24) -> PlayerInventory:
        """Create inventory for player."""
        inventory = PlayerInventory(player_id, max_slots)
        self.player_inventories[player_id] = inventory
        return inventory

    def get_player_inventory(self, player_id: str) -> Optional[PlayerInventory]:
        """Get player inventory."""
        return self.player_inventories.get(player_id)

    def export_system(self, filepath: str):
        """Export entire system state."""
        data = {
            "items": self.item_db.export_database(filepath + ".items.json"),
            "crafting": self.crafting_system.to_dict(),
            "trading": self.trading_system.to_dict(),
            "player_inventories": {
                pid: inv.to_dict()
                for pid, inv in self.player_inventories.items()
            }
        }
        Path(filepath).write_text(json.dumps(data, indent=2))

    def get_system_stats(self) -> Dict:
        """Get system statistics."""
        return {
            "items": self.item_db.get_stats(),
            "recipes": len(self.crafting_system.recipes),
            "active_trades": sum(1 for o in self.trading_system.offers.values() if o.is_available),
            "completed_trades": len(self.trading_system.completed_trades),
            "players": len(self.player_inventories)
        }


def demo_inventory_system():
    """Demonstrate the inventory system."""
    system = AdvancedInventorySystem()
    
    # Create items
    sword = system.item_db.create_item(
        "Iron Sword",
        "A sturdy iron sword",
        ItemType.WEAPON,
        ItemRarity.COMMON,
        value=100,
        weight=5.0
    )
    system.item_db.add_stat_to_item(sword.item_id, Stat.ATTACK_POWER, 10.0)
    
    potion = system.item_db.create_item(
        "Health Potion",
        "Restores 50 HP",
        ItemType.CONSUMABLE,
        ItemRarity.COMMON,
        value=20,
        weight=0.5,
        max_durability=float('inf')
    )
    potion.stackable = True
    potion.max_stack = 99
    
    # Create player inventory
    inv = system.create_player_inventory("player_1")
    inv.add_item(sword)
    inv.add_item(potion, 5)
    inv.add_gold(500)
    
    # Create recipe
    recipe = system.crafting_system.create_recipe(
        "Iron Sword Recipe",
        "Craft an iron sword",
        CraftingCategory.WEAPON,
        sword.item_id,
        crafting_time=10
    )
    
    print("Inventory System Demo:")
    print(f"Items: {inv.used_slots}/{inv.max_slots}")
    print(f"Weight: {inv.total_weight:.1f}/{inv.max_weight}")
    print(f"Gold: {inv.gold}")
    print(f"System Stats: {system.get_system_stats()}")


if __name__ == "__main__":
    demo_inventory_system()
