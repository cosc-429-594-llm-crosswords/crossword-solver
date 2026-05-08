# import libraries
import argparse
import pandas as pd
from datetime import date

from issac.solve_crossword import solve_crossword
from src.constants import RANKING_ALGORITHMS


# Parameters
# RANKING: RANKING_ALGORITHMS = "VAGUENESS_AND_COMPLEXITY_PLUS_KNOWN_LETTERS"
# BATCH_NUM = int # out of 10, because total 50 puzzles

# Constants
BATCH_SIZE = 5 # will need to 
start_date = date(2025, 1, 1)
end_date   = date(2026, 1, 1)


def get_files_in_batch(start: date, end: date, batch_num: int, batch_size: int = 5,) -> list[str]:
    """Return all file names in batch of Mondays."""
    mondays = pd.date_range(start=start, end=end, freq='W-MON').tolist()

    batch_list = []
    for monday in mondays[(batch_num-1) * batch_size: batch_num * batch_size]:
        batch_list.append(monday.strftime('nytm_%Y_%m_%d'))

    return batch_list


def main() -> None:
    try: 
        parser = argparse.ArgumentParser()
        parser.add_argument("--ranking-alg", type=RANKING_ALGORITHMS, required=True)
        parser.add_argument("--batch-num", type=int, required=True)
        args = parser.parse_args()
        
        if args.batch_num < 1 or args.batch_num > 10:
            print(f"Error: batch_num must be an integer between 1 and 10.")
            exit(1)

        batch_list = get_files_in_batch(start_date, end_date, batch_num=args.batch_num, batch_size=BATCH_SIZE)

        for file in batch_list: 
            solve_crossword(file, args.ranking_alg)

    except Exception as e: 
        print(f"Error occurred: {e}")


if __name__ == "__main__":
    main()