"""
Game Environment Builder
Create complete playable game levels from assets
"""

import json
import time
import os
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class GameEnvironment:
    """Complete game environment configuration"""
    environment_id: str
    name: str
    description: str
    assets: List[Dict[str, Any]]
    gameplay_elements: List[Dict[str, Any]]
    lighting: Dict[str, Any]
    physics: Dict[str, Any]
    audio: Dict[str, Any]
    player_start: Dict[str, Any]
    win_conditions: List[str]
    created_at: str
    
    def to_dict(self):
        return asdict(self)

class GameEnvironmentBuilder:
    """
    Build complete playable game environments
    """
    
    def __init__(self):
        self.environments = []
        self.asset_library = []
        self.current_environment = None
        
    def create_environment(
        self,
        name: str,
        template: str = "empty"
    ) -> GameEnvironment:
        """Create new game environment"""
        
        env_id = f"env_{int(time.time())}"
        
        # Load template
        base_config = self._get_template(template)
        
        environment = GameEnvironment(
            environment_id=env_id,
            name=name,
            description=f"Game environment: {name}",
            assets=[],
            gameplay_elements=[],
            lighting=base_config["lighting"],
            physics=base_config["physics"],
            audio=base_config["audio"],
            player_start=base_config["player_start"],
            win_conditions=[],
            created_at=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        self.current_environment = environment
        self.environments.append(environment)
        
        return environment
    
    def _get_template(self, template: str) -> Dict[str, Any]:
        """Get environment template"""
        
        templates = {
            "empty": {
                "lighting": {
                    "type": "directional",
                    "intensity": 1.0,
                    "color": [1.0, 1.0, 1.0],
                    "direction": [0, -1, -1]
                },
                "physics": {
                    "gravity": -980,
                    "physics_simulation": True,
                    "collision_enabled": True
                },
                "audio": {
                    "ambient_sound": None,
                    "music": None,
                    "volume": 1.0
                },
                "player_start": {
                    "position": [0, 0, 100],
                    "rotation": [0, 0, 0]
                }
            },
            "fps_arena": {
                "lighting": {
                    "type": "mixed",
                    "intensity": 0.8,
                    "color": [0.9, 0.9, 1.0],
                    "direction": [0, -1, -1]
                },
                "physics": {
                    "gravity": -980,
                    "physics_simulation": True,
                    "collision_enabled": True
                },
                "audio": {
                    "ambient_sound": "Arena_Ambient",
                    "music": "Action_Theme",
                    "volume": 0.7
                },
                "player_start": {
                    "position": [0, 0, 200],
                    "rotation": [0, 0, 0]
                }
            },
            "platformer": {
                "lighting": {
                    "type": "directional",
                    "intensity": 1.2,
                    "color": [1.0, 0.95, 0.8],
                    "direction": [-0.5, -1, -0.3]
                },
                "physics": {
                    "gravity": -1200,
                    "physics_simulation": True,
                    "collision_enabled": True
                },
                "audio": {
                    "ambient_sound": "Nature_Ambient",
                    "music": "Platformer_Theme",
                    "volume": 0.8
                },
                "player_start": {
                    "position": [0, 0, 150],
                    "rotation": [0, 0, 0]
                }
            }
        }
        
        return templates.get(template, templates["empty"])
    
    def add_asset_to_environment(
        self,
        asset_data: Dict[str, Any],
        position: List[float] = [0, 0, 0],
        rotation: List[float] = [0, 0, 0],
        scale: List[float] = [1, 1, 1]
    ) -> Dict[str, Any]:
        """Add asset to current environment"""
        
        if not self.current_environment:
            return {"error": "No active environment"}
        
        placed_asset = {
            "asset_id": f"placed_{int(time.time())}",
            "source_asset": asset_data.get("asset_path"),
            "asset_name": asset_data.get("asset_name", "Asset"),
            "asset_type": asset_data.get("asset_type", "StaticMesh"),
            "transform": {
                "position": position,
                "rotation": rotation,
                "scale": scale
            },
            "properties": asset_data.get("properties", {}),
            "collision": asset_data.get("collision", True),
            "physics": asset_data.get("physics", False),
            "interactive": False,
            "tags": []
        }
        
        self.current_environment.assets.append(placed_asset)
        
        return {
            "success": True,
            "placed_asset": placed_asset
        }
    
    def create_gameplay_element(
        self,
        element_type: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add gameplay element (spawn point, trigger, objective)"""
        
        if not self.current_environment:
            return {"error": "No active environment"}
        
        gameplay_element = {
            "element_id": f"gameplay_{int(time.time())}",
            "type": element_type,
            "properties": properties,
            "enabled": True
        }
        
        self.current_environment.gameplay_elements.append(gameplay_element)
        
        return {
            "success": True,
            "element": gameplay_element
        }
    
    def add_player_mechanics(
        self,
        mechanics: List[str]
    ) -> Dict[str, Any]:
        """Add player mechanics to environment"""
        
        mechanics_config = {
            "movement": {
                "walk_speed": 600,
                "run_speed": 1000,
                "jump_height": 420,
                "can_crouch": True,
                "can_sprint": True
            },
            "camera": {
                "type": "third_person",
                "distance": 300,
                "fov": 90,
                "can_zoom": True
            },
            "abilities": []
        }
        
        # Add requested mechanics
        for mechanic in mechanics:
            if mechanic == "flying":
                mechanics_config["movement"]["can_fly"] = True
                mechanics_config["movement"]["fly_speed"] = 800
            elif mechanic == "double_jump":
                mechanics_config["movement"]["double_jump"] = True
            elif mechanic == "dash":
                mechanics_config["abilities"].append({
                    "type": "dash",
                    "distance": 500,
                    "cooldown": 2.0
                })
            elif mechanic == "wall_run":
                mechanics_config["movement"]["wall_run"] = True
        
        return {
            "success": True,
            "mechanics": mechanics_config
        }
    
    def generate_level_layout(
        self,
        layout_type: str,
        size: str = "medium"
    ) -> Dict[str, Any]:
        """Generate level layout automatically"""
        
        layouts = {
            "arena": self._generate_arena_layout,
            "linear": self._generate_linear_layout,
            "open_world": self._generate_open_world_layout,
            "maze": self._generate_maze_layout
        }
        
        generator = layouts.get(layout_type, layouts["arena"])
        return generator(size)
    
    def _generate_arena_layout(self, size: str) -> Dict[str, Any]:
        """Generate arena-style level"""
        
        size_configs = {
            "small": {"radius": 2000, "platforms": 3},
            "medium": {"radius": 5000, "platforms": 5},
            "large": {"radius": 10000, "platforms": 8}
        }
        
        config = size_configs.get(size, size_configs["medium"])
        
        layout = {
            "type": "arena",
            "bounds": {
                "min": [-config["radius"], -config["radius"], 0],
                "max": [config["radius"], config["radius"], 1000]
            },
            "zones": [
                {
                    "name": "Center Arena",
                    "position": [0, 0, 0],
                    "radius": config["radius"] * 0.3,
                    "purpose": "main_combat"
                },
                {
                    "name": "Outer Ring",
                    "position": [0, 0, 0],
                    "radius": config["radius"],
                    "purpose": "cover_and_items"
                }
            ],
            "platforms": [],
            "spawn_points": []
        }
        
        # Generate platforms
        import math
        for i in range(config["platforms"]):
            angle = (2 * math.pi / config["platforms"]) * i
            x = math.cos(angle) * config["radius"] * 0.6
            y = math.sin(angle) * config["radius"] * 0.6
            
            layout["platforms"].append({
                "position": [x, y, 100],
                "size": [500, 500, 50],
                "type": "elevated_platform"
            })
            
            layout["spawn_points"].append({
                "position": [x, y, 150],
                "rotation": [0, 0, -angle],
                "team": i % 2
            })
        
        return layout
    
    def _generate_linear_layout(self, size: str) -> Dict[str, Any]:
        """Generate linear level (like platformer)"""
        
        length = {"small": 5000, "medium": 10000, "large": 20000}[size]
        
        layout = {
            "type": "linear",
            "start": [0, 0, 100],
            "end": [length, 0, 100],
            "segments": [],
            "checkpoints": []
        }
        
        # Generate segments
        num_segments = length // 1000
        for i in range(num_segments):
            layout["segments"].append({
                "position": [i * 1000, 0, 100],
                "type": ["platform", "gap", "enemy", "collectible"][i % 4],
                "difficulty": min(1.0, i / num_segments)
            })
        
        # Checkpoints every 25%
        for i in range(1, 4):
            layout["checkpoints"].append({
                "position": [length * (i/4), 0, 100],
                "name": f"Checkpoint {i}"
            })
        
        return layout
    
    def _generate_open_world_layout(self, size: str) -> Dict[str, Any]:
        """Generate open world layout"""
        
        size_km = {"small": 1, "medium": 4, "large": 16}[size]
        size_units = size_km * 100000  # UE units
        
        layout = {
            "type": "open_world",
            "bounds": {
                "min": [-size_units/2, -size_units/2, 0],
                "max": [size_units/2, size_units/2, 5000]
            },
            "regions": [],
            "poi": []  # Points of interest
        }
        
        # Generate regions
        regions = ["forest", "desert", "mountains", "plains"]
        for i, region in enumerate(regions[:size_km]):
            layout["regions"].append({
                "name": region.title(),
                "biome": region,
                "center": [
                    (i % 2) * size_units/2 - size_units/4,
                    (i // 2) * size_units/2 - size_units/4,
                    0
                ],
                "radius": size_units / 4
            })
        
        return layout
    
    def _generate_maze_layout(self, size: str) -> Dict[str, Any]:
        """Generate maze layout"""
        
        grid_size = {"small": 10, "medium": 20, "large": 30}[size]
        cell_size = 500
        
        layout = {
            "type": "maze",
            "grid_size": [grid_size, grid_size],
            "cell_size": cell_size,
            "walls": [],
            "solution_path": []
        }
        
        # Simple maze generation (can be enhanced)
        for x in range(grid_size):
            for y in range(grid_size):
                # Add some walls
                if (x + y) % 3 != 0:
                    layout["walls"].append({
                        "position": [x * cell_size, y * cell_size, cell_size/2],
                        "size": [cell_size, cell_size, cell_size]
                    })
        
        return layout
    
    def export_to_unreal(
        self,
        output_path: str
    ) -> Dict[str, Any]:
        """Export environment to Unreal-compatible format"""
        
        if not self.current_environment:
            return {"error": "No active environment"}
        
        # Create level asset
        level_name = self.current_environment.name
        level_data = {
            "level_name": level_name,
            "level_type": "GameLevel",
            "actors": [],
            "lighting": self.current_environment.lighting,
            "world_settings": {
                "physics": self.current_environment.physics,
                "kill_z": -10000
            }
        }
        
        # Convert assets to actors
        for asset in self.current_environment.assets:
            actor = {
                "class": "StaticMeshActor",
                "name": asset["asset_name"],
                "transform": asset["transform"],
                "static_mesh": asset["source_asset"],
                "materials": [],
                "collision": {
                    "enabled": asset["collision"],
                    "type": "BlockAll" if asset["collision"] else "NoCollision"
                }
            }
            level_data["actors"].append(actor)
        
        # Add gameplay elements
        for element in self.current_environment.gameplay_elements:
            actor = {
                "class": self._get_actor_class_for_element(element["type"]),
                "name": element["element_id"],
                "properties": element["properties"]
            }
            level_data["actors"].append(actor)
        
        # Save level data
        os.makedirs(output_path, exist_ok=True)
        level_path = os.path.join(output_path, f"{level_name}.json")
        
        with open(level_path, 'w') as f:
            json.dump(level_data, f, indent=2)
        
        # Generate import script
        import_script = self._generate_unreal_import_script(level_data)
        script_path = os.path.join(output_path, "ImportLevel.py")
        
        with open(script_path, 'w') as f:
            f.write(import_script)
        
        return {
            "success": True,
            "level_path": level_path,
            "import_script": script_path,
            "actors_count": len(level_data["actors"])
        }
    
    def _get_actor_class_for_element(self, element_type: str) -> str:
        """Get Unreal actor class for gameplay element"""
        
        class_map = {
            "spawn_point": "PlayerStart",
            "trigger": "TriggerBox",
            "pickup": "PickupActor",
            "enemy_spawn": "EnemySpawner",
            "checkpoint": "Checkpoint",
            "objective": "ObjectiveMarker"
        }
        
        return class_map.get(element_type, "Actor")
    
    def _generate_unreal_import_script(self, level_data: Dict[str, Any]) -> str:
        """Generate Python script for Unreal Editor"""
        
        script = f"""# Unreal Engine Level Import Script
# Generated by AI Architect

import unreal

# Create new level
level_name = "{level_data['level_name']}"
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
level = unreal.EditorLevelLibrary.new_level("/Game/Levels/{level_name}")

# Set world settings
world_settings = unreal.EditorLevelLibrary.get_editor_world()

# Spawn actors
"""
        
        for actor in level_data["actors"]:
            script += f"""
# {actor['name']}
actor_{actor['name']} = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.{actor['class']},
    location=unreal.Vector({actor['transform']['position'][0]}, {actor['transform']['position'][1]}, {actor['transform']['position'][2]}),
    rotation=unreal.Rotator({actor['transform']['rotation'][0]}, {actor['transform']['rotation'][1]}, {actor['transform']['rotation'][2]})
)
"""
        
        script += """
# Save level
unreal.EditorLevelLibrary.save_current_level()
print(f"Level {level_name} imported successfully!")
"""
        
        return script
    
    def create_playable_demo(
        self,
        environment: GameEnvironment,
        demo_type: str = "walkthrough"
    ) -> Dict[str, Any]:
        """Create a playable demo of the environment"""
        
        demo_config = {
            "demo_id": f"demo_{int(time.time())}",
            "environment": environment.to_dict(),
            "demo_type": demo_type,
            "player_config": {
                "character": "ThirdPersonCharacter",
                "start_location": environment.player_start["position"],
                "controls": {
                    "movement": "WASD",
                    "jump": "Space",
                    "interact": "E",
                    "menu": "Esc"
                }
            },
            "objectives": environment.win_conditions,
            "ui_elements": [
                "health_bar",
                "minimap",
                "objective_tracker",
                "interaction_prompts"
            ],
            "time_limit": None if demo_type == "walkthrough" else 300
        }
        
        return demo_config
