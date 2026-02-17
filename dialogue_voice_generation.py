"""
AI Voice Generation and Lip Sync System
dialogue_voice_generation.py - Text-to-speech with lip sync data
"""

import json
import asyncio
import base64
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib


class VoiceGender(Enum):
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class VoiceProvider(Enum):
    GOOGLE = "google"
    AZURE = "azure"
    ELEVEN_LABS = "eleven_labs"
    FESTIVAL = "festival"


@dataclass
class LipSyncPhoneme:
    """Phoneme for lip sync animation"""
    phoneme: str  # "A", "E", "I", "O", "U", "Closed", "M", "L"
    start_time: float  # In seconds
    end_time: float
    confidence: float  # 0.0 to 1.0


@dataclass
class VoiceAudioData:
    """Generated voice audio with metadata"""
    audio_id: str
    text: str
    audio_file: str
    duration: float
    sample_rate: int = 44100
    bit_depth: int = 16
    channels: int = 1
    phonemes: List[LipSyncPhoneme] = None
    emotion: str = "neutral"
    voice_type: str = "narrator"
    
    def __post_init__(self):
        if self.phonemes is None:
            self.phonemes = []
    
    def to_dict(self):
        return {
            "audio_id": self.audio_id,
            "text": self.text,
            "audio_file": self.audio_file,
            "duration": self.duration,
            "sample_rate": self.sample_rate,
            "bit_depth": self.bit_depth,
            "channels": self.channels,
            "phonemes": [
                {
                    "phoneme": p.phoneme,
                    "start_time": p.start_time,
                    "end_time": p.end_time,
                    "confidence": p.confidence
                }
                for p in self.phonemes
            ],
            "emotion": self.emotion,
            "voice_type": self.voice_type
        }


class VoiceProfiler:
    """Store and manage voice profiles"""
    
    VOICE_PROFILES = {
        "hero_male": {
            "pitch": 1.0,
            "speed": 0.95,
            "emotion_map": {
                "happy": 1.1,
                "sad": 0.8,
                "angry": 1.2,
                "scared": 0.7,
                "neutral": 1.0
            }
        },
        "hero_female": {
            "pitch": 1.3,
            "speed": 1.0,
            "emotion_map": {
                "happy": 1.15,
                "sad": 0.75,
                "angry": 1.25,
                "scared": 0.65,
                "neutral": 1.0
            }
        },
        "villain": {
            "pitch": 0.8,
            "speed": 0.9,
            "emotion_map": {
                "happy": 0.95,
                "sad": 0.85,
                "angry": 1.3,
                "scared": 0.6,
                "neutral": 1.0
            }
        },
        "elder": {
            "pitch": 0.7,
            "speed": 0.8,
            "emotion_map": {
                "happy": 0.9,
                "sad": 0.8,
                "angry": 1.0,
                "scared": 0.7,
                "neutral": 1.0
            }
        },
        "merchant": {
            "pitch": 1.0,
            "speed": 1.05,
            "emotion_map": {
                "happy": 1.2,
                "sad": 0.7,
                "angry": 1.1,
                "scared": 0.8,
                "neutral": 1.0
            }
        },
        "child": {
            "pitch": 1.5,
            "speed": 1.1,
            "emotion_map": {
                "happy": 1.3,
                "sad": 0.6,
                "angry": 1.2,
                "scared": 0.5,
                "neutral": 1.0
            }
        }
    }
    
    @staticmethod
    def get_profile(voice_type: str) -> Dict:
        """Get voice profile"""
        return VoiceProfiler.VOICE_PROFILES.get(voice_type, VoiceProfiler.VOICE_PROFILES["hero_male"])
    
    @staticmethod
    def apply_emotion(base_speed: float, voice_type: str, emotion: str) -> float:
        """Apply emotion modifier to voice"""
        profile = VoiceProfiler.get_profile(voice_type)
        emotion_map = profile.get("emotion_map", {})
        modifier = emotion_map.get(emotion, 1.0)
        return base_speed * modifier


class LipSyncGenerator:
    """Generate phoneme data for lip sync animation"""
    
    # Basic phoneme mapping
    PHONEME_MAP = {
        'a': 'A', 'e': 'E', 'i': 'I', 'o': 'O', 'u': 'U',
        'b': 'M', 'p': 'M', 'm': 'M',
        'l': 'L', 'r': 'L',
        'f': 'L', 'v': 'L',
        'g': 'E', 'k': 'E',
        'n': 'L', 'd': 'L', 't': 'L',
        's': 'E', 'z': 'E',
        'h': 'E', 'w': 'O'
    }
    
    @staticmethod
    def generate_phonemes(text: str, duration: float) -> List[LipSyncPhoneme]:
        """Generate phoneme sequence from text"""
        phonemes = []
        text_lower = text.lower()
        
        # Remove non-alphabetic characters
        chars = [c for c in text_lower if c.isalpha()]
        
        if not chars or duration == 0:
            return phonemes
        
        time_per_char = duration / len(chars)
        current_time = 0.0
        
        for char in chars:
            phoneme = LipSyncGenerator.PHONEME_MAP.get(char, 'E')
            
            phonemes.append(LipSyncPhoneme(
                phoneme=phoneme,
                start_time=current_time,
                end_time=current_time + time_per_char,
                confidence=0.95
            ))
            
            current_time += time_per_char
        
        return phonemes
    
    @staticmethod
    def interpolate_phonemes(phonemes: List[LipSyncPhoneme], frame_rate: int = 30) -> List[Dict]:
        """Interpolate phonemes for animation frames"""
        frames = []
        
        if not phonemes:
            return frames
        
        frame_duration = 1.0 / frame_rate
        current_frame = 0
        current_time = 0.0
        
        while current_time < phonemes[-1].end_time:
            # Find active phoneme
            active_phoneme = None
            for p in phonemes:
                if p.start_time <= current_time < p.end_time:
                    active_phoneme = p
                    break
            
            # Get next phoneme
            next_phoneme = None
            for p in phonemes:
                if p.start_time >= current_time:
                    next_phoneme = p
                    break
            
            current_phoneme = active_phoneme or phonemes[0]
            
            # Blend between phonemes
            blend_factor = 0.0
            if next_phoneme and active_phoneme:
                total_duration = next_phoneme.start_time - active_phoneme.end_time
                if total_duration > 0:
                    blend_factor = min(1.0, (current_time - active_phoneme.end_time) / total_duration)
            
            frames.append({
                "frame": current_frame,
                "time": current_time,
                "phoneme": current_phoneme.phoneme,
                "next_phoneme": next_phoneme.phoneme if next_phoneme else current_phoneme.phoneme,
                "blend": blend_factor
            })
            
            current_time += frame_duration
            current_frame += 1
        
        return frames


class AIVoiceGenerator:
    """Generate AI voice audio with lip sync data"""
    
    def __init__(
        self,
        provider: VoiceProvider = VoiceProvider.GOOGLE,
        api_key: Optional[str] = None,
        output_dir: str = "voice_output"
    ):
        self.provider = provider
        self.api_key = api_key
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.generated_audio = {}
    
    async def generate_speech(
        self,
        text: str,
        voice_type: str = "hero_male",
        emotion: str = "neutral",
        language: str = "en-US"
    ) -> VoiceAudioData:
        """Generate speech audio"""
        
        audio_id = hashlib.md5(f"{text}{voice_type}{emotion}".encode()).hexdigest()[:8]
        profile = VoiceProfiler.get_profile(voice_type)
        
        # Estimated duration (approximately 0.15 seconds per word)
        word_count = len(text.split())
        base_duration = word_count * 0.15
        emotion_speed = VoiceProfiler.apply_emotion(1.0, voice_type, emotion)
        estimated_duration = base_duration / emotion_speed
        
        # Generate phonemes for lip sync
        phonemes = LipSyncGenerator.generate_phonemes(text, estimated_duration)
        
        # Create audio filename
        audio_file = f"voice_{audio_id}.wav"
        audio_path = self.output_dir / audio_file
        
        # Simulate audio generation (in production, this would call TTS API)
        await self._mock_generate_audio(str(audio_path), text, estimated_duration)
        
        voice_data = VoiceAudioData(
            audio_id=audio_id,
            text=text,
            audio_file=str(audio_path),
            duration=estimated_duration,
            phonemes=phonemes,
            emotion=emotion,
            voice_type=voice_type
        )
        
        self.generated_audio[audio_id] = voice_data
        
        return voice_data
    
    async def generate_batch_speech(
        self,
        texts: List[Tuple[str, str, str]],  # (text, voice_type, emotion)
        language: str = "en-US"
    ) -> List[VoiceAudioData]:
        """Generate multiple speech files"""
        
        tasks = [
            self.generate_speech(text, voice_type, emotion, language)
            for text, voice_type, emotion in texts
        ]
        
        return await asyncio.gather(*tasks)
    
    async def _mock_generate_audio(self, filepath: str, text: str, duration: float):
        """Mock audio generation"""
        # In production, this would call actual TTS API
        # For now, just create a placeholder
        await asyncio.sleep(0.1)  # Simulate API call
        
        # Create simple WAV header (simulation)
        wav_data = self._create_wav_header(duration)
        
        with open(filepath, 'wb') as f:
            f.write(wav_data)
    
    def _create_wav_header(self, duration: float, sample_rate: int = 44100) -> bytes:
        """Create simple WAV file header"""
        import struct
        
        num_samples = int(duration * sample_rate)
        bytes_per_sample = 2  # 16-bit
        num_channels = 1
        byte_rate = sample_rate * num_channels * bytes_per_sample
        block_align = num_channels * bytes_per_sample
        
        # WAV header
        header = b'RIFF'
        header += struct.pack('<I', 36 + num_samples * bytes_per_sample)
        header += b'WAVE'
        
        # fmt sub-chunk
        header += b'fmt '
        header += struct.pack('<I', 16)
        header += struct.pack('<H', 1)  # PCM format
        header += struct.pack('<H', num_channels)
        header += struct.pack('<I', sample_rate)
        header += struct.pack('<I', byte_rate)
        header += struct.pack('<H', block_align)
        header += struct.pack('<H', 16)  # bits per sample
        
        # data sub-chunk
        header += b'data'
        header += struct.pack('<I', num_samples * bytes_per_sample)
        
        return header
    
    def export_voice_metadata(self, audio_id: str, output_file: str) -> str:
        """Export voice audio metadata including lip sync data"""
        
        if audio_id not in self.generated_audio:
            return ""
        
        voice_data = self.generated_audio[audio_id]
        
        # Generate animation frames
        frames = LipSyncGenerator.interpolate_phonemes(
            voice_data.phonemes,
            frame_rate=30
        )
        
        export_data = {
            "audio": voice_data.to_dict(),
            "lip_sync_frames": frames,
            "animation_metadata": {
                "frame_rate": 30,
                "total_frames": len(frames),
                "duration": voice_data.duration,
                "format": "phoneme_based"
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return output_file
    
    def export_for_unreal(self, audio_id: str, output_file: str) -> str:
        """Export audio and lip sync data for Unreal Engine"""
        
        if audio_id not in self.generated_audio:
            return ""
        
        voice_data = self.generated_audio[audio_id]
        frames = LipSyncGenerator.interpolate_phonemes(voice_data.phonemes)
        
        unreal_data = {
            "DialogueVoiceAsset": {
                "AudioFile": voice_data.audio_file,
                "Duration": voice_data.duration,
                "VoiceType": voice_data.voice_type,
                "Emotion": voice_data.emotion,
                "LipSyncData": {
                    "bHasLipSync": True,
                    "Phonemes": [
                        {
                            "Phoneme": f.get("phoneme", "E"),
                            "StartTime": f.get("time", 0.0),
                            "EndTime": f.get("time", 0.0) + (1.0 / 30.0)
                        }
                        for f in frames
                    ]
                }
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(unreal_data, f, indent=2)
        
        return output_file


class VoiceLibraryManager:
    """Manage voice library for all dialogue"""
    
    def __init__(self, output_dir: str = "voice_library"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.library: Dict[str, VoiceAudioData] = {}
        self.index_file = self.output_dir / "index.json"
        self._load_library()
    
    def add_voice(self, voice_data: VoiceAudioData):
        """Add voice to library"""
        self.library[voice_data.audio_id] = voice_data
        self._save_index()
    
    def get_voice(self, audio_id: str) -> Optional[VoiceAudioData]:
        """Get voice from library"""
        return self.library.get(audio_id)
    
    def search_by_text(self, text: str) -> List[VoiceAudioData]:
        """Search voices by text"""
        return [v for v in self.library.values() if v.text == text]
    
    def search_by_voice_type(self, voice_type: str) -> List[VoiceAudioData]:
        """Search voices by type"""
        return [v for v in self.library.values() if v.voice_type == voice_type]
    
    def search_by_emotion(self, emotion: str) -> List[VoiceAudioData]:
        """Search voices by emotion"""
        return [v for v in self.library.values() if v.emotion == emotion]
    
    def _save_index(self):
        """Save library index"""
        index_data = {
            "total_voices": len(self.library),
            "voices": [
                {
                    "audio_id": v.audio_id,
                    "text": v.text,
                    "voice_type": v.voice_type,
                    "emotion": v.emotion,
                    "duration": v.duration
                }
                for v in self.library.values()
            ]
        }
        
        with open(self.index_file, 'w') as f:
            json.dump(index_data, f, indent=2)
    
    def _load_library(self):
        """Load library from disk"""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                index_data = json.load(f)
                # In production, would load actual audio files
                pass
