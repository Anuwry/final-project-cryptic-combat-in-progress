import json
import os
import pygame
import math
import time
import random
from src.config import BASE_DIR

class TileType:
    GRASS = 0
    DIRT = 1
    GRASS_FLOWER = 2
    STONE = 3
    WATER = 4
    BRIDGE = 5

class MapObject:
    def __init__(self, x, y, obj_type, data=None, collected=False):
        self.x = x
        self.y = y
        self.type = obj_type
        self.data = data or {}
        self.collected = collected
        
        if self.type in ['house_red', 'house_grey']:
            self.rect = pygame.Rect(x, y, 192, 192) 
        elif self.type in ['tree_green', 'tree_orange']:
            self.rect = pygame.Rect(x + 16, y + 64, 32, 64) 
        elif self.type == 'statue' and self.data.get('tier') == 'Boss':
            self.rect = pygame.Rect(x - 32, y - 32, 128, 128) 
        else:
            self.rect = pygame.Rect(x, y, 64, 64)
            
    def get_collision_rect(self):
        return self.rect

class GameMap:
    def __init__(self, realm_x=0, realm_y=0, force_normal=False):
        self.realm_x = realm_x
        self.realm_y = realm_y
        self.level = abs(realm_x) + abs(realm_y) + 1
        
        if force_normal:
            self.is_boss_realm = False
        else:
            self.is_boss_realm = (self.level > 1 and self.level % 5 == 0)
            
        self.map_file = os.path.join(BASE_DIR, f"data/maps/realm_{realm_x}_{realm_y}.json")
        self.tile_size = 64
        self.width = 32  
        self.height = 24
        self.grid = []
        self.objects = []
        self.spawn_point = [100, 100]
        self.camera_offset = [0, 0]
        self.target_camera_offset = [0, 0]
        
        self.tiles = {}
        self.prefabs = {}
        self.gods = ["Zeus", "Poseidon", "Hades", "Ares", "Athena", "Apollo", "Hermes"]
        self.load_tileset()
        self.load_map()
        
    def load_tileset(self):
        tileset_path = os.path.join(BASE_DIR, "assets", "images", "tilemap.png")
        try:
            tilesheet = pygame.image.load(tileset_path).convert_alpha()
            
            def get_tile(col, row):
                rect = pygame.Rect(col * 17, row * 17, 16, 16)
                image = pygame.Surface((16, 16), pygame.SRCALPHA)
                image.blit(tilesheet, (0, 0), rect)
                return pygame.transform.scale(image, (self.tile_size, self.tile_size))

            self.tiles['grass'] = get_tile(0, 0)
            self.tiles['grass_flower'] = get_tile(2, 0)
            self.tiles['stone'] = get_tile(0, 8)
            self.tiles['bridge'] = get_tile(8, 5)
            
            self.tiles['dirt'] = {
                'tl': get_tile(0, 1), 'tm': get_tile(1, 1), 'tr': get_tile(2, 1),
                'ml': get_tile(0, 2), 'mm': get_tile(1, 2), 'mr': get_tile(2, 2),
                'bl': get_tile(0, 3), 'bm': get_tile(1, 3), 'br': get_tile(2, 3),
            }

            house_red = pygame.Surface((192, 192), pygame.SRCALPHA)
            for r in range(3):
                for c in range(3): house_red.blit(get_tile(3 + c, 4 + r), (c * 64, r * 64))
            self.prefabs['house_red'] = house_red
            
            house_grey = pygame.Surface((192, 192), pygame.SRCALPHA)
            for r in range(3):
                for c in range(3): house_grey.blit(get_tile(0 + c, 4 + r), (c * 64, r * 64))
            self.prefabs['house_grey'] = house_grey

            tree_green = pygame.Surface((64, 128), pygame.SRCALPHA)
            tree_green.blit(get_tile(4, 0), (0, 0))
            tree_green.blit(get_tile(4, 1), (0, 64))
            self.prefabs['tree_green'] = tree_green
            
            tree_orange = pygame.Surface((64, 128), pygame.SRCALPHA)
            tree_orange.blit(get_tile(3, 0), (0, 0))
            tree_orange.blit(get_tile(3, 1), (0, 64))
            self.prefabs['tree_orange'] = tree_orange

        except Exception as e:
            print(f"Error loading tileset: {e}")
            self.tiles = None

    def load_map(self):
        try:
            with open(self.map_file, 'r') as f:
                data = json.load(f)
            self.width = data.get('width', 32)
            self.height = data.get('height', 24)
            self.tile_size = data.get('tile_size', 64)
            self.grid = data['grid']
            self.spawn_point = data.get('spawn_point', [100, 100])
            self.objects = [MapObject(o['x'], o['y'], o['type'], o.get('data', {}), o.get('collected', False)) for o in data.get('objects', [])]
        except FileNotFoundError:
            if self.realm_x == 0 and self.realm_y == 0:
                self._create_main_hub_map()
            elif self.is_boss_realm:
                self._create_boss_map()
            else:
                self._generate_smart_realm()
            self.save_map()
            
    def ensure_safe_spawn(self, x, y):
        player_rect = pygame.Rect(x - 32, y - 32, 128, 128)
        safe_objects = []
        for obj in self.objects:
            if obj.type in ['house_red', 'house_grey', 'tree_green', 'tree_orange']:
                if not obj.get_collision_rect().colliderect(player_rect):
                    safe_objects.append(obj)
            else:
                safe_objects.append(obj)
        self.objects = safe_objects

    def _create_main_hub_map(self):
        self.width, self.height = 32, 24
        self.grid = [[TileType.GRASS_FLOWER if random.random() < 0.1 else TileType.GRASS 
                      for _ in range(self.width)] for _ in range(self.height)]
        self.objects = []
        
        for y in range(10, 18):
            for x in range(12, 20): self.grid[y][x] = TileType.DIRT
        for y in range(self.height):
            self.grid[y][15] = TileType.DIRT; self.grid[y][16] = TileType.DIRT
        for x in range(self.width):
            self.grid[13][x] = TileType.DIRT; self.grid[14][x] = TileType.DIRT

        for x in range(self.width):
            if x not in (15, 16):
                self.grid[4][x] = TileType.WATER; self.grid[5][x] = TileType.WATER
            else:
                self.grid[4][x] = TileType.DIRT; self.grid[5][x] = TileType.DIRT

        self.objects.append(MapObject(9 * 64, 6 * 64, "house_grey"))
        self.objects.append(MapObject(20 * 64, 6 * 64, "house_red"))
        self.objects.append(MapObject(9 * 64, 17 * 64, "house_red"))
        self.objects.append(MapObject(20 * 64, 17 * 64, "house_grey"))
        
        self.objects.append(MapObject(15 * 64, 11 * 64, "statue", {"god": "Athena", "tier": "Follower"}))
        self.objects.append(MapObject(16 * 64, 11 * 64, "statue", {"god": "Apollo", "tier": "Follower"}))
        
        self.objects.append(MapObject(15 * 64, 15 * 64, "npc", {"name": "Grand Elder", "dialogue": "Welcome to the Sanctuary! Walk to any edge of the map to explore endless realms."}))
        self.objects.append(MapObject(16 * 64, 10 * 64, "npc", {"name": "Merchant", "dialogue": "SHOP"}))

        self.spawn_point = [15 * 64, 15 * 64]
        self._populate_decorations()
        
    def _create_boss_map(self):
        self.width, self.height = 32, 24
        self.grid = [[TileType.STONE for _ in range(self.width)] for _ in range(self.height)]
        self.objects = []
        
        for y in range(self.height):
            for x in range(self.width):
                if (x < 8 or x > self.width - 9) or (y < 6 or y > self.height - 7):
                    if x not in (15, 16) and y not in (11, 12, 13, 14):
                        self.grid[y][x] = TileType.WATER
                
        god = random.choice(self.gods)
        self.objects.append(MapObject(15 * 64, 10 * 64, "statue", {"god": god, "tier": "Boss"}))
        self.spawn_point = [15 * 64, 20 * 64]
            
    def _generate_smart_realm(self):
        self.width, self.height = 32, 24
        self.grid = [[TileType.GRASS_FLOWER if random.random() < 0.1 else TileType.GRASS 
                      for _ in range(self.width)] for _ in range(self.height)]
        self.objects = []
        
        theme = random.choice(['crossroad', 'horizontal', 'vertical', 'river_cross'])
        
        if theme in ['crossroad', 'horizontal', 'river_cross']:
            for x in range(self.width):
                self.grid[13][x] = TileType.DIRT
                self.grid[14][x] = TileType.DIRT
        
        if theme in ['crossroad', 'vertical', 'river_cross']:
            for y in range(self.height):
                self.grid[y][15] = TileType.DIRT
                self.grid[y][16] = TileType.DIRT
                
        if theme == 'river_cross':
            is_horizontal_river = random.choice([True, False])
            if is_horizontal_river:
                ry = random.choice([5, 6, 18, 19])
                for x in range(self.width):
                    if self.grid[ry][x] == TileType.DIRT: pass 
                    else:
                        self.grid[ry][x] = TileType.WATER
                        self.grid[ry+1][x] = TileType.WATER
            else:
                rx = random.choice([6, 7, 24, 25])
                for y in range(self.height):
                    if self.grid[y][rx] == TileType.DIRT: pass
                    else:
                        self.grid[y][rx] = TileType.WATER
                        self.grid[y][rx+1] = TileType.WATER
        
        self._populate_decorations(place_statues=True)

    def _populate_decorations(self, place_statues=False):
        def get_free_spot(w, h):
            for _ in range(50):
                rx, ry = random.randint(2, self.width - 2 - w), random.randint(2, self.height - 2 - h)
                free = True
                for dy in range(h):
                    for dx in range(w):
                        if self.grid[ry+dy][rx+dx] not in (TileType.GRASS, TileType.GRASS_FLOWER):
                            free = False; break
                        check_rect = pygame.Rect((rx+dx)*64, (ry+dy)*64, 64, 64)
                        for obj in self.objects:
                            if obj.get_collision_rect().colliderect(check_rect):
                                free = False; break
                    if not free: break
                if free: return rx, ry
            return None

        if place_statues and random.random() > 0.3:
            num_statues = random.randint(1, min(3, 1 + self.level // 3))
            for _ in range(num_statues):
                spot = get_free_spot(1, 1)
                if spot:
                    god = random.choice(self.gods)
                    tier = random.choices(["Follower", "Zealot", "Apostle"], [60, 30, 10])[0]
                    self.objects.append(MapObject(spot[0] * 64, spot[1] * 64, "statue", {"god": god, "tier": tier}))

        num_houses = random.randint(0, min(3, self.level))
        for _ in range(num_houses):
            spot = get_free_spot(3, 3)
            if spot: self.objects.append(MapObject(spot[0] * 64, spot[1] * 64, random.choice(['house_red', 'house_grey'])))
            
        for _ in range(random.randint(30, 60)):
            spot = get_free_spot(1, 2)
            if spot: self.objects.append(MapObject(spot[0] * 64, spot[1] * 64, random.choice(['tree_green', 'tree_orange'])))

    def save_map(self):
        os.makedirs(os.path.dirname(self.map_file), exist_ok=True)
        data = {
            'width': self.width, 'height': self.height, 'tile_size': self.tile_size,
            'grid': self.grid, 'spawn_point': self.spawn_point,
            'objects': [{'x': o.x, 'y': o.y, 'type': o.type, 'data': o.data, 'collected': o.collected} for o in self.objects]
        }
        with open(self.map_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_statues(self): return [o for o in self.objects if o.type == "statue"]
    def get_npcs(self): return [o for o in self.objects if o.type == "npc"]
    def get_nearby_statue(self, p_rect, dist=50):
        for o in self.objects:
            if o.type == "statue" and not o.collected and p_rect.colliderect(o.rect.inflate(dist, dist)): return o
        return None
    def get_nearby_npc(self, p_rect, dist=50):
        for o in self.objects:
            if o.type == "npc" and p_rect.colliderect(o.rect.inflate(dist, dist)): return o
        return None

    def check_collision_at(self, x, y, width, height):
        check_rect = pygame.Rect(x, y, width, height)
        grid_x, grid_y = int(x // self.tile_size), int(y // self.tile_size)
        
        if 0 <= grid_x < self.width and 0 <= grid_y < self.height:
            if self.grid[grid_y][grid_x] == TileType.WATER:
                return True

        for obj in self.objects:
            if obj.type in ['house_red', 'house_grey', 'tree_green', 'tree_orange']:
                if check_rect.colliderect(obj.get_collision_rect()):
                    return True
        return False
    
    def update_camera(self, player_x, player_y, screen_width, screen_height):
        target_x = screen_width // 2 - player_x
        target_y = screen_height // 2 - player_y
        min_x = screen_width - (self.width * self.tile_size)
        min_y = screen_height - (self.height * self.tile_size)
        self.target_camera_offset[0] = max(min_x, min(0, target_x))
        self.target_camera_offset[1] = max(min_y, min(0, target_y))
        self.camera_offset[0] += (self.target_camera_offset[0] - self.camera_offset[0]) * 0.1
        self.camera_offset[1] += (self.target_camera_offset[1] - self.camera_offset[1]) * 0.1
    
    def draw(self, surface):
        if not self.tiles: return 
        current_time = time.time()
        
        for y in range(self.height):
            for x in range(self.width):
                screen_x = int(x * self.tile_size + self.camera_offset[0])
                screen_y = int(y * self.tile_size + self.camera_offset[1])
                
                if (screen_x + self.tile_size < 0 or screen_x > surface.get_width() or screen_y + self.tile_size < 0 or screen_y > surface.get_height()): continue
                
                tile_type = self.grid[y][x]
                if tile_type not in [TileType.GRASS, TileType.DIRT, TileType.GRASS_FLOWER, TileType.WATER, TileType.STONE]:
                    tile_type = TileType.GRASS
                
                if tile_type == TileType.GRASS: surface.blit(self.tiles['grass'], (screen_x, screen_y))
                elif tile_type == TileType.GRASS_FLOWER: surface.blit(self.tiles['grass_flower'], (screen_x, screen_y))
                elif tile_type == TileType.STONE: surface.blit(self.tiles['stone'], (screen_x, screen_y))
                elif tile_type == TileType.WATER:
                    water_color = (150, 20, 20) if self.is_boss_realm else (41, 128, 185)
                    line_color = (200, 50, 50) if self.is_boss_realm else (74, 163, 223)
                    rect = pygame.Rect(screen_x, screen_y, self.tile_size, self.tile_size)
                    pygame.draw.rect(surface, water_color, rect)
                    wave_offset = math.sin(current_time * 2 + x) * 5
                    pygame.draw.line(surface, line_color, (screen_x + 10, screen_y + 20 + wave_offset), (screen_x + 30, screen_y + 20 + wave_offset), 2)
                    pygame.draw.line(surface, line_color, (screen_x + 30, screen_y + 40 - wave_offset), (screen_x + 50, screen_y + 40 - wave_offset), 2)
                elif tile_type == TileType.DIRT:
                    surface.blit(self.tiles['grass'], (screen_x, screen_y))
                    n = (y > 0 and self.grid[y-1][x] == TileType.DIRT)
                    s = (y < self.height-1 and self.grid[y+1][x] == TileType.DIRT)
                    e = (x < self.width-1 and self.grid[y][x+1] == TileType.DIRT)
                    w = (x > 0 and self.grid[y][x-1] == TileType.DIRT)

                    if s and e and not n and not w: tile = self.tiles['dirt']['tl']
                    elif s and w and not n and not e: tile = self.tiles['dirt']['tr']
                    elif n and e and not s and not w: tile = self.tiles['dirt']['bl']
                    elif n and w and not s and not e: tile = self.tiles['dirt']['br']
                    elif s and not n: tile = self.tiles['dirt']['tm']
                    elif n and not s: tile = self.tiles['dirt']['bm']
                    elif e and not w: tile = self.tiles['dirt']['ml']
                    elif w and not e: tile = self.tiles['dirt']['mr']
                    else: tile = self.tiles['dirt']['mm'] 
                    surface.blit(tile, (screen_x, screen_y))

        if self.is_boss_realm:
            overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
            overlay.fill((40, 0, 10, 80)) 
            surface.blit(overlay, (0, 0))

        sorted_objects = sorted(self.objects, key=lambda obj: obj.y)
        
        for obj in sorted_objects:
            screen_x = int(obj.x + self.camera_offset[0])
            screen_y = int(obj.y + self.camera_offset[1])
            
            if obj.type == "statue" and obj.collected: continue
            
            if obj.type in self.prefabs:
                surface.blit(self.prefabs[obj.type], (screen_x, screen_y))
            else:
                shadow_rect = pygame.Rect(screen_x + 12, screen_y + 48, 40, 12)
                pygame.draw.ellipse(surface, (0, 0, 0, 100), shadow_rect)
                bounce_y = math.sin(current_time * 3 + obj.x) * 4
                
                if obj.type == "statue":
                    is_boss = (obj.data.get('tier') == 'Boss')
                    scale = 2 if is_boss else 1
                    
                    base_rect = pygame.Rect(screen_x + 16 - (16*(scale-1)), screen_y + 40 - (10*(scale-1)), 32 * scale, 16 * scale)
                    pygame.draw.rect(surface, (120, 130, 140), base_rect, border_radius=4)
                    pygame.draw.rect(surface, (80, 90, 100), base_rect, 2, border_radius=4)
                    crystal_y = screen_y + 20 + bounce_y - (20*(scale-1))
                    
                    cx = screen_x + 32
                    points1 = [(cx, crystal_y - 12*scale), (cx + 12*scale, crystal_y), (cx, crystal_y + 12*scale), (cx - 12*scale, crystal_y)]
                    color = (255, 50, 50) if is_boss else (255, 215, 0)
                    color2 = (180, 20, 20) if is_boss else (200, 160, 0)
                    
                    pygame.draw.polygon(surface, color, points1)
                    pygame.draw.polygon(surface, color2, points1, 2)
                    
                elif obj.type == "npc":
                    npc_y = screen_y + 16 + bounce_y
                    body_rect = pygame.Rect(screen_x + 16, npc_y + 12, 32, 28)
                    pygame.draw.rect(surface, (155, 89, 182), body_rect, border_radius=8)
                    pygame.draw.rect(surface, (100, 50, 120), body_rect, 2, border_radius=8)
                    pygame.draw.circle(surface, (255, 224, 189), (screen_x + 32, int(npc_y)), 12)
                    pygame.draw.circle(surface, (200, 170, 140), (screen_x + 32, int(npc_y)), 12, 2)
                    pygame.draw.circle(surface, (0, 0, 0), (screen_x + 28, int(npc_y) - 2), 2)
                    pygame.draw.circle(surface, (0, 0, 0), (screen_x + 36, int(npc_y) - 2), 2)