from typing import Literal, TypeAlias

LLM_MODEL = "gemma4:e4b"

PUZ_FILE_DIR = "puz_files"

DIRECTIONS: TypeAlias = Literal["across", "down"]
UNKNOWN_LETTER: TypeAlias = Literal["_"]
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
    UNKNOWN_LETTER,
]
