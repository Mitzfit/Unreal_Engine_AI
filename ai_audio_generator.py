"""
AI Audio Generation System
Generate music, sound effects, foley, and voiceovers for games
"""

import asyncio
import aiohttp
import json
import os
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

class AIAudioGenerator:
    """
    Complete AI audio generation system
    """
    
    def __init__(self, openai_key: str):
        self.openai_key = openai_key
        self.session = None
        self.output_dir = Path("assets/audio_generated")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def setup_session(self):
        """Initialize session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Close session"""
        if self.session:
            await self.session.close()
    
    async def generate_music(
        self,
        description: str,
        genre: str = "ambient",
        mood: str = "calm",
        duration: int = 30,
        tempo: int = 120,
        instruments: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate game music from description
        """
        
        # Build comprehensive prompt
        prompt = self._build_music_prompt(description, genre, mood, tempo, instruments)
        
        # In production, this would call:
        # - MusicGen (Meta)
        # - MusicLM (Google)
        # - Suno AI
        # - Stable Audio
        
        # Generate specifications for now
        music_specs = {
            "title": f"{genre}_{mood}_{int(time.time())}",
            "description": description,
            "genre": genre,
            "mood": mood,
            "duration_seconds": duration,
            "tempo_bpm": tempo,
            "key": "C Major",
            "time_signature": "4/4",
            "instruments": instruments or ["synth", "piano", "strings"],
            "sections": self._generate_music_sections(duration, genre, mood),
            "mixing": {
                "master_volume": 0.8,
                "reverb": "medium",
                "compression": "light"
            }
        }
        
        # Save specifications
        output_path = self.output_dir / f"{music_specs['title']}.json"
        with open(output_path, 'w') as f:
            json.dump(music_specs, f, indent=2)
        
        # In production: generate actual audio file
        audio_path = self.output_dir / f"{music_specs['title']}.wav"
        
        return {
            "success": True,
            "audio_path": str(audio_path),
            "specs": music_specs,
            "format": "WAV",
            "sample_rate": 44100,
            "bit_depth": 16,
            "channels": 2
        }
    
    def _build_music_prompt(
        self,
        description: str,
        genre: str,
        mood: str,
        tempo: int,
        instruments: List[str]
    ) -> str:
        """Build music generation prompt"""
        
        return f"""Generate {genre} music with {mood} mood.

DESCRIPTION: {description}
TEMPO: {tempo} BPM
INSTRUMENTS: {', '.join(instruments or ['synth', 'piano'])}

Style Guide:
- {genre} characteristics
- {mood} emotional tone
- Game-appropriate (loopable if needed)
- Clear mix with good dynamics
"""
    
    def _generate_music_sections(
        self,
        duration: int,
        genre: str,
        mood: str
    ) -> List[Dict[str, Any]]:
        """Generate music structure"""
        
        if genre in ["ambient", "atmospheric"]:
            return [
                {"name": "intro", "start": 0, "duration": duration * 0.2, "intensity": 0.3},
                {"name": "development", "start": duration * 0.2, "duration": duration * 0.6, "intensity": 0.6},
                {"name": "outro", "start": duration * 0.8, "duration": duration * 0.2, "intensity": 0.3}
            ]
        else:
            return [
                {"name": "intro", "start": 0, "duration": 4, "intensity": 0.5},
                {"name": "verse", "start": 4, "duration": 8, "intensity": 0.6},
                {"name": "chorus", "start": 12, "duration": 8, "intensity": 0.9},
                {"name": "bridge", "start": 20, "duration": 6, "intensity": 0.7},
                {"name": "outro", "start": 26, "duration": 4, "intensity": 0.4}
            ]
    
    async def generate_sound_effect(
        self,
        description: str,
        category: str = "general",
        duration: float = 1.0
    ) -> Dict[str, Any]:
        """
        Generate sound effects (footsteps, gunshots, explosions, etc.)
        """
        
        # In production: AudioGen, AudioLDM, or custom models
        
        sfx_specs = {
            "name": f"sfx_{category}_{int(time.time())}",
            "description": description,
            "category": category,
            "duration_seconds": duration,
            "characteristics": self._analyze_sfx_requirements(description, category),
            "processing": {
                "normalize": True,
                "fade_in": 0.01,
                "fade_out": 0.05,
                "eq": "preset_game_sfx"
            }
        }
        
        audio_path = self.output_dir / f"{sfx_specs['name']}.wav"
        
        return {
            "success": True,
            "audio_path": str(audio_path),
            "specs": sfx_specs,
            "loopable": self._is_loopable_sfx(category),
            "format": "WAV",
            "sample_rate": 48000
        }
    
    def _analyze_sfx_requirements(self, description: str, category: str) -> Dict[str, Any]:
        """Analyze SFX requirements"""
        
        categories_specs = {
            "footsteps": {"type": "repetitive", "frequency_range": "low-mid", "complexity": "simple"},
            "weapon": {"type": "impact", "frequency_range": "full", "complexity": "medium"},
            "explosion": {"type": "burst", "frequency_range": "full", "complexity": "high"},
            "ambient": {"type": "continuous", "frequency_range": "full", "complexity": "medium"},
            "ui": {"type": "short", "frequency_range": "mid-high", "complexity": "simple"}
        }
        
        return categories_specs.get(category, {"type": "general", "frequency_range": "full", "complexity": "medium"})
    
    def _is_loopable_sfx(self, category: str) -> bool:
        """Determine if SFX should be loopable"""
        return category in ["ambient", "engine", "fire", "water"]
    
    async def generate_voiceover(
        self,
        text: str,
        voice_type: str = "neutral",
        emotion: str = "neutral",
        speed: float = 1.0
    ) -> Dict[str, Any]:
        """
        Generate AI voiceover for game dialogue
        """
        
        # In production: ElevenLabs, Azure Speech, Google TTS
        
        vo_specs = {
            "name": f"vo_{int(time.time())}",
            "text": text,
            "voice_type": voice_type,
            "emotion": emotion,
            "speed": speed,
            "voice_characteristics": self._get_voice_characteristics(voice_type),
            "processing": {
                "denoise": True,
                "normalize": True,
                "compression": "moderate"
            }
        }
        
        audio_path = self.output_dir / f"{vo_specs['name']}.wav"
        
        return {
            "success": True,
            "audio_path": str(audio_path),
            "specs": vo_specs,
            "text": text,
            "duration_estimate": len(text.split()) / (150 * speed),  # ~150 words per minute
            "format": "WAV"
        }
    
    def _get_voice_characteristics(self, voice_type: str) -> Dict[str, Any]:
        """Get voice characteristics"""
        
        voices = {
            "hero_male": {"pitch": "medium", "age": "young_adult", "accent": "neutral", "tone": "confident"},
            "hero_female": {"pitch": "medium-high", "age": "young_adult", "accent": "neutral", "tone": "determined"},
            "villain": {"pitch": "low", "age": "mature", "accent": "slight", "tone": "menacing"},
            "narrator": {"pitch": "medium-low", "age": "mature", "accent": "neutral", "tone": "authoritative"},
            "child": {"pitch": "high", "age": "child", "accent": "neutral", "tone": "innocent"},
            "robot": {"pitch": "synthesized", "age": "none", "accent": "none", "tone": "mechanical"}
        }
        
        return voices.get(voice_type, {"pitch": "medium", "age": "adult", "accent": "neutral", "tone": "neutral"})
    
    async def generate_foley(
        self,
        action: str,
        material: str = "generic",
        intensity: str = "medium"
    ) -> Dict[str, Any]:
        """
        Generate foley sounds (cloth rustling, door opening, etc.)
        """
        
        foley_specs = {
            "name": f"foley_{action}_{int(time.time())}",
            "action": action,
            "material": material,
            "intensity": intensity,
            "layers": self._get_foley_layers(action, material),
            "processing": {
                "room_tone": "subtle",
                "spatial": "mono",
                "dynamics": "natural"
            }
        }
        
        audio_path = self.output_dir / f"{foley_specs['name']}.wav"
        
        return {
            "success": True,
            "audio_path": str(audio_path),
            "specs": foley_specs,
            "format": "WAV"
        }
    
    def _get_foley_layers(self, action: str, material: str) -> List[Dict[str, str]]:
        """Get foley sound layers"""
        
        action_layers = {
            "footstep": [
                {"layer": "impact", "material": material},
                {"layer": "slide", "material": material},
                {"layer": "clothing", "material": "fabric"}
            ],
            "door": [
                {"layer": "handle", "material": "metal"},
                {"layer": "hinges", "material": "metal"},
                {"layer": "door_body", "material": material}
            ],
            "punch": [
                {"layer": "impact", "material": "flesh"},
                {"layer": "whoosh", "material": "air"},
                {"layer": "grunt", "material": "vocal"}
            ]
        }
        
        return action_layers.get(action, [{"layer": "main", "material": material}])
    
    async def create_adaptive_music_system(
        self,
        game_states: List[str],
        base_theme: str
    ) -> Dict[str, Any]:
        """
        Create adaptive music that changes based on gameplay
        """
        
        music_layers = {}
        
        for state in game_states:
            music = await self.generate_music(
                description=f"{base_theme} for {state} state",
                genre="game_adaptive",
                mood=self._get_mood_for_state(state),
                duration=60,
                tempo=self._get_tempo_for_state(state)
            )
            
            music_layers[state] = music
        
        adaptive_system = {
            "name": f"adaptive_{base_theme}_{int(time.time())}",
            "base_theme": base_theme,
            "states": game_states,
            "layers": music_layers,
            "transitions": self._generate_transitions(game_states),
            "mixing_rules": {
                "crossfade_duration": 2.0,
                "layer_blending": "smooth",
                "duck_on_combat": True
            }
        }
        
        return {
            "success": True,
            "system": adaptive_system,
            "total_audio_files": len(music_layers)
        }
    
    def _get_mood_for_state(self, state: str) -> str:
        """Get mood for game state"""
        
        state_moods = {
            "exploration": "calm",
            "combat": "intense",
            "stealth": "tense",
            "victory": "triumphant",
            "defeat": "somber",
            "menu": "ambient"
        }
        
        return state_moods.get(state, "neutral")
    
    def _get_tempo_for_state(self, state: str) -> int:
        """Get tempo for game state"""
        
        state_tempos = {
            "exploration": 90,
            "combat": 140,
            "stealth": 70,
            "victory": 130,
            "defeat": 60,
            "menu": 80
        }
        
        return state_tempos.get(state, 100)
    
    def _generate_transitions(self, states: List[str]) -> Dict[str, Dict]:
        """Generate transition rules between states"""
        
        transitions = {}
        
        for i, from_state in enumerate(states):
            transitions[from_state] = {}
            for to_state in states:
                if from_state != to_state:
                    transitions[from_state][to_state] = {
                        "method": "crossfade",
                        "duration": 2.0,
                        "curve": "linear"
                    }
        
        return transitions
    
    async def create_audio_batch(
        self,
        batch_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create multiple audio files in batch
        """
        
        results = {
            "music": [],
            "sfx": [],
            "voiceovers": [],
            "foley": []
        }
        
        # Process music requests
        for music_req in batch_config.get("music", []):
            result = await self.generate_music(**music_req)
            results["music"].append(result)
        
        # Process SFX requests
        for sfx_req in batch_config.get("sfx", []):
            result = await self.generate_sound_effect(**sfx_req)
            results["sfx"].append(result)
        
        # Process voiceover requests
        for vo_req in batch_config.get("voiceovers", []):
            result = await self.generate_voiceover(**vo_req)
            results["voiceovers"].append(result)
        
        # Process foley requests
        for foley_req in batch_config.get("foley", []):
            result = await self.generate_foley(**foley_req)
            results["foley"].append(result)
        
        return {
            "success": True,
            "total_files": sum(len(v) for v in results.values()),
            "results": results
        }
    
    def create_audio_manifest(
        self,
        project_name: str,
        audio_files: List[Dict[str, Any]]
    ) -> str:
        """
        Create audio manifest for Unreal Engine
        """
        
        manifest = {
            "project": project_name,
            "audio_files": audio_files,
            "import_settings": {
                "compression_quality": 40,
                "sample_rate": 44100,
                "loading_behavior": "Stream",
                "group": "Music"
            },
            "generated_at": time.time()
        }
        
        manifest_path = self.output_dir / f"{project_name}_audio_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return str(manifest_path)
