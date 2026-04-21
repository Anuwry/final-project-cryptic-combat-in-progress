import csv
import json
import os
import shutil

from src.config import BASE_DIR
from src.entities import Player
from src.map_loader import GameMap
from src.ui.constants import STATE_OVERWORLD, STATE_SELECTION


class SaveDataMixin:
    def load_stats_csv(self):
        self.stats_data = {"time": [], "attempts": [], "combo": [], "damage": [], "keys": []}
        path = self.get_stats_csv_path()
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self.stats_data["time"].append(float(row.get("time_taken_per_word", 0)))
                        self.stats_data["attempts"].append(float(row.get("attempts_per_word", 0)))
                        self.stats_data["combo"].append(float(row.get("combo_achieved", 0)))
                        self.stats_data["damage"].append(float(row.get("damage_per_turn", 0)))
                        self.stats_data["keys"].append(float(row.get("keystrokes_per_word", 0)))
            except Exception as e:
                print(f"Error loading stats CSV: {e}")

    def load_saves_metadata(self):
        path = os.path.join(BASE_DIR, "data", "saves.json")
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    self.saves = json.load(f)
            except Exception:
                self.saves = {"1": None, "2": None, "3": None}

    def get_slot_dir(self, slot=None):
        slot = self.current_save_slot if slot is None else slot
        if not slot:
            return os.path.join(BASE_DIR, "data", "session")
        return os.path.join(BASE_DIR, "data", "slots", f"slot_{slot}")

    def get_active_map_root(self):
        return os.path.join(self.get_slot_dir(), "maps")

    def get_bosses_path(self, slot=None):
        return os.path.join(self.get_slot_dir(slot), "defeated_bosses.json")

    def get_stats_csv_path(self, slot=None):
        return os.path.join(BASE_DIR, "data", "raw", "gameplay_stats.csv")

    def sync_slot_file_paths(self):
        self.gm.set_csv_filename(self.get_stats_csv_path())

    def load_slot_progress(self, slot=None):
        self.defeated_bosses = {}
        path = self.get_bosses_path(slot)
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    self.defeated_bosses = json.load(f)
                return True
            except json.JSONDecodeError:
                self.defeated_bosses = {}
        return False

    def save_slot_progress(self):
        if not self.current_save_slot:
            return
        path = self.get_bosses_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.defeated_bosses, f)

    def delete_slot_progress(self, slot):
        slot_dir = self.get_slot_dir(slot)
        if os.path.exists(slot_dir):
            shutil.rmtree(slot_dir, ignore_errors=True)

    def save_game_data(self):
        if not self.current_save_slot:
            return
        self.saves[str(self.current_save_slot)] = {
            "hp": self.player.hp,
            "max_hp": self.player_max_hp,
            "base_atk": self.base_atk,
            "gold": self.gold,
            "inventory": self.inventory,
            "realm_x": self.realm_x,
            "realm_y": self.realm_y,
            "pos": self.map_player_pos,
            "defeated_bosses": self.defeated_bosses,
            "selections": self.selections,
            "level": self.current_level,
        }
        path = os.path.join(BASE_DIR, "data", "saves.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.saves, f)
        self.save_slot_progress()

    def load_game_data(self, slot):
        data = self.saves[str(slot)]
        self.current_save_slot = slot
        self.sync_slot_file_paths()
        self.player_max_hp = data.get("max_hp", 100)
        self.base_atk = data.get("base_atk", 15)
        self.player = Player(hp=data.get("hp", 100), base_attack=self.base_atk)
        self.gold = data.get("gold", 50)

        loaded_inv = data.get("inventory", [None] * 50)
        while len(loaded_inv) < 50:
            loaded_inv.append(None)
        self.inventory = loaded_inv

        self.realm_x = data.get("realm_x", 0)
        self.realm_y = data.get("realm_y", 0)
        self.map_player_pos = data.get("pos", [15 * 64, 15 * 64])
        if not self.load_slot_progress(slot):
            self.defeated_bosses = data.get("defeated_bosses", {})
        self.selections = data.get("selections", {k: 0 for k in self.tabs})
        self.current_level = data.get("level", 1)
        self.inv_scroll = 0

        self.update_player_visuals()
        self.game_map = GameMap(self.realm_x, self.realm_y, map_root=self.get_active_map_root())
        self.statues_collected = len([s for s in self.game_map.get_statues() if s.collected])
        self.total_statues = len(self.game_map.get_statues())

        self.setup_overworld()
        self.state = STATE_OVERWORLD

    def reset_player_data(self):
        self.gold = 50
        self.base_atk = 15
        self.player_max_hp = 100
        self.player = Player(hp=self.player_max_hp, base_attack=self.base_atk)
        self.show_inventory = False
        self.inv_scroll = 0
        self.inventory = [None] * 50
        self.add_item("compass", "Warp Scroll", "Teleports you safely", 1)
        self.add_item("potion", "Health Potion", "Heals 50 HP", 2)
        self.add_item("scroll", "Hint Scroll", "Reveals 1 letter", 3)
        self.realm_x, self.realm_y = 0, 0
        self.current_level = 1
        self.last_normal_realm = (0, 0)
        self.defeated_bosses = {}
        self.selections = {k: 0 for k in self.tabs}
        self.update_player_visuals()

    def start_new_game(self, slot):
        self.current_save_slot = slot
        self.sync_slot_file_paths()
        self.reset_player_data()
        self.delete_slot_progress(slot)
        self.load_slot_progress(slot)
        self.game_map = GameMap(0, 0, map_root=self.get_active_map_root())
        self.map_player_pos = list(self.game_map.spawn_point)
        self.statues_collected = len([s for s in self.game_map.get_statues() if s.collected])
        self.total_statues = len(self.game_map.get_statues())
        self.setup_overworld()
        self.state = STATE_SELECTION
