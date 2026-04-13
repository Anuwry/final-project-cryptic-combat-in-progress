import json
import os
import pygame

class TileType:
    GRASS = 0
    DIRT = 1
    STONE = 2
    WATER = 3
    TREE = 4
    WALL = 5
    BRIDGE = 6
    DOOR = 7
    STATUE = 8
    NPC = 9
    SPAWN = 10

TILE_COLORS = {
    TileType.GRASS: (34, 139, 34),
    TileType.DIRT: (139, 90, 43),
    TileType.STONE: (128, 128, 128),
    TileType.WATER: (0, 100, 200),
    TileType.TREE: (0, 100, 0),
    TileType.WALL: (80, 80, 80),
    TileType.BRIDGE: (160, 82, 45),
    TileType.DOOR: (139, 69, 19),
    TileType.STATUE: (255, 215, 0),
    TileType.NPC: (255, 192, 203),
    TileType.SPAWN: (144, 238, 144)
}

COLLISION_TILES = {TileType.WATER, TileType.TREE, TileType.WALL, TileType.STONE}

class MapObject:
    def __init__(self, x, y, obj_type, data=None):
        self.x = x
        self.y = y
        self.type = obj_type
        self.data = data or {}
        self.rect = pygame.Rect(x, y, 64, 64)
        self.collected = False 
        
    def get_collision_rect(self):
        return self.rect

class GameMap:
    def __init__(self, map_file="data/maps/overworld.json"):
        self.map_file = map_file
        self.tile_size = 64
        self.width = 0
        self.height = 0
        self.grid = []
        self.objects = []
        self.spawn_point = [100, 100]
        self.camera_offset = [0, 0]
        
        self.load_map()
        
    def load_map(self):
        try:
            with open(self.map_file, 'r') as f:
                data = json.load(f)
            
            self.width = data['width']
            self.height = data['height']
            self.tile_size = data.get('tile_size', 64)
            self.grid = data['grid']
            self.spawn_point = data.get('spawn_point', [100, 100])
            
            # โหลด objects
            self.objects = []
            for obj_data in data.get('objects', []):
                obj = MapObject(
                    obj_data['x'],
                    obj_data['y'],
                    obj_data['type'],
                    obj_data.get('data', {})
                )
                self.objects.append(obj)
                
            print(f"Map loaded: {self.width}x{self.height}")
            print(f"  - Statues: {len(self.get_statues())}")
            print(f"  - NPCs: {len(self.get_npcs())}")
            
        except FileNotFoundError:
            print(f"Warning: Map file not found at {self.map_file}")
            print("Using default empty map")
            self._create_default_map()
        except Exception as e:
            print(f"Error loading map: {e}")
            self._create_default_map()
    
    def _create_default_map(self):
        self.width = 20
        self.height = 15
        self.grid = [[TileType.GRASS for _ in range(self.width)] for _ in range(self.height)]
        
        # สร้างกรอบ
        for x in range(self.width):
            self.grid[0][x] = TileType.WALL
            self.grid[self.height-1][x] = TileType.WALL
        for y in range(self.height):
            self.grid[y][0] = TileType.WALL
            self.grid[y][self.width-1] = TileType.WALL
        
        self.objects = [MapObject(320, 192, "statue")]
        self.spawn_point = [128, 128]
    
    def get_statues(self):
        return [obj for obj in self.objects if obj.type == "statue"]
    
    def get_npcs(self):
        return [obj for obj in self.objects if obj.type == "npc"]
    
    def get_uncollected_statues(self):
        return [obj for obj in self.objects if obj.type == "statue" and not obj.collected]
    
    def check_collision_at(self, x, y, width, height):
        check_rect = pygame.Rect(x, y, width, height)
        
        grid_x_start = max(0, int(x // self.tile_size))
        grid_y_start = max(0, int(y // self.tile_size))
        grid_x_end = min(self.width, int((x + width) // self.tile_size) + 1)
        grid_y_end = min(self.height, int((y + height) // self.tile_size) + 1)
        
        for grid_y in range(grid_y_start, grid_y_end):
            for grid_x in range(grid_x_start, grid_x_end):
                tile_type = self.grid[grid_y][grid_x]
                if tile_type in COLLISION_TILES:
                    tile_rect = pygame.Rect(
                        grid_x * self.tile_size,
                        grid_y * self.tile_size,
                        self.tile_size,
                        self.tile_size
                    )
                    if check_rect.colliderect(tile_rect):
                        return True
        
        for obj in self.objects:
            if obj.type == "npc":
                if check_rect.colliderect(obj.get_collision_rect()):
                    return True
        
        return False
    
    def get_nearby_statue(self, player_rect, distance=50):
        for obj in self.objects:
            if obj.type == "statue" and not obj.collected:
                if player_rect.colliderect(obj.rect.inflate(distance, distance)):
                    return obj
        return None
    
    def get_nearby_npc(self, player_rect, distance=50):
        for obj in self.objects:
            if obj.type == "npc":
                if player_rect.colliderect(obj.rect.inflate(distance, distance)):
                    return obj
        return None
    
    def update_camera(self, player_x, player_y, screen_width, screen_height):
        target_offset_x = screen_width // 2 - player_x
        target_offset_y = screen_height // 2 - player_y
        
        max_offset_x = 0
        min_offset_x = screen_width - (self.width * self.tile_size)
        max_offset_y = 0
        min_offset_y = screen_height - (self.height * self.tile_size)
        
        self.camera_offset[0] = max(min_offset_x, min(max_offset_x, target_offset_x))
        self.camera_offset[1] = max(min_offset_y, min(max_offset_y, target_offset_y))
    
    def draw(self, surface):
        for y in range(self.height):
            for x in range(self.width):
                screen_x = x * self.tile_size + self.camera_offset[0]
                screen_y = y * self.tile_size + self.camera_offset[1]
                
                if (screen_x + self.tile_size < 0 or screen_x > surface.get_width() or
                    screen_y + self.tile_size < 0 or screen_y > surface.get_height()):
                    continue
                
                tile_type = self.grid[y][x]
                color = TILE_COLORS.get(tile_type, (255, 0, 255))  # Magenta for unknown
                
                rect = pygame.Rect(screen_x, screen_y, self.tile_size, self.tile_size)
                pygame.draw.rect(surface, color, rect)
                
                pygame.draw.rect(surface, (0, 0, 0, 50), rect, 1)
        
        for obj in self.objects:
            screen_x = obj.x + self.camera_offset[0]
            screen_y = obj.y + self.camera_offset[1]
            
            if (screen_x + self.tile_size < 0 or screen_x > surface.get_width() or
                screen_y + self.tile_size < 0 or screen_y > surface.get_height()):
                continue
            
            if obj.type == "statue" and obj.collected:
                continue
            
            rect = pygame.Rect(screen_x, screen_y, self.tile_size, self.tile_size)
            
            if obj.type == "statue":
                pygame.draw.rect(surface, (255, 215, 0), rect, border_radius=8)
                pygame.draw.rect(surface, (0, 0, 0), rect, 3, border_radius=8)
                
                center_x = screen_x + self.tile_size // 2
                center_y = screen_y + self.tile_size // 2
                pygame.draw.circle(surface, (255, 215, 0), (center_x, center_y), 12)
                pygame.draw.circle(surface, (0, 0, 0), (center_x, center_y), 12, 2)
                
            elif obj.type == "npc":
                pygame.draw.rect(surface, (255, 192, 203), rect, border_radius=8)
                pygame.draw.rect(surface, (0, 0, 0), rect, 3, border_radius=8)
                
                head_x = screen_x + self.tile_size // 2
                head_y = screen_y + 20
                pygame.draw.circle(surface, (255, 192, 203), (head_x, head_y), 10)
                pygame.draw.circle(surface, (0, 0, 0), (head_x, head_y), 10, 2)
    
    def draw_spawn_marker(self, surface):
        screen_x = self.spawn_point[0] + self.camera_offset[0]
        screen_y = self.spawn_point[1] + self.camera_offset[1]
        
        pygame.draw.circle(surface, (0, 255, 0), (int(screen_x), int(screen_y)), 5)