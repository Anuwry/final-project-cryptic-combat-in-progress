import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
WORDS_DATA_DIR = os.path.join(DATA_DIR, 'words')

MAX_ATTEMPTS = 6
WORD_LENGTH = 5
CSV_FILENAME = os.path.join(RAW_DATA_DIR, 'gameplay_stats.csv')