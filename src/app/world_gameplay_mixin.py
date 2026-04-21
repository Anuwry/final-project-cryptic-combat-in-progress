import os
import random

import pygame

from src.entities import Enemy
from src.map_loader import GameMap
from src.ui.constants import (
    ACCENT_RED_GLOW,
    CYAN_400,
    EMERALD_500,
    GOLD,
    GOLD_LIGHT,
    STATE_BATTLE,
    STATE_OVERWORLD,
    STATE_WARP,
    TEXT_PRIMARY,
)
from src.config import BASE_DIR


class WorldGameplayMixin:
    def change_realm(self, target_x, target_y, exit_side):
        self.game_map.save_map()

        if not self.game_map.is_boss_realm:
            self.last_normal_realm = (self.realm_x, self.realm_y)

        target_level = abs(target_x) + abs(target_y) + 1
        self.realm_x = target_x
        self.realm_y = target_y
        self.current_level = target_level
        self.game_map = GameMap(self.realm_x, self.realm_y, map_root=self.get_active_map_root())

        self.total_statues = len(self.game_map.get_statues())
        self.statues_collected = len([s for s in self.game_map.get_statues() if s.collected])

        map_pixel_width = self.game_map.width * 64
        map_pixel_height = self.game_map.height * 64

        if self.game_map.is_boss_realm:
            self.map_player_pos = list(self.game_map.spawn_point)
        else:
            if exit_side == "right":
                self.map_player_pos = [64, 13 * 64]
            elif exit_side == "left":
                self.map_player_pos = [map_pixel_width - 128, 13 * 64]
            elif exit_side == "bottom":
                self.map_player_pos = [15 * 64, 64]
            elif exit_side == "top":
                self.map_player_pos = [15 * 64, map_pixel_height - 128]
            elif exit_side == "teleport":
                self.map_player_pos = [15 * 64, 15 * 64]

        self.game_map.ensure_safe_spawn(self.map_player_pos[0], self.map_player_pos[1])
        self.facing_left_overworld = False
        self.game_map.camera_offset = [0, 0]
        self.game_map.target_camera_offset = [0, 0]
        self.save_game_data()

    def execute_warp(self, tx, ty):
        item = self.inventory[self.pending_warp_idx]
        item["qty"] -= 1
        if item["qty"] <= 0:
            self.inventory[self.pending_warp_idx] = None
        self.change_realm(tx, ty, "teleport")
        self.state = STATE_OVERWORLD

    def return_to_sanctuary_after_defeat(self):
        self.player.hp = self.player_max_hp
        self.change_realm(0, 0, "teleport")
        self.last_normal_realm = (0, 0)
        self.state = STATE_OVERWORLD

    def spawn_floating_text(self, text, x, y, color, font_type="large"):
        self.floating_texts.append({"text": text, "x": x, "y": y, "timer": 45, "color": color, "font_type": font_type})

    def randomize_enemy(self):
        god = self.current_statue.data.get("god", "Unknown")
        tier = self.current_statue.data.get("tier", "Follower")

        role = "avatar" if tier.lower() == "boss" else tier.lower()
        bg_name = f"{god.lower()}_{role}.png"
        bg_path = os.path.join(BASE_DIR, "assets", "images", bg_name)

        self.current_battle_bg = None
        if os.path.exists(bg_path):
            try:
                img = pygame.image.load(bg_path).convert()
                self.current_battle_bg = pygame.transform.scale(img, (800, 600))
            except Exception:
                pass

        if tier == "Boss":
            max_hp = 300 + (self.current_level * 50)
            atk = 20 + (self.current_level * 2)
            name = f"Avatar of {god}"
            self.enemy_reward = 150
        elif tier == "Apostle":
            max_hp = 150 + (self.current_level * 15)
            atk = 15 + self.current_level
            name = f"{god}'s Apostle"
            self.enemy_reward = 80
        elif tier == "Zealot":
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
            random.choice(self.options["base"]),
            random.choice(self.options["pants"]),
            random.choice(self.options["armor"][1:]),
            random.choice(self.options["hair"]),
            random.choice(self.options["hat"]),
            random.choice(self.options["shield"]),
            random.choice(self.options["weapon"][1:]),
        ]
        self.enemy_battle_img = self.sprite_sheet.get_equipped_image_by_grid(enemy_layers, 10)
        self.target_word = self.dictionary.generate_random_word()
        self.battle_float_timer, self.crit_timer, self.floating_texts = 0, 0, []
        self.board.current_attempt, self.guess_history, self.current_guess = 1, [], ""
        self.absent_letters, self.yellow_letters = set(), set()
        self.green_letters = [None] * 5

    def use_item(self, hotbar_idx):
        item = self.inventory[hotbar_idx]
        if not item:
            return

        slot_size = 40
        padding = 6
        start_x = (800 - (5 * slot_size + 4 * padding)) // 2
        px = start_x + hotbar_idx * (slot_size + padding) + (slot_size // 2)
        py = 515

        if item["id"] == "compass":
            if self.state == STATE_OVERWORLD:
                self.pending_warp_idx = hotbar_idx
                self.state = STATE_WARP
            else:
                self.spawn_floating_text("Can't use now", px, py, ACCENT_RED_GLOW, "tiny")
        elif item["id"] == "potion":
            if self.player.hp < self.player_max_hp:
                heal_amount = 50
                self.player.hp = min(self.player_max_hp, self.player.hp + heal_amount)
                self.spawn_floating_text(f"+{heal_amount} HP", px, py, EMERALD_500, "tiny")
                item["qty"] -= 1
                if item["qty"] <= 0:
                    self.inventory[hotbar_idx] = None
            else:
                self.spawn_floating_text("HP is Full", px, py, TEXT_PRIMARY, "tiny")
        elif item["id"] == "scroll":
            if self.state == STATE_BATTLE and not self.gm.game_over:
                for idx, c in enumerate(self.target_word):
                    if self.green_letters[idx] is None:
                        self.green_letters[idx] = c
                        self.spawn_floating_text("Hint Used!", px, py, GOLD_LIGHT, "tiny")
                        item["qty"] -= 1
                        if item["qty"] <= 0:
                            self.inventory[hotbar_idx] = None
                        break
            else:
                self.spawn_floating_text("Can't use now", px, py, ACCENT_RED_GLOW, "tiny")

    def get_hovered_slot(self, pos):
        mx, my = pos
        slot_size = 40
        padding = 6

        start_x_hb = (800 - (5 * slot_size + 4 * padding)) // 2
        hotbar_start_y = 540
        for i in range(5):
            if pygame.Rect(start_x_hb + i * (slot_size + padding), hotbar_start_y, slot_size, slot_size).collidepoint(mx, my):
                return i

        if self.show_inventory:
            panel_x, panel_y = 40, 50
            panel_w = 340
            start_x_inv = panel_x + (panel_w - (5 * slot_size + 4 * padding)) // 2
            inv_start_y = panel_y + 90

            for i in range(40):
                r, c = i // 5, i % 5
                idx = 5 + (self.inv_scroll * 5) + i
                if idx < len(self.inventory):
                    rect = pygame.Rect(start_x_inv + c * (slot_size + padding), inv_start_y + r * (slot_size + padding), slot_size, slot_size)
                    if rect.collidepoint(mx, my):
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
        return bool(obj) and (obj.type == "shop" or obj.data.get("name") == "Merchant")

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

            self.p_anim_timer = 20
            self.trigger_shake(8, 15)

            px = self.enemy_battle_pos[0] + 80 + random.randint(-20, 20)
            py = self.enemy_battle_pos[1] - 20 + random.randint(-15, 15)
            self.spawn_floating_text(f"-{damage}", px, py, ACCENT_RED_GLOW)

            if self.player.combo_count > 1:
                self.crit_timer = 60

            if self.gm.check_win_condition(self.enemy):
                self.gm.game_over = True
            else:
                self.reset_for_next_word()
        else:
            if self.board.current_attempt > self.board.grid_size:
                self.player.combo_count = 0

                self.enemy_hit_count += 1
                is_crit = self.enemy_hit_count % 3 == 0

                base_damage = self.enemy.attack_power
                final_damage = base_damage * 2 if is_crit else base_damage

                self.player.hp -= final_damage
                if self.player.hp < 0:
                    self.player.hp = 0

                self.e_anim_timer = 20
                self.trigger_shake(20 if is_crit else 15, 20)

                px = self.player_battle_pos[0] + 80 + random.randint(-20, 20)
                py = self.player_battle_pos[1] - 20 + random.randint(-15, 15)

                if is_crit:
                    self.spawn_floating_text("CRITICAL HIT!", px, py - 20, ACCENT_RED_GLOW, "small")
                self.spawn_floating_text(f"-{final_damage}", px, py, ACCENT_RED_GLOW)

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

    def update_overworld(self):
        keys = pygame.key.get_pressed()
        self.is_moving = False

        old_x, old_y = self.map_player_pos[0], self.map_player_pos[1]
        menu_active = hasattr(self, "nearby_interactables") and len(self.nearby_interactables) > 1 and not self.showing_dialogue

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
            exit_side = ""

            if self.map_player_pos[0] > map_pixel_width - 64 - edge_threshold:
                target_rx += 1
                will_change = True
                exit_side = "right"
            elif self.map_player_pos[0] < edge_threshold:
                target_rx -= 1
                will_change = True
                exit_side = "left"
            elif self.map_player_pos[1] > map_pixel_height - 64 - edge_threshold:
                target_ry += 1
                will_change = True
                exit_side = "bottom"
            elif self.map_player_pos[1] < edge_threshold:
                target_ry -= 1
                will_change = True
                exit_side = "top"

        if will_change:
            target_key = f"{target_rx}_{target_ry}"
            if target_key in self.defeated_bosses:
                self.map_player_pos[0] = old_x
                self.map_player_pos[1] = old_y
                px = self.map_player_pos[0] + self.game_map.camera_offset[0] + 32
                py = self.map_player_pos[1] + self.game_map.camera_offset[1] - 20
                if random.random() < 0.1:
                    self.spawn_floating_text("PATH SEALED BY DIVINE AURA", px, py, ACCENT_RED_GLOW, "small")
                return

            self.change_realm(target_rx, target_ry, exit_side)
            return

        self.game_map.update_camera(self.map_player_pos[0] + 32, self.map_player_pos[1] + 32, self.screen_width, self.screen_height)
        self.move_timer_overworld = self.move_timer_overworld + 0.2 if self.is_moving else 0

        player_rect = pygame.Rect(self.map_player_pos[0], self.map_player_pos[1], 64, 64)
        current_in_range = self.get_nearby_interactables(player_rect)
        if not hasattr(self, "nearby_interactables") or set(current_in_range) != set(self.nearby_interactables):
            self.nearby_interactables = current_in_range
            self.interact_index = 0
