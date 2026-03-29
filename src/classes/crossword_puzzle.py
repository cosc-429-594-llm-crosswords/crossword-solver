import puz
from src.classes.grid import Grid
from src.classes.clue import Clue


class CrosswordPuzzle:
    def __init__(self, puz_file_path):
        p = puz.read(puz_file_path)

        self.grid = Grid(p.width, p.height)
        self.clues = self._extract_clues(p)

    def get_clue(self, number, direction):
        return next(
            (c for c in self.clues if c.number == number and c.direction == direction),
            None,
        )

    def print_info(self):
        print(self.grid)

    def _extract_clues(self, p):
        numbering = p.clue_numbering()
        solution_grid = puz.Grid(p.solution, p.width, p.height)
        extracted_clues = []

        for direction in ["across", "down"]:
            for c_data in getattr(numbering, direction):
                answer = solution_grid.get_string_for_clue(c_data)

                clue_obj = Clue(
                    number=c_data["num"],
                    text=c_data["clue"],
                    answer=answer,
                    row=c_data["row"],
                    col=c_data["col"],
                    direction=direction,
                    grid=self.grid,
                )
                extracted_clues.append(clue_obj)

        return extracted_clues
