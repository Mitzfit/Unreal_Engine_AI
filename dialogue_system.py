"""
╔══════════════════════════════════════════════════════════════╗
║            DIALOGUE SYSTEM  ·  dialogue_system.py            ║
║  Branching Trees · Conditions · Relationships · TTS · Export ║
╚══════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import asyncio, json, sqlite3, uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


# ═══════════════════════════ ENUMS ══════════════════════════════
class DialogueType(Enum):
    STATEMENT   = "statement"
    QUESTION    = "question"
    CHOICE      = "choice"
    CONDITIONAL = "conditional"
    QUEST_GIVE  = "quest_give"
    QUEST_END   = "quest_end"
    SHOP        = "shop"
    FAREWELL    = "farewell"

class Emotion(Enum):
    NEUTRAL   = "neutral"
    HAPPY     = "happy"
    SAD       = "sad"
    ANGRY     = "angry"
    SCARED    = "scared"
    SURPRISED = "surprised"
    SUSPICIOUS= "suspicious"
    EXCITED   = "excited"
    DISGUSTED = "disgusted"

class RelationshipLevel(Enum):
    HOSTILE     = -2
    UNFRIENDLY  = -1
    NEUTRAL     =  0
    FRIENDLY    =  1
    ALLY        =  2
    LOVED       =  3

class VoiceType(Enum):
    HERO_MALE    = "hero_male"
    HERO_FEMALE  = "hero_female"
    VILLAIN      = "villain"
    ELDER        = "elder"
    MERCHANT     = "merchant"
    GUARD        = "guard"
    CHILD        = "child"
    NARRATOR     = "narrator"
    MONSTER      = "monster"
    ROBOT        = "robot"


# ═════════════════════ DATA STRUCTURES ══════════════════════════
@dataclass
class DialogueCondition:
    """Condition that must be met for a node/choice to appear."""
    condition_type: str          # "relationship","flag","quest","item","stat"
    key:            str
    operator:       str          # ">=","<=","==","!=",">","<","has","not_has"
    value:          Any

    def evaluate(self, ctx: "DialogueContext") -> bool:
        actual = ctx.get(self.condition_type, self.key)
        op = self.operator
        try:
            if op == ">=":      return actual >= self.value
            if op == "<=":      return actual <= self.value
            if op == "==":      return actual == self.value
            if op == "!=":      return actual != self.value
            if op == ">":       return actual >  self.value
            if op == "<":       return actual <  self.value
            if op == "has":     return self.value in (actual or [])
            if op == "not_has": return self.value not in (actual or [])
        except Exception:
            return False
        return False


@dataclass
class DialogueEffect:
    """Side-effect triggered when a node is reached."""
    effect_type: str   # "relationship","flag","quest_start","quest_end","give_item","remove_item","play_sound","camera"
    key:         str
    value:       Any

    def apply(self, ctx: "DialogueContext"):
        if self.effect_type == "relationship":
            ctx.set_relationship(self.key, ctx.get("relationship", self.key, 0) + self.value)
        elif self.effect_type == "flag":
            ctx.set_flag(self.key, self.value)
        elif self.effect_type == "quest_start":
            ctx.start_quest(self.key)
        elif self.effect_type == "quest_end":
            ctx.complete_quest(self.key)
        elif self.effect_type == "give_item":
            ctx.give_item(self.key, self.value)
        elif self.effect_type == "remove_item":
            ctx.remove_item(self.key, self.value)


@dataclass
class DialogueChoice:
    choice_id:   str
    text:        str
    next_node_id: str
    conditions:  List[DialogueCondition] = field(default_factory=list)
    effects:     List[DialogueEffect]    = field(default_factory=list)
    skill_check: Optional[Dict]          = None   # {"skill":"persuasion","dc":15}
    is_exit:     bool                    = False

    def is_available(self, ctx: "DialogueContext") -> bool:
        return all(c.evaluate(ctx) for c in self.conditions)


@dataclass
class DialogueNode:
    node_id:     str
    speaker:     str
    text:        str
    node_type:   DialogueType           = DialogueType.STATEMENT
    emotion:     Emotion                = Emotion.NEUTRAL
    voice_type:  VoiceType              = VoiceType.NARRATOR
    choices:     List[DialogueChoice]   = field(default_factory=list)
    conditions:  List[DialogueCondition]= field(default_factory=list)
    effects:     List[DialogueEffect]   = field(default_factory=list)
    next_node_id: Optional[str]         = None
    audio_file:  Optional[str]          = None
    portrait:    Optional[str]          = None
    camera_hint: Optional[str]          = None   # "close_up","medium","over_shoulder"
    wait_secs:   float                  = 0.0
    tags:        List[str]              = field(default_factory=list)

    def get_available_choices(self, ctx: "DialogueContext") -> List[DialogueChoice]:
        return [c for c in self.choices if c.is_available(ctx)]


# ═══════════════════════ CONTEXT ════════════════════════════════
class DialogueContext:
    """Holds all runtime state for an active conversation."""
    def __init__(self, player_id: str = "player"):
        self.player_id     = player_id
        self.relationships: Dict[str, int]      = {}
        self.flags:         Dict[str, Any]      = {}
        self.quests:        Dict[str, str]      = {}
        self.inventory:     Dict[str, int]      = {}
        self.stats:         Dict[str, Any]      = {}
        self.history:       List[str]           = []   # node_ids visited

    def get(self, ctx_type: str, key: str, default: Any = None) -> Any:
        store = {"relationship": self.relationships,
                 "flag":         self.flags,
                 "quest":        self.quests,
                 "item":         self.inventory,
                 "stat":         self.stats}.get(ctx_type, {})
        return store.get(key, default)

    def set_relationship(self, npc_id: str, value: int):
        self.relationships[npc_id] = max(-100, min(100, value))

    def set_flag(self, key: str, value: Any):
        self.flags[key] = value

    def start_quest(self, quest_id: str):
        self.quests[quest_id] = "active"

    def complete_quest(self, quest_id: str):
        self.quests[quest_id] = "completed"

    def give_item(self, item_id: str, qty: int = 1):
        self.inventory[item_id] = self.inventory.get(item_id, 0) + qty

    def remove_item(self, item_id: str, qty: int = 1):
        self.inventory[item_id] = max(0, self.inventory.get(item_id, 0) - qty)

    def relationship_level(self, npc_id: str) -> RelationshipLevel:
        v = self.relationships.get(npc_id, 0)
        if v <= -60: return RelationshipLevel.HOSTILE
        if v <= -20: return RelationshipLevel.UNFRIENDLY
        if v <=  20: return RelationshipLevel.NEUTRAL
        if v <=  60: return RelationshipLevel.FRIENDLY
        if v <=  80: return RelationshipLevel.ALLY
        return RelationshipLevel.LOVED


# ═════════════════════ DIALOGUE TREE ════════════════════════════
class DialogueTree:
    """A complete conversation tree for one NPC interaction."""

    def __init__(self, tree_id: str, npc_id: str, npc_name: str):
        self.tree_id   = tree_id
        self.npc_id    = npc_id
        self.npc_name  = npc_name
        self.nodes:    Dict[str, DialogueNode] = {}
        self.root_id:  Optional[str]           = None
        self.metadata: Dict[str, Any]          = {}

    def add_node(self, node: DialogueNode, is_root: bool = False) -> "DialogueTree":
        self.nodes[node.node_id] = node
        if is_root or not self.root_id:
            self.root_id = node.node_id
        return self

    def node(self, node_id: str) -> Optional[DialogueNode]:
        return self.nodes.get(node_id)

    def validate(self) -> List[str]:
        issues = []
        if not self.root_id:
            issues.append("No root node set.")
        for nid, node in self.nodes.items():
            for choice in node.choices:
                if choice.next_node_id and choice.next_node_id not in self.nodes:
                    issues.append(f"Choice '{choice.choice_id}' references missing node '{choice.next_node_id}'")
            if node.next_node_id and node.next_node_id not in self.nodes:
                issues.append(f"Node '{nid}' next_node_id '{node.next_node_id}' not found.")
        return issues

    def to_dict(self) -> Dict:
        return {
            "tree_id":  self.tree_id,
            "npc_id":   self.npc_id,
            "npc_name": self.npc_name,
            "root_id":  self.root_id,
            "nodes":    {nid: {"node_id":n.node_id,"speaker":n.speaker,"text":n.text,
                               "type":n.node_type.value,"emotion":n.emotion.value,
                               "next":n.next_node_id,
                               "choices":[{"id":c.choice_id,"text":c.text,"next":c.next_node_id}
                                          for c in n.choices]}
                         for nid,n in self.nodes.items()},
            "metadata": self.metadata,
        }


# ═══════════════════ DIALOGUE RUNNER ════════════════════════════
class DialogueRunner:
    """Executes a dialogue tree step by step."""

    def __init__(self, tree: DialogueTree, ctx: DialogueContext):
        self.tree        = tree
        self.ctx         = ctx
        self.current_id  = tree.root_id
        self.active      = True
        self.event_log:  List[Dict] = []

    def current_node(self) -> Optional[DialogueNode]:
        return self.tree.node(self.current_id) if self.current_id else None

    def available_choices(self) -> List[DialogueChoice]:
        node = self.current_node()
        if not node: return []
        return node.get_available_choices(self.ctx)

    def select_choice(self, choice_id: str) -> Optional[DialogueNode]:
        node = self.current_node()
        if not node: return None
        for ch in node.get_available_choices(self.ctx):
            if ch.choice_id == choice_id:
                for eff in ch.effects: eff.apply(self.ctx)
                self._advance(ch.next_node_id)
                if ch.is_exit: self.active = False
                return self.current_node()
        return None

    def advance(self) -> Optional[DialogueNode]:
        """Auto-advance (no choice required)."""
        node = self.current_node()
        if not node: return None
        for eff in node.effects: eff.apply(self.ctx)
        self.ctx.history.append(node.node_id)
        if node.next_node_id:
            self._advance(node.next_node_id)
        elif not node.choices:
            self.active = False
        return self.current_node()

    def _advance(self, next_id: str):
        self.current_id = next_id

    def is_finished(self) -> bool:
        return not self.active or not self.current_id

    def state_snapshot(self) -> Dict:
        node = self.current_node()
        return {
            "active":  self.active,
            "node_id": self.current_id,
            "speaker": node.speaker if node else "",
            "text":    node.text    if node else "",
            "emotion": node.emotion.value if node else "",
            "choices": [{"id": c.choice_id, "text": c.text}
                        for c in self.available_choices()],
        }


# ══════════════════ DIALOGUE MANAGER ════════════════════════════
class DialogueManager:
    """Manages all dialogue trees; generates new ones with AI."""

    def __init__(self, openai_key: str = ""):
        self.openai_key = openai_key
        self.trees:    Dict[str, DialogueTree]  = {}
        self.contexts: Dict[str, DialogueContext]= {}
        self._init_db()

    def _init_db(self):
        c = sqlite3.connect("dialogue_system.db")
        c.executescript("""
        CREATE TABLE IF NOT EXISTS dialogue_trees(
            id TEXT PRIMARY KEY, npc_id TEXT, npc_name TEXT, tree_json TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS conversations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT, npc_id TEXT, nodes_visited TEXT,
            choices_made TEXT, duration_secs REAL, ended_at TEXT);
        CREATE TABLE IF NOT EXISTS relationship_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT, npc_id TEXT, delta INT, new_value INT, reason TEXT, ts TEXT);
        """)
        c.commit(); c.close()

    # ── CRUD ─────────────────────────────────────
    def register_tree(self, tree: DialogueTree):
        self.trees[tree.tree_id] = tree
        c = sqlite3.connect("dialogue_system.db")
        c.execute("INSERT OR REPLACE INTO dialogue_trees VALUES(?,?,?,?,?)",
                  (tree.tree_id, tree.npc_id, tree.npc_name,
                   json.dumps(tree.to_dict()), datetime.utcnow().isoformat()))
        c.commit(); c.close()

    def get_context(self, player_id: str) -> DialogueContext:
        if player_id not in self.contexts:
            self.contexts[player_id] = DialogueContext(player_id)
        return self.contexts[player_id]

    def start_conversation(self, player_id: str, tree_id: str) -> DialogueRunner:
        tree = self.trees.get(tree_id)
        if not tree: raise ValueError(f"Tree '{tree_id}' not found.")
        ctx  = self.get_context(player_id)
        return DialogueRunner(tree, ctx)

    # ── AI generation ────────────────────────────
    async def generate_tree(
        self,
        npc_name:    str,
        npc_role:    str,
        topic:       str,
        game_world:  str = "fantasy",
        branches:    int = 3,
    ) -> DialogueTree:
        prompt = f"""Create a branching game dialogue tree.

NPC:     {npc_name} ({npc_role})
Topic:   {topic}
World:   {game_world}
Branches per choice: {branches}

Respond ONLY with valid JSON matching this schema:
{{
  "npc_name": "{npc_name}",
  "npc_id":   "npc_{npc_name.lower().replace(' ','_')}",
  "nodes": [
    {{
      "node_id": "n1",
      "speaker": "{npc_name}",
      "text": "opening line",
      "emotion": "neutral",
      "next": null,
      "choices": [
        {{"id":"c1","text":"player option 1","next":"n2","effect":null}},
        {{"id":"c2","text":"player option 2","next":"n3","effect":null}}
      ]
    }},
    {{"node_id":"n2","speaker":"{npc_name}","text":"response to option 1","emotion":"happy","next":null,"choices":[]}},
    {{"node_id":"n3","speaker":"{npc_name}","text":"response to option 2","emotion":"sad","next":null,"choices":[]}}
  ]
}}"""
        raw = {}
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.openai_key}",
                             "Content-Type": "application/json"},
                    json={"model": "gpt-4-turbo-preview",
                          "messages": [{"role": "user", "content": prompt}],
                          "response_format": {"type": "json_object"}}
                ) as r:
                    d = await r.json()
                    raw = json.loads(d["choices"][0]["message"]["content"])
        except Exception:
            raw = {"npc_name": npc_name, "npc_id": f"npc_{npc_name}", "nodes": [
                {"node_id": "n1", "speaker": npc_name,
                 "text": f"Hello, traveller. I am {npc_name}.",
                 "emotion": "neutral", "next": None, "choices": []}
            ]}

        return self._parse_ai_tree(raw)

    def _parse_ai_tree(self, raw: Dict) -> DialogueTree:
        tree_id  = str(uuid.uuid4())[:8]
        tree     = DialogueTree(tree_id, raw.get("npc_id","npc"), raw.get("npc_name","NPC"))
        emotions = {e.value: e for e in Emotion}
        for i, nd in enumerate(raw.get("nodes", [])):
            choices = [
                DialogueChoice(
                    choice_id    = c["id"],
                    text         = c["text"],
                    next_node_id = c.get("next") or "",
                )
                for c in nd.get("choices", [])
            ]
            node = DialogueNode(
                node_id      = nd["node_id"],
                speaker      = nd.get("speaker", "NPC"),
                text         = nd.get("text", ""),
                emotion      = emotions.get(nd.get("emotion","neutral"), Emotion.NEUTRAL),
                choices      = choices,
                next_node_id = nd.get("next"),
            )
            tree.add_node(node, is_root=(i == 0))
        return tree

    # ── Pre-built trees ──────────────────────────
    def create_merchant_tree(self, merchant_name: str) -> DialogueTree:
        tree = DialogueTree(str(uuid.uuid4())[:8], "merchant", merchant_name)
        nodes = [
            DialogueNode("root",  merchant_name, f"Welcome! I'm {merchant_name}. Looking to buy or sell?",
                         DialogueType.QUESTION, Emotion.HAPPY,
                         choices=[
                             DialogueChoice("buy",  "I want to buy something.", "buy_node"),
                             DialogueChoice("sell", "I'd like to sell.",         "sell_node"),
                             DialogueChoice("bye",  "Never mind, goodbye.",       "bye_node", is_exit=True),
                         ]),
            DialogueNode("buy_node",  merchant_name, "Excellent! Let me show you my wares.",
                         DialogueType.SHOP, Emotion.HAPPY, next_node_id="root"),
            DialogueNode("sell_node", merchant_name, "Show me what you've got.",
                         DialogueType.SHOP, Emotion.NEUTRAL, next_node_id="root"),
            DialogueNode("bye_node",  merchant_name, "Safe travels, friend!",
                         DialogueType.FAREWELL, Emotion.HAPPY),
        ]
        for n in nodes: tree.add_node(n)
        tree.root_id = "root"
        return tree

    def create_quest_giver_tree(self, npc_name: str, quest_id: str, quest_name: str) -> DialogueTree:
        tree = DialogueTree(str(uuid.uuid4())[:8], "quest_giver", npc_name)
        no_quest_choices = [
            DialogueChoice("accept", f"I'll help you! (Accept: {quest_name})", "accepted",
                           effects=[DialogueEffect("quest_start", quest_id, "active")]),
            DialogueChoice("decline","I'm afraid I can't help right now.","declined"),
        ]
        have_quest_cond  = [DialogueCondition("quest", quest_id, "==", "active")]
        done_cond        = [DialogueCondition("quest", quest_id, "==", "completed")]
        nodes = [
            DialogueNode("root", npc_name, "Ah, an adventurer! I desperately need your help.",
                         conditions=[],
                         choices=no_quest_choices,
                         next_node_id=None),
            DialogueNode("accepted", npc_name, f"Wonderful! {quest_name} is yours. Godspeed!",
                         DialogueType.QUEST_GIVE, Emotion.HAPPY),
            DialogueNode("declined", npc_name, "I understand… please reconsider.",
                         Emotion.SAD),
        ]
        for n in nodes: tree.add_node(n)
        tree.root_id = "root"
        return tree

    # ── Export ───────────────────────────────────
    def export_unreal(self, out: str = "exports") -> List[str]:
        Path(out).mkdir(parents=True, exist_ok=True)
        files = []
        for tree in self.trees.values():
            p = f"{out}/dialogue_{tree.tree_id}.json"
            Path(p).write_text(json.dumps(tree.to_dict(), indent=2))
            files.append(p)
        return files

    def export_srt(self, tree_id: str, out: str = "exports") -> str:
        """Export all NPC lines as an SRT subtitle file."""
        tree = self.trees.get(tree_id)
        if not tree: return ""
        Path(out).mkdir(parents=True, exist_ok=True)
        lines = []; t = 0.0
        for node in tree.nodes.values():
            duration = max(2.0, len(node.text.split()) * 0.35)
            lines.append(f"{len(lines)+1}")
            lines.append(f"{_fmt_srt(t)} --> {_fmt_srt(t+duration)}")
            lines.append(f"[{node.speaker}] {node.text}"); lines.append("")
            t += duration + 0.5
        p = f"{out}/dialogue_{tree_id}.srt"
        Path(p).write_text("\n".join(lines)); return p


def _fmt_srt(s: float) -> str:
    h,r=divmod(int(s),3600); m,sec=divmod(r,60)
    return f"{h:02}:{m:02}:{sec:02},{int((s%1)*1000):03}"


# ════════════════════════ QUICK DEMO ════════════════════════════
if __name__ == "__main__":
    mgr  = DialogueManager()
    tree = mgr.create_merchant_tree("Gareth the Trader")
    mgr.register_tree(tree)
    ctx  = mgr.get_context("player1")
    ctx.set_relationship("merchant", 20)
    run  = mgr.start_conversation("player1", tree.tree_id)
    print("Start:", run.state_snapshot())
    run.select_choice("buy")
    print("After buy:", run.state_snapshot())
