import math
import os
import random

import pygame

from src.app.app_setup_mixin import AppSetupMixin
from src.app.event_handler_mixin import EventHandlerMixin
from src.app.menu_render_mixin import MenuRenderMixin
from src.app.save_data_mixin import SaveDataMixin
from src.app.state_render_mixin import StateRenderMixin
from src.app.stats_inventory_mixin import StatsInventoryMixin
from src.app.world_gameplay_mixin import WorldGameplayMixin
from src.config import BASE_DIR
from src.game_manager import GameManager
from src.map_loader import GameMap
from src.mechanics import TileBoard, WordDictionary
from src.ui.constants import *


class PygameApp(
    MenuRenderMixin,
    SaveDataMixin,
    StatsInventoryMixin,
    AppSetupMixin,
    WorldGameplayMixin,
    EventHandlerMixin,
    StateRenderMixin,
):
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
            self.particles.append(
                {
                    "x": random.uniform(0, 800),
                    "y": random.uniform(0, 600),
                    "vx": random.uniform(-0.2, 0.2),
                    "vy": random.uniform(-0.5, -0.1),
                    "size": random.uniform(1.5, 3.5),
                    "pulse": random.uniform(0, math.pi * 2),
                }
            )

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
        self.sync_slot_file_paths()
        self.dictionary = WordDictionary("normal")
        self.board = TileBoard()

        self.item_icons = {}
        self.inventory = [None] * 50
        self.show_inventory = False
        self.inv_scroll = 0
        self.dragged_item = None
        self.dragged_from_idx = -1
        self.dragging_volume_slider = False

        self.stats_data = {"time": [], "attempts": [], "combo": [], "damage": [], "keys": []}
        self.expanded_graph_key = None
        self.expanded_summary = False
        self.stats_view_mode = "charts"

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

        self.game_map = GameMap(self.realm_x, self.realm_y, False, map_root=self.get_active_map_root())
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

        self.setup_overworld()
        self.sync_music()

    def run(self):
        clock = pygame.time.Clock()
        while True:
            self.handle_events()
            self.sync_music()
            if self.state == STATE_MAIN_MENU:
                self.draw_main_menu()
            elif self.state == STATE_SAVE_SLOTS:
                self.draw_save_slots()
            elif self.state == STATE_SELECTION:
                self.draw_selection()
            elif self.state == STATE_OVERWORLD:
                self.update_overworld()
                self.draw_overworld()
            elif self.state == STATE_BATTLE:
                self.draw_battle()
            elif self.state == STATE_SHOP:
                self.draw_shop()
            elif self.state == STATE_UPGRADE:
                self.draw_upgrade()
            elif self.state == STATE_WARP:
                self.draw_warp_menu()
            elif self.state in [STATE_PAUSE, STATE_SETTINGS]:
                self.draw_settings()
            pygame.display.flip()
            clock.tick(60)
