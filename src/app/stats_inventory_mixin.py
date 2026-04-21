import math
import statistics

import pygame

from src.ui.constants import (
    ACCENT_RED,
    ACCENT_RED_GLOW,
    BG_DARK,
    BORDER_SUBTLE,
    CYAN_400,
    EMERALD_500,
    GOLD,
    GOLD_DIM,
    GOLD_LIGHT,
    TEXT_DIM,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WHITE,
)


class StatsInventoryMixin:
    def format_chart_value(self, value):
        if abs(value - round(value)) < 0.01:
            return str(int(round(value)))
        return f"{value:.1f}"

    def draw_chart_axes(self, surface, x, y, w, h, title, x_label, y_label, max_val):
        title_y = y + 5
        plot_left = x + 42
        plot_right = x + w - 14
        plot_top = y + 30
        plot_bottom = y + h - 20

        surface.blit(self.tiny_font.render(title, True, TEXT_PRIMARY), (x + 5, title_y))
        pygame.draw.line(surface, BORDER_SUBTLE, (plot_left, plot_top), (plot_left, plot_bottom), 1)
        pygame.draw.line(surface, BORDER_SUBTLE, (plot_left, plot_bottom), (plot_right, plot_bottom), 1)

        y_ticks = [0, max_val * 0.5, max_val]
        for tick in y_ticks:
            if max_val <= 0:
                tick_y = plot_bottom
            else:
                tick_y = plot_bottom - int((tick / max_val) * (plot_bottom - plot_top))
            pygame.draw.line(surface, (50, 58, 78), (plot_left, tick_y), (plot_right, tick_y), 1)
            label = self.tiny_font.render(self.format_chart_value(tick), True, TEXT_DIM)
            surface.blit(label, (x + 6, tick_y - label.get_height() // 2))

        x_text = self.tiny_font.render(x_label, True, TEXT_DIM)
        surface.blit(x_text, (plot_right - x_text.get_width(), plot_bottom + 2))

        y_text = self.tiny_font.render(y_label, True, TEXT_DIM)
        y_text_rot = pygame.transform.rotate(y_text, 90)
        surface.blit(y_text_rot, (x + 2, plot_top))

        return plot_left, plot_right, plot_top, plot_bottom

    def draw_line_chart(self, surface, x, y, w, h, data, color, title, mx, my, x_label="Recent Encounters", y_label="Value"):
        pygame.draw.rect(surface, (20, 25, 40, 200), (x, y, w, h))
        pygame.draw.rect(surface, BORDER_SUBTLE, (x, y, w, h), 1)

        if not data:
            no_data = self.tiny_font.render("NO DATA", True, TEXT_DIM)
            surface.blit(no_data, (x + w // 2 - no_data.get_width() // 2, y + h // 2 - no_data.get_height() // 2))
            return

        data = data[-20:]
        max_val = max(data) if max(data) > 0 else 1
        pts = []
        plot_left, plot_right, plot_top, plot_bottom = self.draw_chart_axes(surface, x, y, w, h, title, x_label, y_label, max_val)

        hovered_val = None
        hovered_pos = None

        for i, val in enumerate(data):
            px = plot_left + (i / max(1, len(data) - 1)) * (plot_right - plot_left)
            py = plot_bottom - (val / max_val) * (plot_bottom - plot_top)
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
            pygame.draw.rect(surface, (0, 0, 0, 220), tr.inflate(8, 4))
            pygame.draw.rect(surface, GOLD, tr.inflate(8, 4), 1)
            surface.blit(ts, tr)

    def draw_bar_chart(self, surface, x, y, w, h, data, color, title, mx, my, x_label="Recent Encounters", y_label="Value"):
        pygame.draw.rect(surface, (20, 25, 40, 200), (x, y, w, h))
        pygame.draw.rect(surface, BORDER_SUBTLE, (x, y, w, h), 1)

        if not data:
            no_data = self.tiny_font.render("NO DATA", True, TEXT_DIM)
            surface.blit(no_data, (x + w // 2 - no_data.get_width() // 2, y + h // 2 - no_data.get_height() // 2))
            return

        data = data[-20:]
        max_val = max(data) if max(data) > 0 else 1
        plot_left, plot_right, plot_top, plot_bottom = self.draw_chart_axes(surface, x, y, w, h, title, x_label, y_label, max_val)
        gap = 2
        bar_w = max(2, int((plot_right - plot_left - max(0, len(data) - 1) * gap) / max(1, len(data))))

        hovered_val = None
        hovered_pos = None

        for i, val in enumerate(data):
            px = plot_left + i * (bar_w + gap)
            ph = (val / max_val) * (plot_bottom - plot_top)
            py = plot_bottom - ph
            rect = pygame.Rect(px, py, bar_w, ph)
            pygame.draw.rect(surface, color, rect)

            if rect.collidepoint(mx, my):
                hovered_val = val
                hovered_pos = (px + bar_w / 2, py)

        if hovered_val is not None:
            v_str = f"{round(hovered_val, 2)}"
            ts = self.tiny_font.render(v_str, True, WHITE)
            tr = ts.get_rect(center=(hovered_pos[0], hovered_pos[1] - 12))
            pygame.draw.rect(surface, (0, 0, 0, 220), tr.inflate(8, 4))
            pygame.draw.rect(surface, GOLD, tr.inflate(8, 4), 1)
            surface.blit(ts, tr)

    def get_stats_panel_rect(self):
        panel_x, panel_y = 400, 50
        panel_w = min(360, self.screen_width - panel_x - 40)
        panel_h = min(460, self.screen_height - panel_y - 40)
        return pygame.Rect(panel_x, panel_y, panel_w, panel_h)

    def get_stats_chart_specs(self, graph_x=None, graph_y=None, graph_w=None, graph_h=None):
        panel_rect = self.get_stats_panel_rect()
        graph_x = panel_rect.x if graph_x is None else graph_x
        graph_y = panel_rect.y if graph_y is None else graph_y
        graph_w = panel_rect.width if graph_w is None else graph_w
        graph_h = panel_rect.height if graph_h is None else graph_h

        gx = graph_x + 20
        gw = graph_w - 40
        chart_top = graph_y + 98
        chart_gap = 10
        bottom_padding = 16
        gh = max(74, int((graph_h - (chart_top - graph_y) - bottom_padding - chart_gap * 3) / 4))
        return [
            {"key": "damage", "kind": "line", "x": gx, "y": chart_top, "w": gw, "h": gh, "data": self.stats_data["damage"], "color": ACCENT_RED_GLOW, "title": "DAMAGE PER TURN (TREND)", "x_label": "Recent Turns", "y_label": "Damage"},
            {"key": "time", "kind": "bar", "x": gx, "y": chart_top + (gh + chart_gap), "w": gw, "h": gh, "data": self.stats_data["time"], "color": GOLD, "title": "TIME TAKEN PER WORD (SEC)", "x_label": "Recent Words", "y_label": "Seconds"},
            {"key": "keys", "kind": "line", "x": gx, "y": chart_top + (gh + chart_gap) * 2, "w": gw, "h": gh, "data": self.stats_data["keys"], "color": EMERALD_500, "title": "KEYSTROKES PER WORD", "x_label": "Recent Words", "y_label": "Keys"},
            {"key": "combo", "kind": "bar", "x": gx, "y": chart_top + (gh + chart_gap) * 3, "w": gw, "h": gh, "data": self.stats_data["combo"], "color": CYAN_400, "title": "COMBO ACHIEVED", "x_label": "Recent Words", "y_label": "Combo"},
        ]

    def get_stats_tab_rects(self, graph_x=None, graph_y=None, graph_w=None):
        panel_rect = self.get_stats_panel_rect()
        graph_x = panel_rect.x if graph_x is None else graph_x
        graph_y = panel_rect.y if graph_y is None else graph_y
        graph_w = panel_rect.width if graph_w is None else graph_w
        tab_y = graph_y + 40
        return {
            "summary": pygame.Rect(graph_x + 20, tab_y, 110, 26),
            "charts": pygame.Rect(graph_x + 138, tab_y, 84, 26),
        }

    def format_summary_cell(self, value):
        if value is None:
            return "-"
        if abs(value - round(value)) < 0.01:
            return str(int(round(value)))
        return f"{value:.2f}"

    def get_stat_profile(self, key):
        data = self.stats_data.get(key, [])
        if not data:
            return None
        mean = statistics.mean(data)
        std = statistics.pstdev(data) if len(data) > 1 else 0.0
        return {
            "mean": mean,
            "median": statistics.median(data),
            "std": std,
            "min": min(data),
            "max": max(data),
            "latest": data[-1],
            "count": len(data),
        }

    def get_summary_highlights(self):
        damage = self.get_stat_profile("damage")
        time_profile = self.get_stat_profile("time")
        keys = self.get_stat_profile("keys")
        combo = self.get_stat_profile("combo")
        attempts = self.get_stat_profile("attempts")

        avg_time = time_profile["mean"] if time_profile else 0
        avg_keys = keys["mean"] if keys else 0
        avg_attempts = attempts["mean"] if attempts else 0
        clutch_rate = 0
        if self.stats_data["attempts"]:
            clutch_rate = 100 * sum(1 for val in self.stats_data["attempts"] if val <= 3) / len(self.stats_data["attempts"])
        typing_efficiency = min(100, max(0, (5 / avg_keys) * 100)) if avg_keys else 0
        rhythm_score = 0
        if time_profile and avg_time > 0:
            rhythm_score = max(0, min(100, 100 - (time_profile["std"] / avg_time) * 100))

        return [
            {"title": "Tempo", "value": f"{avg_time:.1f}s" if time_profile else "-", "subtitle": f"Fastest word {time_profile['min']:.1f}s" if time_profile else "No timing data", "accent": GOLD},
            {"title": "Input Efficiency", "value": f"{typing_efficiency:.0f}%" if keys else "-", "subtitle": f"{avg_keys:.1f} keys per word" if keys else "No typing data", "accent": EMERALD_500},
            {"title": "Clutch Rate", "value": f"{clutch_rate:.0f}%" if attempts else "-", "subtitle": f"{avg_attempts:.1f} attempts on average" if attempts else "No attempt data", "accent": ACCENT_RED_GLOW},
            {"title": "Combo Peak", "value": f"x{int(round(combo['max']))}" if combo else "-", "subtitle": f"Average streak x{combo['mean']:.1f}" if combo else "No combo data", "accent": CYAN_400},
            {"title": "Burst Damage", "value": f"{damage['max']:.0f}" if damage else "-", "subtitle": f"Average hit {damage['mean']:.1f}" if damage else "No damage data", "accent": ACCENT_RED},
            {"title": "Rhythm Score", "value": f"{rhythm_score:.0f}" if time_profile else "-", "subtitle": "Higher means steadier pacing", "accent": CYAN_400},
        ]

    def get_summary_insights(self):
        damage = self.get_stat_profile("damage")
        time_profile = self.get_stat_profile("time")
        keys = self.get_stat_profile("keys")
        combo = self.get_stat_profile("combo")
        attempts = self.get_stat_profile("attempts")

        insights = []
        if damage:
            insights.append({"title": "Damage Pressure", "accent": ACCENT_RED_GLOW, "headline": f"{damage['mean']:.1f} avg / {damage['max']:.0f} peak", "detail": f"Recent hit {damage['latest']:.0f} with spread {damage['std']:.1f}"})
        if time_profile and attempts:
            clutch_rate = 100 * sum(1 for val in self.stats_data["attempts"] if val <= 3) / len(self.stats_data["attempts"])
            insights.append({"title": "Solve Control", "accent": GOLD, "headline": f"{attempts['mean']:.1f} attempts and {time_profile['mean']:.1f}s per word", "detail": f"{clutch_rate:.0f}% of words land in 3 guesses or less"})
        if keys:
            efficiency = min(100, max(0, (5 / keys["mean"]) * 100))
            insights.append({"title": "Typing Economy", "accent": EMERALD_500, "headline": f"{keys['mean']:.1f} keys per word", "detail": f"Input efficiency sits at {efficiency:.0f}% with a best case of {keys['min']:.0f} keys"})
        if combo:
            insights.append({"title": "Momentum Window", "accent": CYAN_400, "headline": f"Average streak x{combo['mean']:.1f}, peak x{combo['max']:.0f}", "detail": f"Current run ended on x{combo['latest']:.0f}" if combo["latest"] else "No current streak"})
        return insights[:3]

    def draw_summary_dashboard(self, surface, panel_x, panel_y, panel_w, panel_h):
        content_x = panel_x + 24
        content_y = panel_y + 108
        content_w = panel_w - 48

        highlights = self.get_summary_highlights()
        insights = self.get_summary_insights()

        cols = 3
        card_gap = 14
        card_w = (content_w - card_gap * (cols - 1)) // cols
        card_h = 74

        for idx, card in enumerate(highlights):
            col = idx % cols
            row = idx // cols
            rect = pygame.Rect(content_x + col * (card_w + card_gap), content_y + row * (card_h + 14), card_w, card_h)
            bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(bg, (10, 14, 24, 250), bg.get_rect(), border_radius=10)
            pygame.draw.rect(bg, card["accent"], bg.get_rect(), 1, border_radius=10)
            pygame.draw.rect(bg, (*card["accent"][:3], 28), pygame.Rect(0, 0, rect.width, 6), border_radius=10)
            surface.blit(bg, rect.topleft)

            surface.blit(self.tiny_font.render(card["title"].upper(), True, TEXT_DIM), (rect.x + 14, rect.y + 12))
            surface.blit(self.name_font.render(card["value"], True, WHITE), (rect.x + 14, rect.y + 26))
            surface.blit(self.tiny_font.render(card["subtitle"], True, card["accent"]), (rect.x + 14, rect.y + 54))

        section_y = content_y + (card_h + 14) * 2 + 12
        surface.blit(self.tiny_font.render("COMBAT READOUT", True, GOLD_LIGHT), (content_x, section_y))

        row_y = section_y + 18
        row_h = 42
        row_gap = 8
        for idx, insight in enumerate(insights):
            rect = pygame.Rect(content_x, row_y + idx * (row_h + row_gap), content_w, row_h)
            pygame.draw.rect(surface, (9, 12, 22), rect, border_radius=10)
            pygame.draw.rect(surface, (36, 44, 64), rect, 1, border_radius=10)
            pygame.draw.rect(surface, insight["accent"], pygame.Rect(rect.x, rect.y, 6, rect.height), border_radius=10)

            surface.blit(self.small_font.render(insight["title"], True, WHITE), (rect.x + 18, rect.y + 4))
            summary_line = self.tiny_font.render(f"{insight['headline']}  |  {insight['detail']}", True, insight["accent"])
            surface.blit(summary_line, (rect.x + 18, rect.y + 22))

    def get_stats_chart_at_pos(self, pos):
        if not self.show_inventory:
            return None
        px, py = pos
        for spec in self.get_stats_chart_specs():
            if pygame.Rect(spec["x"], spec["y"], spec["w"], spec["h"]).collidepoint(px, py):
                return spec["key"]
        return None

    def get_expanded_graph_spec(self):
        if not self.expanded_graph_key:
            return None
        for spec in self.get_stats_chart_specs():
            if spec["key"] == self.expanded_graph_key:
                return spec
        return None

    def get_expanded_graph_panel_rect(self):
        panel_w = min(620, self.screen_width - 64)
        panel_h = min(420, self.screen_height - 80)
        return pygame.Rect((self.screen_width - panel_w) // 2, (self.screen_height - panel_h) // 2, panel_w, panel_h)

    def get_expanded_graph_close_rect(self):
        panel_rect = self.get_expanded_graph_panel_rect()
        return pygame.Rect(panel_rect.right - 38, panel_rect.y + 10, 24, 24)

    def get_expanded_summary_panel_rect(self):
        panel_w = min(720, self.screen_width - 48)
        panel_h = min(470, self.screen_height - 64)
        return pygame.Rect((self.screen_width - panel_w) // 2, (self.screen_height - panel_h) // 2, panel_w, panel_h)

    def get_expanded_summary_close_rect(self):
        panel_rect = self.get_expanded_summary_panel_rect()
        return pygame.Rect(panel_rect.right - 38, panel_rect.y + 10, 24, 24)

    def draw_expanded_graph_overlay(self, surface):
        spec = self.get_expanded_graph_spec()
        if not spec:
            return

        mx, my = pygame.mouse.get_pos()
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        surface.blit(overlay, (0, 0))

        panel_rect = self.get_expanded_graph_panel_rect()
        close_rect = self.get_expanded_graph_close_rect()
        panel = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (15, 18, 30, 245), panel.get_rect(), border_radius=8)
        pygame.draw.rect(panel, spec["color"], panel.get_rect(), 2, border_radius=8)
        surface.blit(panel, panel_rect.topleft)

        surface.blit(self.small_font.render(spec["title"], True, spec["color"]), (panel_rect.x + 24, panel_rect.y + 20))
        hint = self.tiny_font.render("ESC or click outside to close", True, TEXT_DIM)
        surface.blit(hint, (panel_rect.x + 24, panel_rect.y + 52))

        hover_close = close_rect.collidepoint(mx, my)
        pygame.draw.rect(surface, ACCENT_RED_GLOW if hover_close else ACCENT_RED, close_rect, border_radius=4)
        pygame.draw.rect(surface, WHITE, close_rect, 1, border_radius=4)
        close_text = self.btn_font.render("X", True, WHITE)
        surface.blit(close_text, close_text.get_rect(center=close_rect.center))

        chart_x = panel_rect.x + 24
        chart_y = panel_rect.y + 92
        chart_w = panel_rect.width - 48
        chart_h = panel_rect.height - 124
        if spec["kind"] == "line":
            self.draw_line_chart(surface, chart_x, chart_y, chart_w, chart_h, spec["data"], spec["color"], spec["title"], mx, my, spec["x_label"], spec["y_label"])
        else:
            self.draw_bar_chart(surface, chart_x, chart_y, chart_w, chart_h, spec["data"], spec["color"], spec["title"], mx, my, spec["x_label"], spec["y_label"])

    def draw_expanded_summary_overlay(self, surface):
        mx, my = pygame.mouse.get_pos()
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((3, 5, 10, 245))
        surface.blit(overlay, (0, 0))

        panel_rect = self.get_expanded_summary_panel_rect()
        close_rect = self.get_expanded_summary_close_rect()
        panel = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (8, 11, 20, 254), panel.get_rect(), border_radius=8)
        pygame.draw.rect(panel, (16, 21, 34, 255), pygame.Rect(14, 14, panel_rect.width - 28, panel_rect.height - 28), border_radius=8)
        pygame.draw.rect(panel, CYAN_400, panel.get_rect(), 2, border_radius=8)
        surface.blit(panel, panel_rect.topleft)

        surface.blit(self.small_font.render("PERFORMANCE SNAPSHOT", True, CYAN_400), (panel_rect.x + 24, panel_rect.y + 20))
        hint = self.tiny_font.render("ESC or click outside to close", True, TEXT_DIM)
        surface.blit(hint, (panel_rect.x + 24, panel_rect.y + 52))

        hover_close = close_rect.collidepoint(mx, my)
        pygame.draw.rect(surface, ACCENT_RED_GLOW if hover_close else ACCENT_RED, close_rect, border_radius=4)
        pygame.draw.rect(surface, WHITE, close_rect, 1, border_radius=4)
        close_text = self.btn_font.render("X", True, WHITE)
        surface.blit(close_text, close_text.get_rect(center=close_rect.center))

        subtitle = self.tiny_font.render("Signal-focused readout from recent gameplay logs", True, GOLD_LIGHT)
        surface.blit(subtitle, (panel_rect.x + 24, panel_rect.y + 76))
        self.draw_summary_dashboard(surface, panel_rect.x, panel_rect.y, panel_rect.width, panel_rect.height)

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
                        surface.blit(self.item_icons[item["id"]], (rect.x + 4, rect.y + 4))
                        if item.get("qty", 1) > 1:
                            surface.blit(self.tiny_font.render(str(item["qty"]), True, WHITE), (rect.right - 10, rect.bottom - 12))

            sb_x = start_x_inv + grid_w + 10
            sb_y = inv_start_y
            sb_h = 8 * slot_size + 7 * padding
            pygame.draw.rect(surface, BG_DARK, (sb_x, sb_y, 10, sb_h))

            max_scroll = max(0, ((len(self.inventory) - 5) // 5) - 8)
            if max_scroll > 0:
                thumb_h = max(10, int(sb_h * (8 / (max_scroll + 8))))
                thumb_y = sb_y + int((self.inv_scroll / max_scroll) * (sb_h - thumb_h))
                pygame.draw.rect(surface, GOLD_DIM, (sb_x, thumb_y, 10, thumb_h))

            stats_panel = self.get_stats_panel_rect()
            graph_x, graph_y = stats_panel.x, stats_panel.y
            graph_w, graph_h = stats_panel.width, stats_panel.height

            g_surf = pygame.Surface((graph_w, graph_h), pygame.SRCALPHA)
            pygame.draw.rect(g_surf, (15, 18, 30, 200), g_surf.get_rect())
            pygame.draw.rect(g_surf, CYAN_400, g_surf.get_rect(), 2)
            surface.blit(g_surf, (graph_x, graph_y))

            surface.blit(self.small_font.render("GAMEPLAY STATISTICS", True, CYAN_400), (graph_x + 20, graph_y + 15))
            tab_rects = self.get_stats_tab_rects(graph_x, graph_y, graph_w)
            for mode, rect in tab_rects.items():
                active = self.expanded_summary if mode == "summary" else (self.stats_view_mode == "charts" and not self.expanded_summary)
                fill = (22, 28, 46, 230) if active else (14, 18, 30, 200)
                border = CYAN_400 if active else BORDER_SUBTLE
                pygame.draw.rect(surface, fill, rect, border_radius=6)
                pygame.draw.rect(surface, border, rect, 1, border_radius=6)
                label = "SUMMARIZE" if mode == "summary" else "CHARTS"
                text_color = CYAN_400 if active else TEXT_SECONDARY
                txt = self.tiny_font.render(label, True, text_color)
                surface.blit(txt, (rect.centerx - txt.get_width() // 2, rect.y + 7))

            surface.blit(self.tiny_font.render("CLICK A GRAPH TO EXPAND", True, TEXT_DIM), (graph_x + 20, graph_y + 76))

            for spec in self.get_stats_chart_specs(graph_x, graph_y, graph_w, graph_h):
                rect = pygame.Rect(spec["x"], spec["y"], spec["w"], spec["h"])
                hovered = rect.collidepoint(mx, my)
                if spec["kind"] == "line":
                    self.draw_line_chart(surface, spec["x"], spec["y"], spec["w"], spec["h"], spec["data"], spec["color"], spec["title"], mx, my, spec["x_label"], spec["y_label"])
                else:
                    self.draw_bar_chart(surface, spec["x"], spec["y"], spec["w"], spec["h"], spec["data"], spec["color"], spec["title"], mx, my, spec["x_label"], spec["y_label"])
                if hovered:
                    pygame.draw.rect(surface, spec["color"], rect, 2)

            if self.expanded_graph_key:
                self.draw_expanded_graph_overlay(surface)
            if self.expanded_summary:
                self.draw_expanded_summary_overlay(surface)

        start_x_hb = (800 - (5 * slot_size + 4 * padding)) // 2
        for i in range(5):
            rect = pygame.Rect(start_x_hb + i * (slot_size + padding), hotbar_start_y, slot_size, slot_size)
            s = pygame.Surface((slot_size, slot_size), pygame.SRCALPHA)
            pygame.draw.rect(s, slot_bg, s.get_rect())
            pygame.draw.rect(s, border_color, s.get_rect(), 1)
            surface.blit(s, (rect.x, rect.y))
            surface.blit(self.tiny_font.render(str(i + 1), True, TEXT_DIM), (rect.x + 4, rect.y + 2))

            item = self.inventory[i]
            if item:
                surface.blit(self.item_icons[item["id"]], (rect.x + 4, rect.y + 4))
                if item.get("qty", 1) > 1:
                    surface.blit(self.tiny_font.render(str(item["qty"]), True, WHITE), (rect.right - 10, rect.bottom - 12))

        if self.dragged_item:
            surface.blit(self.item_icons[self.dragged_item["id"]], (mx - 16, my - 16))
