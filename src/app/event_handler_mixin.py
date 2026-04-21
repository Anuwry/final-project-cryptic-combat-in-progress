import json
import math
import os
import random
import sys

import pygame

from src.config import BASE_DIR
from src.ui.constants import (
    ACCENT_RED_GLOW,
    CYAN_400,
    EMERALD_500,
    GOLD,
    STATE_BATTLE,
    STATE_MAIN_MENU,
    STATE_OVERWORLD,
    STATE_PAUSE,
    STATE_SAVE_SLOTS,
    STATE_SELECTION,
    STATE_SETTINGS,
    STATE_SHOP,
    STATE_UPGRADE,
    STATE_WARP,
    TEXT_PRIMARY,
)


class EventHandlerMixin:
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if hasattr(self, "game_map"):
                    self.game_map.save_map()
                self.save_game_data()
                pygame.quit()
                sys.exit()

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
                                self.save_mode = "load"
                                self.state = STATE_SAVE_SLOTS
                            elif text == "SETTINGS":
                                self.state = STATE_SETTINGS
                            elif text == "EXIT":
                                pygame.quit()
                                sys.exit()

            elif self.state == STATE_SAVE_SLOTS:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = STATE_MAIN_MENU
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if pygame.Rect(20, 20, 100, 40).collidepoint(mx, my):
                        self.state = STATE_MAIN_MENU

                    for i in range(1, 4):
                        data = self.saves[str(i)]
                        y = 100 + (i - 1) * 130
                        slot_rect = pygame.Rect(150, y, 500, 110)
                        del_rect = pygame.Rect(150 + 500 - 45, y + 35, 40, 40)

                        if data and del_rect.collidepoint(mx, my):
                            self.saves[str(i)] = None
                            self.delete_slot_progress(i)
                            path = os.path.join(BASE_DIR, "data", "saves.json")
                            with open(path, "w") as f:
                                json.dump(self.saves, f)
                        elif slot_rect.collidepoint(mx, my):
                            if self.saves[str(i)]:
                                self.load_game_data(i)

            elif self.state in [STATE_SETTINGS, STATE_PAUSE]:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.dragging_volume_slider = False
                    self.state = STATE_OVERWORLD if self.state == STATE_PAUSE else STATE_MAIN_MENU
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    layout = self.get_settings_layout()

                    if layout["slider"].inflate(0, 18).collidepoint(mx, my):
                        self.dragging_volume_slider = True
                        self.update_bgm_volume_from_pos(mx)

                    if layout["shake"].collidepoint(mx, my):
                        self.shake_enabled = not self.shake_enabled

                    if self.state == STATE_PAUSE:
                        if layout["resume"].collidepoint(mx, my):
                            self.state = STATE_OVERWORLD
                        elif layout["quit"].collidepoint(mx, my):
                            self.save_game_data()
                            self.state = STATE_MAIN_MENU
                    else:
                        if layout["back"].collidepoint(mx, my):
                            self.state = STATE_MAIN_MENU
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.dragging_volume_slider = False
                elif event.type == pygame.MOUSEMOTION and self.dragging_volume_slider:
                    self.update_bgm_volume_from_pos(event.pos[0])

            elif self.state == STATE_OVERWORLD:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos

                    if self.show_inventory and self.expanded_summary:
                        if self.get_expanded_summary_close_rect().collidepoint(mx, my) or not self.get_expanded_summary_panel_rect().collidepoint(mx, my):
                            self.expanded_summary = False
                        return

                    if self.show_inventory and self.expanded_graph_key:
                        if self.get_expanded_graph_close_rect().collidepoint(mx, my) or not self.get_expanded_graph_panel_rect().collidepoint(mx, my):
                            self.expanded_graph_key = None
                        return

                    if self.show_inventory:
                        for mode, rect in self.get_stats_tab_rects().items():
                            if rect.collidepoint(mx, my):
                                if mode == "summary":
                                    self.expanded_graph_key = None
                                    self.expanded_summary = True
                                else:
                                    self.stats_view_mode = "charts"
                                    self.expanded_summary = False
                                return

                        if self.stats_view_mode == "charts":
                            clicked_graph = self.get_stats_chart_at_pos(event.pos)
                            if clicked_graph:
                                self.expanded_graph_key = clicked_graph
                                return

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
                            if temp:
                                self.inventory[self.dragged_from_idx] = temp
                        else:
                            self.inventory[self.dragged_from_idx] = self.dragged_item
                        self.dragged_item = None
                        self.dragged_from_idx = -1

                elif event.type == pygame.KEYDOWN:
                    if self.show_inventory and self.expanded_summary and event.key == pygame.K_ESCAPE:
                        self.expanded_summary = False
                        return

                    if self.show_inventory and self.expanded_graph_key and event.key == pygame.K_ESCAPE:
                        self.expanded_graph_key = None
                        return

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

                        menu_active = hasattr(self, "nearby_interactables") and len(self.nearby_interactables) > 1
                        if menu_active and event.key == pygame.K_UP:
                            self.interact_index = (self.interact_index - 1) % len(self.nearby_interactables)
                        elif menu_active and event.key == pygame.K_DOWN:
                            self.interact_index = (self.interact_index + 1) % len(self.nearby_interactables)
                        elif event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_f):
                            if hasattr(self, "nearby_interactables") and self.nearby_interactables:
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
                            if not self.show_inventory:
                                self.expanded_graph_key = None
                                self.expanded_summary = False
                            if self.show_inventory:
                                self.load_stats_csv()
                                self.stats_view_mode = "charts"
                        elif pygame.K_1 <= event.key <= pygame.K_5:
                            self.use_item(event.key - pygame.K_1)

            elif self.state == STATE_WARP:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.state = STATE_OVERWORLD
                    elif event.key == pygame.K_1:
                        self.execute_warp(0, 0)
                    elif event.key == pygame.K_2:
                        self.execute_warp(self.last_normal_realm[0], self.last_normal_realm[1])
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if pygame.Rect(180, 230, 440, 45).collidepoint(mx, my):
                        self.execute_warp(0, 0)
                    elif pygame.Rect(180, 290, 440, 45).collidepoint(mx, my):
                        self.execute_warp(self.last_normal_realm[0], self.last_normal_realm[1])

            elif self.state == STATE_SHOP:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if hasattr(self, "shop_potion_rect") and self.shop_potion_rect.collidepoint(mx, my):
                        if self.gold >= 50 and self.add_item("potion", "Health Potion", "Heals 50 HP", 1):
                            self.gold -= 50
                    elif hasattr(self, "shop_scroll_rect") and self.shop_scroll_rect.collidepoint(mx, my):
                        if self.gold >= 50 and self.add_item("scroll", "Hint Scroll", "Reveals 1 letter", 1):
                            self.gold -= 50
                    elif hasattr(self, "shop_exit_rect") and self.shop_exit_rect.collidepoint(mx, my):
                        self.state = STATE_OVERWORLD
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN):
                        self.state = STATE_OVERWORLD
                    elif event.key == pygame.K_1:
                        if self.gold >= 50 and self.add_item("potion", "Health Potion", "Heals 50 HP", 1):
                            self.gold -= 50
                    elif event.key == pygame.K_2:
                        if self.gold >= 50 and self.add_item("scroll", "Hint Scroll", "Reveals 1 letter", 1):
                            self.gold -= 50

            elif self.state == STATE_UPGRADE:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if hasattr(self, "upg_ares_rect") and self.upg_ares_rect.collidepoint(mx, my):
                        self.base_atk += getattr(self, "current_reward_atk", 5)
                        self.player.base_attack = self.base_atk
                        self.save_game_data()
                        self.state = STATE_OVERWORLD
                    elif hasattr(self, "upg_demeter_rect") and self.upg_demeter_rect.collidepoint(mx, my):
                        self.player_max_hp += getattr(self, "current_reward_hp", 20)
                        self.player.hp = self.player_max_hp
                        self.save_game_data()
                        self.state = STATE_OVERWORLD
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.base_atk += getattr(self, "current_reward_atk", 5)
                        self.player.base_attack = self.base_atk
                        self.save_game_data()
                        self.state = STATE_OVERWORLD
                    elif event.key == pygame.K_2:
                        self.player_max_hp += getattr(self, "current_reward_hp", 20)
                        self.player.hp = self.player_max_hp
                        self.save_game_data()
                        self.state = STATE_OVERWORLD

            elif self.state == STATE_SELECTION:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.start_btn_rect.collidepoint(event.pos):
                        self.save_game_data()
                        self.state = STATE_OVERWORLD
                        return
                    for btn in self.active_buttons:
                        if btn["rect"].collidepoint(event.pos):
                            if btn["type"] == "tab":
                                self.current_tab = btn["tab"]
                            elif btn["type"] == "item":
                                self.selections[self.current_tab] = btn["idx"]
                                self.update_player_visuals()
                            elif btn["type"] == "prev":
                                self.pages[self.current_tab] = max(0, self.pages[self.current_tab] - 1)
                            elif btn["type"] == "next":
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

                                tier = self.current_statue.data.get("tier", "Follower")
                                if tier == "Boss":
                                    self.current_reward_atk = random.randint(8, 15)
                                    self.current_reward_hp = random.randint(40, 60)
                                    self.add_item("compass", "Warp Scroll", "Teleports you safely", 1)
                                    self.spawn_floating_text("+1 Warp Scroll", 400, 200, CYAN_400)
                                    k = f"{self.realm_x}_{self.realm_y}"
                                    self.defeated_bosses[k] = self.game_map.god_theme
                                elif tier == "Apostle":
                                    self.current_reward_atk = random.randint(4, 8)
                                    self.current_reward_hp = random.randint(20, 35)
                                elif tier == "Zealot":
                                    self.current_reward_atk = random.randint(2, 5)
                                    self.current_reward_hp = random.randint(10, 20)
                                else:
                                    self.current_reward_atk = random.randint(1, 3)
                                    self.current_reward_hp = random.randint(5, 10)

                                self.save_game_data()
                                self.state = STATE_UPGRADE
                            else:
                                self.return_to_sanctuary_after_defeat()
                    else:
                        if event.key == pygame.K_ESCAPE:
                            self.state = STATE_OVERWORLD
                        elif event.key == pygame.K_1:
                            px = self.player_battle_pos[0] + 80 + random.randint(-20, 20)
                            py = self.player_battle_pos[1] - 20 + random.randint(-15, 15)
                            potion_idx = next((i for i, item in enumerate(self.inventory) if item and item["id"] == "potion"), None)
                            if potion_idx is not None:
                                if self.player.hp < self.player_max_hp:
                                    self.player.hp = min(self.player_max_hp, self.player.hp + 50)
                                    self.spawn_floating_text("+50 HP", px, py, EMERALD_500, "small")
                                    self.inventory[potion_idx]["qty"] -= 1
                                    if self.inventory[potion_idx]["qty"] <= 0:
                                        self.inventory[potion_idx] = None
                                else:
                                    self.spawn_floating_text("HP is Full", px, py, TEXT_PRIMARY, "small")
                            else:
                                self.spawn_floating_text("No Potions", px, py, ACCENT_RED_GLOW, "small")
                        elif event.key == pygame.K_2:
                            px = self.player_battle_pos[0] + 80 + random.randint(-20, 20)
                            py = self.player_battle_pos[1] - 20 + random.randint(-15, 15)
                            scroll_idx = next((i for i, item in enumerate(self.inventory) if item and item["id"] == "scroll"), None)
                            if scroll_idx is not None:
                                for idx, c in enumerate(self.target_word):
                                    if self.green_letters[idx] is None:
                                        self.green_letters[idx] = c
                                        self.spawn_floating_text("Hint Used!", px, py, GOLD, "small")
                                        self.inventory[scroll_idx]["qty"] -= 1
                                        if self.inventory[scroll_idx]["qty"] <= 0:
                                            self.inventory[scroll_idx] = None
                                        break
                            else:
                                self.spawn_floating_text("No Scrolls", px, py, ACCENT_RED_GLOW, "small")
                        elif event.unicode.isascii() and event.unicode.isalpha() and len(self.current_guess) < 5:
                            self.current_guess += event.unicode.upper()
                            self.gm.keystroke_count += 1
                        elif event.key == pygame.K_BACKSPACE:
                            self.current_guess = self.current_guess[:-1]
                            self.gm.keystroke_count += 1
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and len(self.current_guess) == 5:
                            self.gm.keystroke_count += 1
                            self.submit_guess()

        self.sync_music()
