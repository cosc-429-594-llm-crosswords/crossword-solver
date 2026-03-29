from src.constants import EMPTY_SPACE


class Clue:
    def __init__(self, number, text, answer, row, col, direction, grid):
        self.number = number
        self.text = text
        self.answer = answer
        self.length = len(answer)
        self.row = row
        self.column = col
        self.direction = direction
        self.grid = grid

        self.grid.set_clue_values(self, EMPTY_SPACE)

    @property
    def current_fill(self):
        return self.grid.get_clue_values(self)

    def fill(self, word):
        word = word.upper()
        if len(word) != self.length:
            raise ValueError(
                f"Word length {len(word)} does not match clue length {self.length}"
            )

        current = self.current_fill

        for i, char in enumerate(word):
            if current[i] != EMPTY_SPACE and current[i] != char:
                raise ValueError(
                    f"Conflict at position {i}: grid has '{current[i]}', but trying to fill '{char}'"
                )

        self.grid.set_clue_values(self, list(word))

    def __str__(self):
        return f"{self.number} ({self.direction.upper()}): {self.text}"
