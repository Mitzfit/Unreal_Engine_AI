"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        ADVANCED COMBAT SYSTEM DESIGNER                                      ║
║  Damage Formulas · Status Effects · Combos · Hit Detection · Skills        ║
║  Critical Calculations · Skill Trees · Ability Cooldowns · Combat Flow    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import json
import uuid
import random
import math
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any, Callable
import asyncio


# ═══════════════════════════ ENUMS ═════════════════════════════════════════

class DamageType(Enum):
    PHYSICAL    = "physical"
    FIRE        = "fire"
    ICE         = "ice"
    LIGHTNING   = "lightning"
    POISON      = "poison"
    HOLY        = "holy"
    DARK        = "dark"
    MAGIC       = "magic"

class StatusEffectType(Enum):
    STUN        = "stun"
    SLOW        = "slow"
    BURN        = "burn"
    FREEZE      = "freeze"
    POISON      = "poison"
    BLEED       = "bleed"
    WEAKNESS    = "weakness"
    STRENGTH    = "strength"
    SHIELD      = "shield"
    REGEN       = "regen"
    CONFUSION   = "confusion"
    SLEEP       = "sleep"

class ComboChainType(Enum):
    LINEAR      = "linear"        # A → B → C
    BRANCH      = "branch"        # A → (B or C) → D
    LOOP        = "loop"          # A → B → A
    CONDITIONAL = "conditional"   # A → B if condition

class HitType(Enum):
    MISS        = "miss"
    HIT         = "hit"
    CRITICAL    = "critical"
    DODGE       = "dodge"
    PARRY       = "parry"
    COUNTER     = "counter"

class CooldownType(Enum):
    GLOBAL      = "global"        # All abilities share cooldown
    PER_ABILITY = "per_ability"   # Each ability has own cooldown
    SHARED      = "shared"        # Group of abilities share cooldown

class SkillTreeNodeType(Enum):
    STAT_BOOST      = "stat_boost"
    ABILITY_UNLOCK  = "ability_unlock"
    PASSIVE_EFFECT  = "passive_effect"
    DAMAGE_MODIFIER = "damage_modifier"
    COST_REDUCTION  = "cost_reduction"


# ═══════════════════════════ DATA STRUCTURES ═══════════════════════════════

@dataclass
class DamageFormula:
    """Defines how damage is calculated."""
    formula_id: str
    name: str
    description: str
    
    # Base calculation: base_damage + (attacker_stat * stat_multiplier) + random_variance
    base_damage: float = 10.0
    stat_multiplier: float = 0.5
    random_variance: float = 0.1  # 0-10% variance
    
    # Scaling factors
    level_scaling: float = 1.0
    weapon_scaling: float = 1.0
    
    # Modifiers
    critical_multiplier: float = 2.0
    armor_reduction: float = 0.1  # How much armor reduces damage
    resistance_reduction: float = 0.05  # How much resistance reduces damage
    
    damage_type: DamageType = DamageType.PHYSICAL

    def calculate_damage(
        self,
        attacker_level: int,
        attacker_stat: float,
        weapon_damage: float,
        target_armor: float,
        target_resistance: float,
        is_critical: bool = False
    ) -> float:
        """Calculate final damage value."""
        # Base calculation
        damage = self.base_damage
        damage += attacker_stat * self.stat_multiplier
        damage += weapon_damage * self.weapon_scaling
        damage *= (1.0 + (attacker_level * self.level_scaling / 100.0))
        
        # Apply variance
        variance = random.uniform(-self.random_variance, self.random_variance)
        damage *= (1.0 + variance)
        
        # Apply critical
        if is_critical:
            damage *= self.critical_multiplier
        
        # Apply defenses
        armor_reduction = target_armor * self.armor_reduction
        resistance_reduction = target_resistance * self.resistance_reduction
        final_reduction = 1.0 - ((armor_reduction + resistance_reduction) / 100.0)
        final_reduction = max(0.1, final_reduction)  # Minimum 10% damage goes through
        
        damage *= final_reduction
        
        return max(1.0, damage)

    def to_dict(self) -> Dict:
        return {
            "id": self.formula_id,
            "name": self.name,
            "description": self.description,
            "base_damage": self.base_damage,
            "stat_multiplier": self.stat_multiplier,
            "damage_type": self.damage_type.value
        }


@dataclass
class StatusEffect:
    """Status effect definition."""
    effect_id: str
    name: str
    description: str
    effect_type: StatusEffectType
    
    duration: int = 5  # seconds
    stacks: int = 1    # Can stack multiple times
    max_stacks: int = 5
    
    # Effect values
    damage_per_tick: float = 0.0  # For damage-over-time
    stat_modification: Dict[str, float] = field(default_factory=dict)
    speed_multiplier: float = 1.0
    
    # Immunities and interactions
    can_stack: bool = True
    removes_on_damage: bool = False
    removes_on_action: bool = False
    
    color_hex: str = "#FF0000"  # For UI
    icon_path: str = ""

    def apply_effect(self, target: CombatEntity) -> bool:
        """Apply effect to target."""
        # Check immunity
        if self.effect_type.value in target.status_immunities:
            return False
        
        # Check if already has this effect
        existing = None
        for effect in target.active_effects:
            if effect.effect_id == self.effect_id:
                existing = effect
                break
        
        if existing:
            if self.can_stack and existing.stacks < self.max_stacks:
                existing.stacks += 1
                existing.duration = self.duration
                return True
            return False
        
        # Apply new effect
        target.active_effects.append(self)
        return True

    def to_dict(self) -> Dict:
        return {
            "id": self.effect_id,
            "name": self.name,
            "description": self.description,
            "type": self.effect_type.value,
            "duration": self.duration,
            "stacks": self.stacks
        }


@dataclass
class ComboMove:
    """Single move in a combo."""
    move_id: str
    name: str
    description: str
    
    damage_formula_id: str
    damage_multiplier: float = 1.0
    
    # Animation/timing
    animation_name: str = ""
    duration: float = 0.5  # seconds
    startup_frames: int = 5  # Frames before hit registers
    recovery_frames: int = 10  # Frames of recovery after
    
    # Hit detection
    hit_range: float = 2.0  # meters
    hit_radius: float = 1.0  # meters
    
    # Combo properties
    knockback: float = 0.5  # meters
    can_cancel_into: List[str] = field(default_factory=list)
    applies_effects: List[str] = field(default_factory=list)
    
    # Resource cost
    resource_cost: int = 0  # Mana, stamina, etc.
    cooldown: float = 1.0  # seconds

    def to_dict(self) -> Dict:
        return {
            "id": self.move_id,
            "name": self.name,
            "description": self.description,
            "damage_multiplier": self.damage_multiplier,
            "duration": self.duration,
            "cooldown": self.cooldown
        }


@dataclass
class ComboChain:
    """Sequence of moves forming a combo."""
    chain_id: str
    name: str
    description: str
    
    chain_type: ComboChainType = ComboChainType.LINEAR
    moves: List[str] = field(default_factory=list)  # Move IDs in sequence
    
    # Timing requirements
    max_time_between_moves: float = 1.5  # seconds
    
    # Combo rewards
    damage_bonus: float = 0.0  # Additional damage multiplier
    resource_gain: int = 0  # Resource gained on completion
    status_effects_applied: List[str] = field(default_factory=list)
    
    # Requirements
    level_required: int = 1
    skill_required: int = 0
    
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict:
        return {
            "id": self.chain_id,
            "name": self.name,
            "description": self.description,
            "type": self.chain_type.value,
            "moves": self.moves,
            "damage_bonus": self.damage_bonus
        }


@dataclass
class HitDetectionResult:
    """Result of hit detection."""
    hit_type: HitType
    hit_chance: float  # 0-100
    did_hit: bool
    damage: float = 0.0
    critical: bool = False
    dodge_distance: float = 0.0  # How far defender dodged

    def to_dict(self) -> Dict:
        return {
            "hit_type": self.hit_type.value,
            "hit_chance": self.hit_chance,
            "did_hit": self.did_hit,
            "damage": self.damage,
            "critical": self.critical
        }


@dataclass
class CriticalCalculation:
    """Critical hit calculation."""
    crit_chance: float = 5.0  # Base 5%
    crit_damage_multiplier: float = 2.0
    
    # Scaling
    attacker_dexterity_scaling: float = 0.1  # +0.1% per dex
    weapon_crit_rating: float = 0.0
    
    # Target defense
    target_armor_reduction: float = 0.1  # Armor reduces crit by 0.1% per point
    target_evasion_reduction: float = 0.2  # Evasion reduces crit by 0.2% per point
    
    level_scaling: float = 0.05  # +0.05% per level difference

    def calculate_crit_chance(
        self,
        attacker_level: int,
        attacker_dexterity: float,
        weapon_crit: float,
        target_level: int,
        target_armor: float,
        target_evasion: float
    ) -> float:
        """Calculate final critical chance."""
        chance = self.crit_chance
        
        # Attacker modifiers
        chance += attacker_dexterity * self.attacker_dexterity_scaling
        chance += weapon_crit
        chance += (attacker_level - target_level) * self.level_scaling
        
        # Target defense
        chance -= target_armor * self.target_armor_reduction
        chance -= target_evasion * self.target_evasion_reduction
        
        # Clamp between 1% and 95%
        chance = max(1.0, min(95.0, chance))
        
        return chance

    def is_critical(
        self,
        attacker_level: int,
        attacker_dexterity: float,
        weapon_crit: float,
        target_level: int,
        target_armor: float,
        target_evasion: float
    ) -> bool:
        """Determine if attack is critical."""
        crit_chance = self.calculate_crit_chance(
            attacker_level, attacker_dexterity, weapon_crit,
            target_level, target_armor, target_evasion
        )
        return random.random() * 100 < crit_chance

    def to_dict(self) -> Dict:
        return {
            "base_crit_chance": self.crit_chance,
            "crit_damage_multiplier": self.crit_damage_multiplier,
            "attacker_dex_scaling": self.attacker_dexterity_scaling
        }


@dataclass
class AbilityCooldown:
    """Tracks ability cooldown."""
    ability_id: str
    max_cooldown: float  # seconds
    current_cooldown: float = 0.0
    cooldown_type: CooldownType = CooldownType.PER_ABILITY
    shared_group: str = ""  # For shared cooldowns

    @property
    def is_ready(self) -> bool:
        return self.current_cooldown <= 0.0

    @property
    def cooldown_remaining(self) -> float:
        return max(0.0, self.current_cooldown)

    @property
    def cooldown_pct(self) -> float:
        if self.max_cooldown == 0:
            return 0.0
        return (self.current_cooldown / self.max_cooldown) * 100

    def tick(self, delta_time: float):
        """Reduce cooldown by delta time."""
        self.current_cooldown = max(0.0, self.current_cooldown - delta_time)

    def reset(self):
        """Reset to full cooldown."""
        self.current_cooldown = self.max_cooldown

    def to_dict(self) -> Dict:
        return {
            "ability_id": self.ability_id,
            "max_cooldown": self.max_cooldown,
            "current_cooldown": self.current_cooldown,
            "is_ready": self.is_ready,
            "cooldown_pct": self.cooldown_pct
        }


@dataclass
class SkillTreeNode:
    """Node in a skill tree."""
    node_id: str
    name: str
    description: str
    node_type: SkillTreeNodeType
    
    # Position in tree
    x: int = 0
    y: int = 0
    
    # Requirements
    level_required: int = 1
    points_required: int = 1
    parent_nodes: List[str] = field(default_factory=list)
    
    # Effects
    stat_bonuses: Dict[str, float] = field(default_factory=dict)
    ability_unlock: Optional[str] = None
    passive_effect: Optional[str] = None
    
    # Cost
    skill_point_cost: int = 1
    
    # Metadata
    icon_path: str = ""
    color_hex: str = "#00FF00"

    def to_dict(self) -> Dict:
        return {
            "id": self.node_id,
            "name": self.name,
            "description": self.description,
            "type": self.node_type.value,
            "x": self.x,
            "y": self.y,
            "level_required": self.level_required,
            "cost": self.skill_point_cost
        }


@dataclass
class SkillTree:
    """Complete skill tree."""
    tree_id: str
    name: str
    description: str
    
    nodes: Dict[str, SkillTreeNode] = field(default_factory=dict)
    unlocked_nodes: Set[str] = field(default_factory=set)
    
    available_skill_points: int = 0
    total_skill_points_spent: int = 0

    def unlock_node(self, node_id: str, character) -> bool:
        """Unlock a node in the skill tree."""
        if node_id not in self.nodes:
            return False
        
        node = self.nodes[node_id]
        
        # Check requirements
        if character.level < node.level_required:
            return False
        
        if self.available_skill_points < node.skill_point_cost:
            return False
        
        # Check parent requirements
        for parent_id in node.parent_nodes:
            if parent_id not in self.unlocked_nodes:
                return False
        
        # Unlock node
        self.unlocked_nodes.add(node_id)
        self.available_skill_points -= node.skill_point_cost
        self.total_skill_points_spent += node.skill_point_cost
        
        # Apply effects
        if node.ability_unlock:
            character.unlock_ability(node.ability_unlock)
        
        if node.stat_bonuses:
            for stat, bonus in node.stat_bonuses.items():
                character.stats[stat] = character.stats.get(stat, 0) + bonus
        
        return True

    def to_dict(self) -> Dict:
        return {
            "id": self.tree_id,
            "name": self.name,
            "description": self.description,
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "unlocked_nodes": list(self.unlocked_nodes),
            "available_skill_points": self.available_skill_points,
            "total_spent": self.total_skill_points_spent
        }


@dataclass
class CombatEntity:
    """Entity that can participate in combat."""
    entity_id: str
    name: str
    
    level: int = 1
    health: float = 100.0
    max_health: float = 100.0
    resource: float = 100.0  # Mana, stamina, etc.
    max_resource: float = 100.0
    
    # Stats
    stats: Dict[str, float] = field(default_factory=dict)
    
    # Combat properties
    armor: float = 0.0
    resistances: Dict[DamageType, float] = field(default_factory=dict)
    evasion: float = 0.0
    
    # Active combat state
    active_effects: List[StatusEffect] = field(default_factory=list)
    status_immunities: Set[str] = field(default_factory=set)
    cooldowns: Dict[str, AbilityCooldown] = field(default_factory=dict)
    
    # Combo tracking
    combo_counter: int = 0
    last_hit_time: float = 0.0
    in_combat: bool = False
    
    # Position (for hit detection)
    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0

    @property
    def is_alive(self) -> bool:
        return self.health > 0

    @property
    def health_pct(self) -> float:
        if self.max_health == 0:
            return 0.0
        return (self.health / self.max_health) * 100

    @property
    def resource_pct(self) -> float:
        if self.max_resource == 0:
            return 0.0
        return (self.resource / self.max_resource) * 100

    def take_damage(self, damage: float, damage_type: DamageType = DamageType.PHYSICAL):
        """Take damage."""
        # Apply resistances
        resistance = self.resistances.get(damage_type, 0.0)
        damage *= (1.0 - (resistance / 100.0))
        
        # Apply armor (reduces all damage)
        damage *= (1.0 - (self.armor / 100.0))
        
        # Apply to health
        self.health = max(0, self.health - damage)
        
        # Remove effects that trigger on damage
        self.active_effects = [
            e for e in self.active_effects
            if not e.removes_on_damage
        ]
        
        return damage

    def heal(self, amount: float):
        """Heal entity."""
        self.health = min(self.max_health, self.health + amount)

    def add_effect(self, effect: StatusEffect) -> bool:
        """Add status effect."""
        return effect.apply_effect(self)

    def update_effects(self, delta_time: float):
        """Update active effects (tick down duration, apply damage, etc.)"""
        to_remove = []
        for effect in self.active_effects:
            # Apply damage-over-time
            if effect.damage_per_tick > 0:
                self.take_damage(effect.damage_per_tick * delta_time, DamageType.POISON)
            
            # Reduce duration
            effect.duration -= delta_time
            if effect.duration <= 0:
                to_remove.append(effect)
        
        # Remove expired effects
        for effect in to_remove:
            self.active_effects.remove(effect)

    def to_dict(self) -> Dict:
        return {
            "id": self.entity_id,
            "name": self.name,
            "level": self.level,
            "health": self.health,
            "max_health": self.max_health,
            "health_pct": self.health_pct,
            "resource": self.resource,
            "max_resource": self.max_resource,
            "is_alive": self.is_alive,
            "active_effects": [e.to_dict() for e in self.active_effects],
            "combo_counter": self.combo_counter
        }


# ═══════════════════════════ COMBAT SYSTEM ═════════════════════════════════

class CombatSystem:
    """Main combat system orchestrator."""

    def __init__(self):
        self.damage_formulas: Dict[str, DamageFormula] = {}
        self.status_effects: Dict[str, StatusEffect] = {}
        self.combo_moves: Dict[str, ComboMove] = {}
        self.combo_chains: Dict[str, ComboChain] = {}
        self.crit_calculator = CriticalCalculation()
        self.skill_trees: Dict[str, SkillTree] = {}
        self.active_combats: Dict[str, CombatSession] = {}

    # ═══════════════════════════ DAMAGE FORMULAS ══════════════════════════

    def create_damage_formula(
        self,
        name: str,
        description: str,
        base_damage: float = 10.0,
        damage_type: DamageType = DamageType.PHYSICAL
    ) -> DamageFormula:
        """Create damage formula."""
        formula = DamageFormula(
            formula_id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            base_damage=base_damage,
            damage_type=damage_type
        )
        self.damage_formulas[formula.formula_id] = formula
        return formula

    def calculate_damage(
        self,
        formula_id: str,
        attacker: CombatEntity,
        target: CombatEntity,
        weapon_damage: float = 0.0
    ) -> HitDetectionResult:
        """Calculate damage for an attack."""
        if formula_id not in self.damage_formulas:
            return HitDetectionResult(HitType.MISS, 0, False)
        
        formula = self.damage_formulas[formula_id]
        
        # Get attacker stat (attack power by default)
        attacker_stat = attacker.stats.get("attack_power", 10.0)
        
        # Determine hit
        hit_result = self._determine_hit(attacker, target)
        
        if not hit_result.did_hit:
            return hit_result
        
        # Calculate critical
        is_critical = self.crit_calculator.is_critical(
            attacker.level,
            attacker.stats.get("dexterity", 5.0),
            weapon_damage * 0.1,
            target.level,
            target.armor,
            target.evasion
        )
        
        # Calculate damage
        damage = formula.calculate_damage(
            attacker.level,
            attacker_stat,
            weapon_damage,
            target.armor,
            target.resistances.get(formula.damage_type, 0.0),
            is_critical
        )
        
        hit_result.damage = damage
        hit_result.critical = is_critical
        if is_critical:
            hit_result.hit_type = HitType.CRITICAL
        
        return hit_result

    def _determine_hit(self, attacker: CombatEntity, target: CombatEntity) -> HitDetectionResult:
        """Determine if attack hits."""
        # Base hit chance
        attacker_accuracy = attacker.stats.get("accuracy", 80.0)
        target_evasion = target.evasion
        
        hit_chance = attacker_accuracy - (target_evasion * 0.5)
        hit_chance = max(1.0, min(99.0, hit_chance))
        
        # Roll for hit
        roll = random.random() * 100
        
        if roll > hit_chance:
            # Determine type of miss
            dodge_chance = target_evasion * 0.3
            if random.random() * 100 < dodge_chance:
                return HitDetectionResult(HitType.DODGE, hit_chance, False)
            else:
                return HitDetectionResult(HitType.MISS, hit_chance, False)
        
        return HitDetectionResult(HitType.HIT, hit_chance, True)

    # ═══════════════════════════ STATUS EFFECTS ═══════════════════════════

    def create_status_effect(
        self,
        name: str,
        description: str,
        effect_type: StatusEffectType,
        duration: int = 5
    ) -> StatusEffect:
        """Create status effect."""
        effect = StatusEffect(
            effect_id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            effect_type=effect_type,
            duration=duration
        )
        self.status_effects[effect.effect_id] = effect
        return effect

    # ═══════════════════════════ COMBO SYSTEM ════════════════════════════

    def create_combo_move(
        self,
        name: str,
        description: str,
        formula_id: str,
        damage_multiplier: float = 1.0
    ) -> ComboMove:
        """Create combo move."""
        move = ComboMove(
            move_id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            damage_formula_id=formula_id,
            damage_multiplier=damage_multiplier
        )
        self.combo_moves[move.move_id] = move
        return move

    def create_combo_chain(
        self,
        name: str,
        description: str,
        moves: List[str],
        chain_type: ComboChainType = ComboChainType.LINEAR
    ) -> ComboChain:
        """Create combo chain."""
        chain = ComboChain(
            chain_id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            moves=moves,
            chain_type=chain_type
        )
        self.combo_chains[chain.chain_id] = chain
        return chain

    def validate_combo_sequence(
        self,
        chain_id: str,
        executed_moves: List[str],
        time_between_moves: List[float]
    ) -> Tuple[bool, float]:
        """Validate if executed moves match a combo chain."""
        if chain_id not in self.combo_chains:
            return False, 0.0
        
        chain = self.combo_chains[chain_id]
        
        # Check move sequence matches
        if len(executed_moves) != len(chain.moves):
            return False, 0.0
        
        for i, move_id in enumerate(executed_moves):
            if i >= len(chain.moves):
                return False, 0.0
            if move_id != chain.moves[i]:
                return False, 0.0
            
            # Check timing (if not first move)
            if i > 0 and time_between_moves[i] > chain.max_time_between_moves:
                return False, 0.0
        
        # Combo is valid, return bonus multiplier
        bonus_multiplier = 1.0 + chain.damage_bonus
        return True, bonus_multiplier

    # ═══════════════════════════ HIT DETECTION ═══════════════════════════

    def check_hit_detection(
        self,
        attacker: CombatEntity,
        target: CombatEntity,
        hit_range: float,
        hit_radius: float
    ) -> bool:
        """Check if target is within hit detection range."""
        dx = target.position_x - attacker.position_x
        dy = target.position_y - attacker.position_y
        dz = target.position_z - attacker.position_z
        
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        return distance <= (hit_range + hit_radius)

    # ═══════════════════════════ COOLDOWN SYSTEM ═══════════════════════════

    def add_cooldown(
        self,
        entity_id: str,
        ability_id: str,
        max_cooldown: float,
        cooldown_type: CooldownType = CooldownType.PER_ABILITY
    ):
        """Add ability cooldown."""
        cooldown = AbilityCooldown(
            ability_id=ability_id,
            max_cooldown=max_cooldown,
            current_cooldown=max_cooldown,
            cooldown_type=cooldown_type
        )
        # Would need to store by entity - simplified here
        return cooldown

    def can_use_ability(self, entity: CombatEntity, ability_id: str) -> bool:
        """Check if ability is off cooldown."""
        if ability_id in entity.cooldowns:
            return entity.cooldowns[ability_id].is_ready
        return True

    def trigger_cooldown(self, entity: CombatEntity, ability_id: str):
        """Trigger cooldown for ability."""
        if ability_id in entity.cooldowns:
            entity.cooldowns[ability_id].reset()

    # ═══════════════════════════ SKILL TREES ═════════════════════════════

    def create_skill_tree(
        self,
        name: str,
        description: str
    ) -> SkillTree:
        """Create skill tree."""
        tree = SkillTree(
            tree_id=str(uuid.uuid4())[:6],
            name=name,
            description=description
        )
        self.skill_trees[tree.tree_id] = tree
        return tree

    def add_skill_node(
        self,
        tree_id: str,
        name: str,
        description: str,
        node_type: SkillTreeNodeType,
        x: int = 0,
        y: int = 0
    ) -> SkillTreeNode:
        """Add node to skill tree."""
        if tree_id not in self.skill_trees:
            return None
        
        node = SkillTreeNode(
            node_id=str(uuid.uuid4())[:6],
            name=name,
            description=description,
            node_type=node_type,
            x=x,
            y=y
        )
        
        tree = self.skill_trees[tree_id]
        tree.nodes[node.node_id] = node
        
        return node

    # ═══════════════════════════ COMBAT SESSIONS ═══════════════════════════

    def start_combat_session(
        self,
        attacker: CombatEntity,
        defender: CombatEntity
    ) -> CombatSession:
        """Start a combat session."""
        session = CombatSession(
            session_id=str(uuid.uuid4())[:8],
            attacker=attacker,
            defender=defender
        )
        self.active_combats[session.session_id] = session
        return session

    def to_dict(self) -> Dict:
        return {
            "damage_formulas": len(self.damage_formulas),
            "status_effects": len(self.status_effects),
            "combo_moves": len(self.combo_moves),
            "combo_chains": len(self.combo_chains),
            "skill_trees": len(self.skill_trees),
            "active_combats": len(self.active_combats)
        }


@dataclass
class CombatSession:
    """Active combat between two entities."""
    session_id: str
    attacker: CombatEntity
    defender: CombatEntity
    
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    is_active: bool = True
    
    combat_log: List[Dict] = field(default_factory=list)
    rounds_elapsed: int = 0
    total_damage_dealt: float = 0.0
    total_damage_taken: float = 0.0

    def add_log_entry(self, action: str, details: Dict):
        """Add entry to combat log."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details
        }
        self.combat_log.append(entry)

    def end_combat(self):
        """End combat session."""
        self.is_active = False

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "attacker": self.attacker.name,
            "defender": self.defender.name,
            "is_active": self.is_active,
            "rounds": self.rounds_elapsed,
            "total_damage_dealt": self.total_damage_dealt,
            "total_damage_taken": self.total_damage_taken,
            "log_entries": len(self.combat_log)
        }


def demo_combat_system():
    """Demonstrate combat system."""
    system = CombatSystem()
    
    # Create damage formula
    slash_formula = system.create_damage_formula(
        "Slash",
        "Basic slash attack",
        base_damage=15.0,
        damage_type=DamageType.PHYSICAL
    )
    
    # Create status effect
    burn = system.create_status_effect(
        "Burn",
        "Take damage over time",
        StatusEffectType.BURN,
        duration=5
    )
    burn.damage_per_tick = 2.0
    
    # Create entities
    player = CombatEntity(
        entity_id="player_1",
        name="Player",
        level=5,
        health=100,
        max_health=100,
        stats={"attack_power": 15, "dexterity": 10, "accuracy": 85}
    )
    
    enemy = CombatEntity(
        entity_id="enemy_1",
        name="Enemy",
        level=5,
        health=80,
        max_health=80,
        stats={"attack_power": 12, "dexterity": 8},
        evasion=10,
        armor=5
    )
    
    # Perform attack
    result = system.calculate_damage(slash_formula.formula_id, player, enemy)
    
    print("Combat System Demo:")
    print(f"Hit Result: {result.hit_type.value}")
    print(f"Damage: {result.damage:.1f}")
    print(f"Critical: {result.critical}")
    print(f"System Stats: {system.to_dict()}")


if __name__ == "__main__":
    demo_combat_system()
