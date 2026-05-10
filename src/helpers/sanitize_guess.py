import re


# Remove all the non-alphabetic characters from the guess and convert it to uppercase
def sanitize_guess(guess: str) -> str:
    return re.sub(r"[^A-Z]", "", guess.upper())
