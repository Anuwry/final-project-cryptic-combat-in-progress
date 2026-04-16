import pygame
import json
import os
import sys
from src.config import BASE_DIR

WHITE = (248, 250, 252)
BLACK = (2, 6, 23)
SLATE_900 = (15, 23, 42)
SLATE_800 = (30, 41, 59)
SLATE_700 = (51, 65, 85)
CYAN_400 = (34, 211, 238)
CYAN_500 = (6, 182, 212) 
EMERALD_500 = (16, 185, 129)
RED_500 = (239, 68, 68)
AMBER_500 = (245, 158, 11)

TILE_SIZE = 64
MAP_WIDTH = 25 
MAP_HEIGHT = 18
SCREEN_WIDTH = 1080 
SCREEN_HEIGHT = 720

class TileType:
    GRASS = 0
    DIRT = 1
    GRASS_FLOWER = 2
    WATER = 3

class MapObject:
    def __init__(self, x, y, obj_type, data=None):
        self.x = x
        self.y = y
        self.type = obj_type 
        self.data = data or {}
        
    def to_dict(self):
        return {'x': self.x, 'y': self.y, 'type': self.type, 'data': self.data}

class MapEditor:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Cryptic Combat - Visual Map Editor")
        
        self.font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 24)
        self.tiny_font = pygame.font.Font(None, 20)
        
        self.map_grid = [[TileType.GRASS for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        self.objects = [] 
        self.spawn_point = [100, 100]
        
        self.camera_offset = [0, 0]
        self.dragging = False
        self.last_mouse_pos = None
        
        self.tiles = {}
        self.prefabs = {}
        self.load_tileset()
        
        self.current_mode = "tile"  
        self.current_tile = TileType.GRASS
        self.current_object = "house_grey"
        
        self.mode_buttons = self.create_mode_buttons()
        self.current_map_file = "data/maps/realm_0_0.json"
        
        self.load_map()

    def load_tileset(self):
        tileset_path = os.path.join(BASE_DIR, "assets", "images", "tilemap.png")
        try:
            tilesheet = pygame.image.load(tileset_path).convert_alpha()
            
            def get_tile(col, row):
                rect = pygame.Rect(col * 17, row * 17, 16, 16)
                image = pygame.Surface((16, 16), pygame.SRCALPHA)
                image.blit(tilesheet, (0, 0), rect)
                return pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))

            self.tiles[TileType.GRASS] = get_tile(0, 0)
            self.tiles[TileType.GRASS_FLOWER] = get_tile(2, 0)
            
            self.tiles[TileType.DIRT] = {
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
            tree_green.blit(get_tile(4, 0), (0, 0)); tree_green.blit(get_tile(4, 1), (0, 64))
            self.prefabs['tree_green'] = tree_green
            
            tree_orange = pygame.Surface((64, 128), pygame.SRCALPHA)
            tree_orange.blit(get_tile(3, 0), (0, 0)); tree_orange.blit(get_tile(3, 1), (0, 64))
            self.prefabs['tree_orange'] = tree_orange

            statue_icon = pygame.Surface((64, 64), pygame.SRCALPHA)
            pygame.draw.polygon(statue_icon, AMBER_500, [(32, 10), (50, 32), (32, 54), (14, 32)])
            self.prefabs['statue'] = statue_icon
            
            npc_icon = pygame.Surface((64, 64), pygame.SRCALPHA)
            pygame.draw.rect(npc_icon, (155, 89, 182), (16, 20, 32, 40), border_radius=8)
            pygame.draw.circle(npc_icon, (255, 224, 189), (32, 20), 16)
            self.prefabs['npc'] = npc_icon

        except Exception as e:
            print(f"Error loading tileset: {e}")
            sys.exit(1)

    def create_mode_buttons(self):
        return [
            {'mode': 'tile', 'text': 'PAINT TILES', 'rect': pygame.Rect(SCREEN_WIDTH - 280, 50, 260, 40)},
            {'mode': 'object', 'text': 'PLACE OBJECTS', 'rect': pygame.Rect(SCREEN_WIDTH - 280, 100, 260, 40)},
            {'mode': 'spawn', 'text': 'SET SPAWN (S)', 'rect': pygame.Rect(SCREEN_WIDTH - 280, 150, 260, 40)}
        ]

    def get_tile_at_mouse(self, mouse_pos):
        world_x = mouse_pos[0] - self.camera_offset[0]
        world_y = mouse_pos[1] - self.camera_offset[1]
        grid_x, grid_y = world_x // TILE_SIZE, world_y // TILE_SIZE
        if 0 <= grid_x < MAP_WIDTH and 0 <= grid_y < MAP_HEIGHT:
            return int(grid_x), int(grid_y)
        return None

    def handle_click(self, pos, button):
        for btn in self.mode_buttons:
            if btn['rect'].collidepoint(pos):
                self.current_mode = btn['mode']
                return
        
        palette_start_y = 220
        if self.current_mode == "tile":
            items = [
                (TileType.GRASS, "Grass"), 
                (TileType.GRASS_FLOWER, "Flower"), 
                (TileType.DIRT, "Dirt Path"),
                (TileType.WATER, "River Water")
            ]
            for i, (t_type, name) in enumerate(items):
                if pygame.Rect(SCREEN_WIDTH - 280, palette_start_y + (i*45), 260, 40).collidepoint(pos):
                    self.current_tile = t_type
                    return
        elif self.current_mode == "object":
            items = ["house_grey", "house_red", "tree_green", "tree_orange", "statue", "npc"]
            for i, obj_name in enumerate(items):
                if pygame.Rect(SCREEN_WIDTH - 280, palette_start_y + (i*60), 260, 50).collidepoint(pos):
                    self.current_object = obj_name
                    return

        tile_pos = self.get_tile_at_mouse(pos)
        if tile_pos and pos[0] < SCREEN_WIDTH - 300: 
            gx, gy = tile_pos
            wx, wy = gx * TILE_SIZE, gy * TILE_SIZE
            
            if button == 1: 
                if self.current_mode == "tile":
                    self.map_grid[gy][gx] = self.current_tile
                elif self.current_mode == "object":
                    self.objects = [o for o in self.objects if not (abs(o.x - wx) < 32 and abs(o.y - wy) < 32)]
                    data = {"name": "Villager", "dialogue": "Hello!"} if self.current_object == "npc" else {}
                    self.objects.append(MapObject(wx, wy, self.current_object, data))
                elif self.current_mode == "spawn":
                    self.spawn_point = [wx, wy]
                    
            elif button == 3: 
                if self.current_mode == "tile":
                    self.map_grid[gy][gx] = TileType.GRASS
                elif self.current_mode == "object":
                    self.objects = [o for o in self.objects if not (abs(o.x - wx) < 32 and abs(o.y - wy) < 32)]

    def load_map(self):
        try:
            with open(self.current_map_file, 'r') as f:
                data = json.load(f)
            self.map_grid = data['grid']
            self.spawn_point = data['spawn_point']
            self.objects = [MapObject(o['x'], o['y'], o['type'], o.get('data', {})) for o in data.get('objects', [])]
        except:
            pass

    def save_map(self):
        os.makedirs(os.path.dirname(self.current_map_file), exist_ok=True)
        data = {
            'width': MAP_WIDTH, 'height': MAP_HEIGHT, 'tile_size': TILE_SIZE,
            'grid': self.map_grid, 'spawn_point': self.spawn_point,
            'objects': [o.to_dict() for o in self.objects]
        }
        with open(self.current_map_file, 'w') as f:
            json.dump(data, f, indent=2)

    def draw_grid(self):
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                sx = x * TILE_SIZE + self.camera_offset[0]
                sy = y * TILE_SIZE + self.camera_offset[1]
                if sx + TILE_SIZE < 0 or sx > SCREEN_WIDTH - 300 or sy + TILE_SIZE < 0 or sy > SCREEN_HEIGHT: continue
                
                t_type = self.map_grid[y][x]
                if t_type not in [TileType.GRASS, TileType.DIRT, TileType.GRASS_FLOWER, TileType.WATER]:
                    t_type = TileType.GRASS
                    
                if t_type == TileType.GRASS: self.screen.blit(self.tiles[TileType.GRASS], (sx, sy))
                elif t_type == TileType.GRASS_FLOWER: self.screen.blit(self.tiles[TileType.GRASS_FLOWER], (sx, sy))
                elif t_type == TileType.WATER:
                    pygame.draw.rect(self.screen, (41, 128, 185), (sx, sy, TILE_SIZE, TILE_SIZE))
                elif t_type == TileType.DIRT:
                    self.screen.blit(self.tiles[TileType.GRASS], (sx, sy)) 
                    n = (y > 0 and self.map_grid[y-1][x] == TileType.DIRT)
                    s = (y < MAP_HEIGHT-1 and self.map_grid[y+1][x] == TileType.DIRT)
                    e = (x < MAP_WIDTH-1 and self.map_grid[y][x+1] == TileType.DIRT)
                    w = (x > 0 and self.map_grid[y][x-1] == TileType.DIRT)

                    if s and e and not n and not w: t = self.tiles[TileType.DIRT]['tl']
                    elif s and w and not n and not e: t = self.tiles[TileType.DIRT]['tr']
                    elif n and e and not s and not w: t = self.tiles[TileType.DIRT]['bl']
                    elif n and w and not s and not e: t = self.tiles[TileType.DIRT]['br']
                    elif s and not n: t = self.tiles[TileType.DIRT]['tm']
                    elif n and not s: t = self.tiles[TileType.DIRT]['bm']
                    elif e and not w: t = self.tiles[TileType.DIRT]['ml']
                    elif w and not e: t = self.tiles[TileType.DIRT]['mr']
                    else: t = self.tiles[TileType.DIRT]['mm']
                    self.screen.blit(t, (sx, sy))
                
                pygame.draw.rect(self.screen, (0,0,0, 50), (sx, sy, TILE_SIZE, TILE_SIZE), 1)

    def draw_objects(self):
        sorted_objs = sorted(self.objects, key=lambda o: o.y)
        for obj in sorted_objs:
            sx = obj.x + self.camera_offset[0]
            sy = obj.y + self.camera_offset[1]
            if sx + 192 < 0 or sx > SCREEN_WIDTH - 300 or sy + 192 < 0 or sy > SCREEN_HEIGHT: continue
            
            if obj.type in self.prefabs:
                self.screen.blit(self.prefabs[obj.type], (sx, sy))
                pygame.draw.rect(self.screen, RED_500, (sx, sy, 32, 32), 2)

    def draw_ui(self):
        pygame.draw.rect(self.screen, SLATE_900, (SCREEN_WIDTH - 300, 0, 300, SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, SLATE_700, (SCREEN_WIDTH - 300, 0, 300, SCREEN_HEIGHT), 2)
        
        self.screen.blit(self.font.render("MAP EDITOR", True, CYAN_400), (SCREEN_WIDTH - 280, 15))
        
        for btn in self.mode_buttons:
            is_act = (btn['mode'] == self.current_mode)
            pygame.draw.rect(self.screen, CYAN_500 if is_act else SLATE_800, btn['rect'], border_radius=8)
            pygame.draw.rect(self.screen, BLACK, btn['rect'], 2, border_radius=8)
            txt = self.small_font.render(btn['text'], True, BLACK if is_act else WHITE)
            self.screen.blit(txt, txt.get_rect(center=btn['rect'].center))

        py = 220
        if self.current_mode == "tile":
            items = [
                (TileType.GRASS, "Grass"), 
                (TileType.GRASS_FLOWER, "Flower"), 
                (TileType.DIRT, "Dirt Path"),
                (TileType.WATER, "River Water")
            ]
            for t_type, name in items:
                rect = pygame.Rect(SCREEN_WIDTH - 280, py, 260, 40)
                is_sel = (self.current_tile == t_type)
                pygame.draw.rect(self.screen, SLATE_800, rect, border_radius=8)
                pygame.draw.rect(self.screen, CYAN_400 if is_sel else SLATE_700, rect, 2 if is_sel else 1, border_radius=8)
                self.screen.blit(self.small_font.render(name, True, WHITE), (SCREEN_WIDTH - 260, py + 10))
                py += 45
                
        elif self.current_mode == "object":
            items = ["house_grey", "house_red", "tree_green", "tree_orange", "statue", "npc"]
            for obj_name in items:
                rect = pygame.Rect(SCREEN_WIDTH - 280, py, 260, 50)
                is_sel = (self.current_object == obj_name)
                pygame.draw.rect(self.screen, SLATE_800, rect, border_radius=8)
                pygame.draw.rect(self.screen, CYAN_400 if is_sel else SLATE_700, rect, 2 if is_sel else 1, border_radius=8)
                self.screen.blit(self.small_font.render(obj_name.replace("_", " ").title(), True, WHITE), (SCREEN_WIDTH - 200, py + 15))
                
                preview = pygame.transform.scale(self.prefabs[obj_name], (32, 32) if "house" in obj_name else (24, 48))
                self.screen.blit(preview, (SCREEN_WIDTH - 260, py + (25 - preview.get_height()//2)))
                py += 60

        inst_y = SCREEN_HEIGHT - 120
        self.screen.blit(self.tiny_font.render("L-Click: Place | R-Click: Erase", True, WHITE), (SCREEN_WIDTH - 280, inst_y))
        self.screen.blit(self.tiny_font.render("Hold SPACE + Drag: Pan Camera", True, WHITE), (SCREEN_WIDTH - 280, inst_y + 20))
        self.screen.blit(self.tiny_font.render("Ctrl+S: Save Map | ESC: Exit", True, EMERALD_500), (SCREEN_WIDTH - 280, inst_y + 50))

    def handle_events(self):
        keys = pygame.key.get_pressed()
        is_panning = keys[pygame.K_SPACE]
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return False
                elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL: self.save_map()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: 
                    if is_panning: 
                        self.last_mouse_pos = event.pos
                    else:
                        self.handle_click(event.pos, 1)
                        self.dragging = True
                elif event.button == 3: 
                    self.handle_click(event.pos, 3)
                elif event.button == 2: 
                    self.last_mouse_pos = event.pos
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1: 
                    self.dragging = False
                    self.last_mouse_pos = None
                elif event.button == 2: 
                    self.last_mouse_pos = None
                    
            elif event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[1] or (pygame.mouse.get_pressed()[0] and is_panning):
                    if self.last_mouse_pos:
                        self.camera_offset[0] += event.pos[0] - self.last_mouse_pos[0]
                        self.camera_offset[1] += event.pos[1] - self.last_mouse_pos[1]
                    self.last_mouse_pos = event.pos
                
                elif self.dragging and not is_panning and event.pos[0] < SCREEN_WIDTH - 300:
                    if self.current_mode == "tile":
                        self.handle_click(event.pos, 1)
                        
                elif pygame.mouse.get_pressed()[2] and event.pos[0] < SCREEN_WIDTH - 300:
                    if self.current_mode == "tile":
                        self.handle_click(event.pos, 3)
                        
        return True

    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            running = self.handle_events()
            self.screen.fill(BLACK)
            self.draw_grid()
            
            sx, sy = self.spawn_point[0] + self.camera_offset[0], self.spawn_point[1] + self.camera_offset[1]
            pygame.draw.rect(self.screen, EMERALD_500, (sx, sy, TILE_SIZE, TILE_SIZE), border_radius=8)
            self.screen.blit(self.font.render("S", True, BLACK), (sx + 24, sy + 20))
            
            self.draw_objects()
            self.draw_ui()
            pygame.display.flip()
            clock.tick(60)
            
        if input("Save map before exiting? (y/n): ").lower() == 'y': self.save_map()
        pygame.quit()

if __name__ == "__main__":
    MapEditor().run()