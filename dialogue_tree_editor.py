"""
Enhanced Dialogue System with Visual Tree Editor
dialogue_tree_editor.py - Visual dialogue tree editing and management
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid


class NodePosition(Enum):
    """Node positioning in visual tree"""
    X_OFFSET = 300
    Y_OFFSET = 200


@dataclass
class VisualNode:
    """Node with visual properties for the dialogue tree editor"""
    node_id: str
    x: float
    y: float
    width: float = 200
    height: float = 100
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DialogueTreeVisual:
    """Visual representation of dialogue tree"""
    tree_id: str
    nodes_visual: Dict[str, VisualNode] = field(default_factory=dict)
    connections: List[Dict] = field(default_factory=list)  # {"from": id, "to": id, "label": text}
    zoom: float = 1.0
    pan_x: float = 0.0
    pan_y: float = 0.0
    
    def add_node_visual(self, node_id: str, x: float, y: float):
        """Add visual node to tree"""
        self.nodes_visual[node_id] = VisualNode(node_id, x, y)
    
    def connect_nodes(self, from_id: str, to_id: str, label: str = ""):
        """Create visual connection between nodes"""
        self.connections.append({
            "from": from_id,
            "to": to_id,
            "label": label,
            "id": f"{from_id}_to_{to_id}"
        })
    
    def remove_connection(self, from_id: str, to_id: str):
        """Remove connection between nodes"""
        self.connections = [
            c for c in self.connections 
            if not (c["from"] == from_id and c["to"] == to_id)
        ]
    
    def to_dict(self) -> Dict:
        return {
            "tree_id": self.tree_id,
            "nodes_visual": {nid: n.to_dict() for nid, n in self.nodes_visual.items()},
            "connections": self.connections,
            "zoom": self.zoom,
            "pan_x": self.pan_x,
            "pan_y": self.pan_y
        }


class DialogueTreeEditor:
    """Visual dialogue tree editor for creating/editing conversations"""
    
    def __init__(self, output_dir: str = "dialogue_projects"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.projects: Dict[str, Dict[str, Any]] = {}
        self.visuals: Dict[str, DialogueTreeVisual] = {}
        self._load_projects()
    
    def create_project(
        self,
        project_name: str,
        npc_name: str,
        npc_role: str,
        game_context: str = "fantasy"
    ) -> str:
        """Create new dialogue project"""
        project_id = str(uuid.uuid4())[:8]
        
        project_data = {
            "project_id": project_id,
            "project_name": project_name,
            "npc_name": npc_name,
            "npc_role": npc_role,
            "game_context": game_context,
            "nodes": {},
            "metadata": {
                "created_at": str(__import__('datetime').datetime.now()),
                "last_modified": str(__import__('datetime').datetime.now()),
                "version": 1.0
            }
        }
        
        self.projects[project_id] = project_data
        
        # Create visual tree
        visual_tree = DialogueTreeVisual(project_id)
        self.visuals[project_id] = visual_tree
        
        self._save_project(project_id)
        return project_id
    
    def add_dialogue_node(
        self,
        project_id: str,
        node_id: str,
        speaker: str,
        text: str,
        dialogue_type: str = "statement",
        emotion: str = "neutral",
        x: float = 0,
        y: float = 0,
        audio_file: Optional[str] = None,
        portrait: Optional[str] = None,
        voice_type: str = "narrator"
    ) -> bool:
        """Add node to dialogue tree"""
        
        if project_id not in self.projects:
            return False
        
        node_data = {
            "node_id": node_id,
            "speaker": speaker,
            "text": text,
            "dialogue_type": dialogue_type,
            "emotion": emotion,
            "audio_file": audio_file,
            "portrait": portrait,
            "voice_type": voice_type,
            "choices": [],
            "conditions": [],
            "effects": [],
            "metadata": {
                "created_at": str(__import__('datetime').datetime.now())
            }
        }
        
        self.projects[project_id]["nodes"][node_id] = node_data
        
        # Add visual node
        if project_id in self.visuals:
            self.visuals[project_id].add_node_visual(node_id, x, y)
        
        self._save_project(project_id)
        return True
    
    def add_choice(
        self,
        project_id: str,
        from_node_id: str,
        choice_id: str,
        choice_text: str,
        to_node_id: str,
        conditions: Optional[List[Dict]] = None,
        effects: Optional[List[Dict]] = None
    ) -> bool:
        """Add choice to a dialogue node"""
        
        if project_id not in self.projects:
            return False
        
        if from_node_id not in self.projects[project_id]["nodes"]:
            return False
        
        choice_data = {
            "choice_id": choice_id,
            "text": choice_text,
            "next_node_id": to_node_id,
            "conditions": conditions or [],
            "effects": effects or []
        }
        
        self.projects[project_id]["nodes"][from_node_id]["choices"].append(choice_data)
        
        # Add visual connection
        if project_id in self.visuals:
            self.visuals[project_id].connect_nodes(from_node_id, to_node_id, choice_text)
        
        self._save_project(project_id)
        return True
    
    def add_condition(
        self,
        project_id: str,
        node_id: str,
        condition_type: str,
        key: str,
        operator: str,
        value: Any
    ) -> bool:
        """Add condition to node"""
        
        if project_id not in self.projects:
            return False
        
        if node_id not in self.projects[project_id]["nodes"]:
            return False
        
        condition = {
            "type": condition_type,
            "key": key,
            "operator": operator,
            "value": value
        }
        
        self.projects[project_id]["nodes"][node_id]["conditions"].append(condition)
        self._save_project(project_id)
        return True
    
    def add_effect(
        self,
        project_id: str,
        node_id: str,
        effect_type: str,
        key: str,
        value: Any
    ) -> bool:
        """Add effect to node"""
        
        if project_id not in self.projects:
            return False
        
        if node_id not in self.projects[project_id]["nodes"]:
            return False
        
        effect = {
            "type": effect_type,
            "key": key,
            "value": value
        }
        
        self.projects[project_id]["nodes"][node_id]["effects"].append(effect)
        self._save_project(project_id)
        return True
    
    def get_project_json(self, project_id: str) -> Optional[str]:
        """Export project as JSON"""
        if project_id not in self.projects:
            return None
        return json.dumps(self.projects[project_id], indent=2)
    
    def get_visual_tree_json(self, project_id: str) -> Optional[str]:
        """Export visual tree layout"""
        if project_id not in self.visuals:
            return None
        return json.dumps(self.visuals[project_id].to_dict(), indent=2)
    
    def validate_tree(self, project_id: str) -> List[str]:
        """Validate dialogue tree integrity"""
        if project_id not in self.projects:
            return ["Project not found"]
        
        issues = []
        project = self.projects[project_id]
        nodes = project.get("nodes", {})
        
        if not nodes:
            issues.append("No nodes in tree")
            return issues
        
        # Check for unreachable nodes
        visited = set()
        to_visit = [list(nodes.keys())[0]] if nodes else []
        
        while to_visit:
            node_id = to_visit.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            
            node = nodes.get(node_id)
            if node:
                for choice in node.get("choices", []):
                    next_id = choice.get("next_node_id")
                    if next_id and next_id not in visited:
                        if next_id in nodes:
                            to_visit.append(next_id)
                        else:
                            issues.append(f"Choice references non-existent node: {next_id}")
        
        unreachable = set(nodes.keys()) - visited
        for node_id in unreachable:
            issues.append(f"Node unreachable: {node_id}")
        
        return issues
    
    def _save_project(self, project_id: str):
        """Save project to disk"""
        if project_id not in self.projects:
            return
        
        project_file = self.output_dir / f"{project_id}.json"
        with open(project_file, 'w') as f:
            json.dump(self.projects[project_id], f, indent=2)
        
        # Also save visual layout
        if project_id in self.visuals:
            visual_file = self.output_dir / f"{project_id}_visual.json"
            with open(visual_file, 'w') as f:
                json.dump(self.visuals[project_id].to_dict(), f, indent=2)
    
    def _load_projects(self):
        """Load projects from disk"""
        for project_file in self.output_dir.glob("*.json"):
            if "_visual" not in project_file.name:
                with open(project_file, 'r') as f:
                    project = json.load(f)
                    project_id = project.get("project_id")
                    if project_id:
                        self.projects[project_id] = project
                        
                        # Load visual layout
                        visual_file = self.output_dir / f"{project_id}_visual.json"
                        if visual_file.exists():
                            with open(visual_file, 'r') as vf:
                                visual_data = json.load(vf)
                                visual = DialogueTreeVisual(project_id)
                                visual.zoom = visual_data.get("zoom", 1.0)
                                visual.pan_x = visual_data.get("pan_x", 0.0)
                                visual.pan_y = visual_data.get("pan_y", 0.0)
                                
                                for nid, ndata in visual_data.get("nodes_visual", {}).items():
                                    visual.nodes_visual[nid] = VisualNode(
                                        ndata["node_id"],
                                        ndata["x"],
                                        ndata["y"],
                                        ndata.get("width", 200),
                                        ndata.get("height", 100)
                                    )
                                
                                visual.connections = visual_data.get("connections", [])
                                self.visuals[project_id] = visual


class DialogueTreeExporter:
    """Export dialogue trees to various game engines and formats"""
    
    @staticmethod
    def export_to_unreal(project_data: Dict, output_path: str) -> str:
        """Export to Unreal Engine format"""
        unreal_structure = {
            "DialogueTree": {
                "NPCName": project_data.get("npc_name", "NPC"),
                "NPCRole": project_data.get("npc_role", ""),
                "Nodes": []
            }
        }
        
        for node_id, node_data in project_data.get("nodes", {}).items():
            unreal_node = {
                "NodeID": node_id,
                "Speaker": node_data.get("speaker", ""),
                "Text": node_data.get("text", ""),
                "DialogueType": node_data.get("dialogue_type", "Statement"),
                "Emotion": node_data.get("emotion", "Neutral"),
                "VoiceType": node_data.get("voice_type", "Narrator"),
                "Choices": [],
                "Effects": node_data.get("effects", []),
                "AudioFile": node_data.get("audio_file", "")
            }
            
            for choice in node_data.get("choices", []):
                unreal_node["Choices"].append({
                    "ChoiceID": choice.get("choice_id", ""),
                    "Text": choice.get("text", ""),
                    "NextNodeID": choice.get("next_node_id", "")
                })
            
            unreal_structure["DialogueTree"]["Nodes"].append(unreal_node)
        
        with open(output_path, 'w') as f:
            json.dump(unreal_structure, f, indent=2)
        
        return output_path
    
    @staticmethod
    def export_to_unity(project_data: Dict, output_path: str) -> str:
        """Export to Unity format"""
        unity_structure = {
            "dialogue": {
                "name": project_data.get("project_name", "Dialogue"),
                "npc": project_data.get("npc_name", "NPC"),
                "dialogues": []
            }
        }
        
        for node_id, node_data in project_data.get("nodes", {}).items():
            unity_dialogue = {
                "id": node_id,
                "speaker": node_data.get("speaker", ""),
                "text": node_data.get("text", ""),
                "type": node_data.get("dialogue_type", "statement"),
                "emotion": node_data.get("emotion", "neutral"),
                "voiceFile": node_data.get("audio_file", ""),
                "choices": []
            }
            
            for choice in node_data.get("choices", []):
                unity_dialogue["choices"].append({
                    "id": choice.get("choice_id", ""),
                    "text": choice.get("text", ""),
                    "next": choice.get("next_node_id", "")
                })
            
            unity_structure["dialogue"]["dialogues"].append(unity_dialogue)
        
        with open(output_path, 'w') as f:
            json.dump(unity_structure, f, indent=2)
        
        return output_path
    
    @staticmethod
    def export_to_godot(project_data: Dict, output_path: str) -> str:
        """Export to Godot format"""
        godot_structure = {
            "res://dialogue/": {
                "name": project_data.get("npc_name", "NPC"),
                "entries": []
            }
        }
        
        for node_id, node_data in project_data.get("nodes", {}).items():
            entry = {
                "id": node_id,
                "speaker": node_data.get("speaker", ""),
                "text": node_data.get("text", ""),
                "type": node_data.get("dialogue_type", "statement"),
                "emotion": node_data.get("emotion", "neutral"),
                "next": [],
                "voice": node_data.get("voice_type", "narrator")
            }
            
            for choice in node_data.get("choices", []):
                entry["next"].append({
                    "text": choice.get("text", ""),
                    "target": choice.get("next_node_id", "")
                })
            
            godot_structure["res://dialogue/"]["entries"].append(entry)
        
        with open(output_path, 'w') as f:
            json.dump(godot_structure, f, indent=2)
        
        return output_path
