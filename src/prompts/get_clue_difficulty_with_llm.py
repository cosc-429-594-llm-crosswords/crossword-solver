from functools import cache

from llama_index.core.prompts import RichPromptTemplate
from llama_index.llms.ollama import Ollama

from src.classes.clue import Clue
from src.classes.ranked_clues import RankedClue, RankedClues
from src.constants import CLUE_ID, LLM_MODEL

VAGUENESS_WEIGHT = 0.67
COMPLEXITY_WEIGHT = 0.33

PROMPT_TEMPLATE = RichPromptTemplate(
    """
You are a crossword puzzle solver. You are given a list of crossword clues with the goal of assigning a vagueness score and a complexity score to each.
Assign each clue a vagueness score from 0 to 100, with 0 being the least vague and 100 being the most vague.
Assign each clue a complexity score from 0 to 100, with 0 being the least complex and 100 being the most complex.
Provide a brief explanation of why each clue is considered to have the given vagueness and complexity scores,including any wordplay, obscurity, or other factors that contribute to its difficulty.
At the end of the explanation, provide some potential answers that could fit the clue, which can help illustrate the vagueness and complexity of the clue.
Clues are less vague if they have only one obvious answer, while more vague clues have multiple plausible answers or interpretations, making them harder to solve.
Clues are more complex when they require multiple steps of reasoning, involve intricate wordplay, or require knowledge of obscure references, making them more challenging for solvers to decipher.

Example Clues:

Chinese-zodiac animal (5 letters)
Vagueness score: 82
Complexity score: 11
Explanation: This clue is very vague, because there are multiple 5 letter Chinese zodiac animals ("HORSE", "TIGER", "SNAKE"), but it is not difficult because it does not require any obscure knowledge, or multiple steps of reasoning.

The "p" of m.p.h (3 letters)
Vagueness score: 19
Complexity score: 42
Explanation: The answer to this clue is obvious, because there is only one standard interpretation for m.p.h.. It is not difficult, but complexity is higher because it requires two steps of reasoning: m.p.h commonly means miles per hour => the 'p' in m.p.h. means per

Reason to edit a text message (4 letters)
Vagueness score: 100
Complexity score: 27
Explanation: With 4 letters, there are many plausible answers ("TYPO", "EDIT", "OOPS", "REDO", etc.). The clue remains quite open-ended. Complexity is low since it's a straightforward conceptual clue without wordplay.

Quickly change the topic (5 letters)
Vagueness score: 100
Complexity score: 56
Explanation: Multiple valid synonyms exist ("PIVOT", "EVADE", "SEGUE", "SHIFT", etc.), making it very vague. It's mildly more complex because the solver may need to think in terms of idiomatic expressions rather than a direct synonym.

Swedish furniture giant (4 letters)
Vagueness score: 16
Complexity score: 24
Explanation: There is only one obvious answer ("IKEA"), but requires some cultural knowledge.

Here are your clues to score:
{% for clue in clues %}
- ({{ clue.number }} {{ clue.direction }}): {{ clue.text }} ({{ clue.length }} letters)
{% endfor %}
"""
)


@cache
def __get_llm() -> Ollama:
    return Ollama(
        model=LLM_MODEL,
        request_timeout=1200.0,
        json_mode=True,
        context_window=8000,
        temperature=0,
        top_p=1,
        top_k=1,
    )


def __missing_clues(clues: list[Clue], difficulty_scores: dict[CLUE_ID]) -> list[Clue]:
    return [clue for clue in clues if clue.id not in difficulty_scores]


def __get_difficulty_score(ranked_clue: RankedClue, debug: bool = False) -> int:
    if debug:
        print(
            f"""Scored Clue ({ranked_clue.number} {ranked_clue.direction}):
            - Vagueness Score = {ranked_clue.vagueness_score},
            - Complexity Score = {ranked_clue.complex_score},
            - Explanation: {ranked_clue.explanation}"""
        )

    return int(
        VAGUENESS_WEIGHT * ranked_clue.vagueness_score
        + COMPLEXITY_WEIGHT * ranked_clue.complex_score
    )


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
            clue_id: CLUE_ID = (ranked_clue.number, ranked_clue.direction)
            difficulty_scores[clue_id] = __get_difficulty_score(ranked_clue, debug)

        clues_to_score = __missing_clues(clues, difficulty_scores)
    return difficulty_scores


def get_clue_difficulty_with_llm(clues: list[Clue], debug: bool = False) -> dict[CLUE_ID, int]:
    difficulty_scores = __calculate_difficulty_scores(clues, debug)

    if debug:
        print("=== FINAL CLUE DIFFICULTY SCORES ===")
        clues = sorted(
            clues,
            key=lambda clue: difficulty_scores.get((clue.number, clue.direction), -1),
        )
        for clue in clues:
            score = difficulty_scores.get((clue.number, clue.direction), "N/A")
            print(
                f"Clue ({clue.number} {clue.direction}): Difficulty Score = {score} | {clue.text}"
            )
    return difficulty_scores
