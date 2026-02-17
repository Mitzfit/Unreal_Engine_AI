"""
╔══════════════════════════════════════════════════════════════╗
║    PROCEDURAL GENERATION ENGINE  ·  procedural_gen.py        ║
║  Terrain · Dungeons · Cities · Items · Names · WFC · Biomes  ║
╚══════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import asyncio, json, math, random, uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════ ENUMS ══════════════════════════════
class BiomeType(Enum):
    PLAINS       = "plains"
    FOREST       = "forest"
    DESERT       = "desert"
    TUNDRA       = "tundra"
    SWAMP        = "swamp"
    MOUNTAIN     = "mountain"
    OCEAN        = "ocean"
    JUNGLE       = "jungle"
    VOLCANIC     = "volcanic"
    MAGICAL      = "magical"

class DungeonStyle(Enum):
    CAVE         = "cave"
    RUINS        = "ruins"
    CASTLE       = "castle"
    SEWER        = "sewer"
    CRYPT        = "crypt"
    TEMPLE       = "temple"
    MINE         = "mine"
    LABORATORY   = "laboratory"

class ItemRarity(Enum):
    COMMON       = "common"
    UNCOMMON     = "uncommon"
    RARE         = "rare"
    EPIC         = "epic"
    LEGENDARY    = "legendary"

class ItemType(Enum):
    WEAPON       = "weapon"
    ARMOR        = "armor"
    CONSUMABLE   = "consumable"
    ACCESSORY    = "accessory"
    MATERIAL     = "material"
    QUEST        = "quest"


# ════════════════════════ DATA CLASSES ══════════════════════════
@dataclass
class TerrainCell:
    x: int; z: int
    height:     float = 0.0
    moisture:   float = 0.0
    temperature:float = 0.5
    biome:      BiomeType = BiomeType.PLAINS
    walkable:   bool  = True
    objects:    List[str] = field(default_factory=list)   # "tree","rock","bush"

    def to_dict(self) -> Dict:
        return {"x":self.x,"z":self.z,"height":round(self.height,2),
                "biome":self.biome.value,"walkable":self.walkable,"objects":self.objects}


@dataclass
class Room:
    room_id: str
    x: int; z: int
    width: int; height: int
    room_type: str = "normal"   # normal,boss,treasure,start,shop,puzzle
    connections: List[str] = field(default_factory=list)
    enemies:     List[str] = field(default_factory=list)
    items:       List[str] = field(default_factory=list)
    description: str       = ""

    @property
    def center(self) -> Tuple[int,int]:
        return (self.x + self.width//2, self.z + self.height//2)

    def overlaps(self, other:"Room", padding:int=1) -> bool:
        return not (self.x + self.width  + padding <= other.x or
                    other.x + other.width + padding <= self.x or
                    self.z + self.height + padding <= other.z or
                    other.z + other.height+ padding <= self.z)

    def to_dict(self) -> Dict:
        return {"id":self.room_id,"x":self.x,"z":self.z,
                "w":self.width,"h":self.height,"type":self.room_type,
                "connections":self.connections,"enemies":self.enemies,"items":self.items}


@dataclass
class Dungeon:
    dungeon_id: str
    style:      DungeonStyle
    width:      int
    height:     int
    rooms:      List[Room]             = field(default_factory=list)
    corridors:  List[Tuple[int,int,int,int]] = field(default_factory=list)
    grid:       List[List[int]]        = field(default_factory=list)   # 0=wall,1=floor,2=door
    seed:       int                    = 0

    def to_dict(self) -> Dict:
        return {"dungeon_id":self.dungeon_id,"style":self.style.value,
                "width":self.width,"height":self.height,"seed":self.seed,
                "rooms":[r.to_dict() for r in self.rooms],
                "room_count":len(self.rooms)}


@dataclass
class GeneratedItem:
    item_id:    str
    name:       str
    item_type:  ItemType
    rarity:     ItemRarity
    stats:      Dict[str, Any]
    description:str = ""
    lore:       str = ""
    value:      int = 0

    def to_dict(self) -> Dict:
        return {"id":self.item_id,"name":self.name,"type":self.item_type.value,
                "rarity":self.rarity.value,"stats":self.stats,
                "description":self.description,"value":self.value}


@dataclass
class City:
    city_id:  str
    name:     str
    size:     str          # village, town, city, capital
    biome:    BiomeType
    districts:List[Dict]  = field(default_factory=list)
    npcs:     List[Dict]  = field(default_factory=list)
    shops:    List[Dict]  = field(default_factory=list)
    points_of_interest: List[str] = field(default_factory=list)
    lore:     str         = ""

    def to_dict(self) -> Dict:
        return {"city_id":self.city_id,"name":self.name,"size":self.size,
                "biome":self.biome.value,"districts":len(self.districts),
                "npcs":len(self.npcs),"shops":len(self.shops),
                "poi":self.points_of_interest,"lore":self.lore}


# ═══════════════════════ NOISE UTILITIES ════════════════════════
class Noise:
    """Lightweight pure-Python Perlin-like noise (no deps)."""

    @staticmethod
    def fade(t): return t*t*t*(t*(t*6-15)+10)

    @staticmethod
    def lerp(a,b,t): return a+t*(b-a)

    @staticmethod
    def grad(h,x,y):
        h &= 3
        if h==0: return  x+y
        if h==1: return -x+y
        if h==2: return  x-y
        return          -x-y

    @classmethod
    def perlin(cls, x:float, y:float, seed:int=0) -> float:
        rng = random.Random(seed)
        perm = list(range(256)); rng.shuffle(perm); perm *= 2
        xi,yi = int(x)&255, int(y)&255
        xf,yf = x-int(x), y-int(y)
        u,v   = cls.fade(xf), cls.fade(yf)
        aa = perm[perm[xi  ]+yi]
        ab = perm[perm[xi  ]+yi+1]
        ba = perm[perm[xi+1]+yi]
        bb = perm[perm[xi+1]+yi+1]
        return cls.lerp(
            cls.lerp(cls.grad(aa,xf,yf),   cls.grad(ba,xf-1,yf),   u),
            cls.lerp(cls.grad(ab,xf,yf-1), cls.grad(bb,xf-1,yf-1), u), v)

    @classmethod
    def octave(cls, x:float, y:float, octaves:int=4,
               persistence:float=0.5, lacunarity:float=2.0, seed:int=0) -> float:
        val, amp, freq, mx = 0.0, 1.0, 1.0, 0.0
        for o in range(octaves):
            val += cls.perlin(x*freq, y*freq, seed+o) * amp
            mx  += amp; amp *= persistence; freq *= lacunarity
        return val / mx


# ═══════════════════════ TERRAIN GENERATOR ══════════════════════
class TerrainGenerator:
    """Generates heightmap + biome grid using fractal noise."""

    BIOME_TABLE = {
        # (cold, dry) → biome
        (True,  True):  BiomeType.TUNDRA,
        (True,  False): BiomeType.TUNDRA,
        (False, True):  BiomeType.DESERT,
        (False, False): BiomeType.PLAINS,
    }

    def generate(self, width:int=64, height:int=64, seed:int=None,
                 sea_level:float=0.35) -> List[List[TerrainCell]]:
        seed = seed or random.randint(0, 9999)
        grid: List[List[TerrainCell]] = []
        for z in range(height):
            row = []
            for x in range(width):
                nx, nz = x/width*3, z/height*3
                h  = Noise.octave(nx, nz, octaves=6, seed=seed)
                mo = Noise.octave(nx+100, nz+100, octaves=4, seed=seed+1)
                te = Noise.octave(nx+200, nz+200, octaves=3, seed=seed+2)
                # normalise -1..1 → 0..1
                h  = (h  + 1) / 2
                mo = (mo + 1) / 2
                te = (te + 1) / 2
                cell = TerrainCell(x, z, h, mo, te)
                cell.biome    = self._biome(h, mo, te, sea_level)
                cell.walkable = h > sea_level
                cell.objects  = self._scatter(cell, seed)
                row.append(cell)
            grid.append(row)
        return grid

    def _biome(self, h:float, m:float, t:float, sl:float) -> BiomeType:
        if h < sl:           return BiomeType.OCEAN
        if h > 0.82:         return BiomeType.MOUNTAIN
        if t > 0.75 and m > 0.6: return BiomeType.JUNGLE
        if t > 0.7 and m < 0.3:  return BiomeType.DESERT
        if t < 0.3 and m > 0.4:  return BiomeType.TUNDRA
        if m > 0.7:          return BiomeType.SWAMP
        if m > 0.5:          return BiomeType.FOREST
        if t > 0.6:          return BiomeType.PLAINS
        return BiomeType.PLAINS

    def _scatter(self, cell:TerrainCell, seed:int) -> List[str]:
        if not cell.walkable: return []
        rng = random.Random(seed + cell.x * 1000 + cell.z)
        if rng.random() > 0.85:
            return {"forest":[rng.choice(["pine","oak","birch"])],
                    "jungle":[rng.choice(["palm","fern","vine"])],
                    "desert":[rng.choice(["cactus","dune"])],
                    "mountain":[rng.choice(["boulder","cliff"])],
                    "plains":[rng.choice(["grass_patch","flower","shrub"])],
                    }.get(cell.biome.value, [])
        return []

    def export_json(self, grid:List[List[TerrainCell]], out:str="exports") -> str:
        Path(out).mkdir(parents=True, exist_ok=True)
        p = f"{out}/terrain_{uuid.uuid4().hex[:6]}.json"
        flat = [c.to_dict() for row in grid for c in row]
        Path(p).write_text(json.dumps({"width":len(grid[0]),"height":len(grid),
                                       "cells":flat},indent=2)); return p


# ═══════════════════════ DUNGEON GENERATOR ══════════════════════
class DungeonGenerator:
    """BSP-based dungeon with corridors, room types, enemies & loot."""

    ENEMY_POOLS = {
        DungeonStyle.CAVE:       ["bat","cave_spider","troll","cave_bear"],
        DungeonStyle.RUINS:      ["skeleton","ghost","cursed_knight","lich"],
        DungeonStyle.CASTLE:     ["guard","archer","knight","dark_lord"],
        DungeonStyle.SEWER:      ["rat","slime","rogue","plague_rat"],
        DungeonStyle.CRYPT:      ["zombie","vampire","wraith","death_knight"],
        DungeonStyle.TEMPLE:     ["cultist","golem","high_priest","divine_guardian"],
        DungeonStyle.MINE:       ["miner_zombie","rock_golem","cave_in","drill_bot"],
        DungeonStyle.LABORATORY: ["experiment","robot","mad_scientist","mutant"],
    }

    def generate(self, width:int=80, height:int=60, seed:int=None,
                 style:DungeonStyle=DungeonStyle.RUINS,
                 min_rooms:int=8, max_rooms:int=20,
                 difficulty:int=3) -> Dungeon:
        seed = seed or random.randint(0,99999)
        rng  = random.Random(seed)
        # init grid (0=wall)
        grid = [[0]*width for _ in range(height)]
        rooms: List[Room] = []

        # place rooms
        attempts = 0
        while len(rooms) < max_rooms and attempts < 500:
            attempts += 1
            w = rng.randint(5, 15)
            h = rng.randint(5, 12)
            x = rng.randint(1, width  - w - 1)
            z = rng.randint(1, height - h - 1)
            candidate = Room(str(uuid.uuid4())[:6], x, z, w, h)
            if any(candidate.overlaps(r) for r in rooms): continue
            # carve floor
            for rz in range(z, z+h):
                for rx in range(x, x+w):
                    grid[rz][rx] = 1
            rooms.append(candidate)

        # connect rooms with L-shaped corridors
        for i in range(1, len(rooms)):
            ax, az = rooms[i-1].center
            bx, bz = rooms[i].center
            if rng.random() < 0.5:
                self._hcorridor(grid, ax, bx, az)
                self._vcorridor(grid, az, bz, bx)
            else:
                self._vcorridor(grid, az, bz, ax)
                self._hcorridor(grid, ax, bx, bz)
            rooms[i-1].connections.append(rooms[i].room_id)
            rooms[i].connections.append(rooms[i-1].room_id)

        # assign room types
        rng.shuffle(rooms)
        if rooms: rooms[0].room_type = "start"
        if len(rooms) > 1: rooms[-1].room_type = "boss"
        treasure_idx = len(rooms)//3
        if treasure_idx < len(rooms): rooms[treasure_idx].room_type = "treasure"
        shop_idx = 2*len(rooms)//3
        if shop_idx < len(rooms): rooms[shop_idx].room_type = "shop"

        # populate
        pool = self.ENEMY_POOLS.get(style, ["goblin","orc"])
        for room in rooms:
            if room.room_type == "start": continue
            count = {"boss":3,"treasure":0,"shop":0,"normal":rng.randint(1,difficulty+1)}.get(room.room_type,1)
            room.enemies = [rng.choice(pool) for _ in range(count)]
            if room.room_type in ("treasure","boss"):
                room.items = [ItemGenerator.random_item(rng, difficulty).name for _ in range(rng.randint(1,3))]

        return Dungeon(str(uuid.uuid4())[:8], style, width, height, rooms, [], grid, seed)

    @staticmethod
    def _hcorridor(grid, x1, x2, z):
        for x in range(min(x1,x2), max(x1,x2)+1):
            if 0<=z<len(grid) and 0<=x<len(grid[0]): grid[z][x]=1

    @staticmethod
    def _vcorridor(grid, z1, z2, x):
        for z in range(min(z1,z2), max(z1,z2)+1):
            if 0<=z<len(grid) and 0<=x<len(grid[0]): grid[z][x]=1

    def export_json(self, dungeon:Dungeon, out:str="exports") -> str:
        Path(out).mkdir(parents=True, exist_ok=True)
        p = f"{out}/dungeon_{dungeon.dungeon_id}.json"
        Path(p).write_text(json.dumps(dungeon.to_dict(),indent=2)); return p

    def to_ascii(self, dungeon:Dungeon) -> str:
        symbols = {0:"█", 1:"·", 2:"+"}
        lines   = []
        for row in dungeon.grid:
            lines.append("".join(symbols.get(c,"?") for c in row))
        return "\n".join(lines)


# ═══════════════════════ CITY GENERATOR ═════════════════════════
class CityGenerator:
    DISTRICTS = {
        "capital": ["Palace Quarter","Noble District","Market Place","Temple District",
                    "Scholar's Row","Harbour Front","Slums","Barracks"],
        "city":    ["Market","Residential","Temple","Craftsmen Quarter","Docks","Guard Tower"],
        "town":    ["Town Square","Inn District","Blacksmith Row","Chapel"],
        "village": ["Village Green","Farmsteads","Small Chapel"],
    }
    SHOP_TYPES = ["General Store","Blacksmith","Alchemist","Tailor","Stable",
                  "Jeweller","Herbalist","Enchanter","Tavern","Library"]
    NPC_ROLES  = ["guard","merchant","healer","sage","innkeeper","blacksmith",
                  "farmer","priest","soldier","noble","thief","bard"]

    def generate(self, size:str="town", biome:BiomeType=BiomeType.PLAINS,
                 seed:int=None) -> City:
        seed = seed or random.randint(0,9999)
        rng  = random.Random(seed)
        name = NameGenerator.city_name(seed)
        districts = [{"name":d,"buildings":rng.randint(5,20)}
                     for d in self.DISTRICTS.get(size, self.DISTRICTS["village"])]
        shop_count = {"village":3,"town":6,"city":12,"capital":20}.get(size,4)
        shops = [{"type":rng.choice(self.SHOP_TYPES), "name":f"The {NameGenerator.word(seed+i)} {rng.choice(['Shop','Emporium','Stand'])}"} for i in range(shop_count)]
        npc_count  = {"village":5,"town":15,"city":40,"capital":100}.get(size,5)
        npcs = [{"name":NameGenerator.person_name(seed+i),"role":rng.choice(self.NPC_ROLES)} for i in range(npc_count)]
        poi_pool = ["Ancient Ruins","Hidden Cellar","Mysterious Well","Old Cemetery",
                    "Underground Arena","Secret Garden","Crumbling Tower","Lost Library"]
        poi = rng.sample(poi_pool, min(rng.randint(1,3), len(poi_pool)))
        lore = f"{name} is a {size} nestled in the {biome.value} region. "
        lore += rng.choice(["Founded centuries ago by wandering settlers.",
                             "Built on the ruins of an ancient civilization.",
                             "Grown rich from trade along the river.",
                             "A strategic fortress town guarding the mountain pass."])
        return City(str(uuid.uuid4())[:8], name, size, biome, districts, npcs, shops, poi, lore)


# ═══════════════════════ ITEM GENERATOR ═════════════════════════
class ItemGenerator:
    WEAPON_PREFIXES = {
        ItemRarity.COMMON:    ["Worn","Crude","Basic"],
        ItemRarity.UNCOMMON:  ["Sharp","Sturdy","Reliable"],
        ItemRarity.RARE:      ["Masterwork","Enchanted","Gleaming"],
        ItemRarity.EPIC:      ["Ancient","Mythic","Forged"],
        ItemRarity.LEGENDARY: ["Godslayer","Eternal","Divine"],
    }
    WEAPON_NAMES = ["Sword","Axe","Dagger","Spear","Mace","Bow","Staff","Wand","Crossbow","Halberd"]
    ARMOR_NAMES  = ["Helmet","Chestplate","Gauntlets","Greaves","Shield","Cloak","Ring","Amulet"]
    MATERIALS    = ["Iron","Steel","Mithril","Adamantite","Shadow-","Dragon-","Crystal-","Void-"]
    SUFFIXES     = ["of Power","of Speed","of Protection","of Fire","of Ice","of Lightning",
                    "of the Bear","of the Fox","of the Eagle","of Destruction"]

    RARITY_WEIGHTS = [50, 30, 15, 4, 1]  # common → legendary

    @classmethod
    def random_item(cls, rng:random.Random=None, level:int=1) -> "GeneratedItem":
        rng    = rng or random.Random()
        rarity = random.choices(list(ItemRarity), weights=cls.RARITY_WEIGHTS, k=1)[0]
        itype  = rng.choice(list(ItemType))
        return cls._make(rng, itype, rarity, level)

    @classmethod
    def _make(cls, rng:random.Random, itype:ItemType, rarity:ItemRarity, lvl:int) -> "GeneratedItem":
        mult = {ItemRarity.COMMON:1,ItemRarity.UNCOMMON:1.5,ItemRarity.RARE:2.5,
                ItemRarity.EPIC:4.0,ItemRarity.LEGENDARY:8.0}[rarity]
        prefix = rng.choice(cls.WEAPON_PREFIXES[rarity])
        mat    = rng.choice(cls.MATERIALS)
        suffix = rng.choice(cls.SUFFIXES) if rarity.value in ("rare","epic","legendary") else ""
        if itype == ItemType.WEAPON:
            base = rng.choice(cls.WEAPON_NAMES)
            name = f"{prefix} {mat}{base}{' '+suffix if suffix else ''}"
            stats = {"damage":round(rng.uniform(5,15)*lvl*mult,1),
                     "attack_speed":round(rng.uniform(0.8,1.5),2),
                     "crit_chance":round(rng.uniform(0.02,0.1)*mult,3)}
        elif itype == ItemType.ARMOR:
            base = rng.choice(cls.ARMOR_NAMES)
            name = f"{prefix} {mat}{base}{' '+suffix if suffix else ''}"
            stats = {"defense":round(rng.uniform(3,10)*lvl*mult,1),
                     "hp_bonus":round(rng.uniform(0,20)*lvl*mult,1),
                     "weight":round(rng.uniform(1,5),1)}
        else:
            name  = f"{prefix} Potion of Power"
            stats = {"effect_value":round(50*lvl*mult),"duration_secs":30}
        value = int(10 * lvl * mult * rng.uniform(0.8,1.2))
        desc  = f"A {rarity.value} {itype.value}. {rng.choice(['Found in ancient ruins.','Crafted by master artisans.','Imbued with magical energies.','Passed down through generations.'])}"
        return GeneratedItem(str(uuid.uuid4())[:6], name, itype, rarity, stats, desc, value=value)

    @classmethod
    def loot_table(cls, count:int=5, level:int=1, rng:random.Random=None) -> List["GeneratedItem"]:
        rng = rng or random.Random()
        return [cls.random_item(rng, level) for _ in range(count)]


# ═══════════════════════ NAME GENERATOR ═════════════════════════
class NameGenerator:
    SYLLABLES_F  = ["ar","el","thi","syl","vom","kael","zar","lun","aer","sen"]
    SYLLABLES_M  = ["dor","grim","tor","val","bael","ron","mor","gar","skar","ven"]
    CITY_START   = ["Iron","Silver","Gold","Shadow","Storm","Black","White","Red","Frost","Dawn"]
    CITY_END     = ["keep","haven","ford","hold","port","vale","burg","reach","gate","fall"]
    ADJ          = ["Shimmering","Ancient","Forsaken","Verdant","Molten","Arcane","Crimson","Hollow"]

    @classmethod
    def person_name(cls, seed:int=None) -> str:
        rng = random.Random(seed)
        syl = cls.SYLLABLES_F if rng.random()>0.5 else cls.SYLLABLES_M
        n   = rng.randint(2,3)
        return "".join(rng.choice(syl) for _ in range(n)).capitalize()

    @classmethod
    def city_name(cls, seed:int=None) -> str:
        rng = random.Random(seed)
        return rng.choice(cls.CITY_START) + rng.choice(cls.CITY_END)

    @classmethod
    def word(cls, seed:int=None) -> str:
        rng = random.Random(seed)
        return rng.choice(cls.ADJ)

    @classmethod
    def quest_name(cls, seed:int=None) -> str:
        rng   = random.Random(seed)
        verbs = ["Rescue","Defend","Retrieve","Destroy","Investigate","Escort","Survive"]
        nouns = ["the Lost Relic","the Dark Lord","the Ancient Seal","the Stolen Crown",
                 "the Cursed Village","the Hidden Tomb","the Forbidden Library"]
        return f"{rng.choice(verbs)} {rng.choice(nouns)}"

    @classmethod
    def npc_title(cls, role:str, seed:int=None) -> str:
        rng = random.Random(seed)
        titles = {"warrior":["Blade of ","Warrior of ","Champion of "],
                  "mage":   ["Archmage of ","Sorcerer of ","Keeper of "],
                  "rogue":  ["Shadow of ","Thief of ","Assassin of "]}
        prefix = rng.choice(titles.get(role, ["Guardian of "]))
        return prefix + cls.city_name(seed)


# ═══════════════════════ WAVE FUNCTION COLLAPSE ═════════════════
class WFCTileMap:
    """Simplified Wave Function Collapse for tilemap generation."""

    def __init__(self, tile_rules: Dict[str, List[str]]):
        """
        tile_rules: {tile_id: [allowed_neighbours, ...]}
        Example: {"grass":["grass","dirt"],"water":["water","sand"]}
        """
        self.rules    = tile_rules
        self.all_tiles= list(tile_rules.keys())

    def generate(self, width:int, height:int, seed:int=None) -> List[List[str]]:
        rng   = random.Random(seed)
        # init: every cell can be any tile
        grid:List[List[Optional[Set[str]]]] = [
            [set(self.all_tiles) for _ in range(width)] for _ in range(height)
        ]
        result:List[List[str]] = [["" for _ in range(width)] for _ in range(height)]
        unresolved = set((x,z) for x in range(width) for z in range(height))

        while unresolved:
            # pick lowest entropy cell (fewest options)
            min_e = min(len(grid[z][x]) for x,z in unresolved if grid[z][x])
            candidates = [(x,z) for x,z in unresolved if grid[z][x] and len(grid[z][x])==min_e]
            if not candidates: break
            cx,cz = rng.choice(candidates)
            options = list(grid[cz][cx])
            chosen  = rng.choice(options)
            result[cz][cx] = chosen
            grid[cz][cx]   = {chosen}
            unresolved.discard((cx,cz))
            # propagate constraints
            for dx,dz in [(0,1),(0,-1),(1,0),(-1,0)]:
                nx,nz = cx+dx, cz+dz
                if 0<=nx<width and 0<=nz<height and (nx,nz) in unresolved:
                    allowed = set(self.rules.get(chosen,[]))
                    grid[nz][nx] &= allowed
                    if not grid[nz][nx]:
                        grid[nz][nx] = {rng.choice(self.all_tiles)}  # backtrack fallback
        return result


# ═══════════════════════ MAIN GENERATOR ═════════════════════════
class ProceduralGenerator:
    """One-stop shop: world, dungeon, city, items, names — all from one object."""

    def __init__(self, openai_key:str="", seed:int=None):
        self.openai_key = openai_key
        self.seed       = seed or random.randint(0,999999)
        self._rng       = random.Random(self.seed)
        self.terrain_gen= TerrainGenerator()
        self.dungeon_gen= DungeonGenerator()
        self.city_gen   = CityGenerator()
        self.item_gen   = ItemGenerator()
        self.name_gen   = NameGenerator()

    # ── Terrain ──────────────────────────────────
    def generate_world(self, width:int=64, height:int=64) -> List[List[TerrainCell]]:
        return self.terrain_gen.generate(width, height, seed=self.seed)

    # ── Dungeon ───────────────────────────────────
    def generate_dungeon(self, style:DungeonStyle=DungeonStyle.RUINS,
                         width:int=80, height:int=60, difficulty:int=3) -> Dungeon:
        return self.dungeon_gen.generate(width, height, seed=self._rng.randint(0,99999),
                                         style=style, difficulty=difficulty)

    # ── City ─────────────────────────────────────
    def generate_city(self, size:str="town", biome:BiomeType=BiomeType.PLAINS) -> City:
        return self.city_gen.generate(size, biome, seed=self._rng.randint(0,9999))

    # ── Items ─────────────────────────────────────
    def generate_loot(self, count:int=5, level:int=1) -> List[GeneratedItem]:
        return self.item_gen.loot_table(count, level, self._rng)

    def generate_item(self, itype:ItemType=None, rarity:ItemRarity=None, level:int=1) -> GeneratedItem:
        r = rarity or random.choices(list(ItemRarity), weights=[50,30,15,4,1],k=1)[0]
        t = itype  or self._rng.choice(list(ItemType))
        return self.item_gen._make(self._rng, t, r, level)

    # ── Names ─────────────────────────────────────
    def person_name(self)  -> str: return self.name_gen.person_name(self._rng.randint(0,9999))
    def city_name(self)    -> str: return self.name_gen.city_name(self._rng.randint(0,9999))
    def quest_name(self)   -> str: return self.name_gen.quest_name(self._rng.randint(0,9999))

    # ── WFC tilemap ───────────────────────────────
    def generate_tilemap(self, rules:Dict[str,List[str]], width:int=20, height:int=20) -> List[List[str]]:
        return WFCTileMap(rules).generate(width, height, seed=self.seed)

    # ── AI-enhanced world ─────────────────────────
    async def ai_generate_world_lore(self, world_description:str) -> Dict:
        prompt = f"""Generate rich world-building lore for a game world:

Description: {world_description}

Return JSON:
{{
  "world_name": "Name",
  "history": "3-4 sentence history",
  "factions": [{{"name":"str","description":"str","alignment":"good|neutral|evil"}}],
  "myths": ["myth1","myth2","myth3"],
  "locations": [{{"name":"str","type":"str","description":"str"}}],
  "threats": ["threat1","threat2"]
}}"""
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization":f"Bearer {self.openai_key}","Content-Type":"application/json"},
                    json={"model":"gpt-4-turbo-preview",
                          "messages":[{"role":"user","content":prompt}],
                          "response_format":{"type":"json_object"}}
                ) as r:
                    d = await r.json()
                    return json.loads(d["choices"][0]["message"]["content"])
        except Exception:
            return {"world_name": self.city_name(),
                    "history": "A land shaped by ancient wars and forgotten gods.",
                    "factions": [], "myths": [], "locations": [], "threats": []}

    # ── Full world export ─────────────────────────
    def export_world(self, out:str="exports") -> Dict[str,str]:
        Path(out).mkdir(parents=True, exist_ok=True)
        files = {}
        # terrain
        grid = self.generate_world(64,64)
        files["terrain"] = self.terrain_gen.export_json(grid, out)
        # dungeon
        d = self.generate_dungeon()
        files["dungeon"] = self.dungeon_gen.export_json(d, out)
        # cities
        cities = [self.generate_city(s, self._rng.choice(list(BiomeType)))
                  for s in ("village","town","city","capital")]
        p = f"{out}/cities_{uuid.uuid4().hex[:6]}.json"
        Path(p).write_text(json.dumps([c.to_dict() for c in cities], indent=2))
        files["cities"] = p
        # items
        items = self.generate_loot(20, level=5)
        ip = f"{out}/items_{uuid.uuid4().hex[:6]}.json"
        Path(ip).write_text(json.dumps([i.to_dict() for i in items],indent=2))
        files["items"] = ip
        return files


# ════════════════════════ DEMO ═══════════════════════════════════
if __name__ == "__main__":
    gen = ProceduralGenerator(seed=42)

    print("=== TERRAIN ===")
    grid = gen.generate_world(32, 32)
    biome_counts: Dict[str,int] = {}
    for row in grid:
        for cell in row:
            biome_counts[cell.biome.value] = biome_counts.get(cell.biome.value,0)+1
    print("Biomes:", biome_counts)

    print("\n=== DUNGEON ===")
    d = gen.generate_dungeon(DungeonStyle.CRYPT, difficulty=4)
    print(f"Rooms: {len(d.rooms)} | Size: {d.width}x{d.height}")
    for r in d.rooms[:4]:
        print(f"  [{r.room_type:8s}] enemies={r.enemies[:2]} items={r.items}")
    print(gen.dungeon_gen.to_ascii(d)[:200]+"…")

    print("\n=== CITY ===")
    city = gen.generate_city("city", BiomeType.PLAINS)
    print(f"{city.name} | {city.size} | {len(city.npcs)} NPCs | {len(city.shops)} shops")
    print(city.lore)

    print("\n=== ITEMS ===")
    for item in gen.generate_loot(5, level=10):
        print(f"  [{item.rarity.value:10s}] {item.name} | dmg={item.stats.get('damage','—')} | {item.value}g")

    print("\n=== NAMES ===")
    print("People:", [gen.person_name() for _ in range(5)])
    print("Cities:", [gen.city_name()   for _ in range(5)])
    print("Quests:", [gen.quest_name()  for _ in range(3)])

    print("\n=== WFC TILEMAP ===")
    rules = {"grass":["grass","dirt","forest"],"dirt":["grass","dirt","stone"],
             "forest":["forest","grass"],"stone":["stone","dirt"],"water":["water","sand"],"sand":["sand","water","dirt"]}
    tilemap = gen.generate_tilemap(rules, 12, 6)
    for row in tilemap:
        print(" ".join(f"{c[:2]:2s}" for c in row))

    print("\n=== WORLD EXPORT ===")
    files = gen.export_world()
    for k,v in files.items(): print(f"  {k}: {v}")
