from src.classes.crossword_puzzle import CrosswordPuzzle
from src.constants import PUZ_FILE_DIR


def main():
    crossword_puzzle = CrosswordPuzzle(f"{PUZ_FILE_DIR}/nytm_2025_01_01.puz")

    crossword_puzzle.set_answer(crossword_puzzle.get_clue((2, "down")), "TESTT")
    crossword_puzzle.set_answer(crossword_puzzle.get_clue((4, "down")), "TESTT")
    crossword_puzzle.set_answer(crossword_puzzle.get_clue((7, "across")), "ASBSF")

    crossword_puzzle.print_grid()

    crossword_puzzle.remove_answer(crossword_puzzle.get_clue((4, "down")))

    crossword_puzzle.print_grid()


if __name__ == "__main__":
    main()
