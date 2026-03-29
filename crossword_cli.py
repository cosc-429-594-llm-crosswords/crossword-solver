from src.classes.crossword_puzzle import CrosswordPuzzle
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Crossword Puzzle CLI")
    parser.add_argument("--file", "--f", type=str)
    return parser.parse_args()


def main():
    args = parse_args()

    crossword = CrosswordPuzzle(args.file)

    while True:
        print("Options:")
        print("1. Display clues and grid")
        print("2. Give an answer")
        print("3. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            crossword.print_info()
        elif choice == "2":
            crossword.display_clues()
        elif choice == "3":
            print("Exiting the program.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
