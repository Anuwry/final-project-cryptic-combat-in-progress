import pygame
import sys
import os
import math
import random
from src.config import DATA_DIR, RAW_DATA_DIR, WORDS_DATA_DIR, BASE_DIR
from src.game_manager import GameManager
from src.entities import Player, Enemy
from src.mechanics import WordDictionary, TileBoard
from src.map_loader import GameMap

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

STATE_SELECTION = 0
STATE_OVERWORLD = 1
STATE_BATTLE = 2
STATE_SHOP = 3
STATE_UPGRADE = 4

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
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Cryptic Combat")
        
        self.large_font = pygame.font.Font(None, 64)
        self.combo_font = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 40)
        self.name_font = pygame.font.Font(None, 32)
        self.btn_font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)
        
        self.state = STATE_SELECTION
        self.gm = GameManager()
        self.dictionary = WordDictionary("normal")
        self.board = TileBoard()
        
        self.gold = 0
        self.potions = 1
        self.scrolls = 1
        self.base_atk = 15
        self.player_max_hp = 100
        self.player = Player(hp=self.player_max_hp, base_attack=self.base_atk)
        
        self.realm_x = 0
        self.realm_y = 0
        self.current_level = 1
        
        self.game_map = GameMap(self.realm_x, self.realm_y)
        self.statues_collected = len([s for s in self.game_map.get_statues() if s.collected])
        self.total_statues = len(self.game_map.get_statues())
        
        self.floating_texts = []
        self.p_anim_timer = 0
        self.p_anim_x = 0
        self.e_anim_timer = 0
        self.e_anim_x = 0
        self.battle_float_timer = 0
        self.crit_timer = 0
        
        self.shake_timer = 0
        self.shake_amount = 0
        
        self.target_word = self.dictionary.generate_random_word()
        self.current_guess = ""
        self.guess_history = []
        self.absent_letters = set()
        self.yellow_letters = set()
        self.green_letters = [None] * 5
        
        self.showing_dialogue = False
        self.current_npc = None
        self.dialogue_timer = 0
        self.current_statue = None
        
        self.setup_assets()
        self.setup_selection()
        self.setup_overworld()

    def load_image_safely(self, path, size, fallback_color):
        if os.path.exists(path): return pygame.transform.scale(pygame.image.load(path).convert_alpha(), size)
        surf = pygame.Surface(size); surf.fill(fallback_color); return surf

    def setup_assets(self):
        map_bg_path = os.path.join(BASE_DIR, "assets", "images", "map_bg.png")
        battle_bg_path = os.path.join(BASE_DIR, "assets", "images", "bg.png")
        sprite_path = os.path.join(BASE_DIR, "assets", "images", "roguelikeChar_transparent.png")
        self.overworld_bg = pygame.transform.scale(self.load_image_safely(map_bg_path, (800, 600), (30, 80, 40)), (800, 600))
        self.battle_bg = pygame.transform.scale(self.load_image_safely(battle_bg_path, (800, 600), (80, 120, 200)), (800, 600))
        self.sprite_sheet = SpriteSheet(sprite_path)

    def generate_box(self, c1, r1, c2, r2): return [(c, r) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]

    def filter_empty(self, coords_list):
        valid = []
        for c, r in coords_list:
            img = self.sprite_sheet.get_image_by_grid(c, r, 1)
            if img.get_bounding_rect().width > 0: valid.append((c, r))
        return valid

    def setup_selection(self):
        npc_bases = self.generate_box(0, 0, 1, 11)
        player_bases = [(1, 0), (1, 1), (1, 2)]
        self.enemy_bases = [b for b in npc_bases if b not in player_bases]
        
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
        self.map_player_pos = list(self.game_map.spawn_point)
        self.map_player_speed = 5
        self.facing_left_overworld = False
        self.is_moving = False
        self.move_timer_overworld = 0
        self.enemy_battle_pos = (550, 100)
        self.player_battle_pos = (80, 230)

    def trigger_shake(self, intensity, duration):
        self.shake_amount = intensity
        self.shake_timer = duration

    def change_realm(self, target_x, target_y, exit_side):
        self.game_map.save_map()
        self.realm_x = target_x
        self.realm_y = target_y
        self.current_level = abs(self.realm_x) + abs(self.realm_y) + 1
        
        self.game_map = GameMap(self.realm_x, self.realm_y)
        self.total_statues = len(self.game_map.get_statues())
        self.statues_collected = len([s for s in self.game_map.get_statues() if s.collected])
        
        map_pixel_width = self.game_map.width * 64
        map_pixel_height = self.game_map.height * 64
        
        clamped_x = max(64, min(self.map_player_pos[0], map_pixel_width - 128))
        clamped_y = max(64, min(self.map_player_pos[1], map_pixel_height - 128))
        
        if exit_side == 'right': self.map_player_pos = [64, clamped_y]
        elif exit_side == 'left': self.map_player_pos = [map_pixel_width - 128, clamped_y]
        elif exit_side == 'bottom': self.map_player_pos = [clamped_x, 64]
        elif exit_side == 'top': self.map_player_pos = [clamped_x, map_pixel_height - 128]
            
        self.game_map.ensure_safe_spawn(self.map_player_pos[0], self.map_player_pos[1])
        self.facing_left_overworld = False
        self.game_map.camera_offset = [0, 0]
        self.game_map.target_camera_offset = [0, 0]

    def spawn_floating_text(self, text, x, y, color):
        self.floating_texts.append({'text': text, 'x': x, 'y': y, 'timer': 45, 'color': color})

    def randomize_enemy(self):
        god = self.current_statue.data.get('god', 'Unknown')
        tier = self.current_statue.data.get('tier', 'Follower')
        
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
        
        enemy_layers = [random.choice(self.enemy_bases), random.choice(self.options['pants']), random.choice(self.options['armor'][1:]),
                        random.choice(self.options['hair']), random.choice(self.options['hat']), random.choice(self.options['shield']),
                        random.choice(self.options['weapon'][1:])]
        self.enemy_battle_img = self.sprite_sheet.get_equipped_image_by_grid(enemy_layers, 10)
        self.target_word = self.dictionary.generate_random_word()
        self.battle_float_timer, self.crit_timer, self.floating_texts = 0, 0, []
        self.board.current_attempt, self.guess_history, self.current_guess = 1, [], ""
        self.absent_letters, self.yellow_letters = set(), set()
        self.green_letters = [None] * 5

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                if hasattr(self, 'game_map'): self.game_map.save_map()
                self.gm.export_data_to_csv(); pygame.quit(); sys.exit()
            
            if self.state == STATE_SELECTION:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.start_btn_rect.collidepoint(event.pos): self.state = STATE_OVERWORLD; return
                    for btn in self.active_buttons:
                        if btn['rect'].collidepoint(event.pos):
                            if btn['type'] == 'tab': self.current_tab = btn['tab']
                            elif btn['type'] == 'item': self.selections[self.current_tab] = btn['idx']; self.update_player_visuals()
                            elif btn['type'] == 'prev': self.pages[self.current_tab] = max(0, self.pages[self.current_tab] - 1)
                            elif btn['type'] == 'next': 
                                max_p = math.ceil(len(self.options[self.current_tab]) / self.items_per_page) - 1
                                self.pages[self.current_tab] = min(max_p, self.pages[self.current_tab] + 1)
                            break 
                            
            elif self.state == STATE_OVERWORLD:
                if event.type == pygame.KEYDOWN:
                    if self.showing_dialogue and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self.showing_dialogue = False
                        if self.current_npc and self.current_npc.data.get('name') == 'Merchant':
                            self.state = STATE_SHOP
                        self.current_npc = None
                    elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        player_rect = pygame.Rect(self.map_player_pos[0], self.map_player_pos[1], 64, 64)
                        nearby_statue = self.game_map.get_nearby_statue(player_rect)
                        if nearby_statue:
                            self.current_statue = nearby_statue
                            self.state = STATE_BATTLE
                            self.randomize_enemy()
                            self.gm.start_word_timer()
                    elif event.key == pygame.K_e:
                        player_rect = pygame.Rect(self.map_player_pos[0], self.map_player_pos[1], 64, 64)
                        nearby_npc = self.game_map.get_nearby_npc(player_rect)
                        if nearby_npc:
                            self.showing_dialogue = True
                            self.current_npc = nearby_npc
                            self.dialogue_timer = 180  
                            
            elif self.state == STATE_SHOP:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_SPACE):
                        self.state = STATE_OVERWORLD
                    elif event.key == pygame.K_1:
                        if self.gold >= 50:
                            self.gold -= 50
                            self.potions += 1
                    elif event.key == pygame.K_2:
                        if self.gold >= 50:
                            self.gold -= 50
                            self.scrolls += 1
            
            elif self.state == STATE_UPGRADE:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.base_atk += 5
                        self.player.base_attack = self.base_atk
                        self.state = STATE_OVERWORLD
                    elif event.key == pygame.K_2:
                        self.player_max_hp += 20
                        self.player.hp = self.player_max_hp
                        self.state = STATE_OVERWORLD
                            
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
                                self.state = STATE_UPGRADE 
                            else:
                                self.player.hp = self.player_max_hp
                                self.state = STATE_OVERWORLD 
                    else:
                        if event.key == pygame.K_ESCAPE:
                            self.state = STATE_OVERWORLD
                        elif event.key == pygame.K_1 and self.potions > 0 and self.player.hp < self.player_max_hp:
                            self.potions -= 1
                            self.player.hp = min(self.player_max_hp, self.player.hp + 50)
                            self.spawn_floating_text("+50 HP", self.player_battle_pos[0] + 60, self.player_battle_pos[1] - 30, EMERALD_400)
                        elif event.key == pygame.K_2 and self.scrolls > 0:
                            self.scrolls -= 1
                            for idx, c in enumerate(self.target_word):
                                if self.green_letters[idx] is None:
                                    self.green_letters[idx] = c
                                    break
                        elif event.unicode.isascii() and event.unicode.isalpha() and len(self.current_guess) < 5:
                            self.current_guess += event.unicode.upper(); self.gm.keystroke_count += 1
                        elif event.key == pygame.K_BACKSPACE: self.current_guess = self.current_guess[:-1]; self.gm.keystroke_count += 1
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and len(self.current_guess) == 5:
                            self.gm.keystroke_count += 1; self.submit_guess()

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
            self.spawn_floating_text(f"-{damage}", self.enemy_battle_pos[0] + 60, self.enemy_battle_pos[1] + 30, RED_500)
            if self.player.combo_count > 1: self.crit_timer = 60
            
            if self.gm.check_win_condition(self.enemy): self.gm.game_over = True
            else: self.reset_for_next_word()
        else:
            if self.board.current_attempt > self.board.grid_size:
                self.player.combo_count = 0
                self.enemy.attack_player(self.player)
                self.e_anim_timer = 20
                self.trigger_shake(15, 20) 
                self.spawn_floating_text(f"-{self.enemy.attack_power}", self.player_battle_pos[0] + 60, self.player_battle_pos[1] + 30, RED_500)
                if self.player.hp <= 0: self.gm.game_over = True
                else: self.reset_for_next_word()

    def reset_for_next_word(self):
        self.target_word = self.dictionary.generate_random_word()
        self.board.current_attempt = 1
        self.guess_history = []
        self.absent_letters, self.yellow_letters = set(), set()
        self.gm.start_word_timer()

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
            pygame.draw.rect(self.screen, SLATE_800 if is_sel else (20, 30, 50), rect, border_radius=8)
            pygame.draw.rect(self.screen, CYAN_400 if is_sel else SLATE_700, rect, 2 if is_sel else 1, border_radius=8)
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
            pygame.draw.rect(self.screen, SLATE_700, btn_prev, border_radius=4)
            self.screen.blit(self.small_font.render("<", True, WHITE), (btn_prev.x+7, btn_prev.y+3))
            self.active_buttons.append({'rect': btn_prev, 'type': 'prev', 'cat': cat})
        if cur_page < total_pages - 1:
            pygame.draw.rect(self.screen, SLATE_700, btn_next, border_radius=4)
            self.screen.blit(self.small_font.render(">", True, WHITE), (btn_next.x+7, btn_next.y+3))
            self.active_buttons.append({'rect': btn_next, 'type': 'next', 'cat': cat})

    def draw_selection(self):
        self.screen.blit(self.battle_bg, (0, 0))
        ov = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        ov.fill((15, 23, 42, 220))
        self.screen.blit(ov, (0, 0))
        self.active_buttons = []
        
        self.screen.blit(self.large_font.render("ARMORY", True, CYAN_400), (50, 40))
        self.screen.blit(self.small_font.render("CHOOSE YOUR LOOK (CANNOT BE CHANGED)", True, SLATE_400), (55, 90))
        
        px, py = 175, 400
        pygame.draw.ellipse(self.screen, SLATE_800, (px - 80, py, 160, 30))
        pygame.draw.ellipse(self.screen, CYAN_500, (px - 70, py + 5, 140, 20), 2)
        self.screen.blit(self.player_preview_img, (px - self.player_preview_img.get_width()//2, py - self.player_preview_img.get_height() + 20))
        
        panel = pygame.Rect(330, 40, 440, 530)
        pygame.draw.rect(self.screen, (15, 23, 42, 180), panel, border_radius=16)
        pygame.draw.rect(self.screen, SLATE_700, panel, 2, border_radius=16)
        
        ty = 65
        for i, tab in enumerate(self.tabs):
            is_act = (self.current_tab == tab)
            rect = pygame.Rect(345, ty, 120, 48)
            if is_act:
                pygame.draw.rect(self.screen, SLATE_800, rect, border_radius=8)
                pygame.draw.rect(self.screen, CYAN_400, (rect.x, rect.y, 4, rect.height), border_top_left_radius=8, border_bottom_left_radius=8)
            self.screen.blit(self.small_font.render(self.tab_names[i], True, CYAN_400 if is_act else SLATE_400), (rect.x + 15, rect.y + 16))
            self.active_buttons.append({'rect': rect, 'type': 'tab', 'tab': tab})
            ty += 62
            
        pygame.draw.line(self.screen, SLATE_700, (475, 60), (475, 540), 2)
        self.draw_category_ui(self.current_tab, 495, 60)
        
        pygame.draw.rect(self.screen, CYAN_500, self.start_btn_rect, border_radius=12)
        btn_txt = self.btn_font.render("START JOURNEY >", True, BLACK)
        self.screen.blit(btn_txt, (self.start_btn_rect.centerx - btn_txt.get_width()//2, self.start_btn_rect.centery - btn_txt.get_height()//2))

    def update_overworld(self):
        keys = pygame.key.get_pressed()
        self.is_moving = False
        
        old_x, old_y = self.map_player_pos[0], self.map_player_pos[1]
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: 
            self.map_player_pos[0] -= self.map_player_speed
            self.facing_left_overworld, self.is_moving = True, True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: 
            self.map_player_pos[0] += self.map_player_speed
            self.facing_left_overworld, self.is_moving = False, True
        if keys[pygame.K_UP] or keys[pygame.K_w]: 
            self.map_player_pos[1] -= self.map_player_speed
            self.is_moving = True
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: 
            self.map_player_pos[1] += self.map_player_speed
            self.is_moving = True
        
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

        # 🟢 แก้ไขบักการกระโดดข้ามแผนที่ ส่งพิกัด target ตรงๆ ไปเลย!
        if will_change:
            self.change_realm(target_rx, target_ry, exit_side)
            return
        
        self.game_map.update_camera(self.map_player_pos[0] + 32, self.map_player_pos[1] + 32, 
                                    self.screen_width, self.screen_height)
        
        self.move_timer_overworld = self.move_timer_overworld + 0.2 if self.is_moving else 0
        
        if self.showing_dialogue:
            self.dialogue_timer -= 1
            if self.dialogue_timer <= 0:
                self.showing_dialogue = False
                self.current_npc = None

    def draw_overworld(self):
        self.game_map.draw(self.screen)
        
        img = self.player_overworld_equipped_img
        if self.facing_left_overworld: 
            img = pygame.transform.flip(img, True, False)
        by = abs(math.sin(self.move_timer_overworld)) * 10 if self.is_moving else 0
        
        player_screen_x = self.map_player_pos[0] + self.game_map.camera_offset[0]
        player_screen_y = self.map_player_pos[1] + self.game_map.camera_offset[1]
        self.screen.blit(img, (player_screen_x, player_screen_y - by))
        
        player_rect = pygame.Rect(self.map_player_pos[0], self.map_player_pos[1], 64, 64)
        nearby_statue = self.game_map.get_nearby_statue(player_rect)
        if nearby_statue:
            prompt_box = pygame.Surface((250, 40))
            prompt_box.fill(BLACK)
            prompt_box.set_alpha(180)
            self.screen.blit(prompt_box, (player_screen_x - 90, player_screen_y - 50))
            self.screen.blit(self.small_font.render("Press SPACE to Battle", True, WHITE), 
                           (player_screen_x - 80, player_screen_y - 40))
        
        nearby_npc = self.game_map.get_nearby_npc(player_rect)
        if nearby_npc and not self.showing_dialogue:
            prompt_box = pygame.Surface((200, 40))
            prompt_box.fill(BLACK)
            prompt_box.set_alpha(180)
            self.screen.blit(prompt_box, (player_screen_x - 70, player_screen_y - 50))
            self.screen.blit(self.small_font.render("Press E to Talk", True, CYAN_400), 
                           (player_screen_x - 60, player_screen_y - 40))
        
        if self.showing_dialogue and self.current_npc:
            dialogue_box = pygame.Surface((600, 120))
            dialogue_box.fill(SLATE_900)
            dialogue_box.set_alpha(230)
            
            box_x = (self.screen_width - 600) // 2
            box_y = self.screen_height - 150
            
            self.screen.blit(dialogue_box, (box_x, box_y))
            pygame.draw.rect(self.screen, CYAN_400, (box_x, box_y, 600, 120), 3, border_radius=8)
            
            npc_name = self.current_npc.data.get('name', 'Stranger')
            npc_text = self.current_npc.data.get('dialogue', 'Hello there!')
            
            name_surf = self.name_font.render(npc_name, True, AMBER_400)
            self.screen.blit(name_surf, (box_x + 20, box_y + 15))
            
            words = npc_text.split()
            lines = []
            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                if self.small_font.size(test_line)[0] < 550:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))
            
            for i, line in enumerate(lines[:2]):
                text_surf = self.small_font.render(line, True, WHITE)
                self.screen.blit(text_surf, (box_x + 20, box_y + 50 + i * 25))
        
        custom_cyan = (123, 165, 172)
        
        if self.total_statues > 0:
            statue_text = self.name_font.render(f"{self.statues_collected} / {self.total_statues}", True, WHITE)
            box_width = statue_text.get_width() + 60
            box_height = 40
            box_x, box_y = 20, 20
            
            bg_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
            pygame.draw.rect(bg_surface, (15, 23, 42, 200), bg_surface.get_rect(), border_radius=20)
            self.screen.blit(bg_surface, (box_x, box_y))
            pygame.draw.rect(self.screen, custom_cyan, (box_x, box_y, box_width, box_height), 1, border_radius=20)
            pygame.draw.circle(self.screen, AMBER_500, (box_x + 20, box_y + box_height // 2), 6)
            self.screen.blit(statue_text, (box_x + 36, box_y + (box_height - statue_text.get_height()) // 2))
            
        gold_text = self.name_font.render(f"{self.gold} G", True, WHITE)
        gold_width = gold_text.get_width() + 60
        gold_x = 20 if self.total_statues == 0 else 20 + box_width + 10
        gold_y = 20
        
        bg_surface_gold = pygame.Surface((gold_width, 40), pygame.SRCALPHA)
        pygame.draw.rect(bg_surface_gold, (15, 23, 42, 200), bg_surface_gold.get_rect(), border_radius=20)
        self.screen.blit(bg_surface_gold, (gold_x, gold_y))
        pygame.draw.rect(self.screen, custom_cyan, (gold_x, gold_y, gold_width, 40), 1, border_radius=20)
        pygame.draw.circle(self.screen, EMERALD_500, (gold_x + 20, gold_y + 20), 6)
        self.screen.blit(gold_text, (gold_x + 36, gold_y + (40 - gold_text.get_height()) // 2))

    def draw_shop(self):
        self.draw_overworld()
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        box = pygame.Rect(200, 150, 400, 300)
        pygame.draw.rect(self.screen, SLATE_900, box, border_radius=16)
        pygame.draw.rect(self.screen, AMBER_400, box, 3, border_radius=16)
        
        self.screen.blit(self.font.render("MERCHANT'S SHOP", True, AMBER_500), (220, 170))
        self.screen.blit(self.small_font.render(f"Your Gold: {self.gold} G", True, WHITE), (220, 220))
        
        self.screen.blit(self.name_font.render("[1] Health Potion (50G)", True, EMERALD_400), (220, 280))
        self.screen.blit(self.small_font.render(f"Owned: {self.potions}", True, SLATE_400), (240, 310))
        
        self.screen.blit(self.name_font.render("[2] Hint Scroll (50G)", True, CYAN_400), (220, 360))
        self.screen.blit(self.small_font.render(f"Owned: {self.scrolls}", True, SLATE_400), (240, 390))
        
        self.screen.blit(self.small_font.render("Press SPACE or ESC to leave", True, GRAY), (220, 430))

    def draw_upgrade(self):
        self.draw_overworld()
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        box = pygame.Rect(150, 150, 500, 300)
        pygame.draw.rect(self.screen, SLATE_900, box, border_radius=16)
        pygame.draw.rect(self.screen, CYAN_400, box, 3, border_radius=16)
        
        self.screen.blit(self.font.render("STATUE DESTROYED!", True, AMBER_500), (170, 170))
        self.screen.blit(self.small_font.render("The gods grant you a blessing. Choose your upgrade:", True, WHITE), (170, 220))
        
        self.screen.blit(self.name_font.render("[1] Power of Ares (ATK +5)", True, RED_500), (170, 280))
        self.screen.blit(self.small_font.render(f"Current ATK: {self.base_atk}", True, SLATE_400), (190, 310))
        
        self.screen.blit(self.name_font.render("[2] Vitality of Demeter (MAX HP +20 & Full Heal)", True, EMERALD_400), (170, 360))
        self.screen.blit(self.small_font.render(f"Current Max HP: {self.player_max_hp}", True, SLATE_400), (190, 390))

    def draw_modern_hp_bar(self, surface, x, y, curr, max_hp, fill, name):
        panel_w = 300
        pygame.draw.rect(surface, (15, 23, 42, 220), (x, y, panel_w, 80), border_radius=12)
        
        name_surf = self.name_font.render(name, True, WHITE)
        surface.blit(name_surf, (x + 15, y + 20))
        
        ratio = max(0.0, min(1.0, curr / max_hp))
        pct = int(ratio * 100)
        txt = self.small_font.render(f"{curr}/{max_hp} ({pct}%)", True, SLATE_400)
        surface.blit(txt, (x + panel_w - 15 - txt.get_width(), y + 30))
        
        bx, by, bw, bh = x + 15, y + 50, panel_w - 30, 16
        pygame.draw.rect(surface, BLACK, (bx, by, bw, bh), border_radius=8)
        if ratio > 0: pygame.draw.rect(surface, fill, (bx, by, int(bw * ratio), bh), border_radius=8)

    def draw_battle(self):
        shake_x = random.randint(-self.shake_amount, self.shake_amount) if self.shake_timer > 0 else 0
        shake_y = random.randint(-self.shake_amount, self.shake_amount) if self.shake_timer > 0 else 0
        if self.shake_timer > 0: self.shake_timer -= 1
        
        battle_surf = pygame.Surface((self.screen_width, self.screen_height))
        battle_surf.blit(self.battle_bg, (0, 0))
        
        if self.game_map.is_boss_realm:
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill((40, 0, 10, 120))
            battle_surf.blit(overlay, (0, 0))
        
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
        
        self.draw_modern_hp_bar(battle_surf, 40, 30, self.enemy.current_hp, self.enemy.max_hp, RED_500, self.enemy.name)
        self.draw_modern_hp_bar(battle_surf, 460, 320, self.player.hp, self.player_max_hp, EMERALD_500, "Player")
        
        if self.player.combo_count > 0:
            bonus_dmg = int(self.player.combo_count * 20)
            combo_txt = self.btn_font.render(f"COMBO x{self.player.combo_count} (ATK +{bonus_dmg}%)", True, AMBER_400)
            battle_surf.blit(combo_txt, (460, 295))
        
        for t in self.floating_texts[:]:
            battle_surf.blit(self.combo_font.render(str(t['text']), True, t['color']), (t['x'], t['y']))
            t['y'] -= 2; t['timer'] -= 1
            if t['timer'] <= 0: self.floating_texts.remove(t)
            
        if self.crit_timer > 0:
            crit_txt = self.combo_font.render("CRITICAL!", True, AMBER_500)
            c_x_crit = self.enemy_battle_pos[0] + 80 - crit_txt.get_width() // 2
            c_y_crit = self.enemy_battle_pos[1] - 40 - ((60 - self.crit_timer) * 0.5)
            battle_surf.blit(self.combo_font.render("CRITICAL!", True, BLACK), (c_x_crit + 2, c_y_crit + 2))
            battle_surf.blit(crit_txt, (c_x_crit, c_y_crit))
            self.crit_timer -= 1 

        board_start_y = 440
        pygame.draw.rect(battle_surf, (15, 23, 42, 240), (0, board_start_y, 800, 160))
        pygame.draw.line(battle_surf, SLATE_700, (0, board_start_y), (800, board_start_y), 2)

        if not self.gm.game_over:
            battle_surf.blit(self.small_font.render(f"[1] Potion: {self.potions}   [2] Hint Scroll: {self.scrolls}   [ESC] Flee", True, SLATE_400), (20, board_start_y - 25))

        if self.board.current_attempt >= 4 and not self.gm.game_over:
            hint = f"Ehm.. maybe it's: '{self.dictionary.get_current_hint()}'"
            if len(hint) > 75: hint = hint[:72] + "..."
            hs = self.small_font.render(hint, True, BLACK)
            br = hs.get_rect(midbottom=(self.player_battle_pos[0] + 120, self.player_battle_pos[1] - 20))
            pygame.draw.rect(battle_surf, WHITE, br.inflate(20, 15), border_radius=10)
            pygame.draw.rect(battle_surf, EMERALD_500, br.inflate(20, 15), 2, border_radius=10)
            battle_surf.blit(hs, br)

        battle_surf.blit(self.small_font.render("ABSENT", True, SLATE_700), (40, board_start_y + 15))
        absent_x, absent_y = 40, board_start_y + 40
        for i, char in enumerate(sorted(list(self.absent_letters))):
            r, c = i // 6, i % 6
            pygame.draw.rect(battle_surf, BLACK, (absent_x + c*25, absent_y + r*25, 20, 20), border_radius=4)
            battle_surf.blit(self.small_font.render(char, True, SLATE_700), (absent_x + c*25 + 6, absent_y + r*25 + 3))

        box, m = 50, 10
        cx = (800 - (box*5 + m*4)) // 2
        cy = board_start_y + 45
        for col in range(5):
            x = cx + col * (box + m)
            char = self.current_guess[col] if col < len(self.current_guess) else ""
            is_active = (col == len(self.current_guess) and not self.gm.game_over)
            pygame.draw.rect(battle_surf, SLATE_800 if char else BLACK, (x, cy, box, box), border_radius=8)
            pygame.draw.rect(battle_surf, CYAN_400 if is_active else SLATE_700, (x, cy, box, box), 2 if not is_active else 3, border_radius=8)
            if char:
                t = self.font.render(char, True, WHITE)
                battle_surf.blit(t, t.get_rect(center=(x+box//2, cy+box//2)))

        battle_surf.blit(self.small_font.render("BEST KNOWN", True, EMERALD_500), (580, board_start_y + 15))
        right_x, right_y = 580, board_start_y + 40
        for i in range(5):
            rx = right_x + i*30
            c_char = self.green_letters[i]
            pygame.draw.rect(battle_surf, EMERALD_500 if c_char else SLATE_800, (rx, right_y, 25, 25), border_radius=4)
            if c_char: battle_surf.blit(self.small_font.render(c_char, True, BLACK), (rx + 7, right_y + 5))
        
        if self.yellow_letters:
            battle_surf.blit(self.small_font.render("PRESENT:", True, AMBER_500), (right_x, right_y + 40))
            for i, char in enumerate(sorted(list(self.yellow_letters))):
                pygame.draw.rect(battle_surf, AMBER_500, (right_x + 75 + i*25, right_y + 35, 20, 20), border_radius=4)
                battle_surf.blit(self.small_font.render(char, True, BLACK), (right_x + 75 + i*25 + 5, right_y + 38))

        if self.gm.game_over:
            msg = "VICTORY!" if self.enemy.current_hp <= 0 else "DEFEATED!"
            msg_color = EMERALD_400 if msg == "VICTORY!" else RED_500
            txt_surface = self.large_font.render(msg, True, msg_color)
            txt_rect = txt_surface.get_rect(center=(self.screen_width // 2, 280))
            battle_surf.blit(txt_surface, txt_rect)
            sub_txt = self.small_font.render("Press SPACE to return", True, WHITE)
            sub_rect = sub_txt.get_rect(center=(self.screen_width // 2, 330))
            battle_surf.blit(sub_txt, sub_rect)

        self.screen.blit(battle_surf, (shake_x, shake_y))

    def run(self):
        clock = pygame.time.Clock()
        while True:
            self.handle_events()
            if self.state == STATE_SELECTION: self.draw_selection()
            elif self.state == STATE_OVERWORLD: self.update_overworld(); self.draw_overworld()
            elif self.state == STATE_BATTLE: self.draw_battle()
            elif self.state == STATE_SHOP: self.draw_shop()
            elif self.state == STATE_UPGRADE: self.draw_upgrade()
            pygame.display.flip(); clock.tick(60)

if __name__ == "__main__":
    app = PygameApp(); app.run()