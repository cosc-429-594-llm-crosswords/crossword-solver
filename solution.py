import argparse

from src.classes.crossword_puzzle import CrosswordPuzzle
from src.constants import PUZ_FILE_DIR


def parse_arguments():
    parser = argparse.ArgumentParser(description="Solve a crossword puzzle")
    parser.add_argument(
        "--outlet", "--o", type=str, help="The crossword outlet (e.g., usa, nyt, wsj)"
    )
    parser.add_argument("--year", "--y", type=int, help="year of the crossword (e.g., 2020)")
    parser.add_argument("--month", "--m", type=int, help="month of the crossword (e.g., 1)")
    parser.add_argument("--day", "--d", type=int, help="day of the crossword (e.g., 1)")
    return parser.parse_args()


def main():
    args = parse_arguments()

    file_path = f"{PUZ_FILE_DIR}/{args.outlet}_{args.year}_{args.month:02d}_{args.day:02d}.puz"
    crossword_puzzle = CrosswordPuzzle(file_path)

    clues = crossword_puzzle.get_clues()
    for clue in clues:
        solution = crossword_puzzle.get_solution(clue)
        print(f"{clue}: {solution}")


if __name__ == "__main__":
    main()
