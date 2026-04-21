import math
import os
import random

import pygame

from src.config import BASE_DIR
from src.ui.constants import (
    ACCENT_RED,
    ACCENT_RED_GLOW,
    BG_DARK,
    GOLD,
    GOLD_DIM,
    TEXT_PRIMARY,
    WHITE,
    STATE_BATTLE,
    STATE_MAIN_MENU,
    STATE_OVERWORLD,
    STATE_SAVE_SLOTS,
    STATE_SELECTION,
    STATE_SETTINGS,
    STATE_SHOP,
    STATE_UPGRADE,
    STATE_WARP,
)
from src.ui.spritesheet import SpriteSheet


class AppSetupMixin:
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
            statue_tier = self.current_statue.data.get("tier") if self.current_statue else None
            if statue_tier == "Boss" and self.current_statue:
                self.play_god_bgm(self.current_statue.data.get("god", ""))
            else:
                self.play_music_track("general_battle")
            return

        if self.state in (STATE_OVERWORLD, STATE_SHOP, STATE_UPGRADE, STATE_WARP):
            self.play_music_track("overworld")

    def load_image_safely(self, path, size, fallback_color):
        if os.path.exists(path):
            try:
                return pygame.transform.scale(pygame.image.load(path).convert_alpha(), size)
            except Exception:
                pass
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
        self.item_icons["compass"] = compass_img

        potion_img = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.rect(potion_img, ACCENT_RED_GLOW, (10, 14, 12, 14))
        pygame.draw.rect(potion_img, WHITE, (12, 6, 8, 8))
        pygame.draw.rect(potion_img, BG_DARK, (10, 14, 12, 14), 2)
        pygame.draw.rect(potion_img, BG_DARK, (12, 6, 8, 8), 2)
        self.item_icons["potion"] = potion_img

        scroll_img = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.rect(scroll_img, TEXT_PRIMARY, (8, 8, 16, 20))
        pygame.draw.rect(scroll_img, GOLD_DIM, (6, 12, 20, 5))
        pygame.draw.rect(scroll_img, BG_DARK, (8, 8, 16, 20), 2)
        self.item_icons["scroll"] = scroll_img

    def add_item(self, item_id, name, desc, qty=1):
        for slot in self.inventory:
            if slot and slot["id"] == item_id and slot.get("qty", 1) > 0:
                slot["qty"] += qty
                return True
        for i in range(len(self.inventory)):
            if self.inventory[i] is None:
                self.inventory[i] = {"id": item_id, "name": name, "desc": desc, "qty": qty}
                return True
        return False

    def generate_box(self, c1, r1, c2, r2):
        return [(c, r) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]

    def filter_empty(self, coords_list):
        valid = []
        for c, r in coords_list:
            img = self.sprite_sheet.get_image_by_grid(c, r, 1)
            if img.get_bounding_rect().width > 0:
                valid.append((c, r))
        return valid

    def setup_selection(self):
        player_bases = [(1, 0), (1, 1), (1, 2)]
        self.enemy_bases = player_bases
        self.options = {
            "base": player_bases,
            "pants": [None] + self.filter_empty(self.generate_box(2, 0, 4, 9)),
            "armor": [None] + self.filter_empty(self.generate_box(5, 0, 17, 9)),
            "hair": [None] + self.filter_empty(self.generate_box(18, 0, 25, 7) + self.generate_box(18, 8, 20, 11)),
            "hat": [None] + self.filter_empty(self.generate_box(29, 0, 31, 8)),
            "shield": [None] + self.filter_empty(self.generate_box(36, 0, 39, 8)),
            "weapon": [None] + self.filter_empty(self.generate_box(41, 0, 55, 4) + self.generate_box(41, 5, 54, 9)),
        }
        self.tabs = ["base", "hair", "hat", "armor", "pants", "weapon", "shield"]
        self.tab_names = ["BODY", "HAIR", "HAT", "ARMOR", "PANTS", "WEAPON", "SHIELD"]
        self.current_tab = "base"
        self.selections = {k: 0 for k in self.tabs}
        self.pages = {k: 0 for k in self.tabs}
        self.items_per_page = 30
        self.start_btn_rect = pygame.Rect(495, 495, 260, 50)
        self.active_buttons = []
        self.update_player_visuals()

    def update_player_visuals(self):
        layers = [self.options[k][self.selections[k]] for k in ["base", "pants", "armor", "hair", "hat", "shield", "weapon"]]
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
        if not self.shake_enabled:
            return
        self.shake_amount = intensity
        self.shake_timer = duration
