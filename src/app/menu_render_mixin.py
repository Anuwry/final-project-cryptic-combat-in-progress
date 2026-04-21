import math
import random
import time

import pygame

from src.ui.constants import (
    ACCENT_RED,
    ACCENT_RED_GLOW,
    BG_DARK,
    BG_DEEP,
    BORDER_SUBTLE,
    CYAN_400,
    GOLD,
    GOLD_DIM,
    GOLD_LIGHT,
    RED_500,
    SLATE_400,
    SLATE_700,
    SLATE_800,
    TEXT_DIM,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WHITE,
    STATE_PAUSE,
)


class MenuRenderMixin:
    def draw_particles(self):
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["pulse"] += 0.02
            if p["y"] < -10:
                p["y"] = 610
                p["x"] = random.uniform(0, 800)
            if p["x"] < -10:
                p["x"] = 810
            if p["x"] > 810:
                p["x"] = -10

            alpha = int(100 + 100 * math.sin(p["pulse"]))
            alpha = max(0, min(255, alpha))

            s = pygame.Surface((int(p["size"] * 4), int(p["size"] * 4)), pygame.SRCALPHA)
            pygame.draw.circle(s, (201, 162, 39, int(alpha * 0.3)), (int(p["size"] * 2), int(p["size"] * 2)), int(p["size"] * 2))
            pygame.draw.circle(s, (232, 200, 74, alpha), (int(p["size"] * 2), int(p["size"] * 2)), max(1, int(p["size"] * 0.5)))
            self.screen.blit(s, (int(p["x"]), int(p["y"])))

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
        if is_danger:
            t_color = ACCENT_RED_GLOW

        t_surf = self.btn_font.render(text, True, t_color)
        s.blit(t_surf, (w // 2 - t_surf.get_width() // 2, h // 2 - t_surf.get_height() // 2))

        self.screen.blit(s, (vx, y))
        return rect

    def draw_main_menu(self):
        self.screen.fill(BG_DEEP)
        self.draw_particles()

        pulse = abs(math.sin(time.time() * 2))
        title = self.title_font.render("CRYPTIC COMBAT", True, GOLD)
        glow = self.title_font.render("CRYPTIC COMBAT", True, (int(201 * 0.5 * pulse), int(162 * 0.5 * pulse), int(39 * 0.5 * pulse)))
        tx = self.screen_width // 2 - title.get_width() // 2
        self.screen.blit(glow, (tx, 100))
        self.screen.blit(title, (tx, 100))

        sub = self.small_font.render("I N T O   T H E   U N K N O W N", True, TEXT_SECONDARY)
        self.screen.blit(sub, (self.screen_width // 2 - sub.get_width() // 2, 170))

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
            self.draw_styled_btn(text, rect.x, rect.y, rect.width, rect.height, is_hover, text == "EXIT")

    def draw_save_slots(self):
        self.screen.fill(BG_DEEP)
        self.draw_particles()

        title_surf = self.name_font.render("CHARACTERS", True, GOLD)
        title_x = (self.screen_width // 2) - (title_surf.get_width() // 2)
        self.screen.blit(title_surf, (title_x, 40))

        mx, my = pygame.mouse.get_pos()
        b_rect = pygame.Rect(20, 20, 100, 40)
        b_hover = b_rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (255, 255, 255, 20) if b_hover else (0, 0, 0, 0), b_rect)
        self.screen.blit(self.btn_font.render("< BACK", True, TEXT_PRIMARY), (30, 30))

        for i in range(1, 4):
            data = self.saves[str(i)]
            y = 100 + (i - 1) * 130
            rect = pygame.Rect(150, y, 500, 110)
            del_rect = pygame.Rect(150 + 500 - 45, y + 35, 40, 40)

            hover = rect.collidepoint(mx, my)
            slot_surf = pygame.Surface((500, 110), pygame.SRCALPHA)
            bg_col = (22, 25, 38, 240) if hover else (15, 18, 30, 200)
            pygame.draw.rect(slot_surf, bg_col, slot_surf.get_rect())
            pygame.draw.rect(slot_surf, GOLD if hover else BORDER_SUBTLE, slot_surf.get_rect(), 2)
            self.screen.blit(slot_surf, (150, y))

            if data:
                self.screen.blit(self.name_font.render(f"SLOT {i} - Level {data.get('level', 1)}", True, GOLD), (170, y + 25))
                self.screen.blit(self.small_font.render(f"HP: {data.get('hp')}/{data.get('max_hp')} | ATK: {data.get('base_atk')} | GOLD: {data.get('gold')}G", True, TEXT_PRIMARY), (170, y + 65))

                d_hover = del_rect.collidepoint(mx, my)
                pygame.draw.rect(self.screen, ACCENT_RED_GLOW if d_hover else ACCENT_RED, del_rect)
                pygame.draw.rect(self.screen, WHITE, del_rect, 1)
                self.screen.blit(self.btn_font.render("X", True, WHITE), (del_rect.centerx - 7, del_rect.centery - 10))
            else:
                t = self.name_font.render(f"SLOT {i} - EMPTY", True, TEXT_DIM)
                self.screen.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))

    def get_settings_layout(self):
        box_w, box_h = 460, 420
        bx = 400 - box_w // 2
        by = 100
        inner_left = bx + 32
        inner_right = bx + box_w - 32
        percent_w = 50
        control_gap = 14
        control_w = 132
        percent_x = inner_right - percent_w
        control_right = percent_x - control_gap
        control_x = control_right - control_w

        slider_rect = pygame.Rect(control_x, by + 108, control_w, 16)
        percent_pos = (percent_x, by + 106)
        shake_rect = pygame.Rect(control_x - 8, by + 180, control_w, 32)
        pause_resume_rect = pygame.Rect(inner_left, by + 270, inner_right - inner_left, 44)
        pause_quit_rect = pygame.Rect(inner_left, by + 345, inner_right - inner_left, 44)
        back_rect = pygame.Rect(inner_left, by + 345, inner_right - inner_left, 44)
        return {
            "box": pygame.Rect(bx, by, box_w, box_h),
            "slider": slider_rect,
            "percent_pos": percent_pos,
            "shake": shake_rect,
            "resume": pause_resume_rect,
            "quit": pause_quit_rect,
            "back": back_rect,
            "music_label_pos": (inner_left, by + 105),
            "shake_label_pos": (inner_left, by + 181),
        }

    def update_bgm_volume_from_pos(self, mouse_x):
        slider = self.get_settings_layout()["slider"]
        ratio = (mouse_x - slider.x) / max(1, slider.width)
        self.bgm_volume = max(0.0, min(1.0, ratio))
        pygame.mixer.music.set_volume(self.bgm_volume)

    def draw_settings(self):
        if self.state == STATE_PAUSE:
            self.draw_overworld()
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill(BG_DEEP)
            self.draw_particles()

        layout = self.get_settings_layout()
        box = layout["box"]
        bx, by, box_w, box_h = box.x, box.y, box.width, box.height

        s = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(s, (15, 18, 30, 190), s.get_rect())
        pygame.draw.rect(s, BORDER_SUBTLE, s.get_rect(), 1)
        self.screen.blit(s, (bx, by))

        title_surf = self.name_font.render("SETTINGS", True, GOLD)
        self.screen.blit(title_surf, (400 - title_surf.get_width() // 2, by + 30))

        mx, my = pygame.mouse.get_pos()

        self.screen.blit(self.btn_font.render("MUSIC VOLUME", True, TEXT_SECONDARY), layout["music_label_pos"])

        slider = layout["slider"]
        slider_hover = slider.inflate(0, 16).collidepoint(mx, my) or self.dragging_volume_slider
        track_rect = pygame.Rect(slider.x, slider.y + 3, slider.width, 10)
        glow_rect = track_rect.inflate(10, 8)
        pygame.draw.rect(self.screen, (18, 20, 34), glow_rect, border_radius=10)
        pygame.draw.rect(self.screen, (24, 26, 40), track_rect, border_radius=8)
        pygame.draw.rect(self.screen, (48, 54, 78) if slider_hover else (38, 42, 62), track_rect, 1, border_radius=8)
        fill_w = int(track_rect.width * self.bgm_volume)
        if fill_w > 0:
            fill_rect = pygame.Rect(track_rect.x, track_rect.y, max(10, fill_w), track_rect.height)
            pygame.draw.rect(self.screen, GOLD, fill_rect, border_radius=8)
        knob_x = track_rect.x + int(track_rect.width * self.bgm_volume)
        knob_x = max(track_rect.x + 8, min(track_rect.right - 8, knob_x))
        knob_radius = 9 if slider_hover else 8
        pygame.draw.circle(self.screen, GOLD_LIGHT, (knob_x, track_rect.centery), knob_radius)
        pygame.draw.circle(self.screen, (255, 245, 200), (knob_x, track_rect.centery), 3)
        percent_surf = self.small_font.render(f"{int(self.bgm_volume * 100)}%", True, GOLD_LIGHT)
        self.screen.blit(percent_surf, (layout["percent_pos"][0] + 50 - percent_surf.get_width(), layout["percent_pos"][1]))

        self.screen.blit(self.btn_font.render("SCREEN SHAKE", True, TEXT_SECONDARY), layout["shake_label_pos"])

        sb = layout["shake"]
        shover = sb.collidepoint(mx, my)
        pygame.draw.rect(self.screen, BG_DARK if not shover else (30, 41, 59), sb)
        pygame.draw.rect(self.screen, GOLD if self.shake_enabled else TEXT_DIM, sb, 1)
        s_txt = "ON" if self.shake_enabled else "OFF"
        t_col = GOLD_LIGHT if self.shake_enabled else TEXT_DIM
        self.screen.blit(self.small_font.render(s_txt, True, t_col), (sb.centerx - self.small_font.size(s_txt)[0] // 2, sb.y + 8))

        if self.state == STATE_PAUSE:
            resume = layout["resume"]
            quit_btn = layout["quit"]
            self.draw_styled_btn("RESUME", resume.x, resume.y, resume.width, resume.height, resume.collidepoint(mx, my))
            self.draw_styled_btn("SAVE & QUIT", quit_btn.x, quit_btn.y, quit_btn.width, quit_btn.height, quit_btn.collidepoint(mx, my), True)
        else:
            back = layout["back"]
            self.draw_styled_btn("BACK", back.x, back.y, back.width, back.height, back.collidepoint(mx, my))

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
            rect = pygame.Rect(start_x + c * (box + margin), grid_y + r * (box + margin), box, box)
            is_sel = i == self.selections[cat]
            pygame.draw.rect(self.screen, SLATE_800 if is_sel else (20, 30, 50), rect)
            pygame.draw.rect(self.screen, CYAN_400 if is_sel else SLATE_700, rect, 2 if is_sel else 1)
            if opts[i]:
                img = self.sprite_sheet.get_image_by_grid(opts[i][0], opts[i][1], 2)
                self.screen.blit(img, (rect.x + (box - img.get_width()) // 2, rect.y + (box - img.get_height()) // 2))
            else:
                txt = self.small_font.render("X", True, RED_500)
                self.screen.blit(txt, (rect.x + (box - txt.get_width()) // 2, rect.y + (box - txt.get_height()) // 2))
            self.active_buttons.append({"rect": rect, "type": "item", "cat": cat, "idx": i})

        page_y = 455
        center_x = 625
        page_txt = self.small_font.render(f"PAGE {cur_page + 1}/{total_pages}", True, SLATE_400)
        txt_w = page_txt.get_width()
        self.screen.blit(page_txt, (center_x - txt_w // 2, page_y + 5))

        btn_prev = pygame.Rect(center_x - txt_w // 2 - 35, page_y, 25, 25)
        btn_next = pygame.Rect(center_x + txt_w // 2 + 10, page_y, 25, 25)

        if cur_page > 0:
            pygame.draw.rect(self.screen, SLATE_700, btn_prev)
            self.screen.blit(self.small_font.render("<", True, WHITE), (btn_prev.x + 7, btn_prev.y + 3))
            self.active_buttons.append({"rect": btn_prev, "type": "prev", "cat": cat})
        if cur_page < total_pages - 1:
            pygame.draw.rect(self.screen, SLATE_700, btn_next)
            self.screen.blit(self.small_font.render(">", True, WHITE), (btn_next.x + 7, btn_next.y + 3))
            self.active_buttons.append({"rect": btn_next, "type": "next", "cat": cat})

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
        self.screen.blit(self.player_preview_img, (px - self.player_preview_img.get_width() // 2, py - self.player_preview_img.get_height() + 20))

        panel = pygame.Rect(330, 40, 440, 530)
        s = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (15, 18, 30, 190), s.get_rect())
        pygame.draw.rect(s, BORDER_SUBTLE, s.get_rect(), 2)
        self.screen.blit(s, panel.topleft)

        ty = 65
        for i, tab in enumerate(self.tabs):
            is_act = self.current_tab == tab
            rect = pygame.Rect(345, ty, 120, 48)
            if is_act:
                pygame.draw.rect(self.screen, BG_DARK, rect)
                pygame.draw.rect(self.screen, GOLD, (rect.x, rect.y, 4, rect.height))
            self.screen.blit(self.small_font.render(self.tab_names[i], True, GOLD if is_act else TEXT_SECONDARY), (rect.x + 15, rect.y + 16))
            self.active_buttons.append({"rect": rect, "type": "tab", "tab": tab})
            ty += 62

        pygame.draw.line(self.screen, BORDER_SUBTLE, (475, 60), (475, 540), 2)
        self.draw_category_ui(self.current_tab, 495, 60)

        mx, my = pygame.mouse.get_pos()
        self.draw_styled_btn("START JOURNEY >", 495, 495, 260, 50, self.start_btn_rect.collidepoint(mx, my))
