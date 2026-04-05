# src/game_manager.py
import os
import csv
import time
from src.config import CSV_FILENAME

class GameManager:
    def __init__(self):
        self.current_level = 1
        self.game_over = False
        
        self.word_start_time = 0.0
        self.time_taken = 0.0 
        self.keystroke_count = 0
        self.gameplay_data = []

    def start_word_timer(self):
        self.word_start_time = time.time()
        self.keystroke_count = 0

    def end_word_timer(self):
        self.time_taken = time.time() - self.word_start_time

    def check_win_condition(self, enemy):
        return enemy.current_hp <= 0
        
    def record_word_data(self, attempt_used, combo, damage):
        data_entry = {
            "time_taken_per_word": round(self.time_taken, 2),
            "attempts_per_word": attempt_used,
            "combo_achieved": combo,
            "damage_per_turn": damage,
            "keystrokes_per_word": self.keystroke_count
        }
        self.gameplay_data.append(data_entry)

    def export_data_to_csv(self):
        if not self.gameplay_data:
            return

        file_exists = os.path.isfile(CSV_FILENAME)
        os.makedirs(os.path.dirname(CSV_FILENAME), exist_ok=True)

        with open(CSV_FILENAME, mode='a', newline='') as file:
            fieldnames = ["time_taken_per_word", "attempts_per_word", "combo_achieved", "damage_per_turn", "keystrokes_per_word"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()
            for row in self.gameplay_data:
                writer.writerow(row)
        self.gameplay_data = []