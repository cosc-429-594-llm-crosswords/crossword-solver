from functools import cache

from llama_index.core.prompts import RichPromptTemplate
from llama_index.llms.ollama import Ollama

from src.classes.clue import Clue
from src.classes.ranked_clues import RankedClues
from src.constants import CLUE_ID, LLM_MODEL

PROMPT_TEMPLATE = RichPromptTemplate(
    """
You are a crossword puzzle solver. You are given a list of crossword clues.
Assign each clue a difficulty score from 0 to 100, with 0 being the easiest and 100 being the hardest.
Provide a brief explanation of why each clue is considered to have the given difficulty score,
including any wordplay, obscurity, or other factors that contribute to its difficulty.
If you cannot score a clue confidently, omit it so it can be retried separately.

Clues:
{% for clue in clues %}
- ({{ clue.number }} {{ clue.direction }}): {{ clue.text }}
{% endfor %}
"""
)


@cache
def __get_llm() -> Ollama:
    return Ollama(
        model=LLM_MODEL,
        request_timeout=1200.0,
        temperature=0.0,
        json_mode=True,
    )


def __missing_clues(clues: list[Clue], difficulty_scores: dict[CLUE_ID]) -> list[Clue]:
    return [clue for clue in clues if clue.id not in difficulty_scores]


def __calculate_difficulty_scores(clues: list[Clue], debug: bool = False) -> dict[CLUE_ID, int]:
    llm = __get_llm()

    difficulty_scores: dict[CLUE_ID, int] = {}
    clues_to_score = clues
    attempts = 0

    while clues_to_score:
        attempts += 1
        if attempts > len(clues) + 1:
            missing = ", ".join(f"({clue.number} {clue.direction})" for clue in clues_to_score)
            raise ValueError(
                f"Unable to score all clues after repeated LLM calls. Missing: {missing}"
            )

        if debug:
            print(f"=== REORDER CLUES with {LLM_MODEL} (Attempts: {attempts}) ===")
            print(PROMPT_TEMPLATE.format(clues=clues_to_score))

        ranked_clues: RankedClues = llm.structured_predict(
            RankedClues,
            PROMPT_TEMPLATE,
            clues=clues_to_score,
        )

        for ranked_clue in ranked_clues.ranked_clues:
            print(
                f"Scored Clue ({ranked_clue.number} {ranked_clue.direction}): Difficulty Score = {ranked_clue.difficulty_score} - Explanation: {ranked_clue.explanation}"
            )
            clue_id: CLUE_ID = (ranked_clue.number, ranked_clue.direction)
            difficulty_scores[clue_id] = ranked_clue.difficulty_score

        clues_to_score = __missing_clues(clues, difficulty_scores)

    return difficulty_scores


def get_clue_difficulty_with_llm(clues: list[Clue], debug: bool = False) -> dict[CLUE_ID, int]:
    difficulty_scores = __calculate_difficulty_scores(clues, debug)

    if debug:
        print("=== FINAL CLUE DIFFICULTY SCORES ===")
        for clue in clues:
            clue_id: CLUE_ID = (clue.number, clue.direction)
            score = difficulty_scores.get(clue_id, "N/A")
            print(f"Clue ({clue.number} {clue.direction}): Difficulty Score = {score}")

    return difficulty_scores
