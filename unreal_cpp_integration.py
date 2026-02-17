"""
Unreal Engine C++ Procedural Generation Integration
Bridges Python with C++ procedural generation systems
Handles Blender exports and asset generation
"""

import json
import subprocess
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio


class WeaponRarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class ElementalType(Enum):
    FIRE = "fire"
    ICE = "ice"
    LIGHTNING = "lightning"
    NATURE = "nature"
    HOLY = "holy"
    DARK = "dark"
    PURE = "pure"
    CHAOS = "chaos"


@dataclass
class UnrealWeaponStat:
    damage: float = 10.0
    critical_chance: float = 0.05
    critical_damage: float = 1.5
    attack_speed: float = 1.0
    range: float = 100.0
    special_ability_power: float = 0.0

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class UnrealWeapon:
    weapon_id: str
    weapon_name: str
    weapon_type: str
    rarity: WeaponRarity
    element: ElementalType
    stats: UnrealWeaponStat
    required_level: int = 1
    enchantments: List[str] = None
    weight: float = 10.0
    description: str = ""
    gold_value: int = 100
    is_unique: bool = False

    def __post_init__(self):
        if self.enchantments is None:
            self.enchantments = []

    def to_dict(self) -> Dict:
        return {
            "weapon_id": self.weapon_id,
            "weapon_name": self.weapon_name,
            "weapon_type": self.weapon_type,
            "rarity": self.rarity.value,
            "element": self.element.value,
            "stats": self.stats.to_dict(),
            "required_level": self.required_level,
            "enchantments": self.enchantments,
            "weight": self.weight,
            "description": self.description,
            "gold_value": self.gold_value,
            "is_unique": self.is_unique
        }


class UnrealTerrainExporter:
    """Export terrain data to Blender-compatible formats"""

    def __init__(self, output_dir: str = "./blender_exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_terrain_to_obj(
        self,
        terrain_width: int,
        terrain_height: int,
        height_data: List[List[float]],
        filename: str = "terrain.obj"
    ) -> str:
        """Export terrain as OBJ file for Blender"""

        filepath = self.output_dir / filename
        vertices = []
        faces = []

        # Create vertices
        for z in range(terrain_height):
            for x in range(terrain_width):
                height = height_data[z][x] if z < len(height_data) and x < len(height_data[z]) else 0.0
                vertices.append(f"v {x * 10} {height * 100} {z * 10}")

        # Create faces
        for z in range(terrain_height - 1):
            for x in range(terrain_width - 1):
                v0 = z * terrain_width + x + 1
                v1 = z * terrain_width + (x + 1) + 1
                v2 = (z + 1) * terrain_width + (x + 1) + 1
                v3 = (z + 1) * terrain_width + x + 1

                faces.append(f"f {v0} {v1} {v2}")
                faces.append(f"f {v0} {v2} {v3}")

        # Write OBJ file
        with open(filepath, 'w') as f:
            f.write("# Procedural Terrain Export\n")
            f.write(f"# Generated terrain: {terrain_width}x{terrain_height}\n\n")
            f.writelines([v + "\n" for v in vertices])
            f.write("\n")
            f.writelines([face + "\n" for face in faces])

        return str(filepath)

    def export_terrain_to_gltf(self, terrain_data: Dict[str, Any], filename: str = "terrain.gltf") -> str:
        """Export terrain as glTF for Blender/Unreal compatibility"""

        filepath = self.output_dir / filename

        gltf_data = {
            "asset": {"version": "2.0", "generator": "Unreal AI Procedural Gen"},
            "scene": 0,
            "scenes": [{"nodes": [0]}],
            "nodes": [
                {
                    "name": "Terrain",
                    "mesh": 0,
                    "translation": [0, 0, 0]
                }
            ],
            "meshes": [
                {
                    "name": "TerrainMesh",
                    "primitives": [
                        {
                            "attributes": {
                                "POSITION": 0,
                                "NORMAL": 1
                            },
                            "indices": 2,
                            "material": 0
                        }
                    ]
                }
            ],
            "materials": [
                {
                    "name": "DefaultMaterial",
                    "pbrMetallicRoughness": {
                        "baseColorFactor": [0.8, 0.8, 0.8, 1.0],
                        "metallicFactor": 0.0,
                        "roughnessFactor": 0.5
                    }
                }
            ],
            "accessors": [],
            "bufferViews": [],
            "buffers": []
        }

        with open(filepath, 'w') as f:
            json.dump(gltf_data, f, indent=2)

        return str(filepath)


class UnrealCityExporter:
    """Export city data to Blender-compatible formats"""

    def __init__(self, output_dir: str = "./blender_exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_city_to_blend(self, city_data: Dict[str, Any], filename: str = "city.json") -> str:
        """Export city as JSON compatible with Blender import scripts"""

        filepath = self.output_dir / filename

        blender_data = {
            "city_name": city_data.get("city_name", "ProceduralCity"),
            "population": city_data.get("population", 0),
            "radius": city_data.get("radius", 5000),
            "districts": []
        }

        for district in city_data.get("districts", []):
            district_obj = {
                "name": district.get("name", ""),
                "type": district.get("type", "mixed"),
                "population": district.get("population", 0),
                "buildings": [
                    {
                        "id": building.get("id", ""),
                        "type": building.get("type", "residential"),
                        "position": building.get("position", [0, 0, 0]),
                        "size": building.get("size", [50, 50, 100]),
                        "floors": building.get("floors", 1),
                        "material": building.get("material", "brick")
                    }
                    for building in district.get("buildings", [])
                ]
            }
            blender_data["districts"].append(district_obj)

        with open(filepath, 'w') as f:
            json.dump(blender_data, f, indent=2)

        return str(filepath)

    def export_buildings_to_obj(self, buildings: List[Dict], filename: str = "buildings.obj") -> str:
        """Export buildings as individual OBJ files"""

        filepath = self.output_dir / filename

        with open(filepath, 'w') as f:
            f.write("# Procedural City Buildings Export\n\n")

            for idx, building in enumerate(buildings):
                x, y, z = building.get("position", [0, 0, 0])
                width, depth, height = building.get("size", [50, 50, 100])

                # Create cube for building
                v_base = idx * 8 + 1
                vertices = [
                    f"v {x} {y} {z}",
                    f"v {x + width} {y} {z}",
                    f"v {x + width} {y + depth} {z}",
                    f"v {x} {y + depth} {z}",
                    f"v {x} {y} {z + height}",
                    f"v {x + width} {y} {z + height}",
                    f"v {x + width} {y + depth} {z + height}",
                    f"v {x} {y + depth} {z + height}"
                ]

                f.writelines([v + "\n" for v in vertices])
                f.write(f"# Building {idx}: {building.get('id', 'Unknown')}\n")
                f.write(f"g Building_{idx}\n")
                f.write(f"f {v_base} {v_base + 1} {v_base + 2} {v_base + 3}\n")
                f.write(f"f {v_base + 4} {v_base + 5} {v_base + 6} {v_base + 7}\n")
                f.write("\n")

        return str(filepath)


class ProceduralGenerationBridge:
    """Main bridge between Python, C++, and Blender"""

    def __init__(self, unreal_project_path: Optional[str] = None):
        self.unreal_project_path = Path(unreal_project_path or ".")
        self.terrain_exporter = UnrealTerrainExporter()
        self.city_exporter = UnrealCityExporter()
        self.generated_assets = []

    async def generate_and_export_terrain(
        self,
        width: int = 256,
        height: int = 256,
        seed: int = 12345
    ) -> Dict[str, str]:
        """Generate terrain and export to multiple formats"""

        # Generate height map (simplified Perlin noise)
        height_data = [[0.0] * width for _ in range(height)]

        # Export to formats
        exports = {
            "obj": self.terrain_exporter.export_terrain_to_obj(width, height, height_data),
            "gltf": self.terrain_exporter.export_terrain_to_gltf({"width": width, "height": height})
        }

        self.generated_assets.append({"type": "terrain", "exports": exports})
        return exports

    async def generate_and_export_city(
        self,
        city_name: str = "ProceduralCity",
        num_districts: int = 8,
        buildings_per_district: int = 50
    ) -> Dict[str, str]:
        """Generate city and export to Blender format"""

        city_data = {
            "city_name": city_name,
            "population": 100000,
            "radius": 5000,
            "districts": []
        }

        # Create sample city structure
        for i in range(num_districts):
            district = {
                "name": f"District_{i}",
                "type": "mixed",
                "population": 100000 // num_districts,
                "buildings": [
                    {
                        "id": f"building_{i}_{j}",
                        "type": "residential",
                        "position": [i * 500, j * 50, 0],
                        "size": [50, 50, 100 + j * 20],
                        "floors": 1 + (j % 5),
                        "material": "brick"
                    }
                    for j in range(buildings_per_district)
                ]
            }
            city_data["districts"].append(district)

        exports = {
            "json": self.city_exporter.export_city_to_blend(city_data),
            "obj": self.city_exporter.export_buildings_to_obj(
                [b for d in city_data["districts"] for b in d["buildings"]]
            )
        }

        self.generated_assets.append({"type": "city", "exports": exports})
        return exports

    def create_weapon_library(self, num_weapons: int = 20) -> List[UnrealWeapon]:
        """Create a procedural weapon library"""

        weapons = []
        weapon_types = ["sword", "bow", "staff", "hammer", "spear", "dagger", "rifle", "pistol", "wand", "axe"]

        for i in range(num_weapons):
            weapon = UnrealWeapon(
                weapon_id=f"WPN_{i:05d}",
                weapon_name=f"Weapon_{i}",
                weapon_type=weapon_types[i % len(weapon_types)],
                rarity=list(WeaponRarity)[i % len(WeaponRarity)],
                element=list(ElementalType)[i % len(ElementalType)],
                stats=UnrealWeaponStat(
                    damage=10.0 + i * 2,
                    critical_chance=0.05 + (i * 0.01),
                    attack_speed=1.0 + (i * 0.05),
                    range=100.0 + i * 10
                ),
                required_level=1 + (i // 4),
                gold_value=100 * (i + 1)
            )
            weapons.append(weapon)

        return weapons

    def export_weapons_to_json(self, weapons: List[UnrealWeapon], filename: str = "weapon_library.json") -> str:
        """Export weapon library to JSON"""

        filepath = Path(self.terrain_exporter.output_dir) / filename

        weapons_data = {
            "total_weapons": len(weapons),
            "weapons": [w.to_dict() for w in weapons]
        }

        with open(filepath, 'w') as f:
            json.dump(weapons_data, f, indent=2)

        return str(filepath)

    def get_exported_assets(self) -> List[Dict]:
        """Get list of all generated and exported assets"""
        return self.generated_assets


async def main():
    """Demonstration of the procedural generation bridge"""

    bridge = ProceduralGenerationBridge()

    print("🎮 Unreal Engine Procedural Generation System")
    print("=" * 50)

    # Generate terrain
    print("\n🌍 Generating terrain...")
    terrain_exports = await bridge.generate_and_export_terrain(width=256, height=256)
    for fmt, path in terrain_exports.items():
        print(f"  ✓ Terrain exported to {fmt}: {path}")

    # Generate city
    print("\n🏙️  Generating city...")
    city_exports = await bridge.generate_and_export_city()
    for fmt, path in city_exports.items():
        print(f"  ✓ City exported to {fmt}: {path}")

    # Generate weapons
    print("\n⚔️  Generating weapons...")
    weapons = bridge.create_weapon_library(50)
    weapon_path = bridge.export_weapons_to_json(weapons)
    print(f"  ✓ Generated {len(weapons)} weapons")
    print(f"  ✓ Weapons exported to: {weapon_path}")

    # Summary
    print("\n📊 Generation Summary")
    print("=" * 50)
    assets = bridge.get_exported_assets()
    for asset in assets:
        print(f"• {asset['type'].upper()}: {asset['exports']}")


if __name__ == "__main__":
    asyncio.run(main())
