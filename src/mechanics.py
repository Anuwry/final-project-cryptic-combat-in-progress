# src/mechanics.py
import random
from src.config import MAX_ATTEMPTS, WORD_LENGTH

class WordDictionary:
    def __init__(self, difficulty_level="normal"):
        self.difficulty_level = difficulty_level
        self.word_list = ["APPLE", "BRAVE", "CRANE", "DELTA", "EAGLE"]

    def generate_random_word(self):
        return random.choice(self.word_list).upper()

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