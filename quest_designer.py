"""
╔══════════════════════════════════════════════════════════════╗
║            QUEST DESIGNER  ·  quest_designer.py              ║
║  Visual Designer · Quest Chains · AI Generation · Rewards    ║
╚══════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import asyncio, json, random, sqlite3, uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


# ═══════════════════════════ ENUMS ══════════════════════════════
class QuestType(Enum):
    MAIN         = "main"
    SIDE         = "side"
    DAILY        = "daily"
    WEEKLY       = "weekly"
    HIDDEN       = "hidden"
    FACTION      = "faction"
    ROMANCE      = "romance"
    TUTORIAL     = "tutorial"

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

class Difficulty(Enum):
    TRIVIAL  = 1
    EASY     = 2
    NORMAL   = 3
    HARD     = 4
    EPIC     = 5
    LEGENDARY= 6

class RewardType(Enum):
    GOLD         = "gold"
    XP           = "xp"
    ITEM         = "item"
    SKILL_POINT  = "skill_point"
    REPUTATION   = "reputation"
    UNLOCK       = "unlock"
    TITLE        = "title"
    COMPANION    = "companion"


# ═════════════════════ DATA STRUCTURES ══════════════════════════
@dataclass
class QuestObjective:
    objective_id:  str
    obj_type:      ObjectiveType
    description:   str
    target_id:     str          = ""    # enemy type / item id / location id
    required_qty:  int          = 1
    current_qty:   int          = 0
    is_optional:   bool         = False
    is_hidden:     bool         = False
    location_hint: str          = ""
    time_limit:    Optional[int]= None  # seconds; None = no limit
    on_complete:   Optional[str]= None  # callback key

    @property
    def completed(self) -> bool:
        return self.current_qty >= self.required_qty

    @property
    def progress_pct(self) -> float:
        return min(100.0, self.current_qty / max(1, self.required_qty) * 100)

    def update(self, amount: int = 1):
        self.current_qty = min(self.required_qty, self.current_qty + amount)

    def to_dict(self) -> Dict:
        return {
            "id": self.objective_id, "type": self.obj_type.value,
            "description": self.description, "target": self.target_id,
            "required": self.required_qty, "current": self.current_qty,
            "completed": self.completed, "progress": round(self.progress_pct, 1),
            "optional": self.is_optional, "hidden": self.is_hidden,
        }


@dataclass
class QuestReward:
    reward_type: RewardType
    value:       Any            # int for gold/xp/sp, str for item/title/unlock
    quantity:    int   = 1
    rarity:      str   = "common"   # common, uncommon, rare, epic, legendary
    condition:   str   = ""     # "" = always, "all_objectives" = only if all done

    def to_dict(self) -> Dict:
        return {"type": self.reward_type.value, "value": self.value,
                "qty": self.quantity, "rarity": self.rarity, "condition": self.condition}


@dataclass
class QuestPrerequisite:
    prereq_type: str     # "quest","level","item","faction","flag"
    key:         str
    operator:    str     # "==",">=","has"
    value:       Any

    def is_met(self, player_state: Dict) -> bool:
        actual = player_state.get(self.prereq_type, {}).get(self.key)
        try:
            if self.operator == "==":  return actual == self.value
            if self.operator == ">=":  return actual >= self.value
            if self.operator == "has": return self.value in (actual or [])
        except Exception: pass
        return False


# ══════════════════════ QUEST ═══════════════════════════════════
@dataclass
class Quest:
    quest_id:      str
    name:          str
    description:   str
    quest_type:    QuestType            = QuestType.SIDE
    difficulty:    Difficulty           = Difficulty.NORMAL
    status:        QuestStatus          = QuestStatus.AVAILABLE
    giver_id:      str                  = ""
    giver_name:    str                  = ""
    location:      str                  = ""
    objectives:    List[QuestObjective] = field(default_factory=list)
    rewards:       List[QuestReward]    = field(default_factory=list)
    prerequisites: List[QuestPrerequisite]= field(default_factory=list)
    next_quest_id: Optional[str]        = None   # chain
    time_limit:    Optional[int]        = None
    is_repeatable: bool                 = False
    lore_text:     str                  = ""
    tags:          List[str]            = field(default_factory=list)
    created_at:    str                  = field(default_factory=lambda: datetime.utcnow().isoformat())

    # ── Progress ─────────────────────────────────
    @property
    def all_required_complete(self) -> bool:
        return all(o.completed for o in self.objectives if not o.is_optional)

    @property
    def all_objectives_complete(self) -> bool:
        return all(o.completed for o in self.objectives)

    @property
    def progress_pct(self) -> float:
        req = [o for o in self.objectives if not o.is_optional]
        if not req: return 100.0
        return sum(o.progress_pct for o in req) / len(req)

    def update_objective(self, obj_type: ObjectiveType,
                         target_id: str = "", amount: int = 1) -> List[str]:
        """Update matching objectives; returns list of newly-completed objective ids."""
        completed_now = []
        for obj in self.objectives:
            if obj.obj_type == obj_type and (not target_id or obj.target_id == target_id):
                was = obj.completed
                obj.update(amount)
                if not was and obj.completed:
                    completed_now.append(obj.objective_id)
        return completed_now

    def check_completion(self) -> bool:
        if self.all_required_complete and self.status == QuestStatus.ACTIVE:
            self.status = QuestStatus.COMPLETED
            return True
        return False

    def prerequisites_met(self, player_state: Dict) -> bool:
        return all(p.is_met(player_state) for p in self.prerequisites)

    def to_dict(self) -> Dict:
        return {
            "quest_id":    self.quest_id,
            "name":        self.name,
            "description": self.description,
            "type":        self.quest_type.value,
            "difficulty":  self.difficulty.value,
            "status":      self.status.value,
            "giver":       self.giver_name,
            "location":    self.location,
            "progress":    round(self.progress_pct, 1),
            "objectives":  [o.to_dict() for o in self.objectives],
            "rewards":     [r.to_dict() for r in self.rewards],
            "next_quest":  self.next_quest_id,
            "tags":        self.tags,
        }


# ══════════════════════ QUEST CHAIN ═════════════════════════════
@dataclass
class QuestChain:
    chain_id:   str
    name:       str
    description:str
    quest_ids:  List[str] = field(default_factory=list)  # ordered

    def ordered_quests(self, registry: "QuestManager") -> List[Quest]:
        return [registry.quests[qid] for qid in self.quest_ids if qid in registry.quests]

    def current_quest(self, registry: "QuestManager") -> Optional[Quest]:
        for q in self.ordered_quests(registry):
            if q.status in (QuestStatus.AVAILABLE, QuestStatus.ACTIVE):
                return q
        return None

    def is_complete(self, registry: "QuestManager") -> bool:
        return all(registry.quests.get(qid, Quest("","","")).status == QuestStatus.COMPLETED
                   for qid in self.quest_ids)


# ══════════════════════ BUILDER DSL ═════════════════════════════
class QuestBuilder:
    """Fluent builder for constructing quests cleanly."""

    def __init__(self, quest_id: str = None):
        self._q = Quest(quest_id or str(uuid.uuid4())[:8], "", "")

    def name(self, v): self._q.name = v; return self
    def description(self, v): self._q.description = v; return self
    def type(self, v: QuestType): self._q.quest_type = v; return self
    def difficulty(self, v: Difficulty): self._q.difficulty = v; return self
    def giver(self, npc_id, npc_name): self._q.giver_id=npc_id; self._q.giver_name=npc_name; return self
    def location(self, v): self._q.location = v; return self
    def lore(self, v): self._q.lore_text = v; return self
    def tags(self, *t): self._q.tags.extend(t); return self
    def chain_to(self, next_id): self._q.next_quest_id = next_id; return self
    def repeatable(self): self._q.is_repeatable = True; return self

    def objective(self, obj_type: ObjectiveType, description: str,
                  target_id: str = "", qty: int = 1,
                  optional: bool = False, hidden: bool = False,
                  time_limit: int = None) -> "QuestBuilder":
        self._q.objectives.append(QuestObjective(
            str(uuid.uuid4())[:6], obj_type, description, target_id, qty,
            is_optional=optional, is_hidden=hidden, time_limit=time_limit))
        return self

    def reward(self, reward_type: RewardType, value: Any,
               qty: int = 1, rarity: str = "common") -> "QuestBuilder":
        self._q.rewards.append(QuestReward(reward_type, value, qty, rarity))
        return self

    def requires_quest(self, quest_id: str) -> "QuestBuilder":
        self._q.prerequisites.append(QuestPrerequisite("quest", quest_id, "==", "completed"))
        return self

    def requires_level(self, level: int) -> "QuestBuilder":
        self._q.prerequisites.append(QuestPrerequisite("stat", "level", ">=", level))
        return self

    def build(self) -> Quest:
        return self._q


# ══════════════════════ QUEST MANAGER ═══════════════════════════
class QuestManager:
    """Central quest registry + runtime tracking per player."""

    # Reward multipliers by difficulty
    DIFF_MULTIPLIERS = {
        Difficulty.TRIVIAL: 0.5, Difficulty.EASY: 0.8, Difficulty.NORMAL: 1.0,
        Difficulty.HARD: 1.5, Difficulty.EPIC: 2.5, Difficulty.LEGENDARY: 4.0,
    }

    def __init__(self, openai_key: str = ""):
        self.openai_key = openai_key
        self.quests:  Dict[str, Quest]       = {}
        self.chains:  Dict[str, QuestChain]  = {}
        self.player_quests: Dict[str, Dict[str, QuestStatus]] = {}
        self._init_db()
        self._preload_templates()

    def _init_db(self):
        c = sqlite3.connect("quest_system.db")
        c.executescript("""
        CREATE TABLE IF NOT EXISTS quests(
            id TEXT PRIMARY KEY, name TEXT, type TEXT, difficulty INT,
            quest_json TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS player_progress(
            player_id TEXT, quest_id TEXT, status TEXT,
            objectives_json TEXT, started_at TEXT, completed_at TEXT,
            PRIMARY KEY(player_id,quest_id));
        CREATE TABLE IF NOT EXISTS reward_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT, quest_id TEXT, reward_type TEXT,
            value TEXT, qty INT, ts TEXT);
        """)
        c.commit(); c.close()

    def _preload_templates(self):
        """Register several ready-to-use template quests."""
        templates = [
            (QuestBuilder("tmpl_hunt")
             .name("Bandit Trouble").description("Clear out the bandit camp terrorising the village.")
             .type(QuestType.SIDE).difficulty(Difficulty.EASY).giver("elder","Village Elder").location("Bandit Camp")
             .objective(ObjectiveType.KILL, "Defeat bandits", "bandit", 10)
             .objective(ObjectiveType.KILL, "Defeat bandit leader", "bandit_leader", 1)
             .objective(ObjectiveType.COLLECT, "Recover stolen gold", "stolen_gold", 3, optional=True)
             .reward(RewardType.GOLD, 500).reward(RewardType.XP, 1000)
             .reward(RewardType.REPUTATION, "village_faction", 1, "uncommon")
             .tags("combat","bandits","village").build()),

            (QuestBuilder("tmpl_fetch")
             .name("Healer's Request").description("Gather rare herbs from the Whispering Forest.")
             .type(QuestType.SIDE).difficulty(Difficulty.TRIVIAL).giver("healer","Mira the Healer")
             .objective(ObjectiveType.COLLECT, "Gather Moonbloom flowers", "moonbloom", 5)
             .objective(ObjectiveType.COLLECT, "Collect Silverroot", "silverroot", 3)
             .reward(RewardType.GOLD, 200).reward(RewardType.XP, 400)
             .reward(RewardType.ITEM, "healing_potion_x3", 1, "uncommon")
             .tags("gathering","peaceful","nature").build()),

            (QuestBuilder("tmpl_escort")
             .name("Safe Passage").description("Escort the merchant safely to the capital city.")
             .type(QuestType.SIDE).difficulty(Difficulty.NORMAL).giver("merchant","Aldo the Merchant")
             .objective(ObjectiveType.ESCORT, "Keep Aldo alive", "aldo", 1)
             .objective(ObjectiveType.REACH,  "Arrive at the capital", "capital_gate", 1)
             .reward(RewardType.GOLD, 750).reward(RewardType.XP, 800)
             .reward(RewardType.UNLOCK, "merchant_discount", 1, "rare")
             .tags("escort","travel","merchant").build()),

            (QuestBuilder("tmpl_dungeon")
             .name("Depths of Shadow").description("Descend into the ancient dungeon and retrieve the lost relic.")
             .type(QuestType.MAIN).difficulty(Difficulty.HARD).giver("wizard","Archmage Valdris").location("Shadow Dungeon")
             .objective(ObjectiveType.DISCOVER,  "Find the dungeon entrance",     "dungeon_entrance",1)
             .objective(ObjectiveType.INTERACT,  "Activate the ancient seal",     "ancient_seal",   1)
             .objective(ObjectiveType.KILL,       "Defeat the dungeon guardian",   "dungeon_boss",   1)
             .objective(ObjectiveType.COLLECT,   "Retrieve the Crystal Relic",    "crystal_relic",  1)
             .objective(ObjectiveType.REACH,      "Escape the dungeon",            "dungeon_exit",   1)
             .reward(RewardType.GOLD, 2000).reward(RewardType.XP, 5000)
             .reward(RewardType.ITEM, "crystal_relic_reward", 1, "legendary")
             .reward(RewardType.SKILL_POINT, 2).tags("dungeon","boss","main_story").build()),
        ]
        for q in templates:
            self.register_quest(q)

    # ── CRUD ─────────────────────────────────────
    def register_quest(self, quest: Quest):
        self.quests[quest.quest_id] = quest
        c = sqlite3.connect("quest_system.db")
        c.execute("INSERT OR REPLACE INTO quests VALUES(?,?,?,?,?,?)",
                  (quest.quest_id, quest.name, quest.quest_type.value,
                   quest.difficulty.value, json.dumps(quest.to_dict()),
                   quest.created_at))
        c.commit(); c.close()

    def register_chain(self, chain: QuestChain):
        self.chains[chain.chain_id] = chain

    # ── Player interface ─────────────────────────
    def get_available_quests(self, player_state: Dict) -> List[Quest]:
        return [q for q in self.quests.values()
                if q.status == QuestStatus.AVAILABLE
                and q.prerequisites_met(player_state)]

    def start_quest(self, player_id: str, quest_id: str) -> bool:
        q = self.quests.get(quest_id)
        if not q or q.status not in (QuestStatus.AVAILABLE,): return False
        q.status = QuestStatus.ACTIVE
        c = sqlite3.connect("quest_system.db")
        c.execute("INSERT OR REPLACE INTO player_progress VALUES(?,?,?,?,?,?)",
                  (player_id, quest_id, "active",
                   json.dumps([o.to_dict() for o in q.objectives]),
                   datetime.utcnow().isoformat(), None))
        c.commit(); c.close()
        return True

    def update_objective(self, player_id: str, obj_type: ObjectiveType,
                          target_id: str = "", amount: int = 1) -> Dict:
        results = {"completed_objectives": [], "completed_quests": [], "rewards": []}
        for q in self.quests.values():
            if q.status != QuestStatus.ACTIVE: continue
            newly_done = q.update_objective(obj_type, target_id, amount)
            results["completed_objectives"].extend(newly_done)
            if q.check_completion():
                results["completed_quests"].append(q.quest_id)
                results["rewards"].extend(self.grant_rewards(player_id, q))
                self._unlock_next(q)
        return results

    def grant_rewards(self, player_id: str, quest: Quest) -> List[Dict]:
        mult  = self.DIFF_MULTIPLIERS.get(quest.difficulty, 1.0)
        given = []
        for r in quest.rewards:
            if r.condition == "all_objectives" and not quest.all_objectives_complete:
                continue
            effective_value = int(r.value * mult) if isinstance(r.value, (int, float)) else r.value
            given.append({"type": r.reward_type.value, "value": effective_value,
                          "qty": r.quantity, "rarity": r.rarity})
            c = sqlite3.connect("quest_system.db")
            c.execute("INSERT INTO reward_log(player_id,quest_id,reward_type,value,qty,ts) VALUES(?,?,?,?,?,?)",
                      (player_id, quest.quest_id, r.reward_type.value,
                       str(effective_value), r.quantity, datetime.utcnow().isoformat()))
            c.commit(); c.close()
        return given

    def _unlock_next(self, quest: Quest):
        if quest.next_quest_id and quest.next_quest_id in self.quests:
            nxt = self.quests[quest.next_quest_id]
            if nxt.status == QuestStatus.LOCKED:
                nxt.status = QuestStatus.AVAILABLE

    def abandon_quest(self, quest_id: str):
        q = self.quests.get(quest_id)
        if q and q.status == QuestStatus.ACTIVE:
            q.status = QuestStatus.ABANDONED
            for o in q.objectives: o.current_qty = 0

    # ── AI generation ────────────────────────────
    async def generate_quest(
        self,
        prompt:      str,
        quest_type:  QuestType  = QuestType.SIDE,
        difficulty:  Difficulty = Difficulty.NORMAL,
        world:       str        = "fantasy",
    ) -> Quest:
        mult = self.DIFF_MULTIPLIERS[difficulty]
        ai_prompt = f"""Create a game quest from this idea: {prompt}

World: {world}
Type: {quest_type.value}
Difficulty: {difficulty.name} (multiplier {mult}x)

Respond ONLY with JSON:
{{
  "name": "Quest Name",
  "description": "Short description",
  "giver_name": "NPC name",
  "location": "Location name",
  "lore": "Optional lore text",
  "objectives": [
    {{"type":"kill|collect|deliver|reach|interact|protect|escort|talk_to|discover",
      "description":"Objective description","target":"target_id","qty":1,"optional":false}}
  ],
  "rewards": [
    {{"type":"gold|xp|item|skill_point|reputation|unlock|title","value":500,"qty":1,"rarity":"common"}},
    {{"type":"xp","value":1000,"qty":1,"rarity":"common"}}
  ],
  "tags": ["tag1","tag2"]
}}"""
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.openai_key}",
                             "Content-Type": "application/json"},
                    json={"model": "gpt-4-turbo-preview",
                          "messages": [{"role": "user", "content": ai_prompt}],
                          "response_format": {"type": "json_object"}}
                ) as r:
                    d = await r.json()
                    raw = json.loads(d["choices"][0]["message"]["content"])
        except Exception:
            raw = {"name": "New Quest", "description": prompt,
                   "giver_name": "NPC", "location": "Unknown",
                   "objectives": [{"type":"kill","description":"Defeat enemies","target":"enemy","qty":5,"optional":False}],
                   "rewards": [{"type":"gold","value":300,"qty":1,"rarity":"common"},
                               {"type":"xp",  "value":600,"qty":1,"rarity":"common"}],
                   "tags": []}

        return self._parse_ai_quest(raw, quest_type, difficulty)

    def _parse_ai_quest(self, raw: Dict, qt: QuestType, diff: Difficulty) -> Quest:
        obj_map = {o.value: o for o in ObjectiveType}
        rw_map  = {r.value: r for r in RewardType}
        diff_map= {d.value: d for d in Difficulty}
        qid     = str(uuid.uuid4())[:8]
        builder = (QuestBuilder(qid)
                   .name(raw.get("name","New Quest"))
                   .description(raw.get("description",""))
                   .type(qt).difficulty(diff)
                   .giver("",raw.get("giver_name","NPC"))
                   .location(raw.get("location",""))
                   .lore(raw.get("lore",""))
                   .tags(*raw.get("tags",[])))
        for o in raw.get("objectives", []):
            builder.objective(
                obj_map.get(o.get("type","kill"), ObjectiveType.KILL),
                o.get("description",""), o.get("target",""), o.get("qty",1),
                optional=o.get("optional",False))
        for r in raw.get("rewards", []):
            builder.reward(
                rw_map.get(r.get("type","gold"), RewardType.GOLD),
                r.get("value",100), r.get("qty",1), r.get("rarity","common"))
        q = builder.build()
        self.register_quest(q); return q

    def generate_random_quest(self,
                               quest_type: QuestType = None,
                               difficulty: Difficulty = None) -> Quest:
        qt   = quest_type or random.choice(list(QuestType))
        diff = difficulty  or random.choice(list(Difficulty))
        templates = [
            {"name": "Monster Hunt",       "obj": ObjectiveType.KILL,     "target": random.choice(["wolf","goblin","troll","dragon"])},
            {"name": "Gathering Mission",  "obj": ObjectiveType.COLLECT,  "target": random.choice(["herb","ore","gem","wood"])},
            {"name": "Delivery Run",       "obj": ObjectiveType.DELIVER,  "target": random.choice(["package","letter","artifact"])},
            {"name": "Exploration Task",   "obj": ObjectiveType.DISCOVER, "target": random.choice(["cave","ruins","temple","camp"])},
            {"name": "Diplomatic Visit",   "obj": ObjectiveType.TALK_TO,  "target": random.choice(["lord","merchant","sage","captain"])},
        ]
        t    = random.choice(templates)
        mult = self.DIFF_MULTIPLIERS[diff]
        qty  = max(1, int(random.randint(3,15) * mult))
        q    = (QuestBuilder()
                .name(f"{t['name']}: {t['target'].title()}")
                .description(f"A {diff.name.lower()} quest involving {t['target']}s.")
                .type(qt).difficulty(diff)
                .giver("","Local Contact").location("Nearby Area")
                .objective(t["obj"], f"Complete the task ({qty}/{qty})", t["target"], qty)
                .reward(RewardType.GOLD, int(200 * mult))
                .reward(RewardType.XP,   int(400 * mult))
                .build())
        self.register_quest(q); return q

    # ── Summary views ────────────────────────────
    def active_quests(self) -> List[Quest]:
        return [q for q in self.quests.values() if q.status == QuestStatus.ACTIVE]

    def completed_quests(self) -> List[Quest]:
        return [q for q in self.quests.values() if q.status == QuestStatus.COMPLETED]

    def quest_log(self) -> Dict:
        return {
            "active":    [q.to_dict() for q in self.active_quests()],
            "available": [q.to_dict() for q in self.quests.values() if q.status == QuestStatus.AVAILABLE],
            "completed": [q.to_dict() for q in self.completed_quests()],
            "total":     len(self.quests),
        }

    # ── Export ───────────────────────────────────
    def export_unreal(self, out: str = "exports") -> str:
        Path(out).mkdir(parents=True, exist_ok=True)
        p = f"{out}/quest_data_{int(__import__('time').time())}.json"
        Path(p).write_text(json.dumps({
            "schema": "1.0",
            "generated": datetime.utcnow().isoformat(),
            "quests": [q.to_dict() for q in self.quests.values()],
            "chains": [{"chain_id": c.chain_id, "name": c.name, "quests": c.quest_ids}
                       for c in self.chains.values()],
        }, indent=2)); return p

    def export_csv(self, out: str = "exports") -> str:
        import csv
        Path(out).mkdir(parents=True, exist_ok=True)
        p = f"{out}/quests.csv"
        with open(p, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id","name","type","difficulty","status","giver","location","progress","tags"])
            for q in self.quests.values():
                w.writerow([q.quest_id, q.name, q.quest_type.value,
                             q.difficulty.name, q.status.value, q.giver_name,
                             q.location, f"{q.progress_pct:.0f}%", ";".join(q.tags)])
        return p


# ════════════════════════ QUICK DEMO ════════════════════════════
if __name__ == "__main__":
    mgr = QuestManager()

    # Activate template quest
    q = mgr.quests["tmpl_hunt"]
    mgr.start_quest("player1", q.quest_id)
    print("Started:", q.name)

    # Simulate kills
    r = mgr.update_objective("player1", ObjectiveType.KILL, "bandit", 10)
    print("After 10 bandit kills:", r)

    r = mgr.update_objective("player1", ObjectiveType.KILL, "bandit_leader", 1)
    print("After boss kill:", r)

    # Random quest
    rq = mgr.generate_random_quest(QuestType.DAILY, Difficulty.EASY)
    print("Random quest:", rq.name, "|", [o.description for o in rq.objectives])

    print("\nQuest Log:", json.dumps(mgr.quest_log(), indent=2))
    print("Unreal export:", mgr.export_unreal())
