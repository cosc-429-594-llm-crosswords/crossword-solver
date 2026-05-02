import os

import pandas as pd

from src.classes.crossword_puzzle import CrosswordPuzzle
from src.classes.guesses import Guess
from src.constants import CLUE_ID, PUZ_FILE_DIR, RANKING_ALGORITHMS
from src.prompts.get_clue_difficulty_with_llm import get_clue_difficulty_with_llm
from src.prompts.get_guesses_with_self_consistency import get_guesses_with_self_consistency

MAX_LLM_CALLS = 50


def log_action(logs: pd.DataFrame, action: str, message: str):
    logs.loc[len(logs)] = {
        "timestamp": pd.Timestamp.now(),
        "action": action,
        "message": message,
    }

    print(f"[{pd.Timestamp.now()}] {action}: {message}")


def solve_crossword(filepath: str, ranking: RANKING_ALGORITHMS):
    logs = pd.DataFrame(columns=["timestamp", "action", "message"])
    file = f"{PUZ_FILE_DIR}/{filepath}.puz"
    crossword_puzzle = CrosswordPuzzle(file)
    guesses: dict[CLUE_ID, list[Guess]] = {}
    clue_difficulties: dict[CLUE_ID, int] = {}
    ranked_clues: list[CLUE_ID] = []

    llm_call_counter = 0

    os.makedirs("data/solve_crosswords/", exist_ok=True)

    try:
        if ranking in ["VAGUENESS_AND_COMPLEXITY_PLUS_KNOWN_LETTERS", "VAGUENESS_AND_COMPLEXITY"]:
            clue_difficulties = get_clue_difficulty_with_llm(
                crossword_puzzle.get_clues(), debug=True
            )
            log_action(
                logs, "get_clue_difficulties", f"Getting clue difficulties: {clue_difficulties}"
            )

        while not crossword_puzzle.is_solved and llm_call_counter < MAX_LLM_CALLS:
            log_action(logs, "print_grid", str(crossword_puzzle.get_letter_grid()))

            if ranking == "VAGUENESS_AND_COMPLEXITY_PLUS_KNOWN_LETTERS":
                number_of_known_letters = crossword_puzzle.get_number_of_known_letters_for_all_clues()
                ranked_clues = sorted(
                    crossword_puzzle.incomplete_clues,
                    key=lambda c: (-number_of_known_letters[c.id], clue_difficulties[c.id]),
                )

                log_action(
                    logs,
                    "determine_next_clue",
                    "".join(
                        [
                            f"{c.id} Number of known letters: {number_of_known_letters[c.id]} Difficulty: {clue_difficulties[c.id]}\n"
                            for c in ranked_clues
                        ]
                    ),
                )
            elif ranking == "VAGUENESS_AND_COMPLEXITY":
                ranked_clues = sorted(
                    crossword_puzzle.incomplete_clues,
                    key=lambda c: clue_difficulties[c.id],
                )
                log_action(
                    logs,
                    "determine_next_clue",
                    "".join(
                        [f"{c.id} Difficulty: {clue_difficulties[c.id]}\n" for c in ranked_clues]
                    ),
                )
            elif ranking == "NONE":
                ranked_clues = sorted(crossword_puzzle.incomplete_clues, key=lambda c: c.id)
                log_action(
                    logs,
                    "determine_next_clue",
                    "".join([f"{c.id}\n" for c in ranked_clues]),
                )
            else:
                log_action(logs, "param error", f"Error: Invalid ranking algorithm: {ranking}")
                exit(1)

            clue = ranked_clues[0]

            if clue.id not in guesses:
                pattern = crossword_puzzle.get_pattern(clue)
                clue_guesses = get_guesses_with_self_consistency(
                    clue,
                    pattern,
                    num_samples=3,
                    max_guesses=5,
                    include_suggestions=True,
                    debug=True,
                )
                guesses[clue.id] = clue_guesses
                llm_call_counter += 1

                log_action(
                    logs,
                    "get_guesses_with_llm",
                    f"Generating guesses for clue with self-consistency: {clue.id} {pattern}",
                )

            clue_guesses = guesses[clue.id]

            log_action(
                logs, "show_guesses", f"Guesses for the current clue: {clue.id} | {clue_guesses}"
            )

            if len(clue_guesses) == 0:
                guesses.pop(clue.id)

                if len(crossword_puzzle.completed_clues) > 0:
                    crossword_puzzle.remove_answer(crossword_puzzle.completed_clues[-1])

                if ranking in ["VAGUENESS_AND_COMPLEXITY_PLUS_KNOWN_LETTERS", "VAGUENESS_AND_COMPLEXITY"]:
                    clue_difficulties[clue.id] += 100
                log_action(
                    logs,
                    "backtrack",
                    f"Error setting answer for clue: {clue.id} - No valid guesses available",
                )

                continue

            best_guess = max(clue_guesses, key=lambda g: g.confidence_score)

            try:
                crossword_puzzle.set_answer(clue, best_guess.answer)
                clue_guesses.remove(best_guess)
                log_action(
                    logs, "set_answer", f"Setting answer for clue: {clue.id} - {best_guess.answer}"
                )

            except Exception as e:
                log_action(logs, "set_answer", f"Error setting answer for clue: {clue.id} - {e}")
                clue_guesses.remove(best_guess)

        if crossword_puzzle.is_solved:
            log_action(
                logs,
                "successful_solve",
                f"Crossword successfully solved in {llm_call_counter} guesses!",
            )
        else:
            log_action(
                logs, "failed_solve", f"LLM failed to solve crossword in {MAX_LLM_CALLS} guesses."
            )

        logs.to_csv(f"data/solve_crosswords/ranking_{ranking}_{filepath}.csv", index=False)

    except Exception as e:
        print(f"Error occurred: {e}")

        logs.to_csv(f"data/solve_crosswords/ranking_{ranking}_{filepath}.csv", index=False)
