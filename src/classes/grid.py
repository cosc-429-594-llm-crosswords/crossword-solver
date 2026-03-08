import numpy as np
from src.constants import BLACK_SPACE

class Grid:
    def __init__(self, width, height):
        self.data = np.full(shape=(height, width), fill_value=BLACK_SPACE, dtype=object)

    def __str__(self):
        return "\n".join(" ".join(row) for row in self.data)

    def get_clue_values(self, clue):
        if clue.direction == "across":
            return self.data[clue.row, clue.column : clue.column + clue.length]
        elif clue.direction == "down":
            return self.data[clue.row : clue.row + clue.length, clue.column]

    def set_clue_values(self, clue, values):
        if clue.direction == "across":
            self.data[clue.row, clue.column : clue.column + clue.length] = values
        elif clue.direction == "down":
            self.data[clue.row : clue.row + clue.length, clue.column] = values