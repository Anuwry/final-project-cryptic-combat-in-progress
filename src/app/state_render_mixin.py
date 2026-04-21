import math
import random

import pygame

from src.ui.constants import (
    ACCENT_RED_GLOW,
    BG_CARD,
    BG_DARK,
    BLACK,
    BORDER_SUBTLE,
    CYAN_400,
    GOLD,
    GOLD_DIM,
    GOLD_LIGHT,
    TEXT_DIM,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WHITE,
)


class StateRenderMixin:
    def draw_sealed_auras(self):
        aura_colors = {
            "Zeus": (201, 162, 39, 100),
            "Poseidon": (50, 100, 255, 100),
            "Hades": (180, 50, 255, 100),
            "Athena": (200, 200, 200, 100),
            "Ares": (196, 60, 60, 100),
            "Apollo": (232, 200, 74, 100),
            "Hermes": (50, 255, 100, 100),
        }

        if f"{self.realm_x}_{self.realm_y - 1}" in self.defeated_bosses:
            god = self.defeated_bosses[f"{self.realm_x}_{self.realm_y - 1}"]
            color = aura_colors.get(god, (255, 255, 255, 100))
            s = pygame.Surface((self.screen_width, 60), pygame.SRCALPHA)
            for i in range(60):
                alpha = int(color[3] * (1 - i / 60))
                pygame.draw.line(s, (*color[:3], alpha), (0, i), (self.screen_width, i))
            self.screen.blit(s, (0, 0))

        if f"{self.realm_x}_{self.realm_y + 1}" in self.defeated_bosses:
            god = self.defeated_bosses[f"{self.realm_x}_{self.realm_y + 1}"]
            color = aura_colors.get(god, (255, 255, 255, 100))
            s = pygame.Surface((self.screen_width, 60), pygame.SRCALPHA)
            for i in range(60):
                alpha = int(color[3] * (i / 60))
                pygame.draw.line(s, (*color[:3], alpha), (0, i), (self.screen_width, i))
            self.screen.blit(s, (0, self.screen_height - 60))

        if f"{self.realm_x - 1}_{self.realm_y}" in self.defeated_bosses:
            god = self.defeated_bosses[f"{self.realm_x - 1}_{self.realm_y}"]
            color = aura_colors.get(god, (255, 255, 255, 100))
            s = pygame.Surface((60, self.screen_height), pygame.SRCALPHA)
            for i in range(60):
                alpha = int(color[3] * (1 - i / 60))
                pygame.draw.line(s, (*color[:3], alpha), (i, 0), (i, self.screen_height))
            self.screen.blit(s, (0, 0))

        if f"{self.realm_x + 1}_{self.realm_y}" in self.defeated_bosses:
            god = self.defeated_bosses[f"{self.realm_x + 1}_{self.realm_y}"]
            color = aura_colors.get(god, (255, 255, 255, 100))
            s = pygame.Surface((60, self.screen_height), pygame.SRCALPHA)
            for i in range(60):
                alpha = int(color[3] * (i / 60))
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

        if len(self.nearby_interactables) > 1:
            box_w = 260
            box_h = 20 + (30 * len(self.nearby_interactables))
            prompt_box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            pygame.draw.rect(prompt_box, (15, 18, 30, 215), prompt_box.get_rect())
            pygame.draw.rect(prompt_box, GOLD_DIM, prompt_box.get_rect(), 1)

            px = player_screen_x - box_w // 2 + 32
            py = player_screen_y - box_h - 10
            self.screen.blit(prompt_box, (px, py))

            for i, o in enumerate(self.nearby_interactables):
                is_sel = i == self.interact_index
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

            npc_name = self.current_npc.data.get("name", "Stranger")
            npc_text = self.current_npc.data.get("dialogue", "Hello there!")

            self.screen.blit(self.name_font.render(npc_name, True, GOLD), (dialogue_box.x + 20, dialogue_box.y + 15))
            self.screen.blit(self.small_font.render(npc_text, True, TEXT_PRIMARY), (dialogue_box.x + 20, dialogue_box.y + 50))

            action_txt = "[SPACE] to Shop   |   [ESC] Leave" if self.opens_shop(self.current_npc) else "[SPACE] to Continue   |   [ESC] Leave"
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
        else:
            box_width = 0

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
            f = self.tiny_font if t.get("font_type") == "tiny" else (self.small_font if t.get("font_type") == "small" else self.combo_font)
            txt_str = str(t["text"])
            txt_surf = f.render(txt_str, True, t["color"])
            shadow = f.render(txt_str, True, BLACK)

            draw_x = t["x"] - txt_surf.get_width() // 2
            self.screen.blit(shadow, (draw_x + 1, t["y"] + 1))
            self.screen.blit(shadow, (draw_x - 1, t["y"] - 1))
            self.screen.blit(txt_surf, (draw_x, t["y"]))

            t["y"] -= 1.5 if t.get("font_type") in ["small", "tiny"] else 2
            t["timer"] -= 1
            if t["timer"] <= 0:
                self.floating_texts.remove(t)

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

        potions_owned = sum([item["qty"] for item in self.inventory if item and item["id"] == "potion"])
        scrolls_owned = sum([item["qty"] for item in self.inventory if item and item["id"] == "scroll"])

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

        atk_title = self.btn_font.render("[1] Power", True, GOLD_LIGHT if a_hover else TEXT_PRIMARY)
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

        hp_title = self.btn_font.render("[2] Vitality", True, GOLD_LIGHT if d_hover else TEXT_PRIMARY)
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
        if ratio > 0:
            pygame.draw.rect(surface, fill, (bx, by, int(bw * ratio), bh))

    def draw_battle(self):
        shake_x = random.randint(-self.shake_amount, self.shake_amount) if self.shake_timer > 0 else 0
        shake_y = random.randint(-self.shake_amount, self.shake_amount) if self.shake_timer > 0 else 0
        if self.shake_timer > 0:
            self.shake_timer -= 1

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
        else:
            self.p_anim_x = 0

        if self.e_anim_timer > 0:
            self.e_anim_x -= 15 if self.e_anim_timer > 10 else 15
            self.e_anim_timer -= 1
        else:
            self.e_anim_x = 0

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
            f = self.tiny_font if t.get("font_type") == "tiny" else (self.small_font if t.get("font_type") == "small" else self.combo_font)
            txt_str = str(t["text"])
            txt_surf = f.render(txt_str, True, t["color"])
            shadow = f.render(txt_str, True, BLACK)
            draw_x = t["x"] - txt_surf.get_width() // 2
            battle_surf.blit(shadow, (draw_x + 1, t["y"] + 1))
            battle_surf.blit(shadow, (draw_x - 1, t["y"] - 1))
            battle_surf.blit(txt_surf, (draw_x, t["y"]))
            t["y"] -= 1.5 if t.get("font_type") in ["small", "tiny"] else 2
            t["timer"] -= 1
            if t["timer"] <= 0:
                self.floating_texts.remove(t)

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

        total_potions = sum([item["qty"] for item in self.inventory if item and item["id"] == "potion"])
        total_scrolls = sum([item["qty"] for item in self.inventory if item and item["id"] == "scroll"])

        if not self.gm.game_over:
            flee_surf = self.tiny_font.render(f"PRESS [ESC] TO FLEE (LOST COMBO) | [1] POTION ({total_potions}) | [2] HINT SCROLL ({total_scrolls})", True, TEXT_DIM)
            battle_surf.blit(flee_surf, (20, board_start_y - 25))

        box, m = 50, 10
        cx = (800 - (box * 5 + m * 4)) // 2
        cy = board_start_y + 45

        if self.board.current_attempt >= 4 and not self.gm.game_over:
            hint = f"Ehm.. maybe it's: '{self.dictionary.get_current_hint()}'"
            if len(hint) > 75:
                hint = hint[:72] + "..."
            hs = self.small_font.render(hint, True, BLACK)
            br = hs.get_rect(midbottom=(self.player_battle_pos[0] + 120, self.player_battle_pos[1] - 20))
            pygame.draw.rect(battle_surf, WHITE, br.inflate(20, 15))
            pygame.draw.rect(battle_surf, GOLD, br.inflate(20, 15), 2)
            battle_surf.blit(hs, br)

        battle_surf.blit(self.small_font.render("ABSENT", True, TEXT_SECONDARY), (40, board_start_y + 15))
        absent_x, absent_y = 40, board_start_y + 40
        for i, char in enumerate(sorted(list(self.absent_letters))):
            r, c = i // 6, i % 6
            pygame.draw.rect(battle_surf, BG_DARK, (absent_x + c * 25, absent_y + r * 25, 20, 20))
            battle_surf.blit(self.small_font.render(char, True, TEXT_DIM), (absent_x + c * 25 + 6, absent_y + r * 25 + 3))

        for col in range(5):
            x = cx + col * (box + m)
            char = self.current_guess[col] if col < len(self.current_guess) else ""
            is_active = col == len(self.current_guess) and not self.gm.game_over

            pygame.draw.rect(battle_surf, (30, 35, 50) if char else BG_DARK, (x, cy, box, box))

            if char:
                t = self.font.render(char, True, WHITE)
                t_rect = t.get_rect(center=(x + box // 2, cy + box // 2))
                battle_surf.blit(t, t_rect)

            pygame.draw.rect(battle_surf, GOLD if is_active else BORDER_SUBTLE, (x, cy, box, box), 2 if not is_active else 3)

        battle_surf.blit(self.small_font.render("BEST KNOWN", True, GOLD_LIGHT), (580, board_start_y + 15))
        right_x, right_y = 580, board_start_y + 40
        for i in range(5):
            rx = right_x + i * 30
            c_char = self.green_letters[i]
            pygame.draw.rect(battle_surf, GOLD if c_char else BG_DARK, (rx, right_y, 25, 25))
            if c_char:
                battle_surf.blit(self.small_font.render(c_char, True, BLACK), (rx + 7, right_y + 5))

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
