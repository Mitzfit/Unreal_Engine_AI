╔════════════════════════════════════════════════════════════════════════════╗
║           COMBAT SYSTEM QUICK REFERENCE & CHEAT SHEET                       ║
║                  Fast lookup · Common patterns · Tips                        ║
╚════════════════════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════════════════════
1-MINUTE SETUP
═══════════════════════════════════════════════════════════════════════════════

# Install & Run
pip install -r requirements.txt
python combat_system_web.py
# Visit http://localhost:8000

# Or in Python
from combat_system import CombatSystem
system = CombatSystem()


═══════════════════════════════════════════════════════════════════════════════
COMMON PATTERNS
═══════════════════════════════════════════════════════════════════════════════

┌─ Create Basic Combat Scenario ─────────────────────────────────────────────┐

system = CombatSystem()

# Create entities
hero = system.create_entity(
    name="Hero",
    health=100, max_health=100,
    strength=15, dexterity=12
)

enemy = system.create_entity(
    name="Enemy",
    health=50, max_health=50,
    strength=10, dexterity=8
)

# Create formula
formula = system.create_damage_formula(
    name="sword_slash",
    damage_type="physical",
    base_damage=10.0,
    stat_multipliers={"strength": 0.5}
)

# Attack
damage = system.calculate_damage(hero, enemy, formula)
print(f"Damage: {damage.damage}, Hit: {damage.hit_type}")

┌─ Create Combo Sequence ────────────────────────────────────────────────────┐

m1 = system.create_combo_move("slash", damage_multiplier=1.0)
m2 = system.create_combo_move("slash", damage_multiplier=1.1)
m3 = system.create_combo_move("power", damage_multiplier=1.5)

chain = system.create_combo_chain(
    chain_name="combo",
    chain_type="linear",
    moves=[m1, m2, m3],
    timing_requirement=1.5,
    damage_bonus=0.25
)

# Validate
valid = system.validate_combo_sequence(
    chain,
    ["slash", "slash", "power"],
    [0.0, 0.7, 1.3]
)

┌─ Apply Status Effect ──────────────────────────────────────────────────────┐

burn = system.create_status_effect(
    effect_name="burn",
    effect_type="burn",
    duration=5.0,
    damage_per_tick=10.0
)

system.apply_status_effect(enemy, burn)

┌─ Create Skill Tree ────────────────────────────────────────────────────────┐

tree = system.create_skill_tree("warrior_tree")

node = system.add_skill_node(
    tree=tree,
    node_type="stat_boost",
    stat_name="strength",
    bonus=5,
    position=(0, 0)
)

hero.skill_tree = tree
hero.skill_points = 1
hero.allocate_skill_points([node.node_id])

┌─ Start Combat Session ────────────────────────────────────────────────────┐

session = system.start_combat_session(
    attacker=hero,
    defender=enemy
)

# Log attack
system.log_combat_action(
    session,
    action="attack",
    actor=hero.name,
    target=enemy.name,
    damage=25.0
)


═══════════════════════════════════════════════════════════════════════════════
API ENDPOINTS QUICK LOOKUP
═══════════════════════════════════════════════════════════════════════════════

FORMULAS
--------
POST   /api/formulas/create              Create damage formula
GET    /api/formulas                      List formulas
GET    /api/formulas/{id}                 Get formula
POST   /api/formulas/{id}/clone           Clone formula

EFFECTS
-------
POST   /api/effects/create                Create status effect
GET    /api/effects                       List effects
POST   /api/effects/{id}/apply            Apply effect (test)

COMBOS
------
POST   /api/combos/moves/create           Create move
GET    /api/combos/moves                  List moves
POST   /api/combos/chains/create          Create chain
GET    /api/combos/chains                 List chains
POST   /api/combos/validate               Validate combo

ENTITIES
--------
POST   /api/entities/create               Create entity
GET    /api/entities/{id}                 Get entity
POST   /api/entities/{id}/damage          Apply damage
POST   /api/entities/{id}/heal            Heal
POST   /api/entities/{id}/add-effect      Add effect

COMBAT
------
POST   /api/combat/attack                 Execute attack
POST   /api/combat/session/start          Start session
GET    /api/combat/critical-chance        Calculate crit

SKILLTREES
----------
POST   /api/skilltrees/create             Create tree
GET    /api/skilltrees/{id}               Get tree
POST   /api/skilltrees/{id}/nodes/add     Add node
POST   /api/skilltrees/{id}/allocate      Allocate points

SYSTEM
------
GET    /api/system/stats                  System stats
POST   /api/system/export                 Export data
GET    /health                            Health check


═══════════════════════════════════════════════════════════════════════════════
ENUM VALUES
═══════════════════════════════════════════════════════════════════════════════

DAMAGE TYPES
• physical    • fire    • ice    • lightning
• poison      • holy    • dark   • magic

STATUS EFFECTS
• stun       • slow       • burn       • freeze
• poison     • bleed      • weakness   • strength
• shield     • regen      • confusion  • sleep

COMBO CHAIN TYPES
• linear              • branch           • loop           • conditional

HIT TYPES
• miss      • hit       • critical       • dodge
• parry     • counter

COOLDOWN TYPES
• global       • per_ability       • shared

SKILL NODE TYPES
• stat_boost              • ability_unlock        • passive_effect
• damage_modifier         • cost_reduction        • utility


═══════════════════════════════════════════════════════════════════════════════
STAT REFERENCE
═══════════════════════════════════════════════════════════════════════════════

CORE STATS
Strength        (0-100)   → Melee damage, carry weight
Dexterity       (0-100)   → Critical chance, attack speed, evasion
Intelligence    (0-100)   → Magic damage, mana pool
Armor           (0-500)   → Damage reduction, mitigates ~1 DMG per point
Evasion         (0-100)   → Dodge chance, miss chance
Level           (1-100)   → Scaling factor for formulas

DERIVED VALUES
Health          = BasHealth × (1 + Level × 0.1) + (Armor × 0.1)
Resource (Mana) = BaseResource × (1 + Intelligence × 0.05)
CritChance      = 5% + (Dex × 0.5%) - (Enemy Armor × 0.1%)
CritMultiplier  = 1.5x + (Dex × 0.01x) [max 3.0x]
HitChance       = 85% + Accuracy - Enemy Evasion


═══════════════════════════════════════════════════════════════════════════════
DAMAGE CALCULATION STEPS
═══════════════════════════════════════════════════════════════════════════════

1. Roll hit type (85% base hit chance)
   ├─ Miss       → 0 damage
   ├─ Dodge      → 0 damage (higher evasion)
   ├─ Hit        → Continue
   ├─ Critical   → 5-95% chance
   ├─ Parry      → 50% damage
   └─ Counter    → Attacker takes 50% damage

2. Base damage = formula.base_damage
                 + (attacker.stat × formula.stat_multiplier)

3. Level scaling = base × (1 + formula.level_scaling × (level - 1))

4. Weapon scaling = level_scaled + (weapon_damage × formula.weapon_scaling)

5. Variance = weapon_scaled × random(0.9 to 1.1)

6. Critical (if critical hit)
   = variance × formula.critical_multiplier

7. Armor reduction
   = critical × (1 - target.armor × formula.armor_reduction)

8. Status effects (weakness, strength, shield)
   Apply modifiers or absorb

RESULT: Final damage


═══════════════════════════════════════════════════════════════════════════════
BALANCING QUICK TIPS
═══════════════════════════════════════════════════════════════════════════════

MAKE HARDER
• ↑ Enemy health +20%
• ↑ Enemy damage +20%
• ↑ Enemy armor +20%
• ↓ Player health -10%
• ↓ Crit chance -5%

MAKE EASIER
• ↑ Player health +20%
• ↓ Enemy damage -20%
• ↑ Crit chance +5%
• ↓ Enemy armor -10%

SPEED UP COMBAT
• ↓ Cooldowns -25%
• ↓ Effect duration -30%
• ↑ Combo damage bonus +25%
• ↑ Ability tick rate +50%

SLOW DOWN COMBAT
• ↑ Health +50%
• ↓ Damage -20%
• ↑ Cooldowns +30%
• ↓ Stat multipliers -0.1

BALANCE BY LEVEL
Level    Health    Damage    Armor    Expected EXP
1        50-100    5-15      0-5      100
10       200-400   30-80     10-20    1000
25       500-800   80-150    30-50    5000
50       1000-1500 200-350   100-200  20000


═══════════════════════════════════════════════════════════════════════════════
UNREAL ENGINE INTEGRATION
═══════════════════════════════════════════════════════════════════════════════

START UNREAL SERVER
python combat_unreal_integration.py

CONNECT IN UNREAL
1. Add ACombatBridge to level
2. Call ConnectToSystem("player_id")
3. Subscribe to OnCombatEvent delegate

C++ EXAMPLE
void AMyCharacter::BeginPlay() {
    Super::BeginPlay();
    
    CombatBridge = GetWorld()->SpawnActor<ACombatBridge>();
    CombatBridge->OnCombatEvent.AddDynamic(
        this, &AMyCharacter::OnCombatEvent
    );
    CombatBridge->ConnectToSystem("player_1");
}

EVENTS RECEIVED
• combat_started: Combat session begins
• attack_executed: Attack performed
• damage_taken: Entity takes damage
• status_effect_applied: Effect added
• combo_started: Combo sequence begins
• combo_completed: Full combo finished
• critical_hit: Critical damage dealt
• entity_died: Character death


═══════════════════════════════════════════════════════════════════════════════
DEBUGGING
═══════════════════════════════════════════════════════════════════════════════

CHECK SYSTEM STATUS
GET /api/system/stats
→ Returns total entities, formulas, active combats

EXPORT SYSTEM STATE
POST /api/system/export
→ Save all game state to JSON

TEST FORMULA
POST /api/formulas/{id}/test
Request: { "attacker_level": 10, "target_armor": 20 }
→ Shows damage calculation breakdown

VIEW COMBAT LOG
GET /api/combat/session/{id}/log
→ Full action log from combat session

ENABLE DEBUG LOGGING
In CombatSystem:
  import logging
  logging.basicConfig(level=logging.DEBUG)

PROFILE PERFORMANCE
import cProfile
cProfile.run('system.calculate_damage(...)')


═══════════════════════════════════════════════════════════════════════════════
COMMON ISSUES & FIXES
═══════════════════════════════════════════════════════════════════════════════

ISSUE: Always hitting/never missing
FIX:   Check hit_chance calculation, ensure evasion > 0

ISSUE: Damage too high/low
FIX:   Review base_damage, stat_multiplier, level_scaling values

ISSUE: Combos breaking early
FIX:   Increase timing_requirement window, check execution times

ISSUE: Status effects not applying
FIX:   Verify entity.active_effects list, check immunities

ISSUE: WebSocket not connecting
FIX:   Ensure port 8765 open, check bridge started

ISSUE: Skill tree won't allocate
FIX:   Check skill_points balance, verify node level requirement


═══════════════════════════════════════════════════════════════════════════════
URLS & RESOURCES
═══════════════════════════════════════════════════════════════════════════════

API DOCUMENTATION: http://localhost:8000/docs
INTERACTIVE DASHBOARD: http://localhost:8000/
WEBSOCKET: ws://localhost:8765
FULL GUIDE: See COMBAT_SYSTEM_GUIDE.md
SOURCE CODE: combat_system.py (1,600+ LOC)
WEB SERVER: combat_system_web.py (1,200+ LOC)
UNREAL BRIDGE: combat_unreal_integration.py (900+ LOC)


═══════════════════════════════════════════════════════════════════════════════
FORMULA PRESETS
═══════════════════════════════════════════════════════════════════════════════

BASIC MELEE
{
  "name": "sword_slash",
  "damage_type": "physical",
  "base_damage": 10.0,
  "stat_multipliers": {"strength": 0.5},
  "critical_multiplier": 2.0
}

MAGIC SPELL
{
  "name": "fireball",
  "damage_type": "fire",
  "base_damage": 20.0,
  "stat_multipliers": {"intelligence": 1.0},
  "critical_multiplier": 1.5
}

HEAVY ATTACK
{
  "name": "power_strike",
  "damage_type": "physical",
  "base_damage": 30.0,
  "stat_multipliers": {"strength": 1.0},
  "weapon_scaling": 0.8,
  "critical_multiplier": 2.5
}

ROGUE ATTACK
{
  "name": "backstab",
  "damage_type": "physical",
  "base_damage": 15.0,
  "stat_multipliers": {"dexterity": 0.8},
  "critical_multiplier": 3.0
}


═══════════════════════════════════════════════════════════════════════════════
EFFECT PRESETS
═══════════════════════════════════════════════════════════════════════════════

BURN
{
  "name": "burn",
  "effect_type": "burn",
  "duration": 5.0,
  "damage_per_tick": 10.0,
  "stackable": true,
  "max_stacks": 3
}

STUN
{
  "name": "stun",
  "effect_type": "stun",
  "duration": 1.0,
  "stackable": false
}

POISON
{
  "name": "poison",
  "effect_type": "poison",
  "duration": 10.0,
  "damage_per_tick": 5.0,
  "stackable": true,
  "max_stacks": 5
}

SHIELD
{
  "name": "shield",
  "effect_type": "shield",
  "duration": 30.0,
  "shield_amount": 50.0,
  "stackable": true
}


═══════════════════════════════════════════════════════════════════════════════
SHORT FORMS / ABBREVIATIONS
═══════════════════════════════════════════════════════════════════════════════

STR     = Strength
DEX     = Dexterity
INT     = Intelligence
ARM     = Armor
EVA     = Evasion
DMG     = Damage
HP      = Health
DoT     = Damage over Time
AoE     = Area of Effect
GCD     = Global Cooldown
CD      = Cooldown
CritC   = Critical Chance
CritM   = Critical Multiplier
RNG     = Random Number Generator
UE      = Unreal Engine
API     = Application Programming Interface
WS      = WebSocket
UUID    = Universally Unique Identifier


Last updated: 2024
Combat System v1.0
Production Ready ✓
