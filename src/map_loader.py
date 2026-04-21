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
        self.image = None 
        
        if self.type in ['house_red', 'house_grey']:
            self.rect = pygame.Rect(x, y, 192, 192) 
        elif self.type == 'shop':
            self.rect = pygame.Rect(x + 28, y + 86, 200, 54)
        elif self.type in ['tree_green', 'tree_orange']:
            self.rect = pygame.Rect(x + 16, y + 64, 32, 64) 
        elif self.type == 'statue':
            if self.data.get('tier') == 'Boss':
                self.rect = pygame.Rect(x - 32, y - 32, 128, 128)
            else:
                self.rect = pygame.Rect(x, y, 64, 64)
        else:
            self.rect = pygame.Rect(x, y, 64, 64)

    def load_statue_sprite(self):
        if self.type == "statue":
            god = self.data.get('god', 'Zeus').lower()
            tier = self.data.get('tier', 'Follower').lower()
            role = "avatar" if tier == "boss" else tier
            
            abbr_map = {'follower': 'fol', 'zealot': 'zea', 'apostle': 'apos', 'boss': 'ava', 'avatar': 'ava'}
            abbr = abbr_map.get(role, 'fol')
            
            possible_names = [
                f"{god}_{abbr}-removebg-preview.png",
                f"{god}_{role}-removebg-preview.png",
                f"{god}_{abbr}.png",
                f"{god}_{role}.png"
            ]
            
            for fname in possible_names:
                path = os.path.join(BASE_DIR, "assets", "images", fname)
                if os.path.exists(path):
                    try:
                        img = pygame.image.load(path).convert_alpha()
                        orig_w, orig_h = img.get_size()
                        
                        if role == "avatar": max_size = 256
                        elif role == "apostle": max_size = 192
                        elif role == "zealot": max_size = 128
                        else: max_size = 64
                        
                        if orig_w > orig_h:
                            new_w = max_size
                            new_h = int(orig_h * (max_size / orig_w))
                        else:
                            new_h = max_size
                            new_w = int(orig_w * (max_size / orig_h))
                            
                        self.image = pygame.transform.scale(img, (new_w, new_h))
                        return
                    except: pass
            print(f"Missing statue image for: {god} {role}")
        elif self.type == "shop":
            for fname in ("shop_transparent.png", "shop.png"):
                path = os.path.join(BASE_DIR, "assets", "images", fname)
                if os.path.exists(path):
                    try:
                        img = pygame.image.load(path).convert_alpha()
                        target_w = 256
                        target_h = max(64, int(img.get_height() * (target_w / img.get_width())))
                        self.image = pygame.transform.smoothscale(img, (target_w, target_h))
                        return
                    except Exception:
                        pass
            print("Missing shop image")

    def get_collision_rect(self):
        return self.rect

class GameMap:
    def __init__(self, realm_x=0, realm_y=0, force_normal=False):
        self.realm_x = realm_x
        self.realm_y = realm_y
        self.level = abs(realm_x) + abs(realm_y) + 1
        self.is_boss_realm = (not force_normal and self.level > 1 and self.level % 5 == 0)
        
        self.map_file = os.path.join(BASE_DIR, f"data/maps/realm_{realm_x}_{realm_y}.json")
        self.tile_size = 64
        self.width, self.height = 32, 24
        self.grid = []
        self.objects = []
        self.spawn_point = [100, 100]
        self.camera_offset = [0, 0]
        self.target_camera_offset = [0, 0]
        
        self.god_theme = None
        self.gods = ["Zeus", "Poseidon", "Hades", "Ares", "Athena", "Apollo", "Hermes"]
        
        self.full_bg_image = None
        self.tiles = {}
        self.prefabs = {}
        
        self.load_map()
        self.load_tileset()
        
        for obj in self.objects:
            obj.load_statue_sprite()
            
        if self.is_boss_realm and self.god_theme:
            bg_path = os.path.join(BASE_DIR, "assets", "images", f"{self.god_theme.lower()}_full.png")
            if os.path.exists(bg_path):
                try:
                    img = pygame.image.load(bg_path).convert()
                    self.full_bg_image = pygame.transform.scale(img, (800, 600))
                except: pass

    def load_tileset(self):
        tileset_path = os.path.join(BASE_DIR, "assets", "images", "tilemap.png")
        if not os.path.exists(tileset_path): return
        try:
            tilesheet = pygame.image.load(tileset_path).convert_alpha()
            def get_tile(col, row):
                rect = pygame.Rect(col * 17, row * 17, 16, 16)
                img = pygame.Surface((16, 16), pygame.SRCALPHA)
                img.blit(tilesheet, (0, 0), rect)
                return pygame.transform.scale(img, (self.tile_size, self.tile_size))

            self.tiles = {'grass': get_tile(0, 0), 'grass_flower': get_tile(2, 0), 'stone': get_tile(0, 8), 'water': get_tile(0, 0)}
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

    def load_map(self):
        try:
            with open(self.map_file, 'r') as f:
                data = json.load(f)
            self.width = data.get('width', 32)
            self.height = data.get('height', 24)
            self.tile_size = data.get('tile_size', 64)
            self.grid = data['grid']
            self.spawn_point = data.get('spawn_point', [100, 100])
            self.objects = [
                MapObject(o['x'], o['y'], o['type'], o.get('data', {}), o.get('collected', False))
                for o in data.get('objects', [])
            ]
            for obj in self.objects:
                if obj.type == 'statue' and obj.data.get('tier') == 'Boss':
                    self.god_theme = obj.data.get('god')
        except FileNotFoundError:
            if self.realm_x == 0 and self.realm_y == 0: self._create_main_hub_map()
            elif self.is_boss_realm: self._create_boss_map()
            else: self._generate_smart_realm()
            self.save_map()

    def ensure_safe_spawn(self, x, y):
        if self.is_boss_realm: return
        player_rect = pygame.Rect(x - 32, y - 32, 128, 128)
        safe_objects = []
        for obj in self.objects:
            if obj.type in ['house_red', 'house_grey', 'shop', 'tree_green', 'tree_orange']:
                if not obj.get_collision_rect().colliderect(player_rect):
                    safe_objects.append(obj)
            else:
                safe_objects.append(obj)
        self.objects = safe_objects

    def _create_boss_map(self):
        self.width, self.height = 13, 10
        self.grid = [[TileType.STONE for _ in range(self.width)] for _ in range(self.height)]
                        
        self.god_theme = random.choice(self.gods)
        self.objects.append(MapObject(400 - 32, 250, "statue", {"god": self.god_theme, "tier": "Boss"}))
        self.spawn_point = [400 - 32, 450]

    def _create_main_hub_map(self):
        self.width, self.height = 32, 24
        self.grid = [[TileType.GRASS_FLOWER if random.random() < 0.1 else TileType.GRASS 
                      for _ in range(self.width)] for _ in range(self.height)]
        
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

        self.objects.append(MapObject((16 * 64) + 16, 9 * 64, "shop", {
            "name": "Merchant",
            "dialogue": "Stock up before you leave Sanc."
        }))
        self.objects.append(MapObject(20 * 64, 6 * 64, "house_red"))
        self.objects.append(MapObject(9 * 64, 17 * 64, "house_red"))
        self.objects.append(MapObject(20 * 64, 17 * 64, "house_grey"))
        self.objects.append(MapObject(15 * 64, 11 * 64, "statue", {"god": "Athena", "tier": "Follower"}))
        self.objects.append(MapObject(16 * 64, 11 * 64, "statue", {"god": "Apollo", "tier": "Follower"}))
        self.spawn_point = [15 * 64, 15 * 64]
        self._populate_decorations()

    def _generate_smart_realm(self):
        self.width, self.height = 32, 24
        self.grid = [[TileType.GRASS_FLOWER if random.random() < 0.1 else TileType.GRASS 
                      for _ in range(self.width)] for _ in range(self.height)]
        
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
            if random.choice([True, False]):
                ry = random.choice([5, 6, 18, 19])
                for x in range(self.width):
                    if self.grid[ry][x] != TileType.DIRT:
                        self.grid[ry][x] = TileType.WATER
                        self.grid[ry+1][x] = TileType.WATER
            else:
                rx = random.choice([6, 7, 24, 25])
                for y in range(self.height):
                    if self.grid[y][rx] != TileType.DIRT:
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

        for _ in range(random.randint(0, min(3, self.level))):
            spot = get_free_spot(3, 3)
            if spot: self.objects.append(MapObject(spot[0] * 64, spot[1] * 64, random.choice(['house_red', 'house_grey'])))
            
        for _ in range(random.randint(30, 60)):
            spot = get_free_spot(1, 2)
            if spot: self.objects.append(MapObject(spot[0] * 64, spot[1] * 64, random.choice(['tree_green', 'tree_orange'])))

    def save_map(self):
        os.makedirs(os.path.dirname(self.map_file), exist_ok=True)
        data = {'width': self.width, 'height': self.height, 'tile_size': self.tile_size,
                'grid': self.grid, 'spawn_point': self.spawn_point,
                'objects': [{'x': o.x, 'y': o.y, 'type': o.type, 'data': o.data, 'collected': o.collected} for o in self.objects]}
        with open(self.map_file, 'w') as f: json.dump(data, f)

    def get_statues(self): return [o for o in self.objects if o.type == "statue"]
    
    def check_collision_at(self, x, y, w, h):
        if self.is_boss_realm: return False
        check_rect = pygame.Rect(x, y, w, h)
        gx, gy = int(x // self.tile_size), int(y // self.tile_size)
        if 0 <= gx < self.width and 0 <= gy < self.height:
            if self.grid[gy][gx] == TileType.WATER: return True
        for obj in self.objects:
            if obj.type in ['house_red', 'house_grey', 'shop', 'tree_green', 'tree_orange']:
                if check_rect.colliderect(obj.get_collision_rect()): return True
        return False

    def update_camera(self, px, py, sw, sh):
        if self.is_boss_realm: 
            self.camera_offset = [0, 0]
            return
        tx, ty = sw//2 - px, sh//2 - py
        self.target_camera_offset[0] = max(sw - (self.width * self.tile_size), min(0, tx))
        self.target_camera_offset[1] = max(sh - (self.height * self.tile_size), min(0, ty))
        self.camera_offset[0] += (self.target_camera_offset[0] - self.camera_offset[0]) * 0.1
        self.camera_offset[1] += (self.target_camera_offset[1] - self.camera_offset[1]) * 0.1

    def draw(self, surface):
        current_time = time.time()
        
        if self.is_boss_realm and self.full_bg_image:
            surface.blit(self.full_bg_image, (0, 0))
        else:
            for y in range(len(self.grid)):
                for x in range(len(self.grid[0])):
                    sx = int(x * self.tile_size + self.camera_offset[0])
                    sy = int(y * self.tile_size + self.camera_offset[1])
                    
                    if (sx + self.tile_size < 0 or sx > surface.get_width() or sy + self.tile_size < 0 or sy > surface.get_height()): continue
                    
                    t = self.grid[y][x]
                    
                    if self.tiles and 'grass' in self.tiles:
                        if t == TileType.GRASS: surface.blit(self.tiles['grass'], (sx, sy))
                        elif t == TileType.GRASS_FLOWER: surface.blit(self.tiles['grass_flower'], (sx, sy))
                        elif t == TileType.STONE: surface.blit(self.tiles['stone'], (sx, sy))
                        elif t == TileType.WATER:
                            pygame.draw.rect(surface, (41, 128, 185), (sx, sy, self.tile_size, self.tile_size))
                            wo = math.sin(current_time * 2 + x) * 5
                            pygame.draw.line(surface, (74, 163, 223), (sx+10, sy+20+wo), (sx+30, sy+20+wo), 2)
                            pygame.draw.line(surface, (74, 163, 223), (sx+30, sy+40-wo), (sx+50, sy+40-wo), 2)
                        elif t == TileType.DIRT:
                            surface.blit(self.tiles['grass'], (sx, sy))
                            n = (y > 0 and self.grid[y-1][x] == TileType.DIRT)
                            s = (y < self.height-1 and self.grid[y+1][x] == TileType.DIRT)
                            e = (x < self.width-1 and self.grid[y][x+1] == TileType.DIRT)
                            w = (x > 0 and self.grid[y][x-1] == TileType.DIRT)
                            if s and e and not n and not w: tl = self.tiles['dirt']['tl']
                            elif s and w and not n and not e: tl = self.tiles['dirt']['tr']
                            elif n and e and not s and not w: tl = self.tiles['dirt']['bl']
                            elif n and w and not s and not e: tl = self.tiles['dirt']['br']
                            elif s and not n: tl = self.tiles['dirt']['tm']
                            elif n and not s: tl = self.tiles['dirt']['bm']
                            elif e and not w: tl = self.tiles['dirt']['ml']
                            elif w and not e: tl = self.tiles['dirt']['mr']
                            else: tl = self.tiles['dirt']['mm']
                            surface.blit(tl, (sx, sy))
                    else:
                        if t == TileType.GRASS: color = (106, 190, 48)
                        elif t == TileType.GRASS_FLOWER: color = (129, 199, 132)
                        elif t == TileType.DIRT: color = (215, 168, 118)
                        elif t == TileType.STONE: color = (158, 158, 158)
                        elif t == TileType.WATER: color = (41, 128, 185)
                        else: color = (106, 190, 48)
                        pygame.draw.rect(surface, color, (sx, sy, self.tile_size, self.tile_size))

        for obj in sorted(self.objects, key=lambda o: o.y):
            if obj.type == "statue" and obj.collected: continue
            sx, sy = int(obj.x + self.camera_offset[0]), int(obj.y + self.camera_offset[1])
            
            if obj.type in self.prefabs:
                surface.blit(self.prefabs[obj.type], (sx, sy))
            elif getattr(obj, 'image', None):
                if obj.type == 'statue':
                    img_w = obj.image.get_width()
                    img_h = obj.image.get_height()
                    offset_x = (self.tile_size - img_w) // 2
                    offset_y = (self.tile_size - img_h) 
                    surface.blit(obj.image, (sx + offset_x, sy + offset_y))
                elif obj.type == 'shop':
                    surface.blit(obj.image, (sx, sy))
                else:
                    bob = math.sin(current_time * 3 + obj.x) * 5
                    surface.blit(obj.image, (sx, sy + bob))
            else:
                bob = math.sin(current_time * 3 + obj.x) * 4
                if obj.type == "npc":
                    ny = sy + 16 + bob
                    br = pygame.Rect(sx + 16, ny + 12, 32, 28)
                    pygame.draw.rect(surface, (155, 89, 182), br)
                    pygame.draw.rect(surface, (100, 50, 120), br, 2)
                    pygame.draw.circle(surface, (255, 224, 189), (sx + 32, int(ny)), 12)
                    pygame.draw.circle(surface, (200, 170, 140), (sx + 32, int(ny)), 12, 2)
                    pygame.draw.circle(surface, (0, 0, 0), (sx + 28, int(ny) - 2), 2)
                    pygame.draw.circle(surface, (0, 0, 0), (sx + 36, int(ny) - 2), 2)
                else:
                    pygame.draw.rect(surface, (100, 100, 100), (sx, sy, 64, 64))
                    pygame.draw.rect(surface, (255, 50, 50), (sx, sy, 64, 64), 2)

