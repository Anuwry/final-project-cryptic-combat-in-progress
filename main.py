import pygame
import sys
import os
import math
import random
import json
import time
import csv
from src.config import DATA_DIR, RAW_DATA_DIR, WORDS_DATA_DIR, BASE_DIR
from src.game_manager import GameManager
from src.entities import Player, Enemy
from src.mechanics import WordDictionary, TileBoard
from src.map_loader import GameMap

BG_DEEP = (10, 10, 15)
BG_DARK = (15, 16, 24)
BG_CARD = (15, 18, 30)
GOLD = (201, 162, 39)
GOLD_LIGHT = (232, 200, 74)
GOLD_DIM = (138, 109, 27)
ACCENT_RED = (139, 32, 32)
ACCENT_RED_GLOW = (196, 60, 60)
TEXT_PRIMARY = (212, 207, 192)
TEXT_SECONDARY = (122, 117, 104)
TEXT_DIM = (74, 70, 60)
BORDER_SUBTLE = (40, 35, 20)
BORDER_ACTIVE = (120, 100, 30)

WHITE = (248, 250, 252)
BLACK = (2, 6, 23)
GRAY = (71, 85, 105)
SLATE_950 = (2, 6, 23)
SLATE_900 = (15, 23, 42)
SLATE_800 = (30, 41, 59)
SLATE_700 = (51, 65, 85)
SLATE_400 = (148, 163, 184)
EMERALD_500 = (16, 185, 129)
EMERALD_400 = (52, 211, 153)
RED_500 = (239, 68, 68)
AMBER_500 = (245, 158, 11)
AMBER_400 = (251, 191, 36)
CYAN_400 = (34, 211, 238)
CYAN_500 = (6, 182, 212)

STATE_MAIN_MENU = -1
STATE_SAVE_SLOTS = -2
STATE_SELECTION = 0
STATE_OVERWORLD = 1
STATE_BATTLE = 2
STATE_SHOP = 3
STATE_UPGRADE = 4
STATE_WARP = 5 
STATE_PAUSE = 6
STATE_SETTINGS = 7

class SpriteSheet:
    def __init__(self, filename):
        try:
            self.sheet = pygame.image.load(filename).convert_alpha()
        except pygame.error:
            self.sheet = pygame.Surface((16, 16))
            self.sheet.fill((255, 0, 255))

    def get_image_by_grid(self, col, row, scale):
        w, h, m = 16, 16, 1
        x = col * (w + m)
        y = row * (h + m)
        image = pygame.Surface((w, h), pygame.SRCALPHA)
        image.blit(self.sheet, (0, 0), (x, y, w, h))
        return pygame.transform.scale(image, (w * scale, h * scale))

    def get_equipped_image_by_grid(self, layers, scale):
        w, h, m = 16, 16, 1
        composite = pygame.Surface((w, h), pygame.SRCALPHA)
        for grid in layers:
            if grid is not None:
                x, y = grid[0]*(w+m), grid[1]*(h+m)
                composite.blit(self.sheet.subsurface((x, y, w, h)), (0, 0))
        return pygame.transform.scale(composite, (w * scale, h * scale))

class PygameApp:
    def __init__(self):
        pygame.init()
        pygame.mixer.init() 
        
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Cryptic Combat")
        
        self.large_font = pygame.font.Font(None, 64)
        self.title_font = pygame.font.Font(None, 80) 
        self.combo_font = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 40)
        self.name_font = pygame.font.Font(None, 32)
        self.btn_font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 24)
        self.tiny_font = pygame.font.Font(None, 18) 
        
        self.particles = []
        for _ in range(50):
            self.particles.append({
                'x': random.uniform(0, 800), 'y': random.uniform(0, 600),
                'vx': random.uniform(-0.2, 0.2), 'vy': random.uniform(-0.5, -0.1),
                'size': random.uniform(1.5, 3.5), 'pulse': random.uniform(0, math.pi * 2)
            })
            
        self.bgm_volume = 0.5
        self.sfx_volume = 0.8
        self.shake_enabled = True
        pygame.mixer.music.set_volume(self.bgm_volume)
        self.music_tracks = {
            "main_menu": os.path.join(BASE_DIR, "assets", "sounds", "main_menu.mp3"),
            "overworld": os.path.join(BASE_DIR, "assets", "sounds", "overworld.mp3"),
            "general_battle": os.path.join(BASE_DIR, "assets", "sounds", "general_battle.mp3"),
        }
        
        self.saves = {"1": None, "2": None, "3": None}
        self.current_save_slot = None
        self.load_saves_metadata()
        
        self.state = STATE_MAIN_MENU
        
        self.gm = GameManager()
        self.dictionary = WordDictionary("normal")
        self.board = TileBoard()
        
        self.item_icons = {}
        self.inventory = [None] * 50
        self.show_inventory = False
        self.inv_scroll = 0
        self.dragged_item = None
        self.dragged_from_idx = -1
        
        self.stats_data = {'time': [], 'attempts': [], 'combo': [], 'damage': [], 'keys': []}
        
        self.setup_assets()
        self.setup_selection()
        self.reset_player_data()
        
        self.nearby_interactables = []
        self.interact_index = 0
        self.enemy_hit_count = 0  
        self.pending_warp_idx = -1
        self.current_bgm = None
        self.current_battle_bg = None 
        self.defeated_bosses = {} 
        
        db_path = os.path.join(BASE_DIR, "data/defeated_bosses.json")
        if os.path.exists(db_path):
            try:
                with open(db_path, 'r') as f:
                    self.defeated_bosses = json.load(f)
            except json.JSONDecodeError:
                self.defeated_bosses = {}
        
        self.generated_boss_levels = set()
        maps_dir = os.path.join(BASE_DIR, "data/maps")
        if os.path.exists(maps_dir):
            for f in os.listdir(maps_dir):
                if f.endswith('.json') and f.startswith('realm_'):
                    try:
                        with open(os.path.join(maps_dir, f), 'r') as mf:
                            mdata = json.load(mf)
                            for obj in mdata.get('objects', []):
                                if obj.get('type') == 'statue' and obj.get('data', {}).get('tier') == 'Boss':
                                    parts = f.replace('realm_', '').replace('.json', '').split('_')
                                    rx, ry = int(parts[0]), int(parts[1])
                                    lvl = abs(rx) + abs(ry) + 1
                                    self.generated_boss_levels.add(lvl)
                                    break
                    except: pass
        
        self.game_map = GameMap(self.realm_x, self.realm_y, False)
        self.statues_collected = len([s for s in self.game_map.get_statues() if s.collected])
        self.total_statues = len(self.game_map.get_statues())
        
        self.floating_texts = []
        self.p_anim_timer = 0; self.p_anim_x = 0
        self.e_anim_timer = 0; self.e_anim_x = 0
        self.battle_float_timer = 0
        self.crit_timer = 0
        self.shake_timer = 0
        self.shake_amount = 0
        
        self.target_word = self.dictionary.generate_random_word()
        self.current_guess = ""
        self.guess_history = []
        self.absent_letters = set(); self.yellow_letters = set()
        self.green_letters = [None] * 5
        
        self.showing_dialogue = False
        self.current_npc = None
        self.dialogue_timer = 0
        self.current_statue = None
        
        self.setup_overworld()
        self.sync_music()

    def load_stats_csv(self):
        self.stats_data = {'time': [], 'attempts': [], 'combo': [], 'damage': [], 'keys': []}
        path = os.path.join(BASE_DIR, "data", "raw", "gameplay_stats.csv")
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self.stats_data['time'].append(float(row.get('time_taken_per_word', 0)))
                        self.stats_data['attempts'].append(float(row.get('attempts_per_word', 0)))
                        self.stats_data['combo'].append(float(row.get('combo_achieved', 0)))
                        self.stats_data['damage'].append(float(row.get('damage_per_turn', 0)))
                        self.stats_data['keys'].append(float(row.get('keystrokes_per_word', 0)))
            except Exception as e:
                print(f"Error loading stats CSV: {e}")

    def load_saves_metadata(self):
        path = os.path.join(BASE_DIR, "data", "saves.json")
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    self.saves = json.load(f)
            except:
                self.saves = {"1": None, "2": None, "3": None}

    def save_game_data(self):
        if not self.current_save_slot: return
        self.saves[str(self.current_save_slot)] = {
            "hp": self.player.hp,
            "max_hp": self.player_max_hp,
            "base_atk": self.base_atk,
            "gold": self.gold,
            "inventory": self.inventory,
            "realm_x": self.realm_x,
            "realm_y": self.realm_y,
            "pos": self.map_player_pos,
            "defeated_bosses": self.defeated_bosses,
            "selections": self.selections,
            "level": self.current_level,
            "generated_bosses": list(self.generated_boss_levels) if hasattr(self, 'generated_boss_levels') else []
        }
        path = os.path.join(BASE_DIR, "data", "saves.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.saves, f)

    def load_game_data(self, slot):
        data = self.saves[str(slot)]
        self.current_save_slot = slot
        self.player_max_hp = data.get("max_hp", 100)
        self.base_atk = data.get("base_atk", 15)
        self.player = Player(hp=data.get("hp", 100), base_attack=self.base_atk)
        self.gold = data.get("gold", 50)
        
        loaded_inv = data.get("inventory", [None]*50)
        while len(loaded_inv) < 50: loaded_inv.append(None)
        self.inventory = loaded_inv
        
        self.realm_x = data.get("realm_x", 0)
        self.realm_y = data.get("realm_y", 0)
        self.map_player_pos = data.get("pos", [15*64, 15*64])
        self.defeated_bosses = data.get("defeated_bosses", {})
        self.selections = data.get("selections", {k: 0 for k in self.tabs})
        self.current_level = data.get("level", 1)
        self.generated_boss_levels = set(data.get("generated_bosses", []))
        self.inv_scroll = 0
        
        self.update_player_visuals()
        self.game_map = GameMap(self.realm_x, self.realm_y)
        self.statues_collected = len([s for s in self.game_map.get_statues() if s.collected])
        self.total_statues = len(self.game_map.get_statues())
        
        self.setup_overworld()
        self.state = STATE_OVERWORLD

    def reset_player_data(self):
        self.gold = 50
        self.base_atk = 15
        self.player_max_hp = 100
        self.player = Player(hp=self.player_max_hp, base_attack=self.base_atk)
        self.show_inventory = False
        self.inv_scroll = 0
        self.inventory = [None] * 50
        self.add_item('compass', 'Warp Scroll', 'Teleports you safely', 1)
        self.add_item('potion', 'Health Potion', 'Heals 50 HP', 2)
        self.add_item('scroll', 'Hint Scroll', 'Reveals 1 letter', 3) 
        self.realm_x, self.realm_y = 0, 0
        self.current_level = 1
        self.last_normal_realm = (0, 0)
        self.defeated_bosses = {}
        self.selections = {k: 0 for k in self.tabs}
        self.update_player_visuals()

    def start_new_game(self, slot):
        self.current_save_slot = slot
        self.reset_player_data()
        self.game_map = GameMap(0, 0)
        self.map_player_pos = list(self.game_map.spawn_point)
        self.statues_collected = len([s for s in self.game_map.get_statues() if s.collected])
        self.total_statues = len(self.game_map.get_statues())
        self.setup_overworld()
        self.state = STATE_SELECTION 

    def play_music_track(self, track_name):
        path = self.music_tracks.get(track_name)
        if not path or not os.path.exists(path):
            self.stop_music()
            return

        if self.current_bgm == track_name:
            return

        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1)
            pygame.mixer.music.set_volume(self.bgm_volume)
            self.current_bgm = track_name
        except Exception as e:
            print(f"Error playing music {path}: {e}")
            self.stop_music()

    def play_god_bgm(self, god_name):
        base_path = os.path.join(BASE_DIR, "assets", "sounds", f"{god_name.lower()}_bgm")
        possible_paths = [f"{base_path}.mp3", f"{base_path}.wav", f"{base_path}.ogg"]

        if self.current_bgm != god_name:
            loaded = False
            for path in possible_paths:
                if os.path.exists(path):
                    try:
                        pygame.mixer.music.load(path)
                        pygame.mixer.music.play(-1) 
                        self.current_bgm = god_name
                        loaded = True
                        break
                    except Exception as e:
                        print(f"Error playing music {path}: {e}")
            if not loaded:
                pygame.mixer.music.stop()
                self.current_bgm = None

    def stop_music(self):
        pygame.mixer.music.stop()
        self.current_bgm = None

    def sync_music(self):
        if self.state in (STATE_MAIN_MENU, STATE_SAVE_SLOTS, STATE_SELECTION, STATE_SETTINGS):
            self.play_music_track("main_menu")
            return

        if self.state == STATE_BATTLE:
            statue_tier = self.current_statue.data.get('tier') if self.current_statue else None
            if statue_tier == 'Boss' and self.current_statue:
                self.play_god_bgm(self.current_statue.data.get('god', ''))
            else:
                self.play_music_track("general_battle")
            return

        if self.state in (STATE_OVERWORLD, STATE_SHOP, STATE_UPGRADE, STATE_WARP):
            self.play_music_track("overworld")
            return

    def load_image_safely(self, path, size, fallback_color):
        if os.path.exists(path): 
            try:
                return pygame.transform.scale(pygame.image.load(path).convert_alpha(), size)
            except: pass
        surf = pygame.Surface(size)
        surf.fill(fallback_color)
        return surf

    def setup_assets(self):
        map_bg_path = os.path.join(BASE_DIR, "assets", "images", "map_bg.png")
        battle_bg_path = os.path.join(BASE_DIR, "assets", "images", "bg.png")
        sprite_path = os.path.join(BASE_DIR, "assets", "images", "roguelikeChar_transparent.png")
        self.overworld_bg = pygame.transform.scale(self.load_image_safely(map_bg_path, (800, 600), (30, 80, 40)), (800, 600))
        self.battle_bg = pygame.transform.scale(self.load_image_safely(battle_bg_path, (800, 600), (80, 120, 200)), (800, 600))
        self.sprite_sheet = SpriteSheet(sprite_path)
        
        compass_img = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(compass_img, GOLD, (16, 16), 12)
        pygame.draw.circle(compass_img, BG_DARK, (16, 16), 12, 2)
        pygame.draw.polygon(compass_img, ACCENT_RED, [(16, 6), (12, 16), (20, 16)])
        pygame.draw.polygon(compass_img, TEXT_PRIMARY, [(16, 26), (12, 16), (20, 16)])
        self.item_icons['compass'] = compass_img
        
        potion_img = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.rect(potion_img, ACCENT_RED_GLOW, (10, 14, 12, 14)) 
        pygame.draw.rect(potion_img, WHITE, (12, 6, 8, 8))
        pygame.draw.rect(potion_img, BG_DARK, (10, 14, 12, 14), 2) 
        pygame.draw.rect(potion_img, BG_DARK, (12, 6, 8, 8), 2)
        self.item_icons['potion'] = potion_img
        
        scroll_img = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.rect(scroll_img, TEXT_PRIMARY, (8, 8, 16, 20)) 
        pygame.draw.rect(scroll_img, GOLD_DIM, (6, 12, 20, 5))
        pygame.draw.rect(scroll_img, BG_DARK, (8, 8, 16, 20), 2) 
        self.item_icons['scroll'] = scroll_img

    def add_item(self, item_id, name, desc, qty=1):
        for slot in self.inventory:
            if slot and slot['id'] == item_id and slot.get('qty', 1) > 0:
                slot['qty'] += qty; return True
        for i in range(len(self.inventory)):
            if self.inventory[i] is None:
                self.inventory[i] = {'id': item_id, 'name': name, 'desc': desc, 'qty': qty}
                return True
        return False

    def generate_box(self, c1, r1, c2, r2): return [(c, r) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]

    def filter_empty(self, coords_list):
        valid = []
        for c, r in coords_list:
            img = self.sprite_sheet.get_image_by_grid(c, r, 1)
            if img.get_bounding_rect().width > 0: valid.append((c, r))
        return valid

    def setup_selection(self):
        player_bases = [(1, 0), (1, 1), (1, 2)]
        self.enemy_bases = player_bases
        self.options = {
            'base': player_bases, 'pants': [None] + self.filter_empty(self.generate_box(2, 0, 4, 9)),
            'armor': [None] + self.filter_empty(self.generate_box(5, 0, 17, 9)),
            'hair': [None] + self.filter_empty(self.generate_box(18, 0, 25, 7) + self.generate_box(18, 8, 20, 11)),
            'hat': [None] + self.filter_empty(self.generate_box(29, 0, 31, 8)),
            'shield': [None] + self.filter_empty(self.generate_box(36, 0, 39, 8)),
            'weapon': [None] + self.filter_empty(self.generate_box(41, 0, 55, 4) + self.generate_box(41, 5, 54, 9))
        }
        self.tabs = ['base', 'hair', 'hat', 'armor', 'pants', 'weapon', 'shield']
        self.tab_names = ['BODY', 'HAIR', 'HAT', 'ARMOR', 'PANTS', 'WEAPON', 'SHIELD']
        self.current_tab = 'base'
        self.selections, self.pages = {k: 0 for k in self.tabs}, {k: 0 for k in self.tabs}
        self.items_per_page = 30 
        self.start_btn_rect = pygame.Rect(495, 495, 260, 50)
        self.active_buttons = []
        self.update_player_visuals()

    def update_player_visuals(self):
        layers = [self.options[k][self.selections[k]] for k in ['base', 'pants', 'armor', 'hair', 'hat', 'shield', 'weapon']]
        self.player_preview_img = self.sprite_sheet.get_equipped_image_by_grid(layers, 14)
        self.player_overworld_equipped_img = self.sprite_sheet.get_equipped_image_by_grid(layers, 4)
        self.player_battle_img = self.sprite_sheet.get_equipped_image_by_grid(layers, 10)

    def setup_overworld(self):
        self.map_player_speed = 5
        self.facing_left_overworld = False
        self.is_moving = False
        self.move_timer_overworld = 0
        self.enemy_battle_pos = (550, 100)
        self.player_battle_pos = (80, 230)

    def trigger_shake(self, intensity, duration):
        if not self.shake_enabled: return
        self.shake_amount = intensity
        self.shake_timer = duration

    def change_realm(self, target_x, target_y, exit_side):
        self.game_map.save_map()
        
        if not self.game_map.is_boss_realm:
            self.last_normal_realm = (self.realm_x, self.realm_y)
        
        target_level = abs(target_x) + abs(target_y) + 1
        is_boss_tier = (target_level > 1 and target_level % 5 == 0)
        target_file = os.path.join(BASE_DIR, f"data/maps/realm_{target_x}_{target_y}.json")
        
        force_normal = False
        if not os.path.exists(target_file) and is_boss_tier:
            if target_level in self.generated_boss_levels:
                force_normal = True  
            else:
                self.generated_boss_levels.add(target_level)
                
        self.realm_x = target_x
        self.realm_y = target_y
        self.current_level = target_level
        self.game_map = GameMap(self.realm_x, self.realm_y, force_normal)
        
        self.total_statues = len(self.game_map.get_statues())
        self.statues_collected = len([s for s in self.game_map.get_statues() if s.collected])
        
        map_pixel_width = self.game_map.width * 64
        map_pixel_height = self.game_map.height * 64
        
        if self.game_map.is_boss_realm:
            self.map_player_pos = list(self.game_map.spawn_point)
        else:
            clamped_x = max(64, min(self.map_player_pos[0], map_pixel_width - 128))
            clamped_y = max(64, min(self.map_player_pos[1], map_pixel_height - 128))
            
            if exit_side == 'right': self.map_player_pos = [64, 13 * 64]
            elif exit_side == 'left': self.map_player_pos = [map_pixel_width - 128, 13 * 64]
            elif exit_side == 'bottom': self.map_player_pos = [15 * 64, 64]
            elif exit_side == 'top': self.map_player_pos = [15 * 64, map_pixel_height - 128]
            elif exit_side == 'teleport': self.map_player_pos = [15 * 64, 15 * 64] 
            
        self.game_map.ensure_safe_spawn(self.map_player_pos[0], self.map_player_pos[1])
        self.facing_left_overworld = False
        self.game_map.camera_offset = [0, 0]
        self.game_map.target_camera_offset = [0, 0]
        
        self.save_game_data()

    def execute_warp(self, tx, ty):
        item = self.inventory[self.pending_warp_idx]
        item['qty'] -= 1
        if item['qty'] <= 0:
            self.inventory[self.pending_warp_idx] = None
        self.change_realm(tx, ty, 'teleport')
        self.state = STATE_OVERWORLD

    def spawn_floating_text(self, text, x, y, color, font_type='large'):
        self.floating_texts.append({'text': text, 'x': x, 'y': y, 'timer': 45, 'color': color, 'font_type': font_type})

    def randomize_enemy(self):
        god = self.current_statue.data.get('god', 'Unknown')
        tier = self.current_statue.data.get('tier', 'Follower')
        
        role = "avatar" if tier.lower() == "boss" else tier.lower()
        bg_name = f"{god.lower()}_{role}.png"
        bg_path = os.path.join(BASE_DIR, "assets", "images", bg_name)
        
        self.current_battle_bg = None 
        if os.path.exists(bg_path):
            try:
                img = pygame.image.load(bg_path).convert()
                self.current_battle_bg = pygame.transform.scale(img, (800, 600))
            except: pass
        
        if tier == 'Boss':
            max_hp = 300 + (self.current_level * 50)
            atk = 20 + (self.current_level * 2)
            name = f"Avatar of {god}"
            self.enemy_reward = 150
        elif tier == 'Apostle':
            max_hp = 150 + (self.current_level * 15)
            atk = 15 + self.current_level
            name = f"{god}'s Apostle"
            self.enemy_reward = 80
        elif tier == 'Zealot':
            max_hp = 100 + (self.current_level * 10)
            atk = 10 + self.current_level
            name = f"{god}'s Zealot"
            self.enemy_reward = 50
        else:
            max_hp = 50 + (self.current_level * 5)
            atk = 5 + self.current_level
            name = f"{god}'s Follower"
            self.enemy_reward = 20
            
        self.enemy = Enemy(name=name, max_hp=max_hp, attack_power=atk)
        self.enemy_hit_count = 0 
        
        enemy_layers = [
            random.choice(self.options['base']), 
            random.choice(self.options['pants']), 
            random.choice(self.options['armor'][1:]),
            random.choice(self.options['hair']), 
            random.choice(self.options['hat']), 
            random.choice(self.options['shield']),
            random.choice(self.options['weapon'][1:])
        ]
        self.enemy_battle_img = self.sprite_sheet.get_equipped_image_by_grid(enemy_layers, 10)
        self.target_word = self.dictionary.generate_random_word()
        self.battle_float_timer, self.crit_timer, self.floating_texts = 0, 0, []
        self.board.current_attempt, self.guess_history, self.current_guess = 1, [], ""
        self.absent_letters, self.yellow_letters = set(), set()
        self.green_letters = [None] * 5

    def use_item(self, hotbar_idx):
        item = self.inventory[hotbar_idx]
        if not item: return
        
        slot_size = 40
        padding = 6
        start_x = (800 - (5 * slot_size + 4 * padding)) // 2
        px = start_x + hotbar_idx * (slot_size + padding) + (slot_size // 2)
        py = 515 
        
        if item['id'] == 'compass':
            if self.state == STATE_OVERWORLD:
                self.pending_warp_idx = hotbar_idx
                self.state = STATE_WARP
            else:
                self.spawn_floating_text("Can't use now", px, py, ACCENT_RED_GLOW, 'tiny')
                
        elif item['id'] == 'potion':
            if self.player.hp < self.player_max_hp:
                heal_amount = 50
                self.player.hp = min(self.player_max_hp, self.player.hp + heal_amount)
                self.spawn_floating_text(f"+{heal_amount} HP", px, py, EMERALD_500, 'tiny')
                item['qty'] -= 1
                if item['qty'] <= 0: self.inventory[hotbar_idx] = None
            else:
                self.spawn_floating_text("HP is Full", px, py, TEXT_PRIMARY, 'tiny')
                
        elif item['id'] == 'scroll':
            if self.state == STATE_BATTLE and not self.gm.game_over:
                for idx, c in enumerate(self.target_word):
                    if self.green_letters[idx] is None:
                        self.green_letters[idx] = c
                        self.spawn_floating_text("Hint Used!", px, py, GOLD_LIGHT, 'tiny')
                        item['qty'] -= 1
                        if item['qty'] <= 0: self.inventory[hotbar_idx] = None
                        break
            else:
                self.spawn_floating_text("Can't use now", px, py, ACCENT_RED_GLOW, 'tiny')

    def get_hovered_slot(self, pos):
        mx, my = pos
        slot_size = 40
        padding = 6
        
        start_x_hb = (800 - (5 * slot_size + 4 * padding)) // 2
        hotbar_start_y = 540
        for i in range(5):
            if pygame.Rect(start_x_hb + i * (slot_size + padding), hotbar_start_y, slot_size, slot_size).collidepoint(mx, my): return i
            
        if self.show_inventory:
            panel_x, panel_y = 40, 50
            panel_w = 340
            start_x_inv = panel_x + (panel_w - (5 * slot_size + 4 * padding)) // 2
            inv_start_y = panel_y + 90
            
            for i in range(40): 
                r, c = i // 5, i % 5
                idx = 5 + (self.inv_scroll * 5) + i
                if idx < len(self.inventory):
                    if pygame.Rect(start_x_inv + c * (slot_size + padding), inv_start_y + r * (slot_size + padding), slot_size, slot_size).collidepoint(mx, my): 
                        return idx
        return None

    def get_nearby_interactables(self, p_rect, dist=50):
        interactables = []
        check_rect = p_rect.inflate(dist, dist)
        for o in self.game_map.objects:
            if o.type == "statue" and not o.collected and check_rect.colliderect(o.rect):
                interactables.append(o)
            elif o.type in ("npc", "shop_npc", "shop") and check_rect.colliderect(o.rect):
                interactables.append(o)
        return interactables

    def opens_shop(self, obj):
        return bool(obj) and (obj.type == "shop" or obj.data.get('name') == 'Merchant')

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                if hasattr(self, 'game_map'): self.game_map.save_map()
                self.save_game_data()
                pygame.quit(); sys.exit()
                
            elif event.type == pygame.MOUSEWHEEL:
                if self.state == STATE_OVERWORLD and self.show_inventory:
                    self.inv_scroll -= event.y
                    max_scroll = max(0, ((len(self.inventory) - 5) // 5) - 8)
                    self.inv_scroll = max(0, min(self.inv_scroll, max_scroll))
            
            if self.state == STATE_MAIN_MENU:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    empty_slots = [i for i in range(1, 4) if not self.saves[str(i)]]
                    
                    btn_rects = {}
                    if empty_slots:
                        btn_rects["NEW GAME"] = pygame.Rect(250, 260, 300, 55)
                        btn_rects["LOAD GAME"] = pygame.Rect(250, 330, 300, 55)
                        btn_rects["SETTINGS"] = pygame.Rect(250, 400, 300, 55)
                        btn_rects["EXIT"] = pygame.Rect(250, 470, 300, 55)
                    else:
                        btn_rects["LOAD GAME"] = pygame.Rect(250, 260, 300, 55)
                        btn_rects["SETTINGS"] = pygame.Rect(250, 330, 300, 55)
                        btn_rects["EXIT"] = pygame.Rect(250, 400, 300, 55)

                    for text, rect in btn_rects.items():
                        if rect.collidepoint(mx, my):
                            if text == "NEW GAME":
                                self.start_new_game(empty_slots[0]) 
                            elif text == "LOAD GAME":
                                self.save_mode = 'load'
                                self.state = STATE_SAVE_SLOTS
                            elif text == "SETTINGS":
                                self.state = STATE_SETTINGS
                            elif text == "EXIT":
                                pygame.quit(); sys.exit()
                        
            elif self.state == STATE_SAVE_SLOTS:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = STATE_MAIN_MENU
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if pygame.Rect(20, 20, 100, 40).collidepoint(mx, my):
                        self.state = STATE_MAIN_MENU
                        
                    for i in range(1, 4):
                        data = self.saves[str(i)]
                        y = 100 + (i-1)*130
                        slot_rect = pygame.Rect(150, y, 500, 110)
                        del_rect = pygame.Rect(150 + 500 - 45, y + 35, 40, 40)
                        
                        if data and del_rect.collidepoint(mx, my):
                            self.saves[str(i)] = None
                            path = os.path.join(BASE_DIR, "data", "saves.json")
                            with open(path, 'w') as f: json.dump(self.saves, f)
                            
                        elif slot_rect.collidepoint(mx, my):
                            if self.saves[str(i)]: 
                                self.load_game_data(i)

            elif self.state in [STATE_SETTINGS, STATE_PAUSE]:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = STATE_OVERWORLD if self.state == STATE_PAUSE else STATE_MAIN_MENU
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    
                    if pygame.Rect(370, 200, 35, 35).collidepoint(mx, my):
                        self.bgm_volume = max(0.0, self.bgm_volume - 0.1)
                        pygame.mixer.music.set_volume(self.bgm_volume)
                    elif pygame.Rect(525, 200, 35, 35).collidepoint(mx, my):
                        self.bgm_volume = min(1.0, self.bgm_volume + 0.1)
                        pygame.mixer.music.set_volume(self.bgm_volume)
                        
                    if pygame.Rect(410, 280, 190, 35).collidepoint(mx, my):
                        self.shake_enabled = not self.shake_enabled
                        
                    if self.state == STATE_PAUSE:
                        if pygame.Rect(250, 370, 300, 45).collidepoint(mx, my):
                            self.state = STATE_OVERWORLD
                        elif pygame.Rect(250, 430, 300, 45).collidepoint(mx, my):
                            self.save_game_data()
                            self.state = STATE_MAIN_MENU
                    else:
                        if pygame.Rect(250, 430, 300, 45).collidepoint(mx, my):
                            self.state = STATE_MAIN_MENU

            elif self.state == STATE_OVERWORLD: 
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    
                    if pygame.Rect(740, 20, 40, 40).collidepoint(mx, my):
                        self.state = STATE_PAUSE
                        return
                        
                    slot_idx = self.get_hovered_slot(event.pos)
                    if slot_idx is not None and self.inventory[slot_idx]:
                        self.dragged_item = self.inventory[slot_idx]
                        self.dragged_from_idx = slot_idx
                        self.inventory[slot_idx] = None
                    elif self.showing_dialogue:
                        dialogue_rect = pygame.Rect(100, 400, 600, 120)
                        if dialogue_rect.collidepoint(mx, my):
                            self.showing_dialogue = False
                            if self.opens_shop(self.current_npc):
                                self.state = STATE_SHOP
                            self.current_npc = None

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.dragged_item:
                        slot_idx = self.get_hovered_slot(event.pos)
                        if slot_idx is not None:
                            temp = self.inventory[slot_idx]
                            self.inventory[slot_idx] = self.dragged_item
                            if temp: self.inventory[self.dragged_from_idx] = temp
                        else:
                            self.inventory[self.dragged_from_idx] = self.dragged_item
                        self.dragged_item = None
                        self.dragged_from_idx = -1
                        
                elif event.type == pygame.KEYDOWN:
                    if self.showing_dialogue:
                        if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                            self.showing_dialogue = False
                            if self.opens_shop(self.current_npc):
                                self.state = STATE_SHOP
                            self.current_npc = None
                        elif event.key == pygame.K_ESCAPE:
                            self.showing_dialogue = False
                            self.current_npc = None
                    else:
                        if event.key == pygame.K_ESCAPE:
                            self.state = STATE_PAUSE
                            return
                            
                        menu_active = hasattr(self, 'nearby_interactables') and len(self.nearby_interactables) > 1
                        if menu_active and event.key == pygame.K_UP:
                            self.interact_index = (self.interact_index - 1) % len(self.nearby_interactables)
                        elif menu_active and event.key == pygame.K_DOWN:
                            self.interact_index = (self.interact_index + 1) % len(self.nearby_interactables)
                        elif event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_f):
                            if hasattr(self, 'nearby_interactables') and self.nearby_interactables:
                                o = self.nearby_interactables[self.interact_index]
                                if o.type == "statue":
                                    self.current_statue = o
                                    self.state = STATE_BATTLE
                                    self.randomize_enemy()
                                    self.gm.start_word_timer()
                                elif o.type in ("npc", "shop_npc", "shop"):
                                    self.showing_dialogue = True
                                    self.current_npc = o
                                    self.dialogue_timer = 180  
                        elif event.key == pygame.K_e:
                            self.show_inventory = not self.show_inventory
                            if self.show_inventory:
                                self.load_stats_csv()
                        elif pygame.K_1 <= event.key <= pygame.K_5:
                            self.use_item(event.key - pygame.K_1)

            elif self.state == STATE_WARP:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: self.state = STATE_OVERWORLD
                    elif event.key == pygame.K_1: self.execute_warp(0, 0)
                    elif event.key == pygame.K_2: self.execute_warp(self.last_normal_realm[0], self.last_normal_realm[1])
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if pygame.Rect(180, 230, 440, 45).collidepoint(mx, my): self.execute_warp(0, 0)
                    elif pygame.Rect(180, 290, 440, 45).collidepoint(mx, my): self.execute_warp(self.last_normal_realm[0], self.last_normal_realm[1])

            elif self.state == STATE_SHOP:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if hasattr(self, 'shop_potion_rect') and self.shop_potion_rect.collidepoint(mx, my):
                        if self.gold >= 50 and self.add_item('potion', 'Health Potion', 'Heals 50 HP', 1): self.gold -= 50
                    elif hasattr(self, 'shop_scroll_rect') and self.shop_scroll_rect.collidepoint(mx, my):
                        if self.gold >= 50 and self.add_item('scroll', 'Hint Scroll', 'Reveals 1 letter', 1): self.gold -= 50
                    elif hasattr(self, 'shop_exit_rect') and self.shop_exit_rect.collidepoint(mx, my):
                        self.state = STATE_OVERWORLD
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN): self.state = STATE_OVERWORLD
                    elif event.key == pygame.K_1:
                        if self.gold >= 50 and self.add_item('potion', 'Health Potion', 'Heals 50 HP', 1): self.gold -= 50
                    elif event.key == pygame.K_2:
                        if self.gold >= 50 and self.add_item('scroll', 'Hint Scroll', 'Reveals 1 letter', 1): self.gold -= 50

            elif self.state == STATE_UPGRADE:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if hasattr(self, 'upg_ares_rect') and self.upg_ares_rect.collidepoint(mx, my):
                        self.base_atk += getattr(self, 'current_reward_atk', 5)
                        self.player.base_attack = self.base_atk
                        self.save_game_data()
                        self.state = STATE_OVERWORLD
                    elif hasattr(self, 'upg_demeter_rect') and self.upg_demeter_rect.collidepoint(mx, my):
                        self.player_max_hp += getattr(self, 'current_reward_hp', 20)
                        self.player.hp = self.player_max_hp
                        self.save_game_data()
                        self.state = STATE_OVERWORLD
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.base_atk += getattr(self, 'current_reward_atk', 5)
                        self.player.base_attack = self.base_atk
                        self.save_game_data()
                        self.state = STATE_OVERWORLD
                    elif event.key == pygame.K_2:
                        self.player_max_hp += getattr(self, 'current_reward_hp', 20)
                        self.player.hp = self.player_max_hp
                        self.save_game_data()
                        self.state = STATE_OVERWORLD
            
            elif self.state == STATE_SELECTION:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.start_btn_rect.collidepoint(event.pos): 
                        self.save_game_data()
                        self.state = STATE_OVERWORLD; return
                    for btn in self.active_buttons:
                        if btn['rect'].collidepoint(event.pos):
                            if btn['type'] == 'tab': self.current_tab = btn['tab']
                            elif btn['type'] == 'item': self.selections[self.current_tab] = btn['idx']; self.update_player_visuals()
                            elif btn['type'] == 'prev': self.pages[self.current_tab] = max(0, self.pages[self.current_tab] - 1)
                            elif btn['type'] == 'next': 
                                max_p = math.ceil(len(self.options[self.current_tab]) / self.items_per_page) - 1
                                self.pages[self.current_tab] = min(max_p, self.pages[self.current_tab] + 1)
                            break 
                            
            elif self.state == STATE_BATTLE:
                if event.type == pygame.KEYDOWN:
                    if self.gm.game_over:
                        if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                            self.gm.game_over = False
                            if self.enemy.current_hp <= 0:
                                self.current_statue.collected = True
                                self.statues_collected += 1
                                self.gold += self.enemy_reward
                                self.game_map.save_map()
                                
                                tier = self.current_statue.data.get('tier', 'Follower')
                                if tier == 'Boss':
                                    self.current_reward_atk = random.randint(8, 15)
                                    self.current_reward_hp = random.randint(40, 60)
                                    self.add_item('compass', 'Warp Scroll', 'Teleports you safely', 1)
                                    self.spawn_floating_text("+1 Warp Scroll", 400, 200, CYAN_400)
                                    k = f"{self.realm_x}_{self.realm_y}"
                                    self.defeated_bosses[k] = self.game_map.god_theme
                                elif tier == 'Apostle':
                                    self.current_reward_atk = random.randint(4, 8)
                                    self.current_reward_hp = random.randint(20, 35)
                                elif tier == 'Zealot':
                                    self.current_reward_atk = random.randint(2, 5)
                                    self.current_reward_hp = random.randint(10, 20)
                                else:
                                    self.current_reward_atk = random.randint(1, 3)
                                    self.current_reward_hp = random.randint(5, 10)
                                    
                                self.save_game_data()
                                self.state = STATE_UPGRADE 
                            else:
                                self.player.hp = self.player_max_hp
                                self.state = STATE_OVERWORLD 
                    else:
                        if event.key == pygame.K_ESCAPE:
                            self.state = STATE_OVERWORLD
                        elif event.key == pygame.K_1:
                            px = self.player_battle_pos[0] + 80 + random.randint(-20, 20)
                            py = self.player_battle_pos[1] - 20 + random.randint(-15, 15)
                            potion_idx = next((i for i, item in enumerate(self.inventory) if item and item['id'] == 'potion'), None)
                            if potion_idx is not None:
                                if self.player.hp < self.player_max_hp:
                                    self.player.hp = min(self.player_max_hp, self.player.hp + 50)
                                    self.spawn_floating_text("+50 HP", px, py, EMERALD_500, 'small')
                                    self.inventory[potion_idx]['qty'] -= 1
                                    if self.inventory[potion_idx]['qty'] <= 0: self.inventory[potion_idx] = None
                                else:
                                    self.spawn_floating_text("HP is Full", px, py, TEXT_PRIMARY, 'small')
                            else:
                                self.spawn_floating_text("No Potions", px, py, ACCENT_RED_GLOW, 'small')
                        
                        elif event.key == pygame.K_2:
                            px = self.player_battle_pos[0] + 80 + random.randint(-20, 20)
                            py = self.player_battle_pos[1] - 20 + random.randint(-15, 15)
                            scroll_idx = next((i for i, item in enumerate(self.inventory) if item and item['id'] == 'scroll'), None)
                            if scroll_idx is not None:
                                for idx, c in enumerate(self.target_word):
                                    if self.green_letters[idx] is None:
                                        self.green_letters[idx] = c
                                        self.spawn_floating_text("Hint Used!", px, py, GOLD, 'small')
                                        self.inventory[scroll_idx]['qty'] -= 1
                                        if self.inventory[scroll_idx]['qty'] <= 0: self.inventory[scroll_idx] = None
                                        break
                            else:
                                self.spawn_floating_text("No Scrolls", px, py, ACCENT_RED_GLOW, 'small')
                                
                        elif event.unicode.isascii() and event.unicode.isalpha() and len(self.current_guess) < 5:
                            self.current_guess += event.unicode.upper(); self.gm.keystroke_count += 1
                        elif event.key == pygame.K_BACKSPACE: self.current_guess = self.current_guess[:-1]; self.gm.keystroke_count += 1
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and len(self.current_guess) == 5:
                            self.gm.keystroke_count += 1; self.submit_guess()

        self.sync_music()

    def submit_guess(self):
        guess = self.current_guess; self.current_guess = ""
        colors = self.board.evaluate_colors(guess, self.target_word); self.guess_history.append((guess, colors))
        for i in range(5):
            c = guess[i]; color = colors[i]
            if color == "GREEN":
                self.green_letters[i] = c
                if c in self.yellow_letters: self.yellow_letters.discard(c)
            elif color == "YELLOW":
                if c not in self.green_letters: self.yellow_letters.add(c)
            elif color == "GRAY":
                if c not in self.green_letters and c not in self.yellow_letters: self.absent_letters.add(c)
                
        if guess == self.target_word:
            self.gm.end_word_timer()
            self.player.combo_count += 1
            damage = self.player.calculate_damage()
            self.enemy.take_damage(damage)
            self.gm.record_word_data(self.board.current_attempt - 1, self.player.combo_count, damage)
            
            self.p_anim_timer = 20
            self.trigger_shake(8, 15) 
            
            px = self.enemy_battle_pos[0] + 80 + random.randint(-20, 20)
            py = self.enemy_battle_pos[1] - 20 + random.randint(-15, 15)
            self.spawn_floating_text(f"-{damage}", px, py, ACCENT_RED_GLOW)
            
            if self.player.combo_count > 1: self.crit_timer = 60
            
            if self.gm.check_win_condition(self.enemy): self.gm.game_over = True
            else: self.reset_for_next_word()
        else:
            if self.board.current_attempt > self.board.grid_size:
                self.player.combo_count = 0
                
                self.enemy_hit_count += 1
                is_crit = (self.enemy_hit_count % 3 == 0)
                
                base_damage = self.enemy.attack_power
                final_damage = base_damage * 2 if is_crit else base_damage
                
                self.player.hp -= final_damage
                if self.player.hp < 0: self.player.hp = 0
                
                self.e_anim_timer = 20
                self.trigger_shake(20 if is_crit else 15, 20) 
                
                px = self.player_battle_pos[0] + 80 + random.randint(-20, 20)
                py = self.player_battle_pos[1] - 20 + random.randint(-15, 15)
                
                if is_crit:
                    self.spawn_floating_text("CRITICAL HIT!", px, py - 20, ACCENT_RED_GLOW, 'small')
                self.spawn_floating_text(f"-{final_damage}", px, py, ACCENT_RED_GLOW)
                
                if self.player.hp <= 0: self.gm.game_over = True
                else: self.reset_for_next_word()

    def reset_for_next_word(self):
        self.target_word = self.dictionary.generate_random_word()
        self.board.current_attempt = 1
        self.guess_history = []
        self.absent_letters = set()
        self.yellow_letters = set()
        self.green_letters = [None] * 5 
        self.gm.start_word_timer()

    def draw_particles(self):
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['pulse'] += 0.02
            if p['y'] < -10: 
                p['y'] = 610
                p['x'] = random.uniform(0, 800)
            if p['x'] < -10: p['x'] = 810
            if p['x'] > 810: p['x'] = -10
            
            alpha = int(100 + 100 * math.sin(p['pulse']))
            alpha = max(0, min(255, alpha))
            
            s = pygame.Surface((int(p['size']*4), int(p['size']*4)), pygame.SRCALPHA)
            pygame.draw.circle(s, (201, 162, 39, int(alpha*0.3)), (int(p['size']*2), int(p['size']*2)), int(p['size']*2))
            pygame.draw.circle(s, (232, 200, 74, alpha), (int(p['size']*2), int(p['size']*2)), max(1, int(p['size']*0.5)))
            self.screen.blit(s, (int(p['x']), int(p['y'])))

    def draw_styled_btn(self, text, x, y, w, h, is_hover, is_danger=False):
        vx = x + 6 if is_hover else x
        rect = pygame.Rect(x, y, w, h)
        
        bg_col = (40, 10, 10, 230) if is_danger and is_hover else ((20, 5, 5, 200) if is_danger else ((25, 28, 42, 230) if is_hover else (12, 14, 24, 180)))
        
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, bg_col, s.get_rect())
        
        accent = ACCENT_RED_GLOW if is_danger else GOLD
        border = GOLD_DIM if is_hover else BORDER_SUBTLE
        
        pygame.draw.rect(s, border, s.get_rect(), 1)
        if is_hover:
            pygame.draw.rect(s, accent, (0, 0, 4, h))
            
        t_color = GOLD_LIGHT if is_hover else TEXT_SECONDARY
        if is_danger: t_color = ACCENT_RED_GLOW
        
        t_surf = self.btn_font.render(text, True, t_color)
        s.blit(t_surf, (w//2 - t_surf.get_width()//2, h//2 - t_surf.get_height()//2))
        
        self.screen.blit(s, (vx, y))
        return rect

    def draw_main_menu(self):
        self.screen.fill(BG_DEEP)
        self.draw_particles()
        
        pulse = abs(math.sin(time.time() * 2))
        title = self.title_font.render("CRYPTIC COMBAT", True, GOLD)
        glow = self.title_font.render("CRYPTIC COMBAT", True, (int(201*0.5*pulse), int(162*0.5*pulse), int(39*0.5*pulse)))
        tx = self.screen_width//2 - title.get_width()//2
        self.screen.blit(glow, (tx, 100))
        self.screen.blit(title, (tx, 100))
        
        sub = self.small_font.render("I N T O   T H E   U N K N O W N", True, TEXT_SECONDARY)
        self.screen.blit(sub, (self.screen_width//2 - sub.get_width()//2, 170))
        
        mx, my = pygame.mouse.get_pos()
        
        empty_slots = [i for i in range(1, 4) if not self.saves[str(i)]]
        btn_rects = {}
        
        if empty_slots:
            btn_rects["NEW GAME"] = pygame.Rect(250, 260, 300, 55)
            btn_rects["LOAD GAME"] = pygame.Rect(250, 330, 300, 55)
            btn_rects["SETTINGS"] = pygame.Rect(250, 400, 300, 55)
            btn_rects["EXIT"] = pygame.Rect(250, 470, 300, 55)
        else:
            btn_rects["LOAD GAME"] = pygame.Rect(250, 260, 300, 55)
            btn_rects["SETTINGS"] = pygame.Rect(250, 330, 300, 55)
            btn_rects["EXIT"] = pygame.Rect(250, 400, 300, 55)
            
        for text, rect in btn_rects.items():
            is_hover = rect.collidepoint(mx, my)
            self.draw_styled_btn(text, rect.x, rect.y, rect.width, rect.height, is_hover, text=="EXIT")

    def draw_save_slots(self):
        self.screen.fill(BG_DEEP)
        self.draw_particles()
        
        title_surf = self.name_font.render("CHARACTERS", True, GOLD)
        title_x = (self.screen_width // 2) - (title_surf.get_width() // 2)
        self.screen.blit(title_surf, (title_x, 40))
        
        mx, my = pygame.mouse.get_pos()
        b_rect = pygame.Rect(20, 20, 100, 40)
        b_hover = b_rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (255,255,255,20) if b_hover else (0,0,0,0), b_rect)
        self.screen.blit(self.btn_font.render("< BACK", True, TEXT_PRIMARY), (30, 30))
        
        for i in range(1, 4):
            data = self.saves[str(i)]
            y = 100 + (i-1)*130
            rect = pygame.Rect(150, y, 500, 110)
            del_rect = pygame.Rect(150 + 500 - 45, y + 35, 40, 40) 
            
            hover = rect.collidepoint(mx, my)
            slot_surf = pygame.Surface((500, 110), pygame.SRCALPHA)
            bg_col = (22, 25, 38, 240) if hover else (15, 18, 30, 200)
            pygame.draw.rect(slot_surf, bg_col, slot_surf.get_rect())
            pygame.draw.rect(slot_surf, GOLD if hover else BORDER_SUBTLE, slot_surf.get_rect(), 2)
            self.screen.blit(slot_surf, (150, y))
            
            if data:
                self.screen.blit(self.name_font.render(f"SLOT {i} - Level {data.get('level', 1)}", True, GOLD), (170, y+25))
                self.screen.blit(self.small_font.render(f"HP: {data.get('hp')}/{data.get('max_hp')} | ATK: {data.get('base_atk')} | GOLD: {data.get('gold')}G", True, TEXT_PRIMARY), (170, y+65))
                
                d_hover = del_rect.collidepoint(mx, my)
                pygame.draw.rect(self.screen, ACCENT_RED_GLOW if d_hover else ACCENT_RED, del_rect)
                pygame.draw.rect(self.screen, WHITE, del_rect, 1)
                self.screen.blit(self.btn_font.render("X", True, WHITE), (del_rect.centerx-7, del_rect.centery-10))
            else:
                t = self.name_font.render(f"SLOT {i} - EMPTY", True, TEXT_DIM)
                self.screen.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))

    def draw_line_chart(self, surface, x, y, w, h, data, color, title, mx, my):
        pygame.draw.rect(surface, (20, 25, 40, 200), (x, y, w, h))
        pygame.draw.rect(surface, BORDER_SUBTLE, (x, y, w, h), 1)
        surface.blit(self.tiny_font.render(title, True, TEXT_PRIMARY), (x+5, y+5))
        
        if not data:
            no_data = self.tiny_font.render("NO DATA", True, TEXT_DIM)
            surface.blit(no_data, (x + w//2 - no_data.get_width()//2, y + h//2 - no_data.get_height()//2))
            return
            
        data = data[-20:]
        max_val = max(data) if max(data) > 0 else 1
        pts = []
        pad_x, pad_y = 15, 25
        
        hovered_val = None
        hovered_pos = None

        for i, val in enumerate(data):
            px = x + pad_x + (i / max(1, len(data)-1)) * (w - 2*pad_x)
            py = y + h - 5 - (val / max_val) * (h - pad_y - 10)
            pts.append((px, py))
            if math.hypot(mx - px, my - py) < 8:
                hovered_val = val
                hovered_pos = (px, py)
            
        if len(pts) > 1:
            pygame.draw.lines(surface, color, False, pts, 2)
        for px, py in pts:
            pygame.draw.circle(surface, WHITE, (int(px), int(py)), 2)

        if hovered_val is not None:
            v_str = f"{round(hovered_val, 2)}"
            ts = self.tiny_font.render(v_str, True, WHITE)
            tr = ts.get_rect(center=(hovered_pos[0], hovered_pos[1] - 12))
            pygame.draw.rect(surface, (0,0,0,220), tr.inflate(8, 4))
            pygame.draw.rect(surface, GOLD, tr.inflate(8, 4), 1)
            surface.blit(ts, tr)

    def draw_bar_chart(self, surface, x, y, w, h, data, color, title, mx, my):
        pygame.draw.rect(surface, (20, 25, 40, 200), (x, y, w, h))
        pygame.draw.rect(surface, BORDER_SUBTLE, (x, y, w, h), 1)
        surface.blit(self.tiny_font.render(title, True, TEXT_PRIMARY), (x+5, y+5))
        
        if not data:
            no_data = self.tiny_font.render("NO DATA", True, TEXT_DIM)
            surface.blit(no_data, (x + w//2 - no_data.get_width()//2, y + h//2 - no_data.get_height()//2))
            return
            
        data = data[-20:]
        max_val = max(data) if max(data) > 0 else 1
        pad_x, pad_y = 15, 25
        bar_w = max(2, (w - 2*pad_x) // len(data) - 2)
        
        hovered_val = None
        hovered_pos = None

        for i, val in enumerate(data):
            px = x + pad_x + i * (bar_w + 2)
            ph = (val / max_val) * (h - pad_y - 10)
            py = y + h - 5 - ph
            rect = pygame.Rect(px, py, bar_w, ph)
            pygame.draw.rect(surface, color, rect)
            
            if rect.collidepoint(mx, my):
                hovered_val = val
                hovered_pos = (px + bar_w/2, py)

        if hovered_val is not None:
            v_str = f"{round(hovered_val, 2)}"
            ts = self.tiny_font.render(v_str, True, WHITE)
            tr = ts.get_rect(center=(hovered_pos[0], hovered_pos[1] - 12))
            pygame.draw.rect(surface, (0,0,0,220), tr.inflate(8, 4))
            pygame.draw.rect(surface, GOLD, tr.inflate(8, 4), 1)
            surface.blit(ts, tr)

    def draw_inventory_ui(self, surface):
        slot_size = 40
        padding = 6
        hotbar_start_y = 540
        slot_bg = BG_DARK 
        border_color = BORDER_SUBTLE 
        mx, my = pygame.mouse.get_pos()
        
        if self.show_inventory:
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 220)) 
            surface.blit(overlay, (0, 0))
            
            panel_x, panel_y = 40, 50
            panel_w, panel_h = 340, 480
            
            p_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            pygame.draw.rect(p_surf, (15, 18, 30, 200), p_surf.get_rect())
            pygame.draw.rect(p_surf, GOLD_DIM, p_surf.get_rect(), 2)
            surface.blit(p_surf, (panel_x, panel_y))
            
            surface.blit(self.small_font.render("INVENTORY & STATS", True, GOLD), (panel_x + 20, panel_y + 15))
            surface.blit(self.tiny_font.render(f"HP: {self.player.hp} / {self.player_max_hp}  |  ATK: {self.base_atk}", True, TEXT_PRIMARY), (panel_x + 20, panel_y + 45))
            
            grid_w = 5 * slot_size + 4 * padding
            start_x_inv = panel_x + (panel_w - grid_w) // 2
            inv_start_y = panel_y + 90
            
            for i in range(40): 
                r, c = i // 5, i % 5
                idx = 5 + (self.inv_scroll * 5) + i
                
                if idx < len(self.inventory):
                    rect = pygame.Rect(start_x_inv + c * (slot_size + padding), inv_start_y + r * (slot_size + padding), slot_size, slot_size)
                    
                    s = pygame.Surface((slot_size, slot_size), pygame.SRCALPHA)
                    pygame.draw.rect(s, slot_bg, s.get_rect()) 
                    pygame.draw.rect(s, border_color, s.get_rect(), 1) 
                    surface.blit(s, (rect.x, rect.y))
                    
                    item = self.inventory[idx]
                    if item:
                        surface.blit(self.item_icons[item['id']], (rect.x+4, rect.y+4))
                        if item.get('qty', 1) > 1:
                            surface.blit(self.tiny_font.render(str(item['qty']), True, WHITE), (rect.right-10, rect.bottom-12))

            sb_x = start_x_inv + grid_w + 10
            sb_y = inv_start_y
            sb_h = 8 * slot_size + 7 * padding
            pygame.draw.rect(surface, BG_DARK, (sb_x, sb_y, 10, sb_h))
            
            max_scroll = max(0, ((len(self.inventory) - 5) // 5) - 8)
            if max_scroll > 0:
                thumb_h = max(10, int(sb_h * (8 / (max_scroll + 8))))
                thumb_y = sb_y + int((self.inv_scroll / max_scroll) * (sb_h - thumb_h))
                pygame.draw.rect(surface, GOLD_DIM, (sb_x, thumb_y, 10, thumb_h))

            graph_x, graph_y = 400, 50
            graph_w, graph_h = 360, 480
            
            g_surf = pygame.Surface((graph_w, graph_h), pygame.SRCALPHA)
            pygame.draw.rect(g_surf, (15, 18, 30, 200), g_surf.get_rect())
            pygame.draw.rect(g_surf, CYAN_400, g_surf.get_rect(), 2)
            surface.blit(g_surf, (graph_x, graph_y))
            
            surface.blit(self.small_font.render("GAMEPLAY STATISTICS", True, CYAN_400), (graph_x + 20, graph_y + 15))
            
            gx = graph_x + 20
            gw = graph_w - 40
            gh = 90
            
            self.draw_line_chart(surface, gx, graph_y + 45, gw, gh, self.stats_data['damage'], ACCENT_RED_GLOW, "DAMAGE PER TURN (TREND)", mx, my)
            self.draw_bar_chart(surface, gx, graph_y + 145, gw, gh, self.stats_data['time'], GOLD, "TIME TAKEN PER WORD (SEC)", mx, my)
            self.draw_line_chart(surface, gx, graph_y + 245, gw, gh, self.stats_data['keys'], EMERALD_500, "KEYSTROKES PER WORD", mx, my)
            self.draw_bar_chart(surface, gx, graph_y + 345, gw, gh, self.stats_data['combo'], CYAN_400, "COMBO ACHIEVED", mx, my)
            
        start_x_hb = (800 - (5 * slot_size + 4 * padding)) // 2
        for i in range(5):
            rect = pygame.Rect(start_x_hb + i * (slot_size + padding), hotbar_start_y, slot_size, slot_size)
            s = pygame.Surface((slot_size, slot_size), pygame.SRCALPHA)
            pygame.draw.rect(s, slot_bg, s.get_rect()) 
            pygame.draw.rect(s, border_color, s.get_rect(), 1) 
            surface.blit(s, (rect.x, rect.y))
            surface.blit(self.tiny_font.render(str(i+1), True, TEXT_DIM), (rect.x+4, rect.y+2))
            
            item = self.inventory[i]
            if item:
                surface.blit(self.item_icons[item['id']], (rect.x+4, rect.y+4))
                if item.get('qty', 1) > 1:
                    surface.blit(self.tiny_font.render(str(item['qty']), True, WHITE), (rect.right-10, rect.bottom-12))

        if self.dragged_item:
            surface.blit(self.item_icons[self.dragged_item['id']], (mx - 16, my - 16))

    def draw_settings(self):
        if self.state == STATE_PAUSE:
            self.draw_overworld()
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill(BG_DEEP)
            self.draw_particles()
            
        box_w, box_h = 460, 420
        bx = 400 - box_w//2
        by = 100
        
        s = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(s, (15, 18, 30, 190), s.get_rect())
        pygame.draw.rect(s, BORDER_SUBTLE, s.get_rect(), 1)
        self.screen.blit(s, (bx, by))
        
        title_surf = self.name_font.render("SETTINGS", True, GOLD)
        self.screen.blit(title_surf, (400 - title_surf.get_width()//2, by + 30))
        
        mx, my = pygame.mouse.get_pos()
        
        self.screen.blit(self.btn_font.render("MUSIC VOLUME", True, TEXT_SECONDARY), (210, 208))
        
        b1 = pygame.Rect(370, 200, 35, 35)
        pygame.draw.rect(self.screen, (51, 65, 85) if b1.collidepoint(mx, my) else (30, 41, 59), b1)
        self.screen.blit(self.font.render("-", True, WHITE), (382, 204))
        
        pygame.draw.rect(self.screen, (30, 30, 40), (415, 212, 100, 10))
        pygame.draw.rect(self.screen, GOLD, (415, 212, int(100 * self.bgm_volume), 10))
        
        b2 = pygame.Rect(525, 200, 35, 35)
        pygame.draw.rect(self.screen, (51, 65, 85) if b2.collidepoint(mx, my) else (30, 41, 59), b2)
        self.screen.blit(self.font.render("+", True, WHITE), (535, 204))
        self.screen.blit(self.small_font.render(f"{int(self.bgm_volume*100)}%", True, GOLD_LIGHT), (575, 208))
        
        self.screen.blit(self.btn_font.render("SCREEN SHAKE", True, TEXT_SECONDARY), (210, 288))
        
        sb = pygame.Rect(410, 280, 190, 35)
        shover = sb.collidepoint(mx, my)
        pygame.draw.rect(self.screen, BG_DARK if not shover else (30, 41, 59), sb)
        pygame.draw.rect(self.screen, GOLD if self.shake_enabled else TEXT_DIM, sb, 1)
        s_txt = "ON" if self.shake_enabled else "OFF"
        t_col = GOLD_LIGHT if self.shake_enabled else TEXT_DIM
        self.screen.blit(self.small_font.render(s_txt, True, t_col), (505 - self.small_font.size(s_txt)[0]//2, 288))
        
        if self.state == STATE_PAUSE:
            self.draw_styled_btn("RESUME", 250, 370, 300, 45, pygame.Rect(250, 370, 300, 45).collidepoint(mx, my))
            self.draw_styled_btn("SAVE & QUIT", 250, 430, 300, 45, pygame.Rect(250, 430, 300, 45).collidepoint(mx, my), True)
        else:
            self.draw_styled_btn("BACK", 250, 430, 300, 45, pygame.Rect(250, 430, 300, 45).collidepoint(mx, my))

    def draw_category_ui(self, cat, start_x, start_y):
        opts = self.options[cat]
        total_pages = max(1, math.ceil(len(opts) / self.items_per_page))
        cur_page = self.pages[cat]
        
        self.screen.blit(self.name_font.render(f"SELECT {self.tab_names[self.tabs.index(cat)]}", True, WHITE), (start_x, start_y))
        box, margin, cols = 44, 10, 5
        grid_y = start_y + 45
        start_idx = cur_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(opts))
        
        for i in range(start_idx, end_idx):
            r, c = (i - start_idx) // cols, (i - start_idx) % cols
            rect = pygame.Rect(start_x + c*(box+margin), grid_y + r*(box+margin), box, box)
            is_sel = (i == self.selections[cat])
            pygame.draw.rect(self.screen, SLATE_800 if is_sel else (20, 30, 50), rect) 
            pygame.draw.rect(self.screen, CYAN_400 if is_sel else SLATE_700, rect, 2 if is_sel else 1) 
            if opts[i]:
                img = self.sprite_sheet.get_image_by_grid(opts[i][0], opts[i][1], 2)
                self.screen.blit(img, (rect.x + (box - img.get_width())//2, rect.y + (box - img.get_height())//2))
            else:
                txt = self.small_font.render("X", True, RED_500)
                self.screen.blit(txt, (rect.x + (box - txt.get_width())//2, rect.y + (box - txt.get_height())//2))
            self.active_buttons.append({'rect': rect, 'type': 'item', 'cat': cat, 'idx': i})

        page_y = 455
        center_x = 625 
        page_txt = self.small_font.render(f"PAGE {cur_page+1}/{total_pages}", True, SLATE_400)
        txt_w = page_txt.get_width()
        self.screen.blit(page_txt, (center_x - txt_w//2, page_y + 5))
        
        btn_prev = pygame.Rect(center_x - txt_w//2 - 35, page_y, 25, 25)
        btn_next = pygame.Rect(center_x + txt_w//2 + 10, page_y, 25, 25)
        
        if cur_page > 0:
            pygame.draw.rect(self.screen, SLATE_700, btn_prev) 
            self.screen.blit(self.small_font.render("<", True, WHITE), (btn_prev.x+7, btn_prev.y+3))
            self.active_buttons.append({'rect': btn_prev, 'type': 'prev', 'cat': cat})
        if cur_page < total_pages - 1:
            pygame.draw.rect(self.screen, SLATE_700, btn_next) 
            self.screen.blit(self.small_font.render(">", True, WHITE), (btn_next.x+7, btn_next.y+3))
            self.active_buttons.append({'rect': btn_next, 'type': 'next', 'cat': cat})

    def draw_selection(self):
        self.screen.blit(self.battle_bg, (0, 0))
        ov = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        ov.fill((15, 23, 42, 220))
        self.screen.blit(ov, (0, 0))
        self.active_buttons = []
        
        self.screen.blit(self.large_font.render("ARMORY", True, GOLD), (50, 40))
        self.screen.blit(self.small_font.render("CHOOSE YOUR LOOK", True, TEXT_SECONDARY), (55, 90))
        
        px, py = 175, 400
        pygame.draw.ellipse(self.screen, BG_DARK, (px - 80, py, 160, 30))
        pygame.draw.ellipse(self.screen, GOLD, (px - 70, py + 5, 140, 20), 2)
        self.screen.blit(self.player_preview_img, (px - self.player_preview_img.get_width()//2, py - self.player_preview_img.get_height() + 20))
        
        panel = pygame.Rect(330, 40, 440, 530)
        s = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (15, 18, 30, 190), s.get_rect()) 
        pygame.draw.rect(s, BORDER_SUBTLE, s.get_rect(), 2) 
        self.screen.blit(s, panel.topleft)
        
        ty = 65
        for i, tab in enumerate(self.tabs):
            is_act = (self.current_tab == tab)
            rect = pygame.Rect(345, ty, 120, 48)
            if is_act:
                pygame.draw.rect(self.screen, BG_DARK, rect) 
                pygame.draw.rect(self.screen, GOLD, (rect.x, rect.y, 4, rect.height)) 
            self.screen.blit(self.small_font.render(self.tab_names[i], True, GOLD if is_act else TEXT_SECONDARY), (rect.x + 15, rect.y + 16))
            self.active_buttons.append({'rect': rect, 'type': 'tab', 'tab': tab})
            ty += 62
            
        pygame.draw.line(self.screen, BORDER_SUBTLE, (475, 60), (475, 540), 2)
        self.draw_category_ui(self.current_tab, 495, 60)
        
        mx, my = pygame.mouse.get_pos()
        self.draw_styled_btn("START JOURNEY >", 495, 495, 260, 50, self.start_btn_rect.collidepoint(mx, my))

    def update_overworld(self):
        keys = pygame.key.get_pressed()
        self.is_moving = False
        
        old_x, old_y = self.map_player_pos[0], self.map_player_pos[1]
        menu_active = hasattr(self, 'nearby_interactables') and len(self.nearby_interactables) > 1 and not self.showing_dialogue
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: 
            if keys[pygame.K_a] or not menu_active:
                self.map_player_pos[0] -= self.map_player_speed
                self.facing_left_overworld, self.is_moving = True, True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: 
            if keys[pygame.K_d] or not menu_active:
                self.map_player_pos[0] += self.map_player_speed
                self.facing_left_overworld, self.is_moving = False, True
        if keys[pygame.K_UP] or keys[pygame.K_w]: 
            if keys[pygame.K_w] or not menu_active:
                self.map_player_pos[1] -= self.map_player_speed
                self.is_moving = True
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: 
            if keys[pygame.K_s] or not menu_active:
                self.map_player_pos[1] += self.map_player_speed
                self.is_moving = True
        
        if self.game_map.is_boss_realm:
            self.map_player_pos[0] = max(20, min(self.screen_width - 80, self.map_player_pos[0]))
            self.map_player_pos[1] = max(20, min(self.screen_height - 80, self.map_player_pos[1]))
            will_change = False
        else:
            if self.game_map.check_collision_at(self.map_player_pos[0], self.map_player_pos[1], 64, 64):
                self.map_player_pos[0] = old_x
                self.map_player_pos[1] = old_y
                
            map_pixel_width = self.game_map.width * 64
            map_pixel_height = self.game_map.height * 64
            
            edge_threshold = 10
            target_rx, target_ry = self.realm_x, self.realm_y
            will_change = False
            exit_side = ''

            if self.map_player_pos[0] > map_pixel_width - 64 - edge_threshold:
                target_rx += 1; will_change = True; exit_side = 'right'
            elif self.map_player_pos[0] < edge_threshold:
                target_rx -= 1; will_change = True; exit_side = 'left'
            elif self.map_player_pos[1] > map_pixel_height - 64 - edge_threshold:
                target_ry += 1; will_change = True; exit_side = 'bottom'
            elif self.map_player_pos[1] < edge_threshold:
                target_ry -= 1; will_change = True; exit_side = 'top'

        if will_change:
            target_key = f"{target_rx}_{target_ry}"
            if target_key in self.defeated_bosses:
                self.map_player_pos[0] = old_x
                self.map_player_pos[1] = old_y
                px = self.map_player_pos[0] + self.game_map.camera_offset[0] + 32
                py = self.map_player_pos[1] + self.game_map.camera_offset[1] - 20
                if random.random() < 0.1:
                    self.spawn_floating_text("PATH SEALED BY DIVINE AURA", px, py, ACCENT_RED_GLOW, 'small')
                return
                
            self.change_realm(target_rx, target_ry, exit_side)
            return
        
        self.game_map.update_camera(self.map_player_pos[0] + 32, self.map_player_pos[1] + 32, 
                                    self.screen_width, self.screen_height)
        
        self.move_timer_overworld = self.move_timer_overworld + 0.2 if self.is_moving else 0
        
        player_rect = pygame.Rect(self.map_player_pos[0], self.map_player_pos[1], 64, 64)
        current_in_range = self.get_nearby_interactables(player_rect)
        if not hasattr(self, 'nearby_interactables') or set(current_in_range) != set(self.nearby_interactables):
            self.nearby_interactables = current_in_range
            self.interact_index = 0

    def draw_sealed_auras(self):
        aura_colors = {
            "Zeus": (201, 162, 39, 100),
            "Poseidon": (50, 100, 255, 100),
            "Hades": (180, 50, 255, 100),
            "Athena": (200, 200, 200, 100),
            "Ares": (196, 60, 60, 100),
            "Apollo": (232, 200, 74, 100),
            "Hermes": (50, 255, 100, 100)
        }
        
        if f"{self.realm_x}_{self.realm_y - 1}" in self.defeated_bosses:
            god = self.defeated_bosses[f"{self.realm_x}_{self.realm_y - 1}"]
            color = aura_colors.get(god, (255, 255, 255, 100))
            s = pygame.Surface((self.screen_width, 60), pygame.SRCALPHA)
            for i in range(60):
                alpha = int(color[3] * (1 - i/60))
                pygame.draw.line(s, (*color[:3], alpha), (0, i), (self.screen_width, i))
            self.screen.blit(s, (0, 0))
            
        if f"{self.realm_x}_{self.realm_y + 1}" in self.defeated_bosses:
            god = self.defeated_bosses[f"{self.realm_x}_{self.realm_y + 1}"]
            color = aura_colors.get(god, (255, 255, 255, 100))
            s = pygame.Surface((self.screen_width, 60), pygame.SRCALPHA)
            for i in range(60):
                alpha = int(color[3] * (i/60))
                pygame.draw.line(s, (*color[:3], alpha), (0, i), (self.screen_width, i))
            self.screen.blit(s, (0, self.screen_height - 60))
            
        if f"{self.realm_x - 1}_{self.realm_y}" in self.defeated_bosses:
            god = self.defeated_bosses[f"{self.realm_x - 1}_{self.realm_y}"]
            color = aura_colors.get(god, (255, 255, 255, 100))
            s = pygame.Surface((60, self.screen_height), pygame.SRCALPHA)
            for i in range(60):
                alpha = int(color[3] * (1 - i/60))
                pygame.draw.line(s, (*color[:3], alpha), (i, 0), (i, self.screen_height))
            self.screen.blit(s, (0, 0))
            
        if f"{self.realm_x + 1}_{self.realm_y}" in self.defeated_bosses:
            god = self.defeated_bosses[f"{self.realm_x + 1}_{self.realm_y}"]
            color = aura_colors.get(god, (255, 255, 255, 100))
            s = pygame.Surface((60, self.screen_height), pygame.SRCALPHA)
            for i in range(60):
                alpha = int(color[3] * (i/60))
                pygame.draw.line(s, (*color[:3], alpha), (i, 0), (i, self.screen_height))
            self.screen.blit(s, (self.screen_width - 60, 0))

    def draw_overworld(self):
        self.screen.fill(BLACK)
        
        if self.game_map.is_boss_realm and self.game_map.full_bg_image:
            self.screen.blit(self.game_map.full_bg_image, (0, 0))
            
        self.game_map.draw(self.screen)
        
        img = self.player_overworld_equipped_img
        if self.facing_left_overworld: 
            img = pygame.transform.flip(img, True, False)
        by = abs(math.sin(self.move_timer_overworld)) * 10 if self.is_moving else 0
        
        player_screen_x = self.map_player_pos[0] + self.game_map.camera_offset[0]
        player_screen_y = self.map_player_pos[1] + self.game_map.camera_offset[1]
        self.screen.blit(img, (player_screen_x, player_screen_y - by))
        
        gear_rect = pygame.Rect(740, 20, 40, 40)
        pygame.draw.rect(self.screen, BG_CARD, gear_rect)
        pygame.draw.rect(self.screen, GOLD_DIM, gear_rect, 1)
        self.screen.blit(self.name_font.render("||", True, GOLD), (752, 28))
        
        self.draw_sealed_auras()
        
        if hasattr(self, 'nearby_interactables') and self.nearby_interactables and not self.showing_dialogue:
            if self.interact_index >= len(self.nearby_interactables):
                self.interact_index = 0
                
            box_w = 260
            box_h = 20 + (30 * len(self.nearby_interactables))
            prompt_box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            pygame.draw.rect(prompt_box, (15, 18, 30, 215), prompt_box.get_rect()) 
            pygame.draw.rect(prompt_box, GOLD_DIM, prompt_box.get_rect(), 1) 
            
            px = player_screen_x - box_w//2 + 32
            py = player_screen_y - box_h - 10
            self.screen.blit(prompt_box, (px, py))
            
            for i, o in enumerate(self.nearby_interactables):
                is_sel = (i == self.interact_index)
                color = GOLD_LIGHT if is_sel else TEXT_SECONDARY
                
                if o.type == "statue":
                    text = f"> [SPACE] Battle: {o.data.get('god', 'Statue')}" if is_sel else f"  Battle: {o.data.get('god', 'Statue')}"
                elif self.opens_shop(o):
                    text = f"> [SPACE] Shop: {o.data.get('name', 'Merchant')}" if is_sel else f"  Shop: {o.data.get('name', 'Merchant')}"
                else:
                    text = f"> [SPACE] Talk: {o.data.get('name', 'NPC')}" if is_sel else f"  Talk: {o.data.get('name', 'NPC')}"
                    
                txt_surf = self.small_font.render(text, True, color)
                self.screen.blit(txt_surf, (px + 15, py + 10 + (i * 30)))
        
        if self.showing_dialogue and self.current_npc:
            dialogue_box = pygame.Rect(100, 400, 600, 120)
            
            s = pygame.Surface((dialogue_box.width, dialogue_box.height), pygame.SRCALPHA)
            pygame.draw.rect(s, (15, 18, 30, 215), s.get_rect()) 
            pygame.draw.rect(s, GOLD_DIM, s.get_rect(), 1) 
            self.screen.blit(s, dialogue_box.topleft)
            
            npc_name = self.current_npc.data.get('name', 'Stranger')
            npc_text = self.current_npc.data.get('dialogue', 'Hello there!')
            
            self.screen.blit(self.name_font.render(npc_name, True, GOLD), (dialogue_box.x + 20, dialogue_box.y + 15))
            self.screen.blit(self.small_font.render(npc_text, True, TEXT_PRIMARY), (dialogue_box.x + 20, dialogue_box.y + 50))
            
            if self.opens_shop(self.current_npc): action_txt = "[SPACE] to Shop   |   [ESC] Leave"
            else: action_txt = "[SPACE] to Continue   |   [ESC] Leave"
            
            action_surf = self.tiny_font.render(action_txt, True, TEXT_DIM)
            self.screen.blit(action_surf, (dialogue_box.right - action_surf.get_width() - 20, dialogue_box.bottom - 25))
        
        if self.total_statues > 0:
            statue_text = self.name_font.render(f"{self.statues_collected} / {self.total_statues}", True, TEXT_PRIMARY)
            box_width = statue_text.get_width() + 60
            box_height = 40
            box_x, box_y = 20, 20
            
            bg_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
            pygame.draw.rect(bg_surface, (15, 18, 30, 190), bg_surface.get_rect()) 
            self.screen.blit(bg_surface, (box_x, box_y))
            pygame.draw.rect(self.screen, GOLD_DIM, (box_x, box_y, box_width, box_height), 1) 
            pygame.draw.circle(self.screen, GOLD, (box_x + 20, box_y + box_height // 2), 6)
            self.screen.blit(statue_text, (box_x + 36, box_y + (box_height - statue_text.get_height()) // 2))
            
        gold_text = self.name_font.render(f"{self.gold} G", True, TEXT_PRIMARY)
        gold_width = gold_text.get_width() + 60
        gold_x = 20 if self.total_statues == 0 else 20 + box_width + 10
        gold_y = 20
        
        bg_surface_gold = pygame.Surface((gold_width, 40), pygame.SRCALPHA)
        pygame.draw.rect(bg_surface_gold, (15, 18, 30, 190), bg_surface_gold.get_rect()) 
        self.screen.blit(bg_surface_gold, (gold_x, gold_y))
        pygame.draw.rect(self.screen, GOLD_DIM, (gold_x, gold_y, gold_width, 40), 1) 
        pygame.draw.circle(self.screen, GOLD_LIGHT, (gold_x + 20, gold_y + 20), 6)
        self.screen.blit(gold_text, (gold_x + 36, gold_y + (40 - gold_text.get_height()) // 2))

        self.draw_inventory_ui(self.screen)
        
        for t in self.floating_texts[:]:
            f = self.tiny_font if t.get('font_type') == 'tiny' else (self.small_font if t.get('font_type') == 'small' else self.combo_font)
            txt_str = str(t['text'])
            txt_surf = f.render(txt_str, True, t['color'])
            shadow = f.render(txt_str, True, BLACK)
            
            draw_x = t['x'] - txt_surf.get_width() // 2
            self.screen.blit(shadow, (draw_x + 1, t['y'] + 1))
            self.screen.blit(shadow, (draw_x - 1, t['y'] - 1))
            self.screen.blit(txt_surf, (draw_x, t['y']))
            
            t['y'] -= 1.5 if t.get('font_type') in ['small', 'tiny'] else 2
            t['timer'] -= 1
            if t['timer'] <= 0: self.floating_texts.remove(t)

    def draw_warp_menu(self):
        self.draw_overworld()
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) 
        self.screen.blit(overlay, (0, 0))
        
        box = pygame.Rect(150, 150, 500, 260)
        s = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (15, 18, 30, 190), s.get_rect()) 
        pygame.draw.rect(s, GOLD_DIM, s.get_rect(), 1) 
        self.screen.blit(s, box.topleft)
        
        self.screen.blit(self.name_font.render("WARP SCROLL", True, GOLD), (180, 180))
        
        mx, my = pygame.mouse.get_pos()
        self.draw_styled_btn("[1] Sanctuary (Base)", 180, 230, 440, 45, pygame.Rect(180, 230, 440, 45).collidepoint(mx, my))
        self.draw_styled_btn(f"[2] Previous Area ({self.last_normal_realm[0]}, {self.last_normal_realm[1]})", 180, 290, 440, 45, pygame.Rect(180, 290, 440, 45).collidepoint(mx, my))
        
        self.screen.blit(self.tiny_font.render("[ESC] Cancel", True, TEXT_DIM), (180, 360))

    def draw_shop(self):
        self.draw_overworld()
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) 
        self.screen.blit(overlay, (0, 0))
        
        box = pygame.Rect(180, 80, 440, 300) 
        s = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (15, 18, 30, 190), s.get_rect()) 
        pygame.draw.rect(s, GOLD_DIM, s.get_rect(), 1) 
        self.screen.blit(s, box.topleft)
        
        self.screen.blit(self.name_font.render("MERCHANT'S SHOP", True, GOLD), (210, 100))
        self.screen.blit(self.small_font.render(f"Your Gold: {self.gold} G", True, TEXT_PRIMARY), (210, 140))
        
        potions_owned = sum([item['qty'] for item in self.inventory if item and item['id'] == 'potion'])
        scrolls_owned = sum([item['qty'] for item in self.inventory if item and item['id'] == 'scroll'])
        
        mx, my = pygame.mouse.get_pos()
        
        self.shop_potion_rect = pygame.Rect(200, 180, 280, 45)
        p_hover = self.shop_potion_rect.collidepoint(mx, my)
        self.draw_styled_btn("[1] Health Potion (50G)", 200, 180, 280, 45, p_hover)
        self.screen.blit(self.small_font.render(f"Owned: {potions_owned}", True, WHITE if p_hover else TEXT_DIM), (500, 192))
        
        self.shop_scroll_rect = pygame.Rect(200, 240, 280, 45)
        s_hover = self.shop_scroll_rect.collidepoint(mx, my)
        self.draw_styled_btn("[2] Hint Scroll (50G)", 200, 240, 280, 45, s_hover)
        self.screen.blit(self.small_font.render(f"Owned: {scrolls_owned}", True, WHITE if s_hover else TEXT_DIM), (500, 252))
        
        self.shop_exit_rect = pygame.Rect(200, 310, 400, 45)
        e_hover = self.shop_exit_rect.collidepoint(mx, my)
        self.draw_styled_btn("[ESC] Leave", 200, 310, 400, 45, e_hover, True)

    def draw_upgrade(self):
        self.draw_overworld()
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 90)) 
        self.screen.blit(overlay, (0, 0))

        title_shadow = self.name_font.render("STATUE DESTROYED!", True, BLACK)
        title_surf = self.name_font.render("STATUE DESTROYED!", True, GOLD)
        subtitle_surf = self.small_font.render("Blessing received! Choose an upgrade:", True, TEXT_PRIMARY)
        title_x = 400 - title_surf.get_width() // 2
        subtitle_x = 400 - subtitle_surf.get_width() // 2

        self.screen.blit(title_shadow, (title_x + 2, 72))
        self.screen.blit(title_surf, (title_x, 70))
        self.screen.blit(subtitle_surf, (subtitle_x, 112))

        mx, my = pygame.mouse.get_pos()

        card_w, card_h = 500, 72
        card_x = (self.screen_width - card_w) // 2
        self.upg_ares_rect = pygame.Rect(card_x, 150, card_w, card_h)
        a_hover = self.upg_ares_rect.collidepoint(mx, my)
        atk_card = pygame.Surface((self.upg_ares_rect.width, self.upg_ares_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(atk_card, (18, 22, 34, 110 if a_hover else 80), atk_card.get_rect(), border_radius=14)
        pygame.draw.rect(atk_card, GOLD if a_hover else GOLD_DIM, atk_card.get_rect(), 2, border_radius=14)
        if a_hover:
            pygame.draw.rect(atk_card, (232, 200, 74, 35), (0, 0, self.upg_ares_rect.width, 8), border_top_left_radius=14, border_top_right_radius=14)
        self.screen.blit(atk_card, self.upg_ares_rect.topleft)

        atk_title = self.btn_font.render(f"[1] Power", True, GOLD_LIGHT if a_hover else TEXT_PRIMARY)
        atk_desc = self.small_font.render(f"Attack +{self.current_reward_atk}", True, TEXT_PRIMARY)
        self.screen.blit(atk_title, (400 - atk_title.get_width() // 2, self.upg_ares_rect.y + 10))
        self.screen.blit(atk_desc, (400 - atk_desc.get_width() // 2, self.upg_ares_rect.y + 38))
        atk_color = TEXT_PRIMARY if a_hover else TEXT_DIM
        atk_surf = self.tiny_font.render(f"Current Base ATK: {self.player.base_attack}", True, atk_color)
        self.screen.blit(atk_surf, (400 - atk_surf.get_width() // 2, self.upg_ares_rect.bottom + 6))

        self.upg_demeter_rect = pygame.Rect(card_x, 248, card_w, card_h)
        d_hover = self.upg_demeter_rect.collidepoint(mx, my)
        hp_card = pygame.Surface((self.upg_demeter_rect.width, self.upg_demeter_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(hp_card, (18, 22, 34, 110 if d_hover else 80), hp_card.get_rect(), border_radius=14)
        pygame.draw.rect(hp_card, GOLD if d_hover else GOLD_DIM, hp_card.get_rect(), 2, border_radius=14)
        if d_hover:
            pygame.draw.rect(hp_card, (232, 200, 74, 35), (0, 0, self.upg_demeter_rect.width, 8), border_top_left_radius=14, border_top_right_radius=14)
        self.screen.blit(hp_card, self.upg_demeter_rect.topleft)

        hp_title = self.btn_font.render(f"[2] Vitality", True, GOLD_LIGHT if d_hover else TEXT_PRIMARY)
        hp_desc = self.small_font.render(f"Max HP +{self.current_reward_hp} and Full Heal", True, TEXT_PRIMARY)
        self.screen.blit(hp_title, (400 - hp_title.get_width() // 2, self.upg_demeter_rect.y + 10))
        self.screen.blit(hp_desc, (400 - hp_desc.get_width() // 2, self.upg_demeter_rect.y + 38))
        hp_color = TEXT_PRIMARY if d_hover else TEXT_DIM
        hp_surf = self.tiny_font.render(f"Current Max HP: {self.player_max_hp}", True, hp_color)
        self.screen.blit(hp_surf, (400 - hp_surf.get_width() // 2, self.upg_demeter_rect.bottom + 6))

    def draw_modern_hp_bar(self, surface, x, y, curr, max_hp, fill, name):
        panel_w = 300
        s = pygame.Surface((panel_w, 80), pygame.SRCALPHA)
        pygame.draw.rect(s, (15, 18, 30, 190), s.get_rect()) 
        pygame.draw.rect(s, BORDER_SUBTLE, s.get_rect(), 1)
        surface.blit(s, (x, y))
        
        name_surf = self.small_font.render(name, True, GOLD)
        surface.blit(name_surf, (x + 15, y + 15))
        
        ratio = max(0.0, min(1.0, curr / max_hp))
        txt = self.small_font.render(f"{curr}/{max_hp} HP", True, TEXT_PRIMARY)
        surface.blit(txt, (x + panel_w - 15 - txt.get_width(), y + 15))
        
        bx, by, bw, bh = x + 15, y + 45, panel_w - 30, 20
        pygame.draw.rect(surface, BG_DARK, (bx, by, bw, bh)) 
        if ratio > 0: pygame.draw.rect(surface, fill, (bx, by, int(bw * ratio), bh)) 

    def draw_battle(self):
        shake_x = random.randint(-self.shake_amount, self.shake_amount) if self.shake_timer > 0 else 0
        shake_y = random.randint(-self.shake_amount, self.shake_amount) if self.shake_timer > 0 else 0
        if self.shake_timer > 0: self.shake_timer -= 1
        
        battle_surf = pygame.Surface((self.screen_width, self.screen_height))
        
        if self.current_battle_bg:
            battle_surf.blit(self.current_battle_bg, (0, 0))
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill((10, 10, 15, 80)) 
            battle_surf.blit(overlay, (0, 0))
        else:
            battle_surf.blit(self.battle_bg, (0, 0))
        
        if self.p_anim_timer > 0:
            self.p_anim_x += 15 if self.p_anim_timer > 10 else -15
            self.p_anim_timer -= 1
        else: self.p_anim_x = 0
            
        if self.e_anim_timer > 0:
            self.e_anim_x -= 15 if self.e_anim_timer > 10 else +15
            self.e_anim_timer -= 1
        else: self.e_anim_x = 0
            
        self.battle_float_timer += 0.05
        fo = math.sin(self.battle_float_timer) * 8
        battle_surf.blit(self.enemy_battle_img, (self.enemy_battle_pos[0] + self.e_anim_x, self.enemy_battle_pos[1] + fo))
        battle_surf.blit(self.player_battle_img, (self.player_battle_pos[0] + self.p_anim_x, self.player_battle_pos[1] - fo))
        
        self.draw_modern_hp_bar(battle_surf, 40, 30, self.enemy.current_hp, self.enemy.max_hp, ACCENT_RED_GLOW, self.enemy.name.upper())
        self.draw_modern_hp_bar(battle_surf, 460, 320, self.player.hp, self.player_max_hp, GOLD_LIGHT, "PLAYER")
        
        if self.player.combo_count > 0:
            bonus_dmg = int(self.player.combo_count * 20)
            combo_txt = self.btn_font.render(f"COMBO x{self.player.combo_count} (ATK +{bonus_dmg}%)", True, GOLD)
            battle_surf.blit(combo_txt, (460, 295))
        
        for t in self.floating_texts[:]:
            f = self.tiny_font if t.get('font_type') == 'tiny' else (self.small_font if t.get('font_type') == 'small' else self.combo_font)
            txt_str = str(t['text'])
            txt_surf = f.render(txt_str, True, t['color'])
            shadow = f.render(txt_str, True, BLACK)
            
            draw_x = t['x'] - txt_surf.get_width() // 2
            
            battle_surf.blit(shadow, (draw_x + 1, t['y'] + 1))
            battle_surf.blit(shadow, (draw_x - 1, t['y'] - 1))
            battle_surf.blit(txt_surf, (draw_x, t['y']))
            
            t['y'] -= 1.5 if t.get('font_type') in ['small', 'tiny'] else 2
            t['timer'] -= 1
            if t['timer'] <= 0: self.floating_texts.remove(t)
            
        if self.crit_timer > 0:
            crit_txt = self.combo_font.render("CRITICAL!", True, ACCENT_RED_GLOW)
            c_x_crit = self.enemy_battle_pos[0] + 80 - crit_txt.get_width() // 2
            c_y_crit = self.enemy_battle_pos[1] - 40 - ((60 - self.crit_timer) * 0.5)
            battle_surf.blit(self.combo_font.render("CRITICAL!", True, BLACK), (c_x_crit + 2, c_y_crit + 2))
            battle_surf.blit(crit_txt, (c_x_crit, c_y_crit))
            self.crit_timer -= 1 

        board_start_y = 440
        s_board = pygame.Surface((800, 160), pygame.SRCALPHA)
        pygame.draw.rect(s_board, (15, 18, 30, 240), s_board.get_rect())
        battle_surf.blit(s_board, (0, board_start_y))
        pygame.draw.line(battle_surf, GOLD_DIM, (0, board_start_y), (800, board_start_y), 2)

        total_potions = sum([item['qty'] for item in self.inventory if item and item['id'] == 'potion'])
        total_scrolls = sum([item['qty'] for item in self.inventory if item and item['id'] == 'scroll'])
        
        if not self.gm.game_over:
            flee_surf = self.tiny_font.render(f"PRESS [ESC] TO FLEE (LOST COMBO) | [1] POTION ({total_potions}) | [2] HINT SCROLL ({total_scrolls})", True, TEXT_DIM)
            battle_surf.blit(flee_surf, (20, board_start_y - 25))

        box, m = 50, 10
        cx = (800 - (box*5 + m*4)) // 2
        cy = board_start_y + 45
        
        if self.board.current_attempt >= 4 and not self.gm.game_over:
            hint = f"Ehm.. maybe it's: '{self.dictionary.get_current_hint()}'"
            if len(hint) > 75: hint = hint[:72] + "..."
            hs = self.small_font.render(hint, True, BLACK)
            br = hs.get_rect(midbottom=(self.player_battle_pos[0] + 120, self.player_battle_pos[1] - 20))
            pygame.draw.rect(battle_surf, WHITE, br.inflate(20, 15)) 
            pygame.draw.rect(battle_surf, GOLD, br.inflate(20, 15), 2) 
            battle_surf.blit(hs, br)

        battle_surf.blit(self.small_font.render("ABSENT", True, TEXT_SECONDARY), (40, board_start_y + 15))
        absent_x, absent_y = 40, board_start_y + 40
        for i, char in enumerate(sorted(list(self.absent_letters))):
            r, c = i // 6, i % 6
            pygame.draw.rect(battle_surf, BG_DARK, (absent_x + c*25, absent_y + r*25, 20, 20)) 
            battle_surf.blit(self.small_font.render(char, True, TEXT_DIM), (absent_x + c*25 + 6, absent_y + r*25 + 3))

        for col in range(5):
            x = cx + col * (box + m)
            char = self.current_guess[col] if col < len(self.current_guess) else ""
            is_active = (col == len(self.current_guess) and not self.gm.game_over)
            
            pygame.draw.rect(battle_surf, (30, 35, 50) if char else BG_DARK, (x, cy, box, box)) 
            
            if char:
                t = self.font.render(char, True, WHITE)
                t_rect = t.get_rect(center=(x + box // 2, cy + box // 2))
                battle_surf.blit(t, t_rect)
            
            pygame.draw.rect(battle_surf, GOLD if is_active else BORDER_SUBTLE, (x, cy, box, box), 2 if not is_active else 3) 

        battle_surf.blit(self.small_font.render("BEST KNOWN", True, GOLD_LIGHT), (580, board_start_y + 15))
        right_x, right_y = 580, board_start_y + 40
        for i in range(5):
            rx = right_x + i*30
            c_char = self.green_letters[i]
            pygame.draw.rect(battle_surf, GOLD if c_char else BG_DARK, (rx, right_y, 25, 25)) 
            if c_char: battle_surf.blit(self.small_font.render(c_char, True, BLACK), (rx + 7, right_y + 5))
        
        if self.yellow_letters:
            label_surf = self.small_font.render("PRESENT:", True, TEXT_PRIMARY)
            label_y = right_y + 40
            battle_surf.blit(label_surf, (right_x, label_y))

            present_start_x = right_x + label_surf.get_width() + 10
            present_box = 20
            present_gap = 5
            present_right_limit = 780
            boxes_per_row = max(1, (present_right_limit - present_start_x + present_gap) // (present_box + present_gap))

            for i, char in enumerate(sorted(list(self.yellow_letters))):
                row = i // boxes_per_row
                col = i % boxes_per_row
                box_x = present_start_x + col * (present_box + present_gap)
                box_y = label_y - 5 + row * (present_box + present_gap)
                pygame.draw.rect(battle_surf, TEXT_PRIMARY, (box_x, box_y, present_box, present_box))
                battle_surf.blit(self.small_font.render(char, True, BLACK), (box_x + 5, box_y + 3))

        if self.gm.game_over:
            msg = "VICTORY!" if self.enemy.current_hp <= 0 else "DEFEATED!"
            msg_color = GOLD_LIGHT if self.enemy.current_hp <= 0 else ACCENT_RED_GLOW
            
            txt_surface = self.large_font.render(msg, True, msg_color)
            txt_rect = txt_surface.get_rect(center=(self.screen_width // 2, 280))
            
            txt_shadow = self.large_font.render(msg, True, BLACK)
            battle_surf.blit(txt_shadow, (txt_rect.x + 3, txt_rect.y + 3))
            battle_surf.blit(txt_surface, txt_rect)
            
            sub_txt = self.small_font.render("Press SPACE to continue", True, WHITE)
            sub_rect = sub_txt.get_rect(center=(self.screen_width // 2, 330))
            sub_shadow = self.small_font.render("Press SPACE to continue", True, BLACK)
            battle_surf.blit(sub_shadow, (sub_rect.x + 2, sub_rect.y + 2))
            battle_surf.blit(sub_txt, sub_rect)

        self.screen.blit(battle_surf, (shake_x, shake_y))

    def run(self):
        clock = pygame.time.Clock()
        while True:
            self.handle_events()
            self.sync_music()
            if self.state == STATE_MAIN_MENU: self.draw_main_menu()
            elif self.state == STATE_SAVE_SLOTS: self.draw_save_slots()
            elif self.state == STATE_SELECTION: self.draw_selection()
            elif self.state == STATE_OVERWORLD: self.update_overworld(); self.draw_overworld()
            elif self.state == STATE_BATTLE: self.draw_battle()
            elif self.state == STATE_SHOP: self.draw_shop()
            elif self.state == STATE_UPGRADE: self.draw_upgrade()
            elif self.state == STATE_WARP: self.draw_warp_menu() 
            elif self.state in [STATE_PAUSE, STATE_SETTINGS]: self.draw_settings()
            pygame.display.flip(); clock.tick(60)

if __name__ == "__main__":
    app = PygameApp(); app.run()
