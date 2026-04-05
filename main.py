import pygame
import sys
import os
import math
import random
from src.config import DATA_DIR, RAW_DATA_DIR, WORDS_DATA_DIR
from src.game_manager import GameManager
from src.entities import Player, Enemy
from src.mechanics import WordDictionary, TileBoard

# --- MODERN UI COLORS ---
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
        self.player = Player(hp=100, base_attack=15)
        
        self.battle_float_timer = 0
        self.crit_timer = 0
        self.target_word = self.dictionary.generate_random_word()
        self.current_guess = ""
        self.guess_history = []
        
        self.absent_letters = set()
        self.yellow_letters = set()
        self.green_letters = [None] * 5
        
        self.setup_assets()
        self.setup_selection()
        self.setup_overworld()

    def load_image_safely(self, path, size, fallback_color):
        if os.path.exists(path):
            return pygame.transform.scale(pygame.image.load(path).convert_alpha(), size)
        surf = pygame.Surface(size)
        surf.fill(fallback_color)
        return surf

    def setup_assets(self):
        self.overworld_bg = pygame.transform.scale(self.load_image_safely("assets/images/map_bg.png", (800, 600), (30, 80, 40)), (800, 600))
        self.battle_bg = pygame.transform.scale(self.load_image_safely("assets/images/bg.png", (800, 600), (80, 120, 200)), (800, 600))
        self.statue_img = self.load_image_safely("assets/images/statue.png", (60, 80), (100, 100, 100))
        self.sprite_sheet = SpriteSheet("assets/images/roguelikeChar_transparent.png")

    def generate_box(self, c1, r1, c2, r2):
        return [(c, r) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]

    def filter_empty(self, coords_list):
        valid = []
        for c, r in coords_list:
            img = self.sprite_sheet.get_image_by_grid(c, r, 1)
            rect = img.get_bounding_rect()
            if rect.width > 0:
                valid.append((c, r))
        return valid

    def setup_selection(self):
        npc_bases = self.generate_box(0, 0, 1, 11)
        player_bases = [(1, 0), (1, 1), (1, 2)]
        self.enemy_bases = [b for b in npc_bases if b not in player_bases]
        
        self.options = {
            'base': player_bases,
            'pants': [None] + self.filter_empty(self.generate_box(2, 0, 4, 9)),
            'armor': [None] + self.filter_empty(self.generate_box(5, 0, 17, 9)),
            'hair': [None] + self.filter_empty(self.generate_box(18, 0, 25, 7) + self.generate_box(18, 8, 20, 11)),
            'hat': [None] + self.filter_empty(self.generate_box(29, 0, 31, 8)),
            'shield': [None] + self.filter_empty(self.generate_box(36, 0, 39, 8)),
            'weapon': [None] + self.filter_empty(self.generate_box(41, 0, 55, 4) + self.generate_box(41, 5, 54, 9))
        }
        
        self.tabs = ['base', 'hair', 'hat', 'armor', 'pants', 'weapon', 'shield']
        self.tab_names = ['BODY', 'HAIR', 'HAT', 'ARMOR', 'PANTS', 'WEAPON', 'SHIELD']
        self.current_tab = 'base'
        
        self.selections = {k: 0 for k in self.tabs}
        self.pages = {k: 0 for k in self.tabs}
        self.items_per_page = 30 
        
        self.start_btn_rect = pygame.Rect(495, 495, 260, 50)
        self.active_buttons = []
        self.update_player_visuals()

    def update_player_visuals(self):
        layers = [
            self.options['base'][self.selections['base']],
            self.options['pants'][self.selections['pants']],
            self.options['armor'][self.selections['armor']],
            self.options['hair'][self.selections['hair']],
            self.options['hat'][self.selections['hat']],
            self.options['shield'][self.selections['shield']],
            self.options['weapon'][self.selections['weapon']]
        ]
        self.player_preview_img = self.sprite_sheet.get_equipped_image_by_grid(layers, 14)
        self.player_overworld_equipped_img = self.sprite_sheet.get_equipped_image_by_grid(layers, 4)
        self.player_battle_img = self.sprite_sheet.get_equipped_image_by_grid(layers, 10)

    def setup_overworld(self):
        self.map_player_pos = [400, 300]
        self.map_player_speed = 4
        self.facing_left_overworld = False
        self.is_moving = False
        self.move_timer_overworld = 0
        self.statue_rect = pygame.Rect(375, 100, 60, 80)
        self.enemy_battle_pos = (550, 100)
        self.player_battle_pos = (80, 230)

    def randomize_enemy(self):
        boss_names = ["Corrupted Knight", "Void Fiend", "Cursed Rogue", "Mad Jester", "Shadow Golem", "Dark Mage", "Swamp Terror"]
        self.enemy = Enemy(name=random.choice(boss_names), max_hp=100, attack_power=10)
        
        enemy_layers = [
            random.choice(self.enemy_bases),
            random.choice(self.options['pants']),
            random.choice(self.options['armor'][1:]),
            random.choice(self.options['hair']),
            random.choice(self.options['hat']),
            random.choice(self.options['shield']),
            random.choice(self.options['weapon'][1:])
        ]
        self.enemy_battle_img = self.sprite_sheet.get_equipped_image_by_grid(enemy_layers, 10)
        
        self.target_word = self.dictionary.generate_random_word()
        self.battle_float_timer = 0
        self.crit_timer = 0
        self.board.current_attempt = 1
        self.guess_history = []
        self.current_guess = ""
        self.absent_letters = set()
        self.yellow_letters = set()
        self.green_letters = [None] * 5

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.gm.export_data_to_csv()
                pygame.quit()
                sys.exit()
                
            if self.state == STATE_SELECTION:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.start_btn_rect.collidepoint(event.pos):
                        self.state = STATE_OVERWORLD
                        return
                    for btn in self.active_buttons:
                        if btn['rect'].collidepoint(event.pos):
                            if btn['type'] == 'tab':
                                self.current_tab = btn['tab']
                            elif btn['type'] == 'item':
                                self.selections[self.current_tab] = btn['idx']
                                self.update_player_visuals()
                            elif btn['type'] == 'prev':
                                self.pages[self.current_tab] = max(0, self.pages[self.current_tab] - 1)
                            elif btn['type'] == 'next':
                                max_p = math.ceil(len(self.options[self.current_tab]) / self.items_per_page) - 1
                                self.pages[self.current_tab] = min(max_p, self.pages[self.current_tab] + 1)
                            break 

            elif self.state == STATE_OVERWORLD:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        player_rect = pygame.Rect(self.map_player_pos[0], self.map_player_pos[1], 64, 64)
                        if player_rect.colliderect(self.statue_rect.inflate(50, 50)):
                            self.state = STATE_BATTLE
                            self.randomize_enemy()
                            self.gm.start_word_timer()

            elif self.state == STATE_BATTLE:
                if event.type == pygame.KEYDOWN and not self.gm.game_over:
                    if event.unicode.isascii() and event.unicode.isalpha() and len(self.current_guess) < 5:
                        self.current_guess += event.unicode.upper()
                        self.gm.keystroke_count += 1
                    elif event.key == pygame.K_BACKSPACE:
                        self.current_guess = self.current_guess[:-1]
                        self.gm.keystroke_count += 1
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and len(self.current_guess) == 5:
                        self.gm.keystroke_count += 1
                        self.submit_guess()

    def submit_guess(self):
        guess = self.current_guess
        self.current_guess = ""
        colors = self.board.evaluate_colors(guess, self.target_word)
        self.guess_history.append((guess, colors))
        
        for i in range(5):
            c = guess[i]
            color = colors[i]
            if color == "GREEN":
                self.green_letters[i] = c
                if c in self.yellow_letters:
                    self.yellow_letters.discard(c)
            elif color == "YELLOW":
                if c not in self.green_letters:
                    self.yellow_letters.add(c)
            elif color == "GRAY":
                if c not in self.green_letters and c not in self.yellow_letters:
                    self.absent_letters.add(c)
        
        if guess == self.target_word:
            self.gm.end_word_timer()
            self.player.combo_count += 1
            damage = self.player.calculate_damage()
            self.enemy.take_damage(damage)
            self.gm.record_word_data(self.board.current_attempt - 1, self.player.combo_count, damage)
            
            if self.player.combo_count > 1:
                self.crit_timer = 60
                
            if self.gm.check_win_condition(self.enemy):
                self.gm.game_over = True
            else:
                self.reset_for_next_word()
        else:
            self.player.combo_count = 0
            if self.board.current_attempt > self.board.grid_size:
                self.enemy.attack_player(self.player)
                if self.player.hp <= 0:
                    self.gm.game_over = True
                else:
                    self.reset_for_next_word()

    def reset_for_next_word(self):
        self.target_word = self.dictionary.generate_random_word()
        self.board.current_attempt = 1
        self.guess_history = []
        self.absent_letters = set()
        self.yellow_letters = set()
        self.green_letters = [None] * 5
        self.gm.start_word_timer()

    def draw_category_ui(self, cat, start_x, start_y):
        opts = self.options[cat]
        total_pages = max(1, math.ceil(len(opts) / self.items_per_page))
        cur_page = self.pages[cat]
        
        header_txt = self.name_font.render(f"SELECT {self.tab_names[self.tabs.index(cat)]}", True, WHITE)
        self.screen.blit(header_txt, (start_x, start_y))
        
        box, margin, cols = 44, 10, 5
        grid_start_y = start_y + 45
        start_idx = cur_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(opts))
        
        for i in range(start_idx, end_idx):
            r, c = (i - start_idx) // cols, (i - start_idx) % cols
            rect = pygame.Rect(start_x + c*(box+margin), grid_start_y + r*(box+margin), box, box)
            
            is_selected = (i == self.selections[cat])
            border_color = CYAN_400 if is_selected else SLATE_700
            bg_color = SLATE_800 if is_selected else (20, 30, 50)
            
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=8)
            pygame.draw.rect(self.screen, border_color, rect, 2 if is_selected else 1, border_radius=8)
            
            if opts[i]:
                img = self.sprite_sheet.get_image_by_grid(opts[i][0], opts[i][1], 2)
                self.screen.blit(img, (rect.x + (box - img.get_width())//2, rect.y + (box - img.get_height())//2))
            else:
                txt = self.small_font.render("X", True, RED_500)
                self.screen.blit(txt, (rect.x + (box - txt.get_width())//2, rect.y + (box - txt.get_height())//2))
                
            self.active_buttons.append({'rect': rect, 'type': 'item', 'cat': cat, 'idx': i})

        page_y = 455
        right_edge = start_x + (cols * box) + ((cols - 1) * margin)
        
        btn_next = pygame.Rect(right_edge - 25, page_y, 25, 25)
        btn_prev = pygame.Rect(right_edge - 55, page_y, 25, 25)
        
        page_txt = self.small_font.render(f"PAGE {cur_page+1}/{total_pages}", True, SLATE_400)
        page_txt_x = right_edge - 65 - page_txt.get_width()
        self.screen.blit(page_txt, (page_txt_x, page_y + 5))
        
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
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 220)) 
        self.screen.blit(overlay, (0, 0))
        
        self.active_buttons = []
        
        title = self.large_font.render("A R M O R Y", True, CYAN_400)
        self.screen.blit(title, (50, 40))
        subtitle = self.small_font.render("CUSTOMIZE YOUR HERO", True, SLATE_400)
        self.screen.blit(subtitle, (55, 90))
        
        pedestal_x, pedestal_y = 175, 400
        pygame.draw.ellipse(self.screen, SLATE_800, (pedestal_x - 80, pedestal_y, 160, 30))
        pygame.draw.ellipse(self.screen, CYAN_500, (pedestal_x - 70, pedestal_y + 5, 140, 20), 2)
        
        img_w = self.player_preview_img.get_width()
        img_h = self.player_preview_img.get_height()
        self.screen.blit(self.player_preview_img, (pedestal_x - img_w//2, pedestal_y - img_h + 20))
        
        panel_rect = pygame.Rect(330, 40, 440, 530)
        pygame.draw.rect(self.screen, (15, 23, 42, 180), panel_rect, border_radius=16)
        pygame.draw.rect(self.screen, SLATE_700, panel_rect, 2, border_radius=16)
        
        tab_y = 65
        for i, tab in enumerate(self.tabs):
            is_active = (self.current_tab == tab)
            rect = pygame.Rect(345, tab_y, 120, 48)
            
            if is_active:
                pygame.draw.rect(self.screen, SLATE_800, rect, border_radius=8)
                pygame.draw.rect(self.screen, CYAN_400, (rect.x, rect.y, 4, rect.height), border_top_left_radius=8, border_bottom_left_radius=8)
                color = CYAN_400
            else:
                color = SLATE_400
                
            text = self.small_font.render(self.tab_names[i], True, color)
            self.screen.blit(text, (rect.x + 15, rect.y + 16))
            self.active_buttons.append({'rect': rect, 'type': 'tab', 'tab': tab})
            tab_y += 62
            
        pygame.draw.line(self.screen, SLATE_700, (475, 60), (475, 540), 2)
        
        self.draw_category_ui(self.current_tab, 495, 60)

        pygame.draw.rect(self.screen, CYAN_500, self.start_btn_rect, border_radius=12)
        start_text = self.btn_font.render("START JOURNEY >", True, BLACK)
        self.screen.blit(start_text, (self.start_btn_rect.centerx - start_text.get_width()//2, 
                                      self.start_btn_rect.centery - start_text.get_height()//2))

    def update_overworld(self):
        keys = pygame.key.get_pressed()
        self.is_moving = False
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

        self.map_player_pos[0] = max(0, min(self.screen_width - 64, self.map_player_pos[0]))
        self.map_player_pos[1] = max(0, min(self.screen_height - 64, self.map_player_pos[1]))
        self.move_timer_overworld = self.move_timer_overworld + 0.2 if self.is_moving else 0

    def draw_overworld(self):
        self.screen.blit(self.overworld_bg, (0, 0))
        self.screen.blit(self.statue_img, self.statue_rect)
        
        img = self.player_overworld_equipped_img
        if self.facing_left_overworld:
            img = pygame.transform.flip(img, True, False)
        bounce_y = abs(math.sin(self.move_timer_overworld)) * 10 if self.is_moving else 0
        self.screen.blit(img, (self.map_player_pos[0], self.map_player_pos[1] - bounce_y))

        if pygame.Rect(self.map_player_pos[0], self.map_player_pos[1], 64, 64).colliderect(self.statue_rect.inflate(50, 50)):
            prompt_box = pygame.Surface((250, 40)); prompt_box.fill(BLACK); prompt_box.set_alpha(180)
            self.screen.blit(prompt_box, (self.map_player_pos[0] - 90, self.map_player_pos[1] - 50))
            self.screen.blit(self.small_font.render("Press SPACE to Battle", True, WHITE), (self.map_player_pos[0] - 80, self.map_player_pos[1] - 40))

    def draw_modern_hp_bar(self, surface, x, y, current_hp, max_hp, fill_color, name):
        panel = pygame.Surface((280, 80), pygame.SRCALPHA)
        pygame.draw.rect(panel, (15, 23, 42, 220), (0, 0, 280, 80), border_radius=12)
        pygame.draw.rect(panel, SLATE_700, (0, 0, 280, 80), 2, border_radius=12)
        surface.blit(panel, (x, y))

        name_txt = self.name_font.render(name, True, WHITE)
        surface.blit(name_txt, (x + 15, y + 15))
        
        bar_x, bar_y, bar_w, bar_h = x + 15, y + 50, 250, 16
        pygame.draw.rect(surface, BLACK, (bar_x, bar_y, bar_w, bar_h), border_radius=8)
        
        ratio = max(0.0, min(1.0, current_hp / max_hp))
        if ratio > 0:
            pygame.draw.rect(surface, fill_color, (bar_x, bar_y, int(bar_w * ratio), bar_h), border_radius=8)
        
        hp_txt = self.small_font.render("HP", True, WHITE)
        surface.blit(hp_txt, (bar_x + 5, bar_y + 1))

    def draw_battle(self):
        self.screen.blit(self.battle_bg, (0, 0))
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 140))
        self.screen.blit(overlay, (0, 0))

        self.battle_float_timer += 0.05
        float_off = math.sin(self.battle_float_timer) * 8
        self.screen.blit(self.enemy_battle_img, (self.enemy_battle_pos[0], self.enemy_battle_pos[1] + float_off))
        self.screen.blit(self.player_battle_img, (self.player_battle_pos[0], self.player_battle_pos[1] - float_off))
        
        self.draw_modern_hp_bar(self.screen, 40, 30, self.enemy.current_hp, self.enemy.max_hp, RED_500, self.enemy.name)
        self.draw_modern_hp_bar(self.screen, 480, 320, self.player.hp, 100, EMERALD_500, "Player")
        
        if self.crit_timer > 0:
            crit_txt = self.combo_font.render("CRITICAL!", True, AMBER_500)
            crit_shadow = self.combo_font.render("CRITICAL!", True, BLACK)
            
            c_x_crit = self.enemy_battle_pos[0] + 80 - crit_txt.get_width() // 2
            c_y_crit = self.enemy_battle_pos[1] - 20 - ((60 - self.crit_timer) * 0.5)
            
            self.screen.blit(crit_shadow, (c_x_crit + 2, c_y_crit + 2))
            self.screen.blit(crit_txt, (c_x_crit, c_y_crit))
            
            self.crit_timer -= 1 

        board_start_y = 440
        hud_bg = pygame.Surface((self.screen_width, self.screen_height - board_start_y), pygame.SRCALPHA)
        hud_bg.fill((15, 23, 42, 240))
        self.screen.blit(hud_bg, (0, board_start_y))
        pygame.draw.line(self.screen, SLATE_700, (0, board_start_y), (self.screen_width, board_start_y), 2)

        self.screen.blit(self.small_font.render("ABSENT", True, SLATE_700), (40, board_start_y + 15))
        absent_x, absent_y = 40, board_start_y + 40
        for i, char in enumerate(sorted(list(self.absent_letters))):
            r, c = i // 6, i % 6
            pygame.draw.rect(self.screen, BLACK, (absent_x + c*25, absent_y + r*25, 20, 20), border_radius=4)
            txt = self.small_font.render(char, True, SLATE_700)
            self.screen.blit(txt, (absent_x + c*25 + 6, absent_y + r*25 + 3))

        box, margin = 50, 10
        center_x = (self.screen_width - ((box * 5) + (margin * 4))) // 2
        center_y = board_start_y + 45
        
        for col in range(5):
            x = center_x + (col * (box + margin))
            char = self.current_guess[col] if col < len(self.current_guess) else ""
            is_active = (col == len(self.current_guess) and not self.gm.game_over)
            
            bg_color = SLATE_800 if char else BLACK
            border_color = CYAN_400 if is_active else SLATE_700
            
            pygame.draw.rect(self.screen, bg_color, (x, center_y, box, box), border_radius=8)
            pygame.draw.rect(self.screen, border_color, (x, center_y, box, box), 2 if not is_active else 3, border_radius=8)
            if char:
                txt = self.font.render(char, True, WHITE)
                self.screen.blit(txt, txt.get_rect(center=(x + box//2, center_y + box//2)))
                
        self.screen.blit(self.small_font.render("BEST KNOWN", True, EMERALD_500), (580, board_start_y + 15))
        right_x, right_y = 580, board_start_y + 40
        for i in range(5):
            rx = right_x + i*30
            c_char = self.green_letters[i]
            pygame.draw.rect(self.screen, EMERALD_500 if c_char else SLATE_800, (rx, right_y, 25, 25), border_radius=4)
            if c_char:
                txt = self.small_font.render(c_char, True, BLACK)
                self.screen.blit(txt, (rx + 7, right_y + 5))
        
        if self.yellow_letters:
            self.screen.blit(self.small_font.render("PRESENT:", True, AMBER_500), (right_x, right_y + 40))
            for i, char in enumerate(sorted(list(self.yellow_letters))):
                pygame.draw.rect(self.screen, AMBER_500, (right_x + 75 + i*25, right_y + 35, 20, 20), border_radius=4)
                txt = self.small_font.render(char, True, BLACK)
                self.screen.blit(txt, (right_x + 75 + i*25 + 5, right_y + 38))

        if self.gm.game_over:
            msg, color = ("VICTORY!", EMERALD_400) if self.enemy.current_hp <= 0 else ("DEFEATED!", RED_500)
            txt = self.large_font.render(msg, True, color)
            self.screen.blit(txt, ((self.screen_width - txt.get_width())//2, board_start_y - 60))

    def run(self):
        clock = pygame.time.Clock()
        while True:
            self.handle_events()
            if self.state == STATE_SELECTION: self.draw_selection()
            elif self.state == STATE_OVERWORLD:
                self.update_overworld()
                self.draw_overworld()
            elif self.state == STATE_BATTLE: self.draw_battle()
            pygame.display.flip()
            clock.tick(60)

if __name__ == "__main__":
    app = PygameApp()
    app.run()