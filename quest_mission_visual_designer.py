"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        ADVANCED QUEST & MISSION VISUAL DESIGNER                             ║
║  Visual Editor · Objective Tracking · Reward Calculator · Quest Chains      ║
║  Random Generation · NPC Assignment · Location Mapping                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import asyncio, json, random, uuid, sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
import math


# ═══════════════════════════ ENUMS ══════════════════════════════════════════
class QuestStatus(Enum):
    LOCKED      = "locked"
    AVAILABLE   = "available"
    ACTIVE      = "active"
    COMPLETED   = "completed"
    FAILED      = "failed"
    ABANDONED   = "abandoned"

class ObjectiveType(Enum):
    KILL         = "kill"
    COLLECT      = "collect"
    DELIVER      = "deliver"
    REACH        = "reach"
    INTERACT     = "interact"
    PROTECT      = "protect"
    ESCORT       = "escort"
    SURVIVE      = "survive"
    CRAFT        = "craft"
    TALK_TO      = "talk_to"
    DISCOVER     = "discover"
    SOLVE_PUZZLE = "solve_puzzle"
    STEALTH      = "stealth"
    TIMED        = "timed"
    DEFEND       = "defend"
    RESCUE       = "rescue"
    INVESTIGATE  = "investigate"

class Difficulty(Enum):
    TRIVIAL      = (1, "Trivial",  0.5)
    EASY         = (2, "Easy",     0.8)
    NORMAL       = (3, "Normal",   1.0)
    HARD         = (4, "Hard",     1.5)
    EPIC         = (5, "Epic",     2.5)
    LEGENDARY    = (6, "Legendary", 4.0)
    MYTHIC       = (7, "Mythic",   6.0)

    def __init__(self, level, label, multiplier):
        self.level = level
        self.label = label
        self.multiplier = multiplier

class RewardType(Enum):
    GOLD         = "gold"
    XP           = "xp"
    ITEM         = "item"
    SKILL_POINT  = "skill_point"
    REPUTATION   = "reputation"
    UNLOCK       = "unlock"
    TITLE        = "title"
    COMPANION    = "companion"
    SPELL        = "spell"
    ABILITY      = "ability"
    RECIPE       = "recipe"

class NPCRole(Enum):
    QUEST_GIVER  = "quest_giver"
    QUEST_TARGET = "quest_target"
    ESCORT       = "escort"
    GUARDIAN     = "guardian"
    VENDOR       = "vendor"
    ALLY         = "ally"
    ENEMY        = "enemy"

class LocationType(Enum):
    CITY         = "city"
    DUNGEON      = "dungeon"
    WILDERNESS   = "wilderness"
    CAVE         = "cave"
    CAMP         = "camp"
    FORTRESS     = "fortress"
    SHRINE       = "shrine"
    RUIN         = "ruin"
    TAVERN       = "tavern"
    MARKETPLACE  = "marketplace"


# ═══════════════════════════ DATA STRUCTURES ═════════════════════════════════

@dataclass
class Location:
    """Game location/area with coordinates and properties."""
    location_id: str
    name: str
    location_type: LocationType
    x: float
    y: float
    z: float
    radius: float = 100.0
    difficulty: Difficulty = Difficulty.NORMAL
    npcs: List[str] = field(default_factory=list)  # NPC IDs
    objectives: List[str] = field(default_factory=list)  # Objective IDs
    description: str = ""
    connections: List[str] = field(default_factory=list)  # Connected location IDs
    discovered: bool = False
    tags: List[str] = field(default_factory=list)

    @property
    def coordinates(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)

    def distance_to(self, other: Location) -> float:
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx*dx + dy*dy + dz*dz)

    def to_dict(self) -> Dict:
        return {
            "id": self.location_id,
            "name": self.name,
            "type": self.location_type.value,
            "coords": self.coordinates,
            "radius": self.radius,
            "difficulty": self.difficulty.label,
            "npcs": self.npcs,
            "description": self.description,
        }


@dataclass
class NPC:
    """Non-player character with role and properties."""
    npc_id: str
    name: str
    role: NPCRole
    location_id: str
    description: str = ""
    faction: str = ""
    level: int = 1
    dialogue_tree_id: str = ""  # Link to dialogue system
    available_quests: List[str] = field(default_factory=list)
    personality_traits: List[str] = field(default_factory=list)
    relationships: Dict[str, int] = field(default_factory=dict)  # NPC_ID -> reputation
    schedules: Dict[str, str] = field(default_factory=dict)  # Time-based locations
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "id": self.npc_id,
            "name": self.name,
            "role": self.role.value,
            "location": self.location_id,
            "level": self.level,
            "faction": self.faction,
            "quests": self.available_quests,
            "traits": self.personality_traits,
        }


@dataclass
class Objective:
    """Individual quest objective with tracking."""
    objective_id: str
    quest_id: str
    obj_type: ObjectiveType
    description: str
    target_id: str = ""  # Enemy type / item ID / location ID
    required_qty: int = 1
    current_qty: int = 0
    is_optional: bool = False
    is_hidden: bool = False
    time_limit: Optional[int] = None  # Seconds
    location_hint: str = ""
    location_id: Optional[str] = None
    reward_multiplier: float = 1.0
    on_complete_callback: Optional[str] = None
    status: QuestStatus = QuestStatus.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def completed(self) -> bool:
        return self.current_qty >= self.required_qty

    @property
    def progress_pct(self) -> float:
        return min(100.0, (self.current_qty / max(1, self.required_qty)) * 100)

    def update(self, amount: int = 1):
        self.current_qty = min(self.required_qty, self.current_qty + amount)
        if self.completed:
            self.status = QuestStatus.COMPLETED

    def to_dict(self) -> Dict:
        return {
            "id": self.objective_id,
            "type": self.obj_type.value,
            "description": self.description,
            "target": self.target_id,
            "required": self.required_qty,
            "current": self.current_qty,
            "completed": self.completed,
            "progress": round(self.progress_pct, 1),
            "optional": self.is_optional,
            "hidden": self.is_hidden,
            "location": self.location_id,
        }


@dataclass
class Reward:
    """Quest reward definition."""
    reward_type: RewardType
    value: Any  # int for gold/xp, str for item/title
    quantity: int = 1
    rarity: str = "common"  # common, uncommon, rare, epic, legendary
    condition: str = ""  # "" = always, "all_objectives" = all done
    difficulty_scaled: bool = True

    def calculate_value(self, difficulty: Difficulty) -> Any:
        if self.difficulty_scaled and isinstance(self.value, (int, float)):
            return int(self.value * difficulty.multiplier)
        return self.value

    def to_dict(self) -> Dict:
        return {
            "type": self.reward_type.value,
            "value": self.value,
            "qty": self.quantity,
            "rarity": self.rarity,
            "condition": self.condition,
        }


@dataclass
class Quest:
    """Complete quest definition with all properties."""
    quest_id: str
    name: str
    description: str
    difficulty: Difficulty = Difficulty.NORMAL
    giver_npc_id: str = ""
    giver_location_id: str = ""
    objectives: List[Objective] = field(default_factory=list)
    rewards: List[Reward] = field(default_factory=list)
    quest_chain_id: Optional[str] = None
    next_quest_id: Optional[str] = None
    prerequisite_quests: List[str] = field(default_factory=list)
    prerequisite_level: int = 1
    time_limit: Optional[int] = None  # Seconds
    is_repeatable: bool = False
    is_hidden: bool = False
    status: QuestStatus = QuestStatus.AVAILABLE
    lore_text: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def required_objectives(self) -> List[Objective]:
        return [o for o in self.objectives if not o.is_optional]

    @property
    def all_required_complete(self) -> bool:
        return all(o.completed for o in self.required_objectives)

    @property
    def all_objectives_complete(self) -> bool:
        return all(o.completed for o in self.objectives)

    @property
    def progress_pct(self) -> float:
        req = self.required_objectives
        if not req:
            return 100.0
        return sum(o.progress_pct for o in req) / len(req)

    def calculate_total_reward(self, reward_type: RewardType) -> int:
        total = 0
        for reward in self.rewards:
            if reward.reward_type == reward_type:
                value = reward.calculate_value(self.difficulty)
                total += value * reward.quantity
        return total

    def to_dict(self) -> Dict:
        return {
            "quest_id": self.quest_id,
            "name": self.name,
            "description": self.description,
            "difficulty": self.difficulty.label,
            "giver": self.giver_npc_id,
            "status": self.status.value,
            "progress": round(self.progress_pct, 1),
            "objectives": [o.to_dict() for o in self.objectives],
            "rewards": [r.to_dict() for r in self.rewards],
            "total_gold": self.calculate_total_reward(RewardType.GOLD),
            "total_xp": self.calculate_total_reward(RewardType.XP),
            "tags": self.tags,
        }


@dataclass
class QuestChain:
    """Linked sequence of quests."""
    chain_id: str
    name: str
    description: str
    quest_ids: List[str] = field(default_factory=list)  # Ordered
    difficulty_progression: bool = True  # Each quest harder than previous
    faction: str = ""
    reward_multiplier: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict:
        return {
            "id": self.chain_id,
            "name": self.name,
            "description": self.description,
            "quests": self.quest_ids,
            "faction": self.faction,
        }


# ═══════════════════════════ REWARD CALCULATOR ══════════════════════════════

class RewardCalculator:
    """Calculates quest rewards based on difficulty, objectives, and conditions."""

    # Base reward values
    BASE_REWARDS = {
        RewardType.GOLD: 100,
        RewardType.XP: 250,
        RewardType.SKILL_POINT: 1,
        RewardType.REPUTATION: 10,
    }

    # Objective reward multipliers
    OBJECTIVE_MULTIPLIERS = {
        ObjectiveType.KILL: 1.2,
        ObjectiveType.COLLECT: 0.8,
        ObjectiveType.DELIVER: 0.9,
        ObjectiveType.REACH: 0.7,
        ObjectiveType.INTERACT: 0.6,
        ObjectiveType.PROTECT: 1.5,
        ObjectiveType.ESCORT: 1.3,
        ObjectiveType.SURVIVE: 1.4,
        ObjectiveType.CRAFT: 1.1,
        ObjectiveType.TALK_TO: 0.5,
        ObjectiveType.DISCOVER: 0.8,
        ObjectiveType.SOLVE_PUZZLE: 1.2,
        ObjectiveType.STEALTH: 1.3,
        ObjectiveType.TIMED: 1.5,
        ObjectiveType.DEFEND: 1.4,
        ObjectiveType.RESCUE: 1.6,
        ObjectiveType.INVESTIGATE: 1.0,
    }

    @staticmethod
    def calculate_quest_rewards(quest: Quest) -> List[Reward]:
        """Generate rewards for a quest based on difficulty and objectives."""
        rewards = []
        
        # Calculate complexity multiplier from objectives
        complexity_mult = 1.0
        if quest.objectives:
            avg_mult = sum(
                RewardCalculator.OBJECTIVE_MULTIPLIERS.get(o.obj_type, 1.0)
                for o in quest.objectives
            ) / len(quest.objectives)
            complexity_mult = avg_mult

        # Apply difficulty multiplier
        diff_mult = quest.difficulty.multiplier

        # Gold reward
        gold = int(RewardCalculator.BASE_REWARDS[RewardType.GOLD] * diff_mult * complexity_mult)
        rewards.append(Reward(RewardType.GOLD, gold, difficulty_scaled=False))

        # XP reward
        xp = int(RewardCalculator.BASE_REWARDS[RewardType.XP] * diff_mult * complexity_mult)
        rewards.append(Reward(RewardType.XP, xp, difficulty_scaled=False))

        # Skill point (for hard+ quests)
        if quest.difficulty.level >= Difficulty.HARD.level:
            rewards.append(Reward(RewardType.SKILL_POINT, 1, difficulty_scaled=False))

        # Reputation
        rep = int(RewardCalculator.BASE_REWARDS[RewardType.REPUTATION] * diff_mult)
        rewards.append(Reward(RewardType.REPUTATION, rep, difficulty_scaled=False))

        return rewards

    @staticmethod
    def scale_rewards_by_player_level(rewards: List[Reward], player_level: int, quest_level: int) -> List[Reward]:
        """Scale rewards based on player level relative to quest level."""
        scaled = []
        level_diff = player_level - quest_level
        
        if level_diff < -5:
            scaling = 1.5  # Bonus for underleveled
        elif level_diff < 0:
            scaling = 1.2
        elif level_diff < 3:
            scaling = 1.0
        elif level_diff < 5:
            scaling = 0.8
        else:
            scaling = 0.5

        for reward in rewards:
            if isinstance(reward.value, (int, float)):
                new_reward = Reward(
                    reward.reward_type,
                    int(reward.value * scaling),
                    reward.quantity,
                    reward.rarity,
                    reward.condition,
                    reward.difficulty_scaled
                )
            else:
                new_reward = reward
            scaled.append(new_reward)

        return scaled


# ═══════════════════════════ QUEST CHAIN SYSTEM ════════════════════════════

class QuestChainSystem:
    """Manages quest chains and progression."""

    def __init__(self):
        self.chains: Dict[str, QuestChain] = {}
        self.quest_to_chain: Dict[str, str] = {}

    def create_chain(self, name: str, description: str, faction: str = "") -> QuestChain:
        """Create a new quest chain."""
        chain = QuestChain(
            chain_id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            faction=faction
        )
        self.chains[chain.chain_id] = chain
        return chain

    def add_quest_to_chain(self, chain_id: str, quest: Quest, position: Optional[int] = None):
        """Add a quest to a chain."""
        if chain_id not in self.chains:
            return False

        chain = self.chains[chain_id]
        if position is None:
            chain.quest_ids.append(quest.quest_id)
        else:
            chain.quest_ids.insert(position, quest.quest_id)

        self.quest_to_chain[quest.quest_id] = chain_id
        
        # Link quests in chain
        if position is not None and position > 0:
            prev_quest_id = chain.quest_ids[position - 1]
            # This should be handled by caller setting next_quest_id
        
        return True

    def get_next_in_chain(self, quest: Quest) -> Optional[str]:
        """Get the next quest ID in the chain."""
        if quest.chain_id and quest.chain_id in self.chains:
            chain = self.chains[quest.chain_id]
            try:
                idx = chain.quest_ids.index(quest.quest_id)
                if idx < len(chain.quest_ids) - 1:
                    return chain.quest_ids[idx + 1]
            except ValueError:
                pass
        return None

    def get_chain_progress(self, chain_id: str, completed_quests: Set[str]) -> Tuple[int, int]:
        """Get (completed_count, total_count) for a chain."""
        if chain_id not in self.chains:
            return (0, 0)

        chain = self.chains[chain_id]
        completed = sum(1 for qid in chain.quest_ids if qid in completed_quests)
        return (completed, len(chain.quest_ids))


# ═══════════════════════════ RANDOM GENERATION ════════════════════════════

class QuestRandomGenerator:
    """Generates random quests with appropriate difficulty and structure."""

    QUEST_TEMPLATES = [
        {
            "name": "Eliminate the {enemy_type}",
            "objectives": [ObjectiveType.KILL],
            "min_objectives": 1,
            "max_objectives": 3,
        },
        {
            "name": "Collect {item_name}",
            "objectives": [ObjectiveType.COLLECT],
            "min_objectives": 1,
            "max_objectives": 2,
        },
        {
            "name": "Deliver {item_name} to {npc_name}",
            "objectives": [ObjectiveType.COLLECT, ObjectiveType.DELIVER],
            "min_objectives": 2,
            "max_objectives": 2,
        },
        {
            "name": "Rescue {npc_name}",
            "objectives": [ObjectiveType.REACH, ObjectiveType.RESCUE],
            "min_objectives": 2,
            "max_objectives": 3,
        },
        {
            "name": "Investigate {location_name}",
            "objectives": [ObjectiveType.INVESTIGATE, ObjectiveType.INTERACT],
            "min_objectives": 2,
            "max_objectives": 3,
        },
        {
            "name": "Protect {location_name} from {enemy_type}",
            "objectives": [ObjectiveType.PROTECT, ObjectiveType.KILL],
            "min_objectives": 2,
            "max_objectives": 2,
        },
    ]

    @staticmethod
    def generate_quest(
        difficulty: Difficulty = None,
        location: Location = None,
        quest_giver: NPC = None,
    ) -> Quest:
        """Generate a random quest."""
        if difficulty is None:
            difficulty = random.choice(list(Difficulty))

        # Select template
        template = random.choice(QuestRandomGenerator.QUEST_TEMPLATES)
        name = template["name"]
        
        # Generate objectives
        num_objectives = random.randint(
            template["min_objectives"],
            template["max_objectives"]
        )
        objectives = []
        for i in range(num_objectives):
            obj_type = template["objectives"][i % len(template["objectives"])]
            obj = Objective(
                objective_id=str(uuid.uuid4())[:6],
                quest_id="",  # Will be set by quest
                obj_type=obj_type,
                description=f"Objective {i+1}",
                required_qty=random.randint(1, 5) if obj_type == ObjectiveType.COLLECT else 1,
                location_id=location.location_id if location else None,
            )
            objectives.append(obj)

        # Create quest
        quest = Quest(
            quest_id=str(uuid.uuid4())[:8],
            name=name,
            description=f"Complete the following objectives",
            difficulty=difficulty,
            giver_npc_id=quest_giver.npc_id if quest_giver else "",
            giver_location_id=location.location_id if location else "",
            objectives=objectives,
            tags=["randomly_generated"],
        )

        # Set objective quest_ids
        for obj in quest.objectives:
            obj.quest_id = quest.quest_id

        # Calculate rewards
        quest.rewards = RewardCalculator.calculate_quest_rewards(quest)

        return quest


# ═══════════════════════════ LOCATION MAPPING ═════════════════════════════

class LocationMapper:
    """Manages game world locations and spatial relationships."""

    def __init__(self):
        self.locations: Dict[str, Location] = {}
        self.location_index: Dict[str, List[str]] = {}  # Type -> Location IDs

    def create_location(
        self,
        name: str,
        location_type: LocationType,
        x: float, y: float, z: float,
        difficulty: Difficulty = Difficulty.NORMAL,
        description: str = "",
    ) -> Location:
        """Create a new location."""
        loc = Location(
            location_id=str(uuid.uuid4())[:8],
            name=name,
            location_type=location_type,
            x=x, y=y, z=z,
            difficulty=difficulty,
            description=description,
        )
        self.locations[loc.location_id] = loc
        
        # Index by type
        if location_type.value not in self.location_index:
            self.location_index[location_type.value] = []
        self.location_index[location_type.value].append(loc.location_id)
        
        return loc

    def connect_locations(self, loc1_id: str, loc2_id: str):
        """Create bidirectional connection between locations."""
        if loc1_id in self.locations and loc2_id in self.locations:
            self.locations[loc1_id].connections.append(loc2_id)
            self.locations[loc2_id].connections.append(loc1_id)

    def find_nearest_location(self, location: Location, count: int = 5) -> List[Location]:
        """Find nearest locations by distance."""
        distances = [
            (loc, location.distance_to(loc))
            for loc in self.locations.values()
            if loc.location_id != location.location_id
        ]
        distances.sort(key=lambda x: x[1])
        return [loc for loc, _ in distances[:count]]

    def get_path_between(self, loc1_id: str, loc2_id: str) -> List[str]:
        """Find shortest path between two locations (BFS)."""
        if loc1_id not in self.locations or loc2_id not in self.locations:
            return []

        from collections import deque
        
        queue = deque([(loc1_id, [loc1_id])])
        visited = {loc1_id}

        while queue:
            current, path = queue.popleft()
            if current == loc2_id:
                return path

            loc = self.locations[current]
            for neighbor_id in loc.connections:
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))

        return []

    def get_locations_by_type(self, location_type: LocationType) -> List[Location]:
        """Get all locations of a specific type."""
        loc_ids = self.location_index.get(location_type.value, [])
        return [self.locations[lid] for lid in loc_ids]

    def to_dict(self) -> Dict:
        """Export all locations as dictionary."""
        return {
            loc_id: loc.to_dict()
            for loc_id, loc in self.locations.items()
        }


# ═══════════════════════════ NPC ASSIGNMENT ═════════════════════════════

class NPCAssignmentSystem:
    """Manages NPC assignment to quests and locations."""

    def __init__(self, location_mapper: LocationMapper):
        self.npcs: Dict[str, NPC] = {}
        self.location_mapper = location_mapper
        self.npc_index: Dict[str, List[str]] = {}  # Role -> NPC IDs

    def create_npc(
        self,
        name: str,
        role: NPCRole,
        location_id: str,
        faction: str = "",
        level: int = 1,
        description: str = "",
    ) -> NPC:
        """Create a new NPC."""
        npc = NPC(
            npc_id=str(uuid.uuid4())[:6],
            name=name,
            role=role,
            location_id=location_id,
            faction=faction,
            level=level,
            description=description,
        )
        self.npcs[npc.npc_id] = npc

        # Index by role
        if role.value not in self.npc_index:
            self.npc_index[role.value] = []
        self.npc_index[role.value].append(npc.npc_id)

        return npc

    def assign_quest_to_npc(self, npc_id: str, quest_id: str) -> bool:
        """Assign a quest to an NPC as quest giver."""
        if npc_id in self.npcs and self.npcs[npc_id].role == NPCRole.QUEST_GIVER:
            self.npcs[npc_id].available_quests.append(quest_id)
            return True
        return False

    def find_suitable_npcs(self, role: NPCRole, faction: str = "", count: int = 1) -> List[NPC]:
        """Find NPCs suitable for a role."""
        candidates = []
        for npc_id in self.npc_index.get(role.value, []):
            npc = self.npcs[npc_id]
            if not faction or npc.faction == faction:
                candidates.append(npc)
        
        random.shuffle(candidates)
        return candidates[:count]

    def get_npcs_at_location(self, location_id: str) -> List[NPC]:
        """Get all NPCs at a location."""
        return [npc for npc in self.npcs.values() if npc.location_id == location_id]

    def set_npc_schedule(self, npc_id: str, time: str, location_id: str):
        """Set time-based location for NPC (schedule)."""
        if npc_id in self.npcs:
            self.npcs[npc_id].schedules[time] = location_id

    def to_dict(self) -> Dict:
        """Export all NPCs as dictionary."""
        return {
            npc_id: npc.to_dict()
            for npc_id, npc in self.npcs.items()
        }


# ═══════════════════════════ OBJECTIVE TRACKING ═════════════════════════════

class ObjectiveTracker:
    """Tracks player progress through quest objectives."""

    def __init__(self):
        self.player_objectives: Dict[str, Dict[str, Objective]] = {}  # Player ID -> Quest ID -> Objective

    def start_objective(self, player_id: str, objective: Objective):
        """Start tracking an objective."""
        if player_id not in self.player_objectives:
            self.player_objectives[player_id] = {}

        self.player_objectives[player_id][objective.objective_id] = objective

    def update_objective(self, player_id: str, objective_id: str, amount: int = 1) -> bool:
        """Update objective progress."""
        if player_id not in self.player_objectives:
            return False

        objectives = self.player_objectives[player_id]
        if objective_id not in objectives:
            return False

        obj = objectives[objective_id]
        obj.update(amount)
        return obj.completed

    def get_objective_status(self, player_id: str, objective_id: str) -> Optional[Objective]:
        """Get current objective status."""
        if player_id in self.player_objectives:
            return self.player_objectives[player_id].get(objective_id)
        return None

    def get_active_objectives(self, player_id: str, quest_id: str) -> List[Objective]:
        """Get all active objectives for a quest."""
        if player_id not in self.player_objectives:
            return []

        objectives = self.player_objectives[player_id]
        return [obj for obj in objectives.values() if obj.quest_id == quest_id]

    def complete_objective(self, player_id: str, objective_id: str):
        """Mark objective as complete."""
        if player_id in self.player_objectives:
            obj = self.player_objectives[player_id].get(objective_id)
            if obj:
                obj.status = QuestStatus.COMPLETED

    def get_objective_progress(self, player_id: str, quest_id: str) -> Tuple[int, int]:
        """Get (completed_count, total_count) for a quest."""
        if player_id not in self.player_objectives:
            return (0, 0)

        objectives = self.player_objectives[player_id]
        all_objs = [o for o in objectives.values() if o.quest_id == quest_id]
        completed = sum(1 for o in all_objs if o.completed)
        return (completed, len(all_objs))


# ═══════════════════════════ VISUAL EDITOR (DATA) ═════════════════════════════

@dataclass
class QuestNodeVisualData:
    """Visual representation of quest node in editor."""
    node_id: str
    quest_id: str
    label: str
    x: float
    y: float
    width: float = 150.0
    height: float = 80.0
    color: str = "#4A90E2"
    connected_to: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "id": self.node_id,
            "quest_id": self.quest_id,
            "label": self.label,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "color": self.color,
            "connections": self.connected_to,
        }


class QuestVisualEditor:
    """Visual editor for quest chains and relationships."""

    def __init__(self):
        self.nodes: Dict[str, QuestNodeVisualData] = {}
        self.edges: List[Tuple[str, str]] = []  # (from_node_id, to_node_id)
        self.canvas_width: int = 1920
        self.canvas_height: int = 1080

    def add_quest_node(self, quest: Quest, x: float = None, y: float = None) -> QuestNodeVisualData:
        """Add a quest as a visual node."""
        if x is None:
            x = random.randint(100, self.canvas_width - 200)
        if y is None:
            y = random.randint(100, self.canvas_height - 200)

        node_id = f"node_{quest.quest_id}"
        color = self._difficulty_color(quest.difficulty)
        
        node = QuestNodeVisualData(
            node_id=node_id,
            quest_id=quest.quest_id,
            label=quest.name,
            x=x,
            y=y,
            color=color,
        )
        self.nodes[node_id] = node
        return node

    def connect_quests(self, from_quest_id: str, to_quest_id: str) -> bool:
        """Create visual connection between quests."""
        from_node = f"node_{from_quest_id}"
        to_node = f"node_{to_quest_id}"

        if from_node in self.nodes and to_node in self.nodes:
            self.edges.append((from_node, to_node))
            self.nodes[from_node].connected_to.append(to_node)
            return True
        return False

    def auto_layout(self):
        """Auto-arrange nodes in a hierarchical layout."""
        if not self.nodes:
            return

        # Simple hierarchical layout
        levels: Dict[int, List[str]] = {}
        visited: Set[str] = set()

        def assign_level(node_id: str, level: int):
            if node_id in visited:
                return
            visited.add(node_id)
            if level not in levels:
                levels[level] = []
            levels[level].append(node_id)

            node = self.nodes[node_id]
            for connected in node.connected_to:
                assign_level(connected, level + 1)

        # Start from root nodes
        root_nodes = [nid for nid, node in self.nodes.items() if not any(
            nid in self.nodes[other].connected_to for other in self.nodes if other != nid
        )]

        for root in root_nodes:
            assign_level(root, 0)

        # Position nodes
        y_spacing = 150
        x_offset = 100
        for level, node_ids in levels.items():
            y = 100 + level * y_spacing
            x_spacing = self.canvas_width / (len(node_ids) + 1)
            for i, node_id in enumerate(node_ids):
                self.nodes[node_id].x = x_spacing * (i + 1)
                self.nodes[node_id].y = y

    def export_visualization(self) -> Dict:
        """Export visualization data."""
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [
                {"from": from_id, "to": to_id}
                for from_id, to_id in self.edges
            ],
            "canvas": {
                "width": self.canvas_width,
                "height": self.canvas_height,
            }
        }

    def import_visualization(self, data: Dict):
        """Import visualization data."""
        self.canvas_width = data.get("canvas", {}).get("width", 1920)
        self.canvas_height = data.get("canvas", {}).get("height", 1080)

        # Import nodes
        for node_data in data.get("nodes", []):
            node = QuestNodeVisualData(
                node_id=node_data["id"],
                quest_id=node_data["quest_id"],
                label=node_data["label"],
                x=node_data["x"],
                y=node_data["y"],
                width=node_data.get("width", 150),
                height=node_data.get("height", 80),
                color=node_data.get("color", "#4A90E2"),
            )
            self.nodes[node.node_id] = node

        # Import edges
        for edge_data in data.get("edges", []):
            from_id = edge_data["from"]
            to_id = edge_data["to"]
            self.edges.append((from_id, to_id))
            if from_id in self.nodes:
                self.nodes[from_id].connected_to.append(to_id)

    @staticmethod
    def _difficulty_color(difficulty: Difficulty) -> str:
        """Get color for difficulty."""
        colors = {
            Difficulty.TRIVIAL: "#90EE90",
            Difficulty.EASY: "#87CEEB",
            Difficulty.NORMAL: "#4A90E2",
            Difficulty.HARD: "#FF8C00",
            Difficulty.EPIC: "#9932CC",
            Difficulty.LEGENDARY: "#FFD700",
            Difficulty.MYTHIC: "#FF0000",
        }
        return colors.get(difficulty, "#4A90E2")


# ═══════════════════════════ COMPLETE QUEST SYSTEM ═══════════════════════════

class AdvancedQuestSystem:
    """Complete integrated quest and mission system."""

    def __init__(self, db_path: str = "quest_system.db"):
        self.db_path = db_path
        self.quests: Dict[str, Quest] = {}
        self.chains = QuestChainSystem()
        self.location_mapper = LocationMapper()
        self.npc_system = NPCAssignmentSystem(self.location_mapper)
        self.objective_tracker = ObjectiveTracker()
        self.visual_editor = QuestVisualEditor()
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS quests(
            quest_id TEXT PRIMARY KEY, name TEXT, description TEXT,
            difficulty INT, giver_id TEXT, status TEXT, data TEXT
        );
        CREATE TABLE IF NOT EXISTS objectives(
            objective_id TEXT PRIMARY KEY, quest_id TEXT,
            obj_type TEXT, description TEXT, required_qty INT,
            current_qty INT, data TEXT
        );
        CREATE TABLE IF NOT EXISTS chains(
            chain_id TEXT PRIMARY KEY, name TEXT, quest_ids TEXT
        );
        CREATE TABLE IF NOT EXISTS locations(
            location_id TEXT PRIMARY KEY, name TEXT,
            location_type TEXT, x REAL, y REAL, z REAL, data TEXT
        );
        CREATE TABLE IF NOT EXISTS npcs(
            npc_id TEXT PRIMARY KEY, name TEXT, role TEXT,
            location_id TEXT, data TEXT
        );
        """)
        conn.commit()
        conn.close()

    def create_quest(
        self,
        name: str,
        description: str,
        difficulty: Difficulty = Difficulty.NORMAL,
        giver_npc_id: str = "",
        giver_location_id: str = "",
        tags: List[str] = None,
    ) -> Quest:
        """Create a new quest."""
        quest = Quest(
            quest_id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            difficulty=difficulty,
            giver_npc_id=giver_npc_id,
            giver_location_id=giver_location_id,
            tags=tags or [],
        )
        self.quests[quest.quest_id] = quest
        self.visual_editor.add_quest_node(quest)
        return quest

    def add_objective_to_quest(
        self,
        quest_id: str,
        obj_type: ObjectiveType,
        description: str,
        target_id: str = "",
        required_qty: int = 1,
        optional: bool = False,
    ) -> Optional[Objective]:
        """Add objective to a quest."""
        if quest_id not in self.quests:
            return None

        obj = Objective(
            objective_id=str(uuid.uuid4())[:6],
            quest_id=quest_id,
            obj_type=obj_type,
            description=description,
            target_id=target_id,
            required_qty=required_qty,
            is_optional=optional,
        )
        self.quests[quest_id].objectives.append(obj)
        return obj

    def generate_random_quest(self) -> Quest:
        """Generate a random quest."""
        return QuestRandomGenerator.generate_quest()

    def export_system_state(self, filepath: str):
        """Export entire system state to JSON."""
        data = {
            "quests": {qid: q.to_dict() for qid, q in self.quests.items()},
            "chains": {cid: c.to_dict() for cid, c in self.chains.chains.items()},
            "locations": self.location_mapper.to_dict(),
            "npcs": self.npc_system.to_dict(),
            "visualization": self.visual_editor.export_visualization(),
        }
        Path(filepath).write_text(json.dumps(data, indent=2))

    def import_system_state(self, filepath: str):
        """Import system state from JSON."""
        data = json.loads(Path(filepath).read_text())
        # Implementation for full import would go here
        pass

    def get_system_stats(self) -> Dict:
        """Get statistics about the quest system."""
        return {
            "total_quests": len(self.quests),
            "total_chains": len(self.chains.chains),
            "total_locations": len(self.location_mapper.locations),
            "total_npcs": len(self.npc_system.npcs),
            "total_objectives": sum(
                len(q.objectives) for q in self.quests.values()
            ),
            "total_rewards": sum(
                len(q.rewards) for q in self.quests.values()
            ),
        }


# ═══════════════════════════ EXAMPLE USAGE ═══════════════════════════════════

def demo_quest_system():
    """Demonstrate the quest system."""
    system = AdvancedQuestSystem()

    # Create locations
    city = system.location_mapper.create_location(
        "Brighthaven",
        LocationType.CITY,
        0, 0, 0,
        difficulty=Difficulty.EASY,
        description="A prosperous city"
    )

    dungeon = system.location_mapper.create_location(
        "Darkpeak Cavern",
        LocationType.DUNGEON,
        500, 0, -300,
        difficulty=Difficulty.HARD,
        description="A dangerous dungeon"
    )

    system.location_mapper.connect_locations(city.location_id, dungeon.location_id)

    # Create NPCs
    npc_giver = system.npc_system.create_npc(
        "Gerald the Guard",
        NPCRole.QUEST_GIVER,
        city.location_id,
        faction="City Guard",
        level=5,
        description="Leader of the city guards"
    )

    # Create quest
    quest = system.create_quest(
        "Clear the Cavern",
        "The dungeons have become overrun with creatures. Clear them out!",
        difficulty=Difficulty.HARD,
        giver_npc_id=npc_giver.npc_id,
        giver_location_id=city.location_id,
        tags=["combat", "dungeon"]
    )

    # Add objectives
    system.add_objective_to_quest(
        quest.quest_id,
        ObjectiveType.KILL,
        "Defeat 5 Cave Spiders",
        target_id="spider",
        required_qty=5
    )

    system.add_objective_to_quest(
        quest.quest_id,
        ObjectiveType.REACH,
        "Reach the dungeon center",
        target_id=dungeon.location_id
    )

    # Calculate rewards
    quest.rewards = RewardCalculator.calculate_quest_rewards(quest)

    # Assign quest to NPC
    system.npc_system.assign_quest_to_npc(npc_giver.npc_id, quest.quest_id)

    # Export
    print("Quest System Demo:")
    print(f"Quests: {len(system.quests)}")
    print(f"Locations: {len(system.location_mapper.locations)}")
    print(f"NPCs: {len(system.npc_system.npcs)}")
    print(f"Quest: {quest.name}")
    print(f"Objectives: {len(quest.objectives)}")
    print(f"Rewards: {quest.rewards}")
    print("\nSystem Stats:")
    print(system.get_system_stats())

    return system


if __name__ == "__main__":
    demo_quest_system()
