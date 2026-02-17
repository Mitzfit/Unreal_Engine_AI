"""
Complete Enhanced Dialogue System Integration
dialogue_complete_system.py - Unified dialogue system with all features
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from dialogue_tree_editor import DialogueTreeEditor, DialogueTreeExporter
from dialogue_voice_generation import AIVoiceGenerator, VoiceLibraryManager, LipSyncGenerator
from dialogue_relationship_system import RelationshipTracker, RelationshipChangeReason, RelationshipTier


@dataclass
class DialogueSessionConfig:
    """Configuration for dialogue session"""
    player_id: str
    npc_id: str
    npc_name: str
    npc_role: str
    include_voice: bool = True
    include_lip_sync: bool = True
    track_relationships: bool = True
    voice_type: str = "narrator"
    emotion_detection: bool = True


class EnhancedDialogueSystem:
    """Complete integrated dialogue system"""
    
    def __init__(
        self,
        projects_dir: str = "dialogue_projects",
        voice_dir: str = "voice_output",
        db_path: str = "dialogue_system.db"
    ):
        self.editor = DialogueTreeEditor(projects_dir)
        self.voice_generator = AIVoiceGenerator(output_dir=voice_dir)
        self.voice_library = VoiceLibraryManager(voice_dir)
        self.relationship_tracker = RelationshipTracker(db_path)
        self.active_sessions: Dict[str, Dict] = {}
    
    async def create_npc_dialogue(
        self,
        npc_name: str,
        npc_role: str,
        dialogue_topic: str,
        game_context: str = "fantasy",
        voice_type: str = "narrator",
        generate_voice: bool = True
    ) -> Dict:
        """Create complete NPC dialogue with visual tree and voice"""
        
        # Create dialogue tree project
        project_id = self.editor.create_project(
            project_name=f"{npc_name}_Dialogue",
            npc_name=npc_name,
            npc_role=npc_role,
            game_context=game_context
        )
        
        # Add root dialogue node
        self.editor.add_dialogue_node(
            project_id=project_id,
            node_id="greeting",
            speaker=npc_name,
            text=f"Greetings, traveler. I am {npc_name}, {npc_role}.",
            dialogue_type="statement",
            emotion="neutral",
            x=0, y=0,
            voice_type=voice_type
        )
        
        # Add sample dialogue branches
        # Branch 1: Friendly
        self.editor.add_dialogue_node(
            project_id=project_id,
            node_id="friendly_response",
            speaker=npc_name,
            text="It's always good to meet new people. What brings you here?",
            dialogue_type="question",
            emotion="happy",
            x=300, y=-200,
            voice_type=voice_type
        )
        
        # Branch 2: Suspicious
        self.editor.add_dialogue_node(
            project_id=project_id,
            node_id="suspicious_response",
            speaker=npc_name,
            text="I'm not sure I trust you. State your business.",
            dialogue_type="question",
            emotion="suspicious",
            x=-300, y=-200,
            voice_type=voice_type
        )
        
        # Add choices from greeting
        self.editor.add_choice(
            project_id=project_id,
            from_node_id="greeting",
            choice_id="greet_friendly",
            choice_text="You seem like an honorable person.",
            to_node_id="friendly_response",
            effects=[{"type": "relationship", "key": npc_name, "value": 10}]
        )
        
        self.editor.add_choice(
            project_id=project_id,
            from_node_id="greeting",
            choice_id="greet_suspicious",
            choice_text="I don't know if I can trust you.",
            to_node_id="suspicious_response",
            effects=[{"type": "relationship", "key": npc_name, "value": -5}]
        )
        
        # Generate voice for all nodes if enabled
        voice_files = {}
        if generate_voice:
            project = self.editor.projects[project_id]
            texts_to_voice = [
                (node["text"], voice_type, node.get("emotion", "neutral"))
                for node in project.get("nodes", {}).values()
            ]
            
            voice_data_list = await self.voice_generator.generate_batch_speech(texts_to_voice)
            
            for idx, (node_id, node) in enumerate(project.get("nodes", {}).items()):
                if idx < len(voice_data_list):
                    voice_data = voice_data_list[idx]
                    node["audio_file"] = voice_data.audio_file
                    voice_files[node_id] = voice_data
                    self.voice_library.add_voice(voice_data)
        
        # Validate tree
        validation_issues = self.editor.validate_tree(project_id)
        
        return {
            "project_id": project_id,
            "npc_name": npc_name,
            "npc_role": npc_role,
            "voice_files": voice_files,
            "validation_issues": validation_issues,
            "nodes_count": len(self.editor.projects[project_id].get("nodes", {}))
        }
    
    async def start_dialogue_session(
        self,
        config: DialogueSessionConfig,
        project_id: str
    ) -> str:
        """Start a dialogue session with NPC"""
        
        session_id = f"{config.player_id}_{config.npc_id}_{__import__('uuid').uuid4().hex[:8]}"
        
        # Initialize relationship if tracking
        if config.track_relationships:
            self.relationship_tracker.initialize_relationship(
                config.player_id,
                config.npc_id,
                config.npc_name
            )
        
        # Load dialogue project
        project = self.editor.projects.get(project_id)
        if not project:
            return ""
        
        session_data = {
            "session_id": session_id,
            "config": {
                "player_id": config.player_id,
                "npc_id": config.npc_id,
                "npc_name": config.npc_name,
                "include_voice": config.include_voice,
                "include_lip_sync": config.include_lip_sync,
                "track_relationships": config.track_relationships
            },
            "project_id": project_id,
            "current_node": None,
            "dialogue_history": [],
            "relationship_changes": [],
            "start_time": __import__('datetime').datetime.now().isoformat()
        }
        
        self.active_sessions[session_id] = session_data
        
        return session_id
    
    async def progress_dialogue(
        self,
        session_id: str,
        choice_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Progress to next dialogue node"""
        
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        project_id = session["project_id"]
        project = self.editor.projects.get(project_id)
        
        if not project:
            return None
        
        nodes = project.get("nodes", {})
        
        # Get current or first node
        if session["current_node"] is None:
            current_node_id = list(nodes.keys())[0] if nodes else None
        else:
            current_node_id = session["current_node"]
        
        if not current_node_id or current_node_id not in nodes:
            return None
        
        current_node = nodes[current_node_id]
        
        # Handle choice
        next_node_id = None
        if choice_id:
            for choice in current_node.get("choices", []):
                if choice["choice_id"] == choice_id:
                    next_node_id = choice.get("next_node_id")
                    
                    # Apply effects
                    if session["config"]["track_relationships"]:
                        for effect in choice.get("effects", []):
                            if effect["type"] == "relationship":
                                self.relationship_tracker.modify_relationship(
                                    session["config"]["player_id"],
                                    session["config"]["npc_id"],
                                    effect.get("value", 0),
                                    RelationshipChangeReason.DIALOGUE_CHOICE,
                                    f"Choice: {choice['text']}"
                                )
                                session["relationship_changes"].append({
                                    "choice": choice["text"],
                                    "delta": effect.get("value", 0)
                                })
                    break
        
        # Add to history
        session["dialogue_history"].append({
            "node_id": current_node_id,
            "speaker": current_node.get("speaker", ""),
            "text": current_node.get("text", ""),
            "emotion": current_node.get("emotion", "neutral"),
            "timestamp": __import__('datetime').datetime.now().isoformat()
        })
        
        # Move to next node
        if next_node_id and next_node_id in nodes:
            next_node = nodes[next_node_id]
            session["current_node"] = next_node_id
            
            # Prepare response
            response = {
                "node_id": next_node_id,
                "speaker": next_node.get("speaker", ""),
                "text": next_node.get("text", ""),
                "emotion": next_node.get("emotion", "neutral"),
                "voice_type": next_node.get("voice_type", "narrator"),
                "choices": [
                    {
                        "choice_id": c["choice_id"],
                        "text": c["text"]
                    }
                    for c in next_node.get("choices", [])
                ]
            }
            
            # Add voice and lip sync if enabled
            if session["config"]["include_voice"] and next_node.get("audio_file"):
                response["audio_file"] = next_node["audio_file"]
            
            if session["config"]["include_lip_sync"] and next_node.get("audio_file"):
                # Find corresponding voice data
                for voice in self.voice_library.search_by_text(next_node.get("text", "")):
                    if voice.audio_id:
                        frames = LipSyncGenerator.interpolate_phonemes(voice.phonemes)
                        response["lip_sync_frames"] = frames
                        break
            
            return response
        
        return None
    
    def end_dialogue_session(self, session_id: str) -> Dict:
        """End dialogue session and return summary"""
        
        if session_id not in self.active_sessions:
            return {}
        
        session = self.active_sessions[session_id]
        
        summary = {
            "session_id": session_id,
            "player_id": session["config"]["player_id"],
            "npc_name": session["config"]["npc_name"],
            "dialogue_count": len(session["dialogue_history"]),
            "relationship_changes": session.get("relationship_changes", []),
            "end_time": __import__('datetime').datetime.now().isoformat()
        }
        
        if session["config"]["track_relationships"]:
            final_relationship = self.relationship_tracker.get_relationship(
                session["config"]["player_id"],
                session["config"]["npc_id"]
            )
            final_tier = self.relationship_tracker.get_tier(
                session["config"]["player_id"],
                session["config"]["npc_id"]
            )
            summary["final_relationship_value"] = final_relationship
            summary["final_relationship_tier"] = final_tier.value
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        return summary
    
    def export_dialogue_project(
        self,
        project_id: str,
        export_format: str = "unreal",
        output_dir: str = "dialogue_exports"
    ) -> str:
        """Export dialogue project to game engine format"""
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        project = self.editor.projects.get(project_id)
        
        if not project:
            return ""
        
        output_file = Path(output_dir) / f"dialogue_{project_id}_{export_format}.json"
        
        if export_format == "unreal":
            DialogueTreeExporter.export_to_unreal(project, str(output_file))
        elif export_format == "unity":
            DialogueTreeExporter.export_to_unity(project, str(output_file))
        elif export_format == "godot":
            DialogueTreeExporter.export_to_godot(project, str(output_file))
        
        return str(output_file)
    
    def get_system_status(self) -> Dict:
        """Get system status and statistics"""
        
        return {
            "projects_count": len(self.editor.projects),
            "active_sessions": len(self.active_sessions),
            "voice_files_generated": len(self.voice_generator.generated_audio),
            "relationships_tracked": len(self.relationship_tracker.relationships)
        }


async def demo_enhanced_dialogue():
    """Demonstration of enhanced dialogue system"""
    
    print("\n" + "="*70)
    print("ENHANCED DIALOGUE SYSTEM DEMONSTRATION")
    print("="*70)
    
    system = EnhancedDialogueSystem()
    
    # Create NPC dialogue
    print("\n🎭 Creating NPC dialogue tree with voice generation...")
    dialogue_result = await system.create_npc_dialogue(
        npc_name="Elara",
        npc_role="Wise Mage",
        dialogue_topic="Ancient Magic",
        voice_type="elder"
    )
    
    print(f"✓ Created dialogue project: {dialogue_result['project_id']}")
    print(f"✓ Generated voice for {len(dialogue_result['voice_files'])} nodes")
    print(f"✓ Total dialogue nodes: {dialogue_result['nodes_count']}")
    
    if dialogue_result['validation_issues']:
        print(f"⚠ Validation issues: {dialogue_result['validation_issues']}")
    
    # Start dialogue session
    print("\n💬 Starting dialogue session...")
    config = DialogueSessionConfig(
        player_id="player_001",
        npc_id="elara_001",
        npc_name="Elara",
        npc_role="Wise Mage",
        include_voice=True,
        include_lip_sync=True,
        track_relationships=True,
        voice_type="elder"
    )
    
    session_id = await system.start_dialogue_session(config, dialogue_result['project_id'])
    print(f"✓ Session started: {session_id}")
    
    # Progress through dialogue
    print("\n📖 Progressing through dialogue...")
    response = await system.progress_dialogue(session_id)
    
    if response:
        print(f"\n{response['speaker']}: {response['text']}")
        print(f"Emotion: {response['emotion']}")
        print(f"Available choices:")
        for choice in response['choices']:
            print(f"  [{choice['choice_id']}] {choice['text']}")
    
    # Make a choice
    print("\n🎯 Making a dialogue choice...")
    if response and response['choices']:
        choice_id = response['choices'][0]['choice_id']
        next_response = await system.progress_dialogue(session_id, choice_id)
        
        if next_response:
            print(f"\n{next_response['speaker']}: {next_response['text']}")
            print(f"Emotion: {next_response['emotion']}")
    
    # End session
    print("\n🏁 Ending dialogue session...")
    session_summary = system.end_dialogue_session(session_id)
    
    print(f"\n📊 Session Summary:")
    print(f"  Dialogue exchanges: {session_summary['dialogue_count']}")
    print(f"  Relationship changes: {session_summary['relationship_changes']}")
    if 'final_relationship_tier' in session_summary:
        print(f"  Final relationship tier: {session_summary['final_relationship_tier']}")
    
    # Export dialogue
    print("\n💾 Exporting dialogue project...")
    export_path = system.export_dialogue_project(
        dialogue_result['project_id'],
        export_format="unreal"
    )
    print(f"✓ Exported to: {export_path}")
    
    # System status
    print("\n📈 System Status:")
    status = system.get_system_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(demo_enhanced_dialogue())
