from functools import cache

from llama_index.llms.ollama import Ollama

from src.classes.clue import Clue
from src.classes.ranked_clues import RankedClues
from src.constants import CLUE_ID, LLM_MODEL


@cache
def __get_structured_llm() -> Ollama:
    llm = Ollama(
        model=LLM_MODEL,
        request_timeout=1200.0,
        context_window=1000,
        temperature=0.1,
        json_mode=True,
    )

    return llm.as_structured_llm(RankedClues)


def __generate_prompt(clues: list[Clue]) -> str:
    clues_text = "\n".join(f"- ({clue.number} {clue.direction}): {clue.text}" for clue in clues)
    return (
        "You are a crossword puzzle solver. You are given a list of crossword clues. "
        "Assign each clue a difficulty score from 1 to 100, with 1 being the easiest and 100 being the hardest. "
        "Provide a brief explanation of why each clue is considered to have the given difficulty score, "
        "including any wordplay, obscurity, or other factors that contribute to its difficulty. "
        "If you cannot score a clue confidently, omit it so it can be retried separately.\n\n"
        f"Clues:\n{clues_text}"
    )


def __missing_clues(clues: list[Clue], difficulty_scores: dict[CLUE_ID, int]) -> list[Clue]:
    return [clue for clue in clues if clue.id not in difficulty_scores]


def __collect_difficulty_scores(
    structured_llm: Ollama,
    clues: list[Clue],
) -> dict[CLUE_ID, int]:
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

        prompt = __generate_prompt(clues_to_score)
        ranked_clues: RankedClues = structured_llm.complete(prompt).raw

        for ranked_clue in ranked_clues.ranked_clues:
            clue_id: CLUE_ID = (ranked_clue.number, ranked_clue.direction)
            difficulty_scores[clue_id] = ranked_clue.difficulty_score

        clues_to_score = __missing_clues(clues, difficulty_scores)

    return difficulty_scores


def reorder_clues_using_llm(clues: list[Clue]) -> list[Clue]:
    structured_llm = __get_structured_llm()
    difficulty_scores = __collect_difficulty_scores(structured_llm, clues)

    clues.sort(reverse=True, key=lambda clue: difficulty_scores[clue.id])

    return clues
