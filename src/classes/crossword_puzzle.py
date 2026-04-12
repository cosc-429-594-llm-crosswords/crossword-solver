from typing import get_args

import numpy as np
import puz

from src.classes.clue import Clue
from src.constants import DIRECTIONS, LETTERS, UNKNOWN_LETTER


def get_slice(clue: Clue, grid: np.ndarray) -> np.ndarray:
    if clue.direction == "across":
        return grid[clue.row, clue.col : clue.col + clue.length]
    else:
        return grid[clue.row : clue.row + clue.length, clue.col]


class CrosswordPuzzle:
    def __init__(self, puz_file_path):
        p = puz.read(puz_file_path)

        self.__clues = self.__get_clues(p)

        self.__letter_grid = np.full((p.height, p.width), fill_value=UNKNOWN_LETTER, dtype="U1")
        self.__overlap_grid = self.__create_overlap_grid(p)
        self.__filled_in_clues = set()

    def __get_clues(self, p: puz.Puzzle) -> list[Clue]:
        numbering = p.clue_numbering()

        return [
            Clue(
                text=data["clue"],
                length=data["len"],
                number=data["num"],
                direction=direction,
                row=data["row"],
                col=data["col"],
            )
            for direction in get_args(DIRECTIONS)
            for data in getattr(numbering, direction)
        ]

    def __get_letter_grid_slice(self, clue: Clue) -> np.ndarray:
        return get_slice(clue, self.__letter_grid)

    def __get_overlap_grid_slice(self, clue: Clue) -> np.ndarray:
        return get_slice(clue, self.__overlap_grid)

    def __create_overlap_grid(self, p: puz.Puzzle) -> np.ndarray:
        overlap_grid = np.frompyfunc(set, 0, 1)(np.empty((p.width, p.height), dtype=object))

        for clue in self.__clues:
            grid_slice = get_slice(clue, overlap_grid)

            for i in range(clue.length):
                grid_slice[i].add(clue)

        return overlap_grid

    def get_clue(self, id: tuple[int, DIRECTIONS]) -> Clue | None:
        return next(
            (clue for clue in self.__clues if clue.id == id),
            None,
        )

    def get_clues(self) -> list[Clue]:
        return self.__clues

    def get_answer(self, clue: Clue) -> list[LETTERS]:
        return self.__get_letter_grid_slice(clue).tolist()

    def set_answer(self, clue: Clue, answer: str) -> None:
        if len(answer) != clue.length:
            raise ValueError(
                f"Answer length {len(answer)} does not match clue length {clue.length}"
            )

        grid_slice = self.__get_letter_grid_slice(clue)

        answer_arr = np.array(list(answer))
        known_mask = grid_slice != UNKNOWN_LETTER
        conflicts = known_mask & (grid_slice != answer_arr)

        if np.any(conflicts):
            idx = np.where(conflicts)[0][0]
            raise ValueError(
                f"Answer letter '{answer_arr[idx]}' does not match "
                f"existing letter '{grid_slice[idx]}' in grid"
            )

        grid_slice[:] = answer_arr
        self.__filled_in_clues.add(clue)

    def remove_answer(self, clue: Clue) -> None:
        if clue not in self.__filled_in_clues:
            raise ValueError("Cannot remove answer because clue is not filled in")

        overlap_grid_slice = self.__get_overlap_grid_slice(clue)
        current_clue_letter_grid_slice = self.__get_letter_grid_slice(clue)

        for idx, overlapping_clues in enumerate(overlap_grid_slice):
            if any(c not in self.__filled_in_clues for c in overlapping_clues if c != clue):
                current_clue_letter_grid_slice[idx] = UNKNOWN_LETTER

    def print_grid(self) -> None:
        for row in self.__letter_grid:
            print(" ".join(row))
