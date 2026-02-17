# Enhanced Dialogue System
## Complete Implementation Guide

A production-ready dialogue system for game engines featuring visual tree editing, AI voice generation, lip sync animation, and dynamic relationship tracking.

---

## 📋 Table of Contents

1. [System Overview](#overview)
2. [Components](#components)
3. [Features](#features)
4. [Installation](#installation)
5. [Quick Start](#quick-start)
6. [Usage Examples](#usage-examples)
7. [API Reference](#api-reference)
8. [Advanced Usage](#advanced-usage)
9. [Best Practices](#best-practices)

---

## Overview

The Enhanced Dialogue System provides:

- **Visual Dialogue Tree Editor** - Create and edit dialogue trees with an intuitive interface
- **AI Voice Generation** - Generate realistic speech from text with emotion control
- **Lip Sync Animation** - Automatic phoneme-based lip sync data for character animation
- **Relationship Tracking** - Dynamic NPC relationship system with memory
- **Multi-Engine Export** - Export to Unreal Engine, Unity, or Godot
- **Branching Conversations** - Complex dialogue trees with conditions and effects

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│         Enhanced Dialogue System Architecture                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │ Dialogue Editor  │  │ Voice Generator  │  │ Lip Sync   │ │
│  ├──────────────────┤  ├──────────────────┤  ├────────────┤ │
│  │ • Tree Creation  │  │ • TTS            │  │ • Phonemes │ │
│  │ • Visual Layout  │  │ • Voice Profiles │  │ • Animation│ │
│  │ • Branching      │  │ • Emotion Mod    │  │ • Frames   │ │
│  │ • Validation     │  │ • Audio Library  │  │ • Blending │ │
│  └──────────────────┘  └──────────────────┘  └────────────┘ │
│           │                    │                     │        │
│           └────────┬───────────┴─────────────────────┘        │
│                    │                                          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │    Relationship Tracking & Session Management           │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │ • Relationship Values (-100 to 100)                     │ │
│  │ • Relationship Tiers (Hostile to Intimate)             │ │
│  │ • Character Memory                                       │ │
│  │ • Dialogue History                                       │ │
│  │ • Session Management                                     │ │
│  └─────────────────────────────────────────────────────────┘ │
│           │                                                   │
│           └──────────────────────┬──────────────────────────┘ │
│                                  │                             │
│                        Multi-Engine Export                     │
│                 (Unreal / Unity / Godot)                       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Dialogue Tree Editor (`dialogue_tree_editor.py`)

Visual node-based dialogue editing system.

**Key Classes:**
- `DialogueTreeEditor` - Main editor for creating/managing dialogue projects
- `VisualNode` - Node with screen position and size
- `DialogueTreeVisual` - Visual representation of tree
- `DialogueTreeExporter` - Export to multiple formats

**Features:**
- Create unlimited dialogue nodes
- Add choices with conditions and effects
- Visual node positioning and connections
- Project validation
- Multi-engine export

### 2. Voice Generation (`dialogue_voice_generation.py`)

AI text-to-speech with emotional modulation.

**Key Classes:**
- `AIVoiceGenerator` - Generate speech audio
- `VoiceProfiler` - Emotional voice profiles
- `LipSyncGenerator` - Create phoneme sequences
- `VoiceLibraryManager` - Manage voice library

**Features:**
- Emotion-based voice modification
- Phoneme generation for lip sync
- Frame interpolation for animation
- Audio library management
- Batch generation

### 3. Relationship System (`dialogue_relationship_system.py`)

Track NPC relationships and character memory.

**Key Classes:**
- `RelationshipTracker` - Manage all relationships
- `CharacterMemory` - Store NPC memories
- `RelationshipSnapshot` - Point-in-time relationship data

**Features:**
- Relationship values (-100 to 100)
- Relationship tiers (Hostile to Intimate)
- Character memory system
- Preference tracking
- Relationship history

### 4. Integrated System (`dialogue_complete_system.py`)

Complete unified dialogue system.

**Key Classes:**
- `EnhancedDialogueSystem` - Main system orchestrator
- `DialogueSessionConfig` - Session configuration

---

## Features

### Visual Dialogue Tree Editor

```python
editor = DialogueTreeEditor()

# Create project
project_id = editor.create_project(
    project_name="Elara's Dialogue",
    npc_name="Elara",
    npc_role="Wise Mage"
)

# Add dialogue nodes
editor.add_dialogue_node(
    project_id=project_id,
    node_id="greeting",
    speaker="Elara",
    text="Greetings, adventurer!",
    emotion="happy",
    x=0, y=0
)

# Add choices
editor.add_choice(
    project_id=project_id,
    from_node_id="greeting",
    choice_id="ask_quest",
    choice_text="Tell me of your quest",
    to_node_id="quest_info"
)
```

### AI Voice Generation

```python
generator = AIVoiceGenerator()

# Generate speech
voice_data = await generator.generate_speech(
    text="Greetings, adventurer!",
    voice_type="elder",
    emotion="happy"
)

# Generate batch
voices = await generator.generate_batch_speech([
    ("Hello", "hero_male", "neutral"),
    ("Welcome", "hero_female", "happy")
])
```

### Lip Sync Animation

```python
from dialogue_voice_generation import LipSyncGenerator

# Generate phonemes
phonemes = LipSyncGenerator.generate_phonemes(
    text="Hello world",
    duration=2.5
)

# Interpolate for animation
frames = LipSyncGenerator.interpolate_phonemes(phonemes, frame_rate=30)

# Use in character animation
for frame in frames:
    character.animate_mouth(frame['phoneme'], frame['blend'])
```

### Relationship Tracking

```python
tracker = RelationshipTracker()

# Initialize relationship
tracker.initialize_relationship("player_001", "elara_001", "Elara", 0)

# Modify relationship
tracker.modify_relationship(
    player_id="player_001",
    npc_id="elara_001",
    delta=15,
    reason=RelationshipChangeReason.DIALOGUE_CHOICE
)

# Get tier
tier = tracker.get_tier("player_001", "elara_001")
print(f"Relationship: {tier.value}")

# Record memory
tracker.record_memory(
    npc_id="elara_001",
    memory_type="quest_given",
    content="Player received the Lost Amulet quest",
    emotional_weight=2
)
```

---

## Installation

### Prerequisites
- Python 3.10+
- SQLite3 (usually included)
- Optional: Google TTS, Azure Speech, or Eleven Labs API keys

### Setup

1. **Clone/Copy Files:**
```bash
cp dialogue_*.py /your/project/path/
cp dialogue_complete_system.py /your/project/path/
```

2. **Install Dependencies:**
```bash
pip install aiohttp google-cloud-texttospeech  # Optional TTS
```

3. **Initialize Database:**
```python
from dialogue_relationship_system import RelationshipTracker
tracker = RelationshipTracker()  # Creates DB automatically
```

---

## Quick Start

### Basic Example: Create and Play Dialogue

```python
import asyncio
from dialogue_complete_system import EnhancedDialogueSystem, DialogueSessionConfig

async def main():
    system = EnhancedDialogueSystem()
    
    # Create NPC dialogue
    result = await system.create_npc_dialogue(
        npc_name="Gandalf",
        npc_role="Wizard",
        dialogue_topic="Magic",
        generate_voice=True
    )
    
    project_id = result['project_id']
    
    # Start dialogue
    config = DialogueSessionConfig(
        player_id="hero",
        npc_id="gandalf",
        npc_name="Gandalf"
    )
    
    session_id = await system.start_dialogue_session(config, project_id)
    
    # Play dialogue
    response = await system.progress_dialogue(session_id)
    print(f"{response['speaker']}: {response['text']}")
    
    # Make choice
    if response['choices']:
        choice_id = response['choices'][0]['choice_id']
        next = await system.progress_dialogue(session_id, choice_id)
        print(f"{next['speaker']}: {next['text']}")
    
    # End session
    summary = system.end_dialogue_session(session_id)
    print(f"Dialogue ended. Relationship: {summary.get('final_relationship_tier')}")

asyncio.run(main())
```

---

## Usage Examples

### Example 1: Create Complex Dialogue Tree

```python
editor = DialogueTreeEditor()

# Create project
pid = editor.create_project("Merchant", "merchant", "Trader")

# Create greeting
editor.add_dialogue_node(
    pid, "greet", "Merchant",
    "Welcome to my shop!",
    emotion="happy", x=0, y=0
)

# Friendly path
editor.add_dialogue_node(
    pid, "friendly", "Merchant",
    "Always happy to help! What interests you?",
    x=300, y=-200
)

# Suspicious path
editor.add_dialogue_node(
    pid, "suspicious", "Merchant",
    "Hmm, I'm not sure about you...",
    x=-300, y=-200
)

# Add choices
editor.add_choice(pid, "greet", "nice", "You seem nice", "friendly")
editor.add_choice(pid, "greet", "rude", "I'm not here for small talk", "suspicious")

# Add conditions
editor.add_condition(
    pid, "friendly",
    "relationship", "merchant", ">=", 20
)

# Validate
issues = editor.validate_tree(pid)
```

### Example 2: Export for Unreal Engine

```python
system = EnhancedDialogueSystem()

# Get project ID
project_id = "abc12345"

# Export to Unreal format
export_path = system.export_dialogue_project(
    project_id,
    export_format="unreal",
    output_dir="unreal_exports"
)

print(f"Exported to: {export_path}")
```

### Example 3: Character Memory and Personality

```python
tracker = RelationshipTracker()

# Initialize NPC
tracker.initialize_relationship("player", "npc_001", "Elena")

# Record memories
tracker.record_memory(
    "npc_001",
    "player_helped",
    "Player saved me from bandits",
    emotional_weight=5
)

tracker.record_memory(
    "npc_001",
    "betrayal",
    "Player stole from my shop",
    emotional_weight=-8
)

# Get character
character = tracker.get_character_memory("npc_001")
character.add_preference("magic", 8)
character.add_preference("combat", 5)
character.add_quirk("superstitious")
character.add_quirk("loves music")

# Generate report
print(tracker.generate_relationship_report("player"))
```

### Example 4: Relationship Events

```python
system = EnhancedDialogueSystem()

# Create NPC
result = await system.create_npc_dialogue(
    "Aragorn", "Ranger", "Destiny"
)

# Start session
session_id = await system.start_dialogue_session(config, result['project_id'])

# Make dialogue choices affecting relationships
await system.progress_dialogue(session_id, "choice_honorable")

# Check relationship changes
session = system.active_sessions[session_id]
changes = session['relationship_changes']
for change in changes:
    print(f"Choice '{change['choice']}' changed relationship by {change['delta']}")
```

---

## API Reference

### DialogueTreeEditor

```python
# Create project
project_id = editor.create_project(project_name, npc_name, npc_role)

# Add node
editor.add_dialogue_node(project_id, node_id, speaker, text, 
                        dialogue_type, emotion, x, y)

# Add choice
editor.add_choice(project_id, from_node_id, choice_id, choice_text, 
                 to_node_id, conditions, effects)

# Validate
issues = editor.validate_tree(project_id)

# Export
json_str = editor.get_project_json(project_id)
visual_str = editor.get_visual_tree_json(project_id)
```

### AIVoiceGenerator

```python
# Generate single
voice = await generator.generate_speech(text, voice_type, emotion)

# Generate batch
voices = await generator.generate_batch_speech(texts_list)

# Export
generator.export_voice_metadata(audio_id, output_file)
generator.export_for_unreal(audio_id, output_file)
```

### RelationshipTracker

```python
# Initialize
tracker.initialize_relationship(player_id, npc_id, npc_name)

# Modify
new_value = tracker.modify_relationship(player_id, npc_id, delta, reason)

# Query
value = tracker.get_relationship(player_id, npc_id)
tier = tracker.get_tier(player_id, npc_id)
tiers = tracker.get_relationship_tiers(player_id)

# Memory
tracker.record_memory(npc_id, memory_type, content, emotional_weight)
memory = tracker.get_character_memory(npc_id)

# History
history = tracker.get_relationship_history(player_id, npc_id)

# Export
tracker.export_relationships(player_id, output_file)
```

### EnhancedDialogueSystem

```python
# Create dialogue
result = await system.create_npc_dialogue(npc_name, npc_role, topic)

# Session management
session_id = await system.start_dialogue_session(config, project_id)
response = await system.progress_dialogue(session_id, choice_id)
summary = system.end_dialogue_session(session_id)

# Export
path = system.export_dialogue_project(project_id, export_format)

# Status
status = system.get_system_status()
```

---

## Advanced Usage

### Custom Voice Profiles

```python
VoiceProfiler.VOICE_PROFILES["custom_voice"] = {
    "pitch": 1.2,
    "speed": 0.95,
    "emotion_map": {
        "happy": 1.3,
        "sad": 0.6,
        "angry": 1.4,
        "neutral": 1.0
    }
}
```

### Dynamic Dialogue Conditions

```python
editor.add_condition(
    project_id, node_id,
    condition_type="relationship",
    key="npc_name",
    operator=">=",
    value=50  # Only show if relationship >= 50
)

editor.add_condition(
    project_id, node_id,
    condition_type="quest",
    key="quest_id",
    operator="==",
    value="completed"
)
```

### Multi-Language Support

```python
voices = await generator.generate_batch_speech(
    texts_list,
    language="es-ES"  # Spanish
)
```

---

## Best Practices

1. **Tree Validation**: Always validate trees before export
   ```python
   issues = editor.validate_tree(project_id)
   if issues:
       print(f"Tree issues: {issues}")
   ```

2. **Voice Generation**: Cache generated voice files
   ```python
   library = VoiceLibraryManager()
   if not library.get_voice(audio_id):
       voice = await generator.generate_speech(text)
       library.add_voice(voice)
   ```

3. **Relationship Management**: Always initialize before modifying
   ```python
   tracker.initialize_relationship(player_id, npc_id, npc_name)
   tracker.modify_relationship(player_id, npc_id, delta, reason)
   ```

4. **Session Cleanup**: Always end sessions properly
   ```python
   summary = system.end_dialogue_session(session_id)
   ```

5. **Error Handling**: Validate exports before use
   ```python
   export_path = system.export_dialogue_project(pid, "unreal")
   if export_path:
       print(f"Export successful: {export_path}")
   ```

---

## Performance Considerations

| Operation | Time | Notes |
|-----------|------|-------|
| Create dialogue tree | ~100ms | Fast |
| Generate voice (1 line) | ~500ms | Network dependent |
| Generate batch (10 lines) | ~3s | Parallel processing |
| Export to Unreal | ~50ms | File I/O |
| Relationship query | <1ms | In-memory |
| Dialogue progression | ~10ms | Tree traversal |

---

## Troubleshooting

**Issue**: Voice generation fails
- **Solution**: Check API key, internet connection, API limits

**Issue**: Phonemes don't sync correctly
- **Solution**: Adjust frame_rate parameter in LipSyncGenerator.interpolate_phonemes()

**Issue**: Dialogue tree validation fails
- **Solution**: Ensure all choice `next_node_id` values reference existing nodes

**Issue**: Relationships not tracking
- **Solution**: Ensure RelationshipChangeReason is valid enum value

---

## Future Enhancements

- [ ] Real-time voice streaming
- [ ] Custom phoneme mapping per language
- [ ] Neural voice cloning
- [ ] Procedural dialogue generation with AI
- [ ] Dynamic emotion detection
- [ ] Multi-speaker dialogue
- [ ] Dialogue branching based on player stats
- [ ] NPC emotional state system

---

**Version**: 1.0.0  
**Last Updated**: February 17, 2026
