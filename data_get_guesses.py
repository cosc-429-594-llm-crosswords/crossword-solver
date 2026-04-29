import argparse
import random
import sys
import os
from datetime import datetime
from dataclasses import dataclass, field

import pandas as pd

from src.classes.clue import Clue
from src.prompts.get_guesses_with_self_consistency import get_guesses_with_self_consistency, get_guesses_for_clue_using_llm

# --- Constants ---

CLUE_LENGTH = 4
NUM_FILLED = 0       # Must be less than CLUE_LENGTH
NUM_CLUES = 2       # Must be an int or "All"
DAY_OF_WEEK = "Monday"  # "All", "Monday", ..., "Sunday"
SELF_CONSISTENCY = True

# Ignore these
VALID_DAYS = {"All", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
TOP_N_GUESSES = 5
INPUT_CSV = "crossword_clues.csv"
OUTPUT_DIR = "data/get_guesses_per_clue"


# --- Config & Validation ---

@dataclass
class ExperimentConfig:
    clue_length: int
    num_filled: int
    num_clues: int | str
    day_of_week: str
    self_consistency: bool

    def validate(self) -> None:
        if self.day_of_week not in VALID_DAYS:
            _exit(f"Invalid DAY_OF_WEEK '{self.day_of_week}'. Must be one of: {VALID_DAYS}")
        if self.num_filled >= self.clue_length:
            _exit("NUM_FILLED must be strictly less than CLUE_LENGTH.")
        if not isinstance(self.num_clues, int) and self.num_clues != "All":
            _exit("NUM_CLUES must be an integer or 'All'.")

    @property
    def output_path(self) -> str:
        return os.path.join(OUTPUT_DIR, f"test_sc_{self.self_consistency}_clues_{self.num_clues}_{self.day_of_week}_fill_{self.num_filled}_length_{self.clue_length}.csv")


def parse_args() -> ExperimentConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clue-length", type=int, required=True)
    parser.add_argument("--num-filled", type=int, required=True)
    parser.add_argument("--num-clues", default="All")  # int or "All"
    parser.add_argument("--day-of-week", default="All")
    parser.add_argument("--self-consistency", type=bool, default=True)
    args = parser.parse_args()
    return ExperimentConfig(
        clue_length=args.clue_length,
        num_filled=args.num_filled,
        num_clues=int(args.num_clues) if args.num_clues != "All" else "All",
        day_of_week=args.day_of_week,
        self_consistency=args.self_consistency,
    )


# --- Data Loading ---

def load_clues(csv_path: str, config: ExperimentConfig) -> pd.DataFrame:
    data = pd.read_csv(csv_path)
    print(f"Loaded dataset: {data.shape}")

    clues = data[data["length"] == config.clue_length]

    if config.day_of_week != "All":
        clues = clues[clues["day_of_week"] == config.day_of_week]

    if isinstance(config.num_clues, int):
        if config.num_clues > len(clues):
            _exit(
                f"Requested {config.num_clues} clues, but only {len(clues)} match your criteria."
            )
        clues = clues.iloc[: config.num_clues]

    print(f"Filtered clues: {clues.shape}")
    return clues


# --- Pattern Generation ---

# Return a letter pattern with `num_filled` positions revealed.
def build_pattern(solution: str, num_filled: int) -> list[str]:
    pattern = ["_"] * len(solution)
    fill_positions = random.sample(range(len(solution) - 1), num_filled)
    for pos in fill_positions:
        pattern[pos] = solution[pos]
    return pattern


# --- Guess Evaluation ---

@dataclass
class GuessResult:
    guesses: list[str] = field(default_factory=lambda: [""] * TOP_N_GUESSES)
    confidences: list[float] = field(default_factory=lambda: [0.0] * TOP_N_GUESSES)
    top1_correct: bool = False
    top5_correct: bool = False


def evaluate_clue(clue: Clue, pattern: list[str], solution: str, self_consistency: bool) -> GuessResult:
    result = GuessResult()

    if self_consistency:
        clue_guesses = get_guesses_with_self_consistency(clue, pattern, filter=False, debug=True)
    else: 
        clue_guesses = get_guesses_for_clue_using_llm(clue, pattern, filter=False, debug=True)

    for i, guess in enumerate(clue_guesses[:TOP_N_GUESSES]):
        result.guesses[i] = guess.answer
        result.confidences[i] = guess.confidence_score

    result.top5_correct = solution in result.guesses
    result.top1_correct = result.guesses[0] == solution
    return result


# --- Result Building ---

RESULT_COLUMNS = [
    "file", "date", "day_of_week", "number", "direction", "length",
    "text", "solution", "pattern",
    *[f"guess{i}" for i in range(1, TOP_N_GUESSES + 1)],
    *[f"confidence{i}" for i in range(1, TOP_N_GUESSES + 1)],
]


def build_result_row(row: pd.Series, solution: str, pattern: list[str], result: GuessResult) -> list:
    return [
        row["file"], row["date"], row["day_of_week"], row["number"],
        row["direction"], row["length"], row["text"], solution,
        " ".join(pattern),
        *result.guesses,
        *result.confidences,
    ]


# --- Main ---

def _exit(message: str) -> None:
    sys.exit(message)


def main() -> None:
    start = datetime.now()

    config = parse_args()
    config.validate()

    clues = load_clues(INPUT_CSV, config)

    results = []
    top1_success = 0
    top5_success = 0

    for _, row in clues.iterrows():
        print(row)
        clue = Clue(
            text=row["text"],
            length=row["length"],
            number=row["number"],
            direction=row["direction"],
        )
        solution = row["solution"]
        pattern = build_pattern(solution, config.num_filled)
        result = evaluate_clue(clue, pattern, solution, config.self_consistency)

        if result.top1_correct:
            top1_success += 1
        if result.top5_correct:
            top5_success += 1

        results.append(build_result_row(row, solution, pattern, result))

    results_df = pd.DataFrame(results, columns=RESULT_COLUMNS)
    os.makedirs(os.path.dirname(config.output_path), exist_ok=True)
    results_df.to_csv(config.output_path, index=False)

    elapsed = datetime.now() - start
    print(f"Elapsed time: {elapsed}")

    total = len(clues)
    print("Successfully wrote results to CSV file: {config.output_path}.")
    print(f"Top-1 success rate: {top1_success}/{total} ({top1_success/total:.1%})")
    print(f"Top-5 success rate: {top5_success}/{total} ({top5_success/total:.1%})")


if __name__ == "__main__":
    main()