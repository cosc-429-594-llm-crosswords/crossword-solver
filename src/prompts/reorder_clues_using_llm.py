from functools import cache

from llama_index.core.prompts import RichPromptTemplate
from llama_index.llms.ollama import Ollama

from src.classes.clue import Clue
from src.classes.ranked_clues import RankedClues
from src.constants import CLUE_ID, LLM_MODEL

PROMPT_TEMPLATE = RichPromptTemplate(
    """
You are a crossword puzzle solver. You are given a list of crossword clues.
Assign each clue a difficulty score from 1 to 100, with 1 being the easiest and 100 being the hardest.
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
        context_window=1000,
        temperature=0.1,
        json_mode=True,
    )


def __missing_clues(clues: list[Clue], difficulty_scores: dict[CLUE_ID, int]) -> list[Clue]:
    return [clue for clue in clues if clue.id not in difficulty_scores]


def __collect_difficulty_scores(clues: list[Clue], debug: bool = False) -> dict[CLUE_ID, int]:
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
            clue_id: CLUE_ID = (ranked_clue.number, ranked_clue.direction)
            difficulty_scores[clue_id] = ranked_clue.difficulty_score

        clues_to_score = __missing_clues(clues, difficulty_scores)

    return difficulty_scores


def reorder_clues_using_llm(clues: list[Clue], debug: bool = False) -> list[Clue]:
    difficulty_scores = __collect_difficulty_scores(clues, debug)

    clues.sort(key=lambda clue: difficulty_scores[clue.id])

    if debug:
        print(f"=== REORDERED CLUES {LLM_MODEL} ===")
        for clue in clues:
            print(
                f"  {clue.number} {clue.direction}: {clue.text} (Difficulty: {difficulty_scores[clue.id]})"
            )

    return clues
