import re


def sanitize_guess(guess: str) -> str:
    return re.sub(r"[^A-Z]", "", guess.upper())
