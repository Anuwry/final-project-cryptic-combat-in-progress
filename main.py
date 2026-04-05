import pygame
import sys
import os
import math
import random
from src.config import DATA_DIR, RAW_DATA_DIR, WORDS_DATA_DIR
from src.game_manager import GameManager
from src.entities import Player, Enemy
from src.mechanics import WordDictionary, TileBoard

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (83, 141, 78)
YELLOW = (181, 159, 59)
GRAY = (58, 58, 60)
UI_BG = (25, 25, 30)
SLOT_BG = (40, 40, 50)
SLOT_SELECT = (100, 255, 100)

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
        self.font = pygame.font.Font(None, 40)
        self.small_font = pygame.font.Font(None, 20)
        
        self.state = STATE_SELECTION
        self.gm = GameManager()
        self.dictionary = WordDictionary("normal")
        self.board = TileBoard()
        self.player = Player(hp=100, base_attack=15)
        
        self.battle_float_timer = 0
        self.target_word = self.dictionary.generate_random_word()
        self.current_guess = ""
        self.guess_history = []
        
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
        
        self.available_enemies_data = [
            {"name": "Orc Grunt", "grid_pos": (1, 4)},
            {"name": "Mad Jester", "grid_pos": (0, 10)},
            {"name": "Swamp Fiend", "grid_pos": (0, 5)}
        ]

    def generate_box(self, c1, r1, c2, r2):
        return [(c, r) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]

    def filter_empty(self, coords_list):
        valid = []
        for c, r in coords_list:
            img = self.sprite_sheet.get_image_by_grid(c, r, 1)
            rect = img.get_bounding_rect()
            # ปลดล็อกระบบกรอง: ขอแค่ภาพมีความกว้าง > 0 (มีสีแม้แต่ 1 พิกเซล) ก็เอามาใช้เลย 
            # (กู้คืนกางเกงและรองเท้าที่สูงแค่ 1 พิกเซลกลับมา)
            if rect.width > 0:
                valid.append((c, r))
        return valid

    def setup_selection(self):
        npc_bases = self.generate_box(0, 0, 1, 11)
        player_bases = [(1, 0), (1, 1), (1, 2)]
        enemies = [(1, 4), (0, 10), (0, 5)]
        
        for ex in player_bases + enemies:
            if ex in npc_bases:
                npc_bases.remove(ex)
                
        self.options = {
            'base': player_bases + self.filter_empty(npc_bases),
            'pants': [None] + self.filter_empty(self.generate_box(2, 0, 4, 9)),
            'armor': [None] + self.filter_empty(self.generate_box(5, 0, 17, 9)),
            'hair': [None] + self.filter_empty(self.generate_box(18, 0, 25, 7) + self.generate_box(18, 8, 20, 11)),
            'hat': [None] + self.filter_empty(self.generate_box(29, 0, 31, 8)),
            'shield': [None] + self.filter_empty(self.generate_box(36, 0, 39, 8)),
            'weapon': [None] + self.filter_empty(self.generate_box(41, 0, 55, 4) + self.generate_box(41, 5, 54, 9))
        }
        
        self.tabs = ['base', 'pants', 'armor', 'hair', 'hat', 'shield', 'weapon']
        self.tab_names = ['BODY', 'PANTS', 'ARMOR', 'HAIR/BEARD', 'HAT', 'SHIELD', 'WEAPON']
        self.current_tab = 'base'
        
        self.selections = {k: 0 for k in self.tabs}
        self.pages = {k: 0 for k in self.tabs}
        self.items_per_page = 36 
        
        self.start_btn_rect = pygame.Rect(550, 520, 200, 50)
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
        self.enemy_battle_pos = (500, 50)
        self.player_battle_pos = (100, 250)

    def randomize_enemy(self):
        enemy_info = random.choice(self.available_enemies_data)
        self.enemy = Enemy(name=enemy_info["name"], max_hp=100, attack_power=10)
        self.enemy_battle_img = self.sprite_sheet.get_image_by_grid(enemy_info["grid_pos"][0], enemy_info["grid_pos"][1], 10)
        self.enemy_battle_pos = (500, 50)
        self.target_word = self.dictionary.generate_random_word()
        self.battle_float_timer = 0
        self.board.current_attempt = 1
        self.guess_history = []
        self.current_guess = ""

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
                    if event.unicode.isalpha() and len(self.current_guess) < 5:
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
        
        if guess == self.target_word:
            self.gm.end_word_timer()
            self.player.combo_count += 1
            damage = self.player.calculate_damage()
            self.enemy.take_damage(damage)
            self.gm.record_word_data(self.board.current_attempt - 1, self.player.combo_count, damage)
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
        self.gm.start_word_timer()

    def draw_category_ui(self, cat, start_x, start_y):
        opts = self.options[cat]
        total_pages = max(1, math.ceil(len(opts) / self.items_per_page))
        cur_page = self.pages[cat]
        
        page_txt = self.small_font.render(f"Page {cur_page+1}/{total_pages}", True, WHITE)
        self.screen.blit(page_txt, (start_x + 60, start_y))
        
        btn_prev = pygame.Rect(start_x + 20, start_y - 2, 25, 25)
        btn_next = pygame.Rect(start_x + 130, start_y - 2, 25, 25)
        
        if cur_page > 0:
            pygame.draw.rect(self.screen, GRAY, btn_prev, border_radius=3)
            self.screen.blit(self.small_font.render("<", True, WHITE), (btn_prev.x+8, btn_prev.y+5))
            self.active_buttons.append({'rect': btn_prev, 'type': 'prev', 'cat': cat})
        if cur_page < total_pages - 1:
            pygame.draw.rect(self.screen, GRAY, btn_next, border_radius=3)
            self.screen.blit(self.small_font.render(">", True, WHITE), (btn_next.x+8, btn_next.y+5))
            self.active_buttons.append({'rect': btn_next, 'type': 'next', 'cat': cat})
            
        box, margin, cols = 38, 8, 9
        start_idx = cur_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(opts))
        
        for i in range(start_idx, end_idx):
            r, c = (i - start_idx) // cols, (i - start_idx) % cols
            rect = pygame.Rect(start_x + c*(box+margin), start_y + 40 + r*(box+margin), box, box)
            
            border_color = SLOT_SELECT if i == self.selections[cat] else GRAY
            pygame.draw.rect(self.screen, SLOT_BG, rect, border_radius=4)
            pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=4)
            
            if opts[i]:
                img = self.sprite_sheet.get_image_by_grid(opts[i][0], opts[i][1], 2)
                self.screen.blit(img, (rect.x + (box - img.get_width())//2, rect.y + (box - img.get_height())//2))
            else:
                txt = self.small_font.render("X", True, (200, 100, 100))
                self.screen.blit(txt, (rect.x + (box - txt.get_width())//2, rect.y + (box - txt.get_height())//2))
                
            self.active_buttons.append({'rect': rect, 'type': 'item', 'cat': cat, 'idx': i})

    def draw_selection(self):
        self.screen.fill(UI_BG)
        self.active_buttons = []
        
        self.screen.blit(self.font.render("WARDROBE", True, WHITE), (50, 40))
        self.screen.blit(self.player_preview_img, (75, 120))
        
        tab_x = 310
        tab_y = 30
        for i, tab in enumerate(self.tabs):
            text = self.small_font.render(self.tab_names[i], True, BLACK if self.current_tab == tab else WHITE)
            rect = pygame.Rect(tab_x, tab_y, text.get_width() + 14, 30)
            if tab_x + rect.width > 780:
                tab_x = 310
                tab_y += 35
                rect.x = tab_x
                rect.y = tab_y
            pygame.draw.rect(self.screen, GREEN if self.current_tab == tab else GRAY, rect, border_radius=5)
            self.screen.blit(text, (rect.x + 7, rect.y + 7))
            self.active_buttons.append({'rect': rect, 'type': 'tab', 'tab': tab})
            tab_x += rect.width + 5
            
        self.draw_category_ui(self.current_tab, 310, 120)

        pygame.draw.rect(self.screen, GREEN, self.start_btn_rect, border_radius=10)
        start_text = self.font.render("START GAME", True, BLACK)
        self.screen.blit(start_text, (self.start_btn_rect.x + (self.start_btn_rect.width - start_text.get_width())//2, 
                                      self.start_btn_rect.y + (self.start_btn_rect.height - start_text.get_height())//2))

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

    def draw_pokemon_style_hp(self, surface, x, y, current_hp, max_hp, color, name, level="Lv.50"):
        pygame.draw.rect(surface, UI_BG, (x, y, 260, 75), border_radius=10)
        pygame.draw.rect(surface, UI_BORDER, (x, y, 260, 75), 4, border_radius=10)
        surface.blit(self.font.render(name, True, BLACK), (x + 15, y + 10))
        surface.blit(self.small_font.render(level, True, BLACK), (x + 195, y + 20))
        
        bar_x, bar_y, bar_w, bar_h = x + 45, y + 45, 190, 14
        pygame.draw.rect(surface, GRAY, (bar_x, bar_y, bar_w, bar_h), border_radius=5)
        pygame.draw.rect(surface, color, (bar_x, bar_y, bar_w * (current_hp/max_hp), bar_h), border_radius=5)
        pygame.draw.rect(surface, BLACK, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=5)
        surface.blit(self.small_font.render("HP", True, (200, 150, 50)), (x + 15, y + 43))

    def draw_battle(self):
        self.screen.blit(self.battle_bg, (0, 0))
        self.battle_float_timer += 0.05
        float_off = math.sin(self.battle_float_timer) * 10
        self.screen.blit(self.enemy_battle_img, (self.enemy_battle_pos[0], self.enemy_battle_pos[1] + float_off))
        self.screen.blit(self.player_battle_img, (self.player_battle_pos[0], self.player_battle_pos[1] - float_off))
        
        self.draw_pokemon_style_hp(self.screen, 50, 40, self.enemy.current_hp, self.enemy.max_hp, (220, 50, 50), self.enemy.name, "Lv.99")
        self.draw_pokemon_style_hp(self.screen, 480, 320, self.player.hp, 100, GREEN, "Player", "Lv.50")
        self.screen.blit(self.font.render(f"COMBO: x{self.player.combo_count}", True, BLACK), (495, 280))

        board_y, box, margin = 440, 45, 10
        start_x = (self.screen_width - ((box * 5) + (margin * 4))) // 2
        
        ui_surf = pygame.Surface((self.screen_width, 160))
        ui_surf.fill(UI_BORDER)
        self.screen.blit(ui_surf, (0, 440))

        for row in range(self.board.grid_size):
            if row < self.board.current_attempt - 2: continue
            draw_y = board_y + 15 + ((row - max(0, self.board.current_attempt - 2)) * (box + margin))
            
            if row < len(self.guess_history):
                word, colors = self.guess_history[row]
                for col in range(5):
                    x = start_x + (col * (box + margin))
                    c_val = GREEN if colors[col] == "GREEN" else YELLOW if colors[col] == "YELLOW" else GRAY
                    pygame.draw.rect(self.screen, c_val, (x, draw_y, box, box), border_radius=5)
                    txt = self.font.render(word[col], True, WHITE)
                    self.screen.blit(txt, txt.get_rect(center=(x + box//2, draw_y + box//2)))
            elif row == len(self.guess_history) and not self.gm.game_over:
                for col in range(5):
                    x = start_x + (col * (box + margin))
                    pygame.draw.rect(self.screen, BLACK, (x, draw_y, box, box), border_radius=5)
                    pygame.draw.rect(self.screen, WHITE, (x, draw_y, box, box), 2, border_radius=5)
                    if col < len(self.current_guess):
                        txt = self.font.render(self.current_guess[col], True, WHITE)
                        self.screen.blit(txt, txt.get_rect(center=(x + box//2, draw_y + box//2)))

        if self.gm.game_over:
            msg, color = ("BATTLE WON!", GREEN) if self.enemy.current_hp <= 0 else ("BLACKED OUT!", (255, 50, 50))
            txt = self.font.render(msg, True, color)
            self.screen.blit(txt, ((self.screen_width - txt.get_width())//2, 250))

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