from typing import Literal, TypeAlias

# LLM_MODEL = "gemma4:e4b"
LLM_MODEL = "llama3.1:latest"

# self-consistency parameters
DEFAULT_NUM_SAMPLES = 3
DEFAULT_MAX_GUESSES = 5

# suggestion character threshold for including in the prompt
SUGGESTION_CHAR_THRESHOLD = 2

PUZ_FILE_DIR = "puz_files"
PUZ_FILE_DIR2 = "goobix_puzzles"
CROSSHARE_PUZ_DIR = "crosshare_puz_files"
DIRECTIONS: TypeAlias = Literal["across", "down"]
UNKNOWN_LETTER = "_"
LETTERS: TypeAlias = Literal[
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
    "_",
]
CLUE_ID: TypeAlias = tuple[int, DIRECTIONS]
