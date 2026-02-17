╔════════════════════════════════════════════════════════════════════════════╗
║                    COMBAT SYSTEM COMPLETE GUIDE                             ║
║    Architecture · Features · API Reference · Implementation Guide           ║
╚════════════════════════════════════════════════════════════════════════════╝

## TABLE OF CONTENTS
1. System Overview
2. Architecture
3. Core Features
4. API Reference (20+ endpoints)
5. Combat Mechanics Guide
6. Balancing & Tuning
7. Integration Examples
8. Advanced Topics


═══════════════════════════════════════════════════════════════════════════════
1. SYSTEM OVERVIEW
═══════════════════════════════════════════════════════════════════════════════

The Combat System is a complete, production-ready framework providing:
- Advanced damage formula engine with scaling
- Status effect system with stacking mechanics
- Combo builder with timing validation
- Hit detection (3D range-based)
- Critical hit calculations (1-95% range)
- Skill tree progression system
- Ability cooldown management
- Real-time WebSocket updates
- Unreal Engine integration


═══════════════════════════════════════════════════════════════════════════════
2. ARCHITECTURE
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                           COMBAT SYSTEM LAYERS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Layer 1: Core Combat (combat_system.py)                                    │
│  ├─ DamageFormula: Damage calculation with scaling                         │
│  ├─ StatusEffect: Effect management & stacking                            │
│  ├─ ComboMove: Individual combat moves                                      │
│  ├─ ComboChain: Multi-move sequences                                       │
│  ├─ CriticalCalculation: Crit chance & multiplier                         │
│  ├─ AbilityCooldown: Cooldown tracking                                    │
│  ├─ SkillTree: Progression system                                          │
│  ├─ CombatEntity: Entity with full state                                  │
│  └─ CombatSystem: Main orchestrator (15+ methods)                         │
│                                                                              │
│  Layer 2: Web Interface (combat_system_web.py)                              │
│  ├─ FastAPI Server: 20+ REST endpoints                                    │
│  ├─ Pydantic Models: Type validation & docs                               │
│  ├─ WebSocket Handler: Real-time updates                                  │
│  └─ HTML5 Dashboard: Interactive UI (6 tabs)                              │
│                                                                              │
│  Layer 3: Unreal Integration (combat_unreal_integration.py)                 │
│  ├─ UnrealCombatBridge: Bidirectional sync                                │
│  ├─ Event Broadcasting: 8+ combat events                                  │
│  ├─ WebSocket Server: Player connections                                  │
│  └─ C++ Header Generation: Unreal bindings                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
3. CORE FEATURES
═══════════════════════════════════════════════════════════════════════════════

┌─ DAMAGE FORMULAS ───────────────────────────────────────────────────────────┐
│                                                                              │
│  8 Damage Types:                                                            │
│  • Physical: Affected by armor                                             │
│  • Fire: Residual burn damage                                              │
│  • Ice: Freeze chance & movement slow                                      │
│  • Lightning: Stun chance & AOE                                            │
│  • Poison: Damage over time                                                │
│  • Holy: Bonus vs undead                                                   │
│  • Dark: Bonus vs holy enemies                                             │
│  • Magic: Affected by magic resistance                                     │
│                                                                              │
│  Damage Formula Components:                                                 │
│  • BaseDamage: Starting damage value (10-100)                             │
│  • StatMultipliers: Scale with attacker stats (0.0-2.0)                  │
│  • LevelScaling: Bonus per level (0.01-0.1 per level)                    │
│  • WeaponScaling: Weapon damage contribution (0.0-1.0)                    │
│  • CriticalMultiplier: Damage on crit (1.5-3.0x)                         │
│  • ArmorReduction: Target armor mitigation (10-90%)                       │
│                                                                              │
│  Damage Variance: ±10% random variance per hit                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ STATUS EFFECTS ───────────────────────────────────────────────────────────┐
│                                                                              │
│  12 Status Effect Types:                                                    │
│  • Stun: Disable actions (0.5-3.0s)                                       │
│  • Slow: Reduce movement speed (50-90% reduction, 3-10s)                  │
│  • Burn: Deal damage over time (5-20 DMG/sec, 3-15s)                     │
│  • Freeze: Immobilize target (1.0-5.0s)                                   │
│  • Poison: Tick damage (5-10 DMG/sec, 5-20s)                             │
│  • Bleed: Physical damage over time (3-5 DMG/sec, 10-30s)                │
│  • Weakness: Reduce attack power (30-50% reduction)                       │
│  • Strength: Increase attack power (20-50% bonus)                         │
│  • Shield: Absorb damage (50-200 DMG)                                     │
│  • Regen: Heal over time (10-20 HP/sec)                                   │
│  • Confusion: Random action selection                                      │
│  • Sleep: Immobilize & reset on damage                                    │
│                                                                              │
│  Stacking Mechanics:                                                        │
│  • Stackable effects: Multiple instances (default 5 max)                  │
│  • Non-stackable: Refreshed by new application                            │
│  • Immunities: Prevent application of specific effects                    │
│  • Duration: Counts down per tick (default 100 ticks/sec)                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ COMBO BUILDER ────────────────────────────────────────────────────────────┐
│                                                                              │
│  4 Combo Chain Types:                                                       │
│  • Linear: Execute moves in sequence (A→B→C)                              │
│  • Branch: Multiple paths available (A→[B|C]→D)                           │
│  • Loop: Repeat sequence (A→B→A→B)                                        │
│  • Conditional: Execute based on conditions                               │
│                                                                              │
│  Combo Components:                                                          │
│  • Move ID: Unique move identifier                                        │
│  • DamageMultiplier: Bonus damage (1.0-3.0x)                             │
│  • AnimationTime: Animation duration                                       │
│  • HitDetectionRange: Detection radius (0.0-500.0)                        │
│  • Knockback: Push distance (0.0-200.0)                                   │
│  • ResourceCost: Mana/energy cost (0-500)                                 │
│  • Cooldown: Between-move cooldown (0.0-5.0s)                            │
│                                                                              │
│  Timing Requirements:                                                       │
│  • Default window: 1.5 seconds between moves                              │
│  • Early bonus: 50% damage boost if at <0.5s window                       │
│  • Late penalty: 25% damage reduction if at >1.0s window                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ HIT DETECTION ────────────────────────────────────────────────────────────┐
│                                                                              │
│  6 Hit Types:                                                               │
│  • Miss: Attack fails (reduced hit chance)                                │
│  • Hit: Normal damage (full damage)                                        │
│  • Critical: Increased damage (1.5-3.0x multiplier)                       │
│  • Dodge: Completely avoided (0 damage)                                    │
│  • Parry: Attacker blocked (50% damage)                                    │
│  • Counter: Defender attacks back (50-100% damage)                        │
│                                                                              │
│  3D Range-Based Detection:                                                  │
│  • Distance check: 3D Euclidean distance                                   │
│  • Radius check: Attacker range vs distance                               │
│  • LOS check: Optional line-of-sight validation                           │
│  • Hitbox: Spherical collision at hit point                               │
│                                                                              │
│  Hit Chance Modifiers:                                                      │
│  • Base hit: 85%                                                            │
│  • Attacker accuracy: +/-5% per point                                     │
│  • Target evasion: -1% per point                                          │
│  • Distance penalty: -5% per 50 units beyond optimal range               │
│  • Elevation bonus: +10% if above target                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ CRITICAL CALCULATIONS ────────────────────────────────────────────────────┐
│                                                                              │
│  Critical Range: 1% - 95%                                                   │
│                                                                              │
│  Crit Chance Factors (cumulative):                                          │
│  • Base chance: 5%                                                          │
│  • Attacker dexterity: +0.5% per point (0-50pts = 0-25%)                 │
│  • Weapon rating: +0.1% per point (0-100pts = 0-10%)                     │
│  • Target armor: -0.1% per point (0-200pts = 0-20%)                      │
│  • Target evasion: -0.5% per point (0-50pts = 0-25%)                     │
│  • Level differential: +1% per 5 levels advantage                         │
│  • Combo multiplier: +1% per active combo counter                         │
│                                                                              │
│  Crit Multiplier Calculation:                                               │
│  • Base: 1.5x                                                               │
│  • Per 10 dex: +0.1x (1.5-2.0x range typical)                            │
│  • Weapon bonus: +0.05x-0.5x based on rarity                             │
│  • Trait bonus: +0.0-0.5x from skill tree                                 │
│  • Status bonus: +0.1-0.3x from buffs                                     │
│  • Maximum: 3.0x                                                            │
│                                                                              │
│  Example Calculation:                                                       │
│  Attacker: 30 dex, weapon +10%, level 10                                   │
│  Target: 20 armor, 10 evasion, level 8                                     │
│                                                                              │
│  Crit Chance = 5 + 15 + 3 - 2 - 5 + 2 + 0 = 18%                          │
│  Crit Mult = 1.5 + 0.3 + 0.1 = 1.9x                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ SKILL TREES ──────────────────────────────────────────────────────────────┐
│                                                                              │
│  6 Skill Node Types:                                                        │
│  • StatBoost: Increase core stat (+1 to +10)                             │
│  • AbilityUnlock: Unlock new ability/move                                 │
│  • PassiveEffect: Permanent stat bonus                                    │
│  • DamageModifier: Modify ability damage                                  │
│  • CostReduction: Reduce resource costs                                   │
│  • Utility: Other effects (movement, regen, etc.)                         │
│                                                                              │
│  Node Requirements:                                                         │
│  • Skill point cost: 1-5 points per node                                  │
│  • Level requirement: 1-50                                                │
│  • Parent nodes: Prerequisites (0-3 per node)                             │
│  • Mutually exclusive: Cannot pick both branches                          │
│                                                                              │
│  Progression Rules:                                                         │
│  • Skill points: +1 per level gained                                      │
│  • Max respec: Once per session (configurable)                            │
│  • Passive stacking: Most stack (+10% movement = 2 nodes × 5%)            │
│  • Active abilities: Single unlock, unlimited use                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ ABILITY COOLDOWNS ────────────────────────────────────────────────────────┐
│                                                                              │
│  3 Cooldown Sharing Types:                                                  │
│  • Global: Shared across all abilities (e.g., GCD)                        │
│  • PerAbility: Separate cooldown per ability                              │
│  • Shared: Groups of abilities share single cooldown                      │
│                                                                              │
│  Cooldown Properties:                                                       │
│  • Ability ID: Unique identifier                                          │
│  • Duration: Cooldown time in seconds (0.1-60.0s)                        │
│  • RemainingTime: Time until ability ready                                │
│  • ReadyAt: Timestamp when ready again                                    │
│                                                                              │
│  Cooldown Reduction:                                                        │
│  • Base reduction: 0%                                                       │
│  • Skill tree: Up to 50% reduction from nodes                             │
│  • Buffs: Up to 30% from status effects                                    │
│  • Haste: Additional % reduction per point                                │
│  • Maximum reduction: 90% (minimum 10% of base)                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
4. API REFERENCE (20+ ENDPOINTS)
═══════════════════════════════════════════════════════════════════════════════

BASE URL: http://localhost:8000/api

┌─ DAMAGE FORMULAS ─────────────────────────────────────────────────────────┐

POST /formulas/create
  Create damage formula
  Request:
    {
      "name": "fireball",
      "damage_type": "fire",
      "base_damage": 50.0,
      "stat_multipliers": {"intelligence": 0.8},
      "level_scaling": 0.05,
      "weapon_scaling": 0.3,
      "critical_multiplier": 2.0,
      "armor_reduction": 0.2
    }
  Response: { "formula_id": "uuid", "status": "created" }

GET /formulas
  List all damage formulas
  Response: { "formulas": [{ ... }], "count": 42 }

GET /formulas/{formula_id}
  Get specific formula
  Response: { "formula": { ... } }

POST /formulas/{formula_id}/clone
  Clone existing formula
  Response: { "new_formula_id": "uuid" }

┌─ STATUS EFFECTS ──────────────────────────────────────────────────────────┐

POST /effects/create
  Create status effect
  Request:
    {
      "name": "burn",
      "effect_type": "burn",
      "duration": 5.0,
      "stackable": true,
      "max_stacks": 5,
      "damage_per_tick": 10.0,
      "tick_interval": 0.5
    }
  Response: { "effect_id": "uuid" }

GET /effects
  List all effects
  Response: { "effects": [...], "count": 12 }

POST /effects/{effect_id}/apply
  Apply effect (test)
  Request: { "entity_id": "uuid", "duration": 5.0 }
  Response: { "success": true, "active_duration": 5.0 }

┌─ COMBO MOVES ─────────────────────────────────────────────────────────────┐

POST /combos/moves/create
  Create combo move
  Request:
    {
      "move_id": "slash",
      "damage_multiplier": 1.2,
      "animation_time": 0.8,
      "hit_detection_range": 150.0,
      "knockback_distance": 50.0,
      "resource_cost": 20.0,
      "cooldown": 1.5
    }
  Response: { "move": { ... } }

GET /combos/moves
  List all combo moves
  Response: { "moves": [...], "count": 20 }

┌─ COMBO CHAINS ────────────────────────────────────────────────────────────┐

POST /combos/chains/create
  Create combo chain
  Request:
    {
      "chain_name": "triple_slash",
      "chain_type": "linear",
      "moves": ["slash", "slash", "power_slash"],
      "timing_requirement": 1.5,
      "damage_bonus": 0.25,
      "resource_reward": 50
    }
  Response: { "chain_id": "uuid" }

GET /combos/chains
  List all combo chains
  Response: { "chains": [...], "count": 8 }

POST /combos/validate
  Validate combo sequence
  Request:
    {
      "chain_id": "uuid",
      "executed_moves": ["slash", "slash", "power_slash"],
      "execution_times": [0.0, 0.8, 1.4]
    }
  Response: 
    {
      "valid": true,
      "damage_bonus": 0.25,
      "combo_count": 3
    }

┌─ COMBAT ENTITIES ────────────────────────────────────────────────────────┐

POST /entities/create
  Create combat entity
  Request:
    {
      "name": "player",
      "entity_type": "character",
      "health": 100.0,
      "max_health": 100.0,
      "stats": {
        "strength": 10,
        "dexterity": 10,
        "intelligence": 10,
        "armor": 0,
        "evasion": 0,
        "level": 1
      }
    }
  Response: { "entity_id": "uuid", "status": "created" }

GET /entities/{entity_id}
  Get entity details
  Response: { "entity": { ... } }

POST /entities/{entity_id}/damage
  Apply damage to entity
  Request:
    {
      "damage": 25.0,
      "damage_type": "physical",
      "source": "player"
    }
  Response: 
    {
      "damage_applied": 25.0,
      "health_remaining": 75.0,
      "is_alive": true
    }

POST /entities/{entity_id}/heal
  Heal entity
  Request: { "amount": 20.0 }
  Response: { "health": 95.0, "healed": 20.0 }

POST /entities/{entity_id}/add-effect
  Add status effect
  Request:
    {
      "effect_id": "uuid",
      "duration": 5.0,
      "intensity": 1.0
    }
  Response: { "success": true, "active_effects": [...] }

┌─ COMBAT SYSTEM ───────────────────────────────────────────────────────────┐

POST /combat/attack
  Execute attack
  Request:
    {
      "attacker_id": "uuid",
      "target_id": "uuid",
      "formula_id": "uuid",
      "attacker_position": [0, 0, 100],
      "target_position": [50, 0, 100]
    }
  Response:
    {
      "hit_type": "critical",
      "damage": 150.0,
      "critical": true,
      "target_health": 50.0
    }

POST /combat/session/start
  Start combat session
  Request:
    {
      "attacker_id": "uuid",
      "defender_id": "uuid"
    }
  Response: { "session_id": "uuid", "status": "active" }

GET /combat/critical-chance
  Calculate crit chance
  Request:
    {
      "attacker_id": "uuid",
      "target_id": "uuid"
    }
  Response: 
    {
      "crit_chance": 0.25,
      "crit_multiplier": 1.9
    }

┌─ SKILL TREES ─────────────────────────────────────────────────────────────┐

POST /skilltrees/create
  Create skill tree
  Request:
    {
      "tree_name": "warrior_tree",
      "description": "Warrior progression"
    }
  Response: { "tree_id": "uuid" }

GET /skilltrees/{tree_id}
  Get skill tree
  Response: { "tree": { "nodes": [...], "player_skills": [...] } }

POST /skilltrees/{tree_id}/nodes/add
  Add node to tree
  Request:
    {
      "node_type": "stat_boost",
      "stat": "strength",
      "bonus": 5,
      "position": [0, 0],
      "level_requirement": 1,
      "skill_point_cost": 1
    }
  Response: { "node_id": "uuid", "added": true }

POST /skilltrees/{tree_id}/allocate
  Allocate skill points
  Request:
    {
      "player_id": "uuid",
      "node_ids": ["uuid1", "uuid2"]
    }
  Response: 
    {
      "allocated": 2,
      "remaining_points": 3,
      "stat_bonuses": {"strength": 5, "dexterity": 5}
    }

┌─ SYSTEM ──────────────────────────────────────────────────────────────────┐

GET /system/stats
  Get system statistics
  Response:
    {
      "total_formulas": 42,
      "total_effects": 12,
      "total_entities": 156,
      "active_combats": 5,
      "active_sessions": 5
    }

POST /system/export
  Export system state
  Response: { "export_id": "uuid", "entities": [...], "formulas": [...] }

GET /system/export/{export_id}
  Get exported data
  Response: { "export": { ... } }

GET /health
  Health check
  Response: { "status": "healthy" }


═══════════════════════════════════════════════════════════════════════════════
5. COMBAT MECHANICS GUIDE
═══════════════════════════════════════════════════════════════════════════════

┌─ DAMAGE CALCULATION FLOW ──────────────────────────────────────────────────┐

Step 1: Determine Hit Type (Miss/Hit/Critical/Dodge/Parry/Counter)
  hit_chance = base_hit (85%) + attacker_accuracy - target_evasion

Step 2: Calculate Base Damage
  base = formula.base_damage + (attacker.stat × formula.stat_multiplier)

Step 3: Apply Level Scaling
  scaled = base × (1 + formula.level_scaling × (attacker.level - 1))

Step 4: Apply Weapon Scaling
  with_weapon = scaled + (attacker.weapon_damage × formula.weapon_scaling)

Step 5: Calculate Variance (±10%)
  variance_factor = random(0.9, 1.1)
  with_variance = with_weapon × variance_factor

Step 6: Apply Critical Modifier (if critical hit)
  if is_critical:
    with_variance = with_variance × crit_multiplier

Step 7: Apply Armor/Resistance
  armor_reduction = target.armor × formula.armor_reduction
  final_damage = max(with_variance - armor_reduction, 0)

Step 8: Apply Active Effects
  if target has weakness:
    final_damage = final_damage × 1.5
  if target has shield:
    shield.absorb(final_damage)

┌─ COMBO EXECUTION FLOW ────────────────────────────────────────────────────┐

1. Start Combo
   - Set combo_active = true
   - Start timer

2. First Move
   - Check resource cost
   - Deal damage (base multiplier)
   - Set combo_counter = 1
   - Start timing window (1.5s)

3. Second Move (within 1.5s)
   - Check timing window
   - Calculate bonus:
     * if < 0.5s: +50% damage
     * if 0.5-1.0s: +0% damage
     * if 1.0-1.5s: -25% damage
   - Deal (base × move_multiplier × (1 + bonus)) damage
   - Set combo_counter = 2
   - Reset timing window

4. Final Move (completes chain)
   - Check if matches chain definition
   - Apply chain damage bonus (+25% per the example)
   - Apply chain resource reward
   - Set combo_complete = true

┌─ SKILL POINT ALLOCATION ──────────────────────────────────────────────────┐

Earning Points:
- Start with 0 skill points
- +1 point per level gained
- Cannot exceed total available points

Allocating Points:
- Choose unallocated node
- Spend required skill points
- Gain stat bonuses immediately
- Unlock related nodes/abilities

Example Tree Path (Warrior):
Level 1→ Strength +1 (1pt)
Level 2→ Defense Stance (1pt)
Level 3→ Armor +5 (1pt)
Level 4→ Power Slash (1pt) ← requires Defense Stance
Level 5→ Strength +1 (1pt)
Total: 5pts spent, 5pts earned, 0 remaining


═══════════════════════════════════════════════════════════════════════════════
6. BALANCING & TUNING
═══════════════════════════════════════════════════════════════════════════════

┌─ RECOMMENDED STAT RANGES ──────────────────────────────────────────────────┐

For Level 1 Characters:
- Health: 50-100 HP
- Attack Power: 5-15 damage
- Armor: 0-5
- Evasion: 0-5%
- Core Stats (Str/Dex/Int): 1-15 points

For Level 50 Characters:
- Health: 500-1000 HP
- Attack Power: 50-150 damage
- Armor: 50-200
- Evasion: 20-40%
- Core Stats: 50-100 points

┌─ DAMAGE BALANCE MATRIX ────────────────────────────────────────────────────┐

Ability Type        Duration    Cooldown    Damage      Resource
Basic Attack        0.5s        0.0s        1.0x        0
Heavy Attack        1.0s        2.0s        1.5x        20
Special Move        1.2s        5.0s        2.0x        50
Ultimate Ability    2.0s        15.0s       3.0x        100

Mob Scaling:
- Boss: 3x health, 1.5x damage multiplier
- Elite: 2x health, 1.25x damage
- Regular: 1x health, 1.0x damage
- Weak: 0.5x health, 0.75x damage

┌─ TUNING PARAMETERS ───────────────────────────────────────────────────────┐

To adjust difficulty (modify in CombatSystem):

EASIER:
- Increase player health by 20%
- Reduce enemy damage by 20%
- Increase critical chance by 5%
- Decrease enemy armor by 10%

HARDER:
- Decrease player health by 20%
- Increase enemy damage by 20%
- Decrease critical chance by 5%
- Increase enemy armor by 10%

FASTER COMBAT:
- Reduce cooldowns by 25%
- Reduce status effect duration by 30%
- Increase combo damage bonus to 50%

LONGER COMBAT:
- Increase health values by 50%
- Reduce damage multipliers by 20%
- Add more armor values


═══════════════════════════════════════════════════════════════════════════════
7. INTEGRATION EXAMPLES
═══════════════════════════════════════════════════════════════════════════════

┌─ BASIC USAGE ──────────────────────────────────────────────────────────────┐

from combat_system import CombatSystem, CombatEntity

# Create system
system = CombatSystem()

# Create entities
player = CombatEntity(
    name="Hero",
    entity_type="character",
    health=100, max_health=100,
    stats={
        "strength": 15,
        "dexterity": 12,
        "intelligence": 10,
        "armor": 5,
        "evasion": 0,
        "level": 1
    }
)

enemy = CombatEntity(
    name="Goblin",
    entity_type="enemy",
    health=30, max_health=30,
    stats={
        "strength": 8,
        "dexterity": 10,
        "intelligence": 5,
        "armor": 0,
        "evasion": 0,
        "level": 1
    }
)

# Create damage formula
formula = system.create_damage_formula(
    name="sword_slash",
    damage_type="physical",
    base_damage=15.0,
    stat_multipliers={"strength": 0.5},
    critical_multiplier=2.0
)

# Execute attack
damage_result = system.calculate_damage(
    attacker=player,
    target=enemy,
    formula=formula
)

print(f"Hit Type: {damage_result.hit_type}")
print(f"Damage: {damage_result.damage}")
print(f"Critical: {damage_result.is_critical}")

┌─ COMBO CHAIN EXAMPLE ──────────────────────────────────────────────────────┐

# Create combo moves
move1 = system.create_combo_move("slash", damage_multiplier=1.0)
move2 = system.create_combo_move("slash", damage_multiplier=1.1)
move3 = system.create_combo_move("power_slash", damage_multiplier=1.5)

# Create chain
chain = system.create_combo_chain(
    chain_name="triple_slash",
    chain_type="linear",
    moves=[move1, move2, move3],
    timing_requirement=1.5,
    damage_bonus=0.25
)

# Execute combo
executed = ["slash", "slash", "power_slash"]
times = [0.0, 0.7, 1.3]

is_valid = system.validate_combo_sequence(chain, executed, times)
if is_valid:
    bonus_damage = chain.damage_bonus
    player.combo_counter = 3

┌─ STATUS EFFECT EXAMPLE ────────────────────────────────────────────────────┐

# Create effect
burn_effect = system.create_status_effect(
    effect_name="burn",
    effect_type="burn",
    duration=5.0,
    damage_per_tick=10.0
)

# Apply to target
system.apply_status_effect(enemy, burn_effect)

# Each tick, damage is applied
for i in range(10):  # Simulate 5 seconds @ 2 ticks/sec
    for effect in enemy.active_effects:
        if effect.effect_type == "burn":
            enemy.health -= effect.damage_per_tick

┌─ SKILL TREE EXAMPLE ──────────────────────────────────────────────────────┐

# Create skill tree
tree = system.create_skill_tree("warrior_tree")

# Add nodes
strength_node = system.add_skill_node(
    tree=tree,
    node_type="stat_boost",
    stat_name="strength",
    bonus=5,
    position=(0, 0)
)

power_slash_node = system.add_skill_node(
    tree=tree,
    node_type="ability_unlock",
    ability_name="power_slash",
    position=(1, 0),
    parent_nodes=[strength_node],
    level_requirement=2
)

# Allocate to player
player.skill_tree = tree
player.skill_points = 5
player.allocate_skill_points([strength_node.node_id])
player.stats["strength"] += 5


═══════════════════════════════════════════════════════════════════════════════
8. ADVANCED TOPICS
═══════════════════════════════════════════════════════════════════════════════

┌─ CUSTOM DAMAGE FORMULAS ───────────────────────────────────────────────────┐

Design formulas for specific abilities:

Scaling Damage Ability:
  base_damage: 20
  stat_multipliers: {"intelligence": 1.2}
  level_scaling: 0.1
  Result @ Level 10, INT 20: 20 + (20×1.2) + (20×0.1×9) = 56

Two-Handed Weapon:
  base_damage: 40
  stat_multipliers: {"strength": 0.8}
  weapon_scaling: 0.5
  Result with 50 STR, 50 DMG weapon: 40 + (50×0.8) + (50×0.5) = 90

Magic Attack:
  base_damage: 15
  stat_multipliers: {"intelligence": 1.5}
  critical_multiplier: 1.5 (low crit on magic)
  Result @ INT 25: 15 + (25×1.5) = 52.5

┌─ EFFECT INTERACTION CHAINS ────────────────────────────────────────────────┐

Chain reactions from status effects:

Burn + Cold = Explosion
  - 50% chance on each tick
  - Deals 2x burn damage + 2x cold damage
  - Removes both effects

Poison + Bleed = Hemorrhage
  - Stacks toxin counter
  - Every 3 tacks: damage spikes
  - 5s duration, 3 stacks maximum

Weakness + Strength Cancel
  - Cannot stack both
  - Latest application wins
  - 3s minimum duration between swaps

┌─ PERFORMANCE OPTIMIZATION ────────────────────────────────────────────────┐

For large battles (100+ entities):

1. Use object pooling for effects
2. Batch damage calculations
3. Cache formula calculations
4. Reduce tick rate for passive effects
5. Use lazy evaluation for non-visible entities

Cache Example:
  cache_key = f"{attacker.level}_{target.armor}"
  if cache_key in damage_cache:
    return damage_cache[cache_key]

Batch Processing:
  def process_entity_effects(entities):
    for entity in entities:
      if should_update(entity):
        update_effects(entity)

═══════════════════════════════════════════════════════════════════════════════
QUICK REFERENCE
═══════════════════════════════════════════════════════════════════════════════

Default Values:
- Base Hit Chance: 85%
- Crit Range: 1-95%
- Combo Window: 1.5s
- Effect Tick Rate: 100 ticks/sec
- Status Duration: 1-30 seconds
- Cooldown Range: 0.1-60 seconds

Damage Type Chart:
Physical    Fire        Ice         Lightning   Poison
└Armor      └Burn       └Freeze     └Stun       └DoT
  5-50%       3-20/s     Movement    0.5-3s      5-20/s
             3-15s       50-90%                  5-20s

Effect Immunities:
Stun immune vs: slowed, frozen
Poison immune: nature forms, constructs
Bleed immune: non-organic, flying

Port: 8000
API Docs: http://localhost:8000/docs
Dashboard: http://localhost:8000/
WebSocket: ws://localhost:8765

For complete API documentation, visit http://localhost:8000/docs
For interactive testing, visit http://localhost:8000/
For Unreal integration details, see combat_unreal_integration.py
