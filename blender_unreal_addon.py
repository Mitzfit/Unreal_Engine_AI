"""
Blender Addon for Importing Unreal Engine Procedural Generation Assets
bl_info = {
    "name": "Unreal Procedural Import",
    "blender": (3, 0, 0),
    "category": "Import-Export",
}
"""

import bpy
import json
import mathutils
from pathlib import Path
from typing import Dict, Any, List


class UnrealTerrainImporter:
    """Import procedural terrain into Blender"""

    @staticmethod
    def import_terrain_from_obj(filepath: str) -> bpy.types.Object:
        """Import terrain OBJ file"""
        bpy.ops.import_scene.obj(filepath=filepath)
        imported_obj = bpy.context.selected_objects[0]
        imported_obj.name = "ProceduralTerrain"

        # Add subdivision surface for detail
        subdiv = imported_obj.modifiers.new(name="Subdiv", type='SUBSURF')
        subdiv.levels = 2

        # Add smooth shading
        for face in imported_obj.data.polygons:
            face.use_smooth = True

        return imported_obj

    @staticmethod
    def apply_terrain_material(terrain_obj: bpy.types.Object) -> bpy.types.Material:
        """Apply procedural material to terrain"""

        mat = bpy.data.materials.new(name="TerrainMaterial")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Clear default nodes
        nodes.clear()

        # Create noise texture for terrain variation
        noise = nodes.new(type='ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 50.0

        # Create principled BSDF
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = (0.3, 0.6, 0.2, 1.0)

        # Create output
        output = nodes.new(type='ShaderNodeOutputMaterial')

        # Connect nodes
        links.new(noise.outputs['Fac'], bsdf.inputs['Base Color'])
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

        if terrain_obj.data.materials:
            terrain_obj.data.materials[0] = mat
        else:
            terrain_obj.data.materials.append(mat)

        return mat


class UnrealCityImporter:
    """Import procedural cities into Blender"""

    def __init__(self):
        self.building_objects = []
        self.district_collections = []

    def import_city_from_json(self, filepath: str) -> Dict[str, Any]:
        """Import city data from JSON"""

        with open(filepath, 'r') as f:
            city_data = json.load(f)

        city_name = city_data.get('city_name', 'ProceduralCity')

        # Create main collection for city
        city_collection = bpy.data.collections.new(city_name)
        bpy.context.scene.collection.children.link(city_collection)

        # Import districts
        for district_data in city_data.get('districts', []):
            self.import_district(district_data, city_collection)

        return city_data

    def import_district(self, district_data: Dict[str, Any], parent_collection: bpy.types.Collection):
        """Import individual district"""

        district_name = district_data.get('name', 'District')
        district_collection = bpy.data.collections.new(district_name)
        parent_collection.children.link(district_collection)

        # Import buildings in district
        for building_data in district_data.get('buildings', []):
            self.import_building(building_data, district_collection)

        self.district_collections.append(district_collection)

    def import_building(self, building_data: Dict[str, Any], collection: bpy.types.Collection):
        """Import individual building"""

        # Create mesh data
        mesh = bpy.data.meshes.new("BuildingMesh")
        obj = bpy.data.objects.new(building_data.get('id', 'Building'), mesh)

        # Add to collection
        collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        # Create cube geometry for building
        position = building_data.get('position', [0, 0, 0])
        size = building_data.get('size', [50, 50, 100])

        # Create simple cube
        verts = [
            (0, 0, 0), (size[0], 0, 0), (size[0], size[1], 0), (0, size[1], 0),
            (0, 0, size[2]), (size[0], 0, size[2]), (size[0], size[1], size[2]), (0, size[1], size[2])
        ]

        faces = [
            (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
            (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7)
        ]

        mesh.from_pydata(verts, [], faces)
        mesh.update()

        # Set position
        obj.location = position

        # Apply material based on building type
        material = self.create_building_material(building_data.get('material', 'brick'))
        obj.data.materials.append(material)

        self.building_objects.append(obj)

        return obj

    @staticmethod
    def create_building_material(material_type: str) -> bpy.types.Material:
        """Create material for building based on type"""

        mat = bpy.data.materials.new(name=f"Material_{material_type}")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        bsdf = nodes["Principled BSDF"]

        # Set colors based on material type
        color_map = {
            'brick': (0.8, 0.4, 0.3, 1.0),
            'glass': (0.7, 0.9, 1.0, 0.3),
            'concrete': (0.5, 0.5, 0.5, 1.0),
            'marble': (0.9, 0.9, 0.9, 1.0),
            'mixed': (0.6, 0.6, 0.6, 1.0)
        }

        color = color_map.get(material_type, (0.8, 0.8, 0.8, 1.0))
        bsdf.inputs['Base Color'].default_value = color

        if material_type == 'glass':
            bsdf.inputs['Transmission'].default_value = 1.0
            bsdf.inputs['Alpha'].default_value = 0.3

        return mat

    def apply_city_lighting(self, city_obj_collection: bpy.types.Collection):
        """Apply lighting to city"""

        # Add sun light
        light_data = bpy.data.lights.new(name="CityLight", type='SUN')
        light_data.energy = 2.0
        light_obj = bpy.data.objects.new("CityLight", light_data)
        bpy.context.scene.collection.objects.link(light_obj)
        light_obj.location = (0, 0, 100)
        light_obj.rotation_euler = (0.5, 0.5, 0)

        # Add ambient light
        ambient_data = bpy.data.lights.new(name="AmbientLight", type='AREA')
        ambient_data.energy = 1.0
        ambient_obj = bpy.data.objects.new("AmbientLight", ambient_data)
        bpy.context.scene.collection.objects.link(ambient_obj)
        ambient_obj.location = (0, 0, 200)

    def create_road_network(self, roads_data: List[Dict[str, Any]]) -> List[bpy.types.Object]:
        """Create road network between buildings"""

        road_objects = []

        for road_idx, road in enumerate(roads_data):
            start = road.get('start', [0, 0, 0])
            end = road.get('end', [100, 100, 0])
            width = road.get('width', 10.0)

            # Create road mesh
            mesh = bpy.data.meshes.new(f"Road_{road_idx}")
            obj = bpy.data.objects.new(f"Road_{road_idx}", mesh)

            bpy.context.scene.collection.objects.link(obj)

            # Create simple road (rectangular plane)
            verts = [
                (start[0], start[1] - width/2, start[2]),
                (start[0], start[1] + width/2, start[2]),
                (end[0], end[1] + width/2, end[2]),
                (end[0], end[1] - width/2, end[2])
            ]

            faces = [(0, 1, 2, 3)]

            mesh.from_pydata(verts, [], faces)
            mesh.update()

            road_objects.append(obj)

        return road_objects

    def get_city_summary(self) -> Dict[str, Any]:
        """Get summary of imported city"""
        return {
            "total_buildings": len(self.building_objects),
            "total_districts": len(self.district_collections),
            "buildings": [obj.name for obj in self.building_objects]
        }


class UnrealWeaponImporter:
    """Import procedural weapons into Blender"""

    @staticmethod
    def import_weapons_from_json(filepath: str) -> List[Dict[str, Any]]:
        """Import weapon data from JSON"""

        with open(filepath, 'r') as f:
            data = json.load(f)

        return data.get('weapons', [])

    @staticmethod
    def create_weapon_model(weapon_data: Dict[str, Any]) -> bpy.types.Object:
        """Create 3D model for weapon"""

        weapon_type = weapon_data.get('weapon_type', 'sword')

        # Create mesh based on weapon type
        mesh = bpy.data.meshes.new(f"Weapon_{weapon_data.get('weapon_id', 'default')}")
        obj = bpy.data.objects.new(weapon_data.get('weapon_name', 'Weapon'), mesh)

        bpy.context.scene.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj

        # Generate simple weapon geometry
        if weapon_type == 'sword':
            verts = [
                (-1, 0, 0), (1, 0, 0), (1, 0, 5), (-1, 0, 5),  # Blade
                (-0.5, 0, 5), (0.5, 0, 5), (0.5, 0, 6), (-0.5, 0, 6)  # Cross-guard
            ]
            faces = [
                (0, 1, 2, 3),  # Blade
                (4, 5, 6, 7),  # Cross-guard
                (0, 3, 6, 5, 1)  # Connection
            ]

        elif weapon_type == 'bow':
            verts = [
                (0, -3, 0), (0.5, -2, 0), (0.5, 2, 0), (0, 3, 0),
                (-0.5, 2, 0), (-0.5, -2, 0)
            ]
            faces = [(0, 1, 2, 3, 4, 5)]

        elif weapon_type == 'hammer':
            verts = [
                (-1, 0, 3), (1, 0, 3), (1, 1, 3), (-1, 1, 3),  # Head
                (-1, 1, 4), (1, 1, 4), (0.2, 1, 5), (-0.2, 1, 5)  # Handle
            ]
            faces = [
                (0, 1, 2, 3),
                (4, 5, 6, 7),
                (3, 2, 5, 4)
            ]

        else:
            # Default simple weapon
            verts = [(0, 0, 0), (1, 0, 0), (1, 0, 5), (0, 0, 5)]
            faces = [(0, 1, 2, 3)]

        mesh.from_pydata(verts, [], faces)
        mesh.update()

        # Add material
        material = UnrealCityImporter.create_building_material('mixed')
        obj.data.materials.append(material)

        return obj


# Blender operator for importing
class UNREAL_OT_import_terrain(bpy.types.Operator):
    """Import procedural terrain from OBJ"""
    bl_idname = "unreal.import_terrain"
    bl_label = "Import Terrain"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        terrain = UnrealTerrainImporter.import_terrain_from_obj(self.filepath)
        UnrealTerrainImporter.apply_terrain_material(terrain)
        self.report({'INFO'}, f"Terrain imported: {terrain.name}")
        return {'FINISHED'}


class UNREAL_OT_import_city(bpy.types.Operator):
    """Import procedural city from JSON"""
    bl_idname = "unreal.import_city"
    bl_label = "Import City"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        importer = UnrealCityImporter()
        city_data = importer.import_city_from_json(self.filepath)
        self.report({'INFO'}, f"City imported: {city_data.get('city_name')}")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(UNREAL_OT_import_terrain)
    bpy.utils.register_class(UNREAL_OT_import_city)


def unregister():
    bpy.utils.unregister_class(UNREAL_OT_import_terrain)
    bpy.utils.unregister_class(UNREAL_OT_import_city)


if __name__ == "__main__":
    register()
