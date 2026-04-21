# src/mechanics.py
import os
import random
import csv
from src.config import MAX_ATTEMPTS, WORD_LENGTH, WORDS_DATA_DIR

class WordDictionary:
    def __init__(self, difficulty_level="normal"):
        self.difficulty_level = difficulty_level
        self.word_data_list = self._load_words_from_file()
        
        self.current_hint = "" 

    def _load_words_from_file(self):
        file_path = os.path.join(WORDS_DATA_DIR, f"{self.difficulty_level}.csv")
        words_data = []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    word = row['word'].strip().upper()
                    if len(word) == WORD_LENGTH and word.isalpha():
                        words_data.append({
                            'word': word,
                            'definition': row['definition']
                        })
            
            if not words_data:
                print(f"Warning: The word file {file_path} is empty. Using default word.")
                return [{'word': 'ERROR', 'definition': 'A mistake.'}]
            return words_data
            
        except FileNotFoundError:
            print(f"Warning: Word file not found at {file_path}. Using fallback words.")
            return [
                {'word': 'APPLE', 'definition': 'A round fruit with red or green skin.'},
                {'word': 'BRAVE', 'definition': 'Ready to face and endure danger or pain.'}
            ]

    def generate_random_word(self):
        chosen_data = random.choice(self.word_data_list)
        
        self.current_hint = chosen_data['definition']
        
        return chosen_data['word'].upper()

    def get_current_hint(self):
        return self.current_hint

    def validate_word_length(self, word):
        return len(word) == WORD_LENGTH

class TileBoard:
    def __init__(self, grid_size=MAX_ATTEMPTS):
        self.grid_size = grid_size
        self.current_attempt = 1

    def evaluate_colors(self, guessed_word, target_word):
        guessed_word = guessed_word.upper()
        target_word = target_word.upper()
        
        result = ["GRAY"] * len(guessed_word)
        target_chars = list(target_word)

        for i in range(len(guessed_word)):
            if guessed_word[i] == target_word[i]:
                result[i] = "GREEN"
                target_chars[i] = None

        for i in range(len(guessed_word)):
            if result[i] == "GRAY" and guessed_word[i] in target_chars:
                result[i] = "YELLOW"
                target_chars[target_chars.index(guessed_word[i])] = None
        self.current_attempt += 1
        return result