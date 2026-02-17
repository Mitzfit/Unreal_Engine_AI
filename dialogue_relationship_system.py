"""
Relationship and Character Tracking System
dialogue_relationship_system.py - Track NPC relationships and character emotions
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum


class RelationshipTier(Enum):
    HOSTILE = "hostile"           # < -60
    UNFRIENDLY = "unfriendly"     # -60 to -20
    NEUTRAL = "neutral"           # -20 to 20
    FRIENDLY = "friendly"         # 20 to 60
    ALLIED = "allied"             # 60 to 80
    INTIMATE = "intimate"         # > 80


class RelationshipChangeReason(Enum):
    DIALOGUE_CHOICE = "dialogue_choice"
    QUEST_COMPLETION = "quest_completion"
    COMBAT_ALLIANCE = "combat_alliance"
    BETRAYAL = "betrayal"
    GIFT = "gift"
    INSULT = "insult"
    FAVOR = "favor"
    RIVALRY = "rivalry"
    ROMANCE = "romance"
    TRAGEDY = "tragedy"


@dataclass
class RelationshipModifier:
    """Modifier for relationship changes"""
    name: str
    base_value: int
    reason: RelationshipChangeReason
    conditions: List[Dict] = field(default_factory=list)
    cooldown_hours: int = 0  # Cooldown between applications
    max_uses: int = -1  # -1 for unlimited


@dataclass
class RelationshipSnapshot:
    """Point-in-time relationship data"""
    player_id: str
    npc_id: str
    npc_name: str
    relationship_value: int
    tier: RelationshipTier
    timestamp: str
    reason: str
    recent_interactions: int  # How many interactions recently
    trend: str  # "increasing", "stable", "decreasing"


class CharacterMemory:
    """Track what NPCs remember about the player"""
    
    def __init__(self, npc_id: str, npc_name: str):
        self.npc_id = npc_id
        self.npc_name = npc_name
        self.memories: List[Dict] = []
        self.preferences: Dict[str, int] = {}  # topic -> interest level
        self.quirks: List[str] = []
        self.favorite_topics: List[str] = []
        self.forbidden_topics: List[str] = []
    
    def add_memory(
        self,
        memory_type: str,
        content: str,
        emotional_weight: int = 0
    ):
        """Add memory for NPC"""
        self.memories.append({
            "type": memory_type,
            "content": content,
            "emotional_weight": emotional_weight,
            "timestamp": datetime.now().isoformat(),
            "recalled_count": 0
        })
    
    def add_preference(self, topic: str, interest_level: int):
        """Add topic preference"""
        self.preferences[topic] = interest_level
    
    def add_quirk(self, quirk: str):
        """Add character quirk"""
        if quirk not in self.quirks:
            self.quirks.append(quirk)
    
    def recall_memories(self, memory_type: Optional[str] = None) -> List[Dict]:
        """Recall memories, optionally filtered by type"""
        memories = self.memories
        if memory_type:
            memories = [m for m in memories if m["type"] == memory_type]
        
        # Mark as recalled
        for m in memories:
            m["recalled_count"] += 1
        
        return memories
    
    def get_emotional_impact(self, memory_type: str) -> int:
        """Calculate emotional impact from memories"""
        matching = [m for m in self.memories if m["type"] == memory_type]
        if not matching:
            return 0
        return sum(m["emotional_weight"] for m in matching) // len(matching)


class RelationshipTracker:
    """Track all relationships between player and NPCs"""
    
    def __init__(self, db_path: str = "relationships.db"):
        self.db_path = db_path
        self.relationships: Dict[str, Dict[str, int]] = {}  # player_id -> npc_id -> value
        self.character_memories: Dict[str, CharacterMemory] = {}
        self.relationship_history: List[RelationshipSnapshot] = []
        self.modifiers: Dict[str, List[RelationshipModifier]] = {}
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT,
            npc_id TEXT,
            npc_name TEXT,
            relationship_value INTEGER,
            tier TEXT,
            timestamp TEXT,
            reason TEXT,
            UNIQUE(player_id, npc_id)
        );
        
        CREATE TABLE IF NOT EXISTS relationship_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT,
            npc_id TEXT,
            old_value INTEGER,
            new_value INTEGER,
            delta INTEGER,
            reason TEXT,
            timestamp TEXT
        );
        
        CREATE TABLE IF NOT EXISTS character_memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT,
            npc_id TEXT,
            memory_type TEXT,
            content TEXT,
            emotional_weight INTEGER,
            timestamp TEXT,
            recalled_count INTEGER DEFAULT 0
        );
        
        CREATE TABLE IF NOT EXISTS npc_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            npc_id TEXT,
            topic TEXT,
            interest_level INTEGER
        );
        """)
        
        conn.commit()
        conn.close()
    
    def initialize_relationship(
        self,
        player_id: str,
        npc_id: str,
        npc_name: str,
        starting_value: int = 0
    ):
        """Initialize relationship with NPC"""
        if player_id not in self.relationships:
            self.relationships[player_id] = {}
        
        self.relationships[player_id][npc_id] = starting_value
        
        # Create character memory
        if npc_id not in self.character_memories:
            self.character_memories[npc_id] = CharacterMemory(npc_id, npc_name)
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO relationships 
            (player_id, npc_id, npc_name, relationship_value, tier, timestamp, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            player_id, npc_id, npc_name,
            starting_value,
            self._get_tier(starting_value).value,
            datetime.now().isoformat(),
            "initialization"
        ))
        conn.commit()
        conn.close()
    
    def modify_relationship(
        self,
        player_id: str,
        npc_id: str,
        delta: int,
        reason: RelationshipChangeReason,
        details: Optional[str] = None
    ) -> int:
        """Modify relationship value"""
        
        if player_id not in self.relationships:
            self.relationships[player_id] = {}
        
        old_value = self.relationships[player_id].get(npc_id, 0)
        new_value = max(-100, min(100, old_value + delta))
        self.relationships[player_id][npc_id] = new_value
        
        # Log to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO relationship_history 
            (player_id, npc_id, old_value, new_value, delta, reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            player_id, npc_id, old_value, new_value, delta,
            reason.value, datetime.now().isoformat()
        ))
        
        cursor.execute("""
            UPDATE relationships
            SET relationship_value = ?, tier = ?, timestamp = ?
            WHERE player_id = ? AND npc_id = ?
        """, (
            new_value,
            self._get_tier(new_value).value,
            datetime.now().isoformat(),
            player_id, npc_id
        ))
        
        conn.commit()
        conn.close()
        
        # Create snapshot
        tier = self._get_tier(new_value)
        snapshot = RelationshipSnapshot(
            player_id=player_id,
            npc_id=npc_id,
            npc_name=self.character_memories.get(npc_id, CharacterMemory(npc_id, "")).npc_name,
            relationship_value=new_value,
            tier=tier,
            timestamp=datetime.now().isoformat(),
            reason=reason.value,
            recent_interactions=1,
            trend="stable"
        )
        self.relationship_history.append(snapshot)
        
        return new_value
    
    def get_relationship(self, player_id: str, npc_id: str) -> int:
        """Get current relationship value"""
        return self.relationships.get(player_id, {}).get(npc_id, 0)
    
    def get_tier(self, player_id: str, npc_id: str) -> RelationshipTier:
        """Get relationship tier"""
        value = self.get_relationship(player_id, npc_id)
        return self._get_tier(value)
    
    def _get_tier(self, value: int) -> RelationshipTier:
        """Determine tier from value"""
        if value < -60:
            return RelationshipTier.HOSTILE
        elif value < -20:
            return RelationshipTier.UNFRIENDLY
        elif value < 20:
            return RelationshipTier.NEUTRAL
        elif value < 60:
            return RelationshipTier.FRIENDLY
        elif value < 80:
            return RelationshipTier.ALLIED
        else:
            return RelationshipTier.INTIMATE
    
    def get_relationship_tiers(self, player_id: str) -> Dict[str, RelationshipTier]:
        """Get all relationship tiers for player"""
        if player_id not in self.relationships:
            return {}
        
        return {
            npc_id: self._get_tier(value)
            for npc_id, value in self.relationships[player_id].items()
        }
    
    def record_memory(
        self,
        npc_id: str,
        memory_type: str,
        content: str,
        emotional_weight: int = 0
    ):
        """Record memory for NPC"""
        if npc_id not in self.character_memories:
            return
        
        character = self.character_memories[npc_id]
        character.add_memory(memory_type, content, emotional_weight)
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO character_memories 
            (npc_id, memory_type, content, emotional_weight, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (npc_id, memory_type, content, emotional_weight, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    def get_character_memory(self, npc_id: str) -> Optional[CharacterMemory]:
        """Get character memory"""
        return self.character_memories.get(npc_id)
    
    def get_relationship_history(
        self,
        player_id: str,
        npc_id: Optional[str] = None,
        days: int = 30
    ) -> List[Dict]:
        """Get relationship change history"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        if npc_id:
            cursor.execute("""
                SELECT player_id, npc_id, old_value, new_value, delta, reason, timestamp
                FROM relationship_history
                WHERE player_id = ? AND npc_id = ? AND timestamp > ?
                ORDER BY timestamp DESC
            """, (player_id, npc_id, cutoff_date))
        else:
            cursor.execute("""
                SELECT player_id, npc_id, old_value, new_value, delta, reason, timestamp
                FROM relationship_history
                WHERE player_id = ? AND timestamp > ?
                ORDER BY timestamp DESC
            """, (player_id, cutoff_date))
        
        history = [
            {
                "player_id": row[0],
                "npc_id": row[1],
                "old_value": row[2],
                "new_value": row[3],
                "delta": row[4],
                "reason": row[5],
                "timestamp": row[6]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return history
    
    def export_relationships(self, player_id: str, output_file: str) -> str:
        """Export all relationships to JSON"""
        
        if player_id not in self.relationships:
            return ""
        
        export_data = {
            "player_id": player_id,
            "relationships": {}
        }
        
        for npc_id, value in self.relationships[player_id].items():
            tier = self._get_tier(value)
            memory = self.character_memories.get(npc_id)
            
            export_data["relationships"][npc_id] = {
                "value": value,
                "tier": tier.value,
                "memories_count": len(memory.memories) if memory else 0,
                "last_modified": datetime.now().isoformat()
            }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return output_file
    
    def generate_relationship_report(self, player_id: str) -> str:
        """Generate relationship report"""
        
        if player_id not in self.relationships:
            return "No relationships found"
        
        report_lines = [
            "═" * 60,
            f"RELATIONSHIP REPORT FOR PLAYER: {player_id}",
            "═" * 60,
            ""
        ]
        
        for npc_id, value in sorted(
            self.relationships[player_id].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            tier = self._get_tier(value)
            memory = self.character_memories.get(npc_id)
            
            report_lines.append(f"\n[{tier.value.upper()}] {memory.npc_name if memory else npc_id}")
            report_lines.append(f"  Value: {value}/100")
            
            if memory:
                if memory.memories:
                    report_lines.append(f"  Memories: {len(memory.memories)}")
                if memory.quirks:
                    report_lines.append(f"  Quirks: {', '.join(memory.quirks)}")
                if memory.favorite_topics:
                    report_lines.append(f"  Likes: {', '.join(memory.favorite_topics)}")
        
        report_lines.append("\n" + "═" * 60)
        return "\n".join(report_lines)
