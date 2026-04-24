from functools import cache

from llama_index.core.prompts import RichPromptTemplate
from llama_index.llms.ollama import Ollama

from src.classes.clue import Clue
from src.classes.guesses import Guess, Guesses
from src.constants import LLM_MODEL

PROMPT_TEMPLATE = RichPromptTemplate(
    """
You are a crossword solver. Provide up to five unique guesses matching the clue and pattern.
Constraints:
- Clue: {{ clue_text }}
- Length: {{ pattern_length }} letters

{{ pattern_text }}

Final Output:
Return only the matching words in ALL CAPS, a confidence score (0-100), and an explanation.
No spaces or punctuation in guesses.
Do not hallucinate. Every answer must have a reasonable explanation.
If a word generated has a confidence score of 95 or above but does not fit the pattern constraint, ignore the pattern constraint and fill in the puzzle with the word.
If abbreviate, abbreviation, abbr., or abbrev. are not specified in the clue, then do not abbreviate the answer to fit the pattern.
""".strip()
)


@cache
def __get_llm() -> Ollama:
    llm = Ollama(
        model=LLM_MODEL,
        request_timeout=1200.0,
        context_window=1000,
        json_mode=True,
        temperature=0.1,
        top_p=0.9,
        top_k=5,
    )

    return llm


def __get_ordinal(n: int) -> str:
    low_ordinals = {
        1: "first",
        2: "second",
        3: "third",
        4: "fourth",
        5: "fifth",
        6: "sixth",
        7: "seventh",
        8: "eighth",
        9: "ninth",
        10: "tenth",
    }
    return low_ordinals.get(n, f"{n}th")


def __generate_pattern_text(pattern: list[str]) -> str:
    constraints = []
    for i, letter in enumerate(pattern, start=1):
        status = f"is {letter}" if letter != "_" else "is unknown"
        constraints.append(f" - The {__get_ordinal(i)} letter {status}.")

    return "\n".join(constraints)


def __filter_invalid_guesses(guesses: list[Guess], pattern: list[str]) -> list[Guess]:
    valid_guesses = []
    for guess in guesses:
        if len(guess.answer) != len(pattern):
            continue

        is_valid = True
        for g_char, p_char in zip(guess.answer, pattern, strict=True):
            if p_char != "_" and g_char != p_char:
                is_valid = False
                break

        if is_valid:
            valid_guesses.append(guess)

    return valid_guesses


def get_guesses_for_clue_using_llm(
    clue: Clue, pattern: list[str], debug: bool = False
) -> list[Guess]:
    llm = __get_llm()
    pattern_text = __generate_pattern_text(pattern)

    if debug:
        print(f"=== GENERATE GUESSES with {LLM_MODEL} ===")
        print(
            PROMPT_TEMPLATE.format(
                clue_text=clue.text,
                pattern_length=clue.length,
                pattern_text=pattern_text,
            )
        )

    response: Guesses = llm.structured_predict(
        Guesses,
        PROMPT_TEMPLATE,
        clue_text=clue.text,
        pattern_length=clue.length,
        pattern_text=pattern_text,
    )

    response.guesses.sort(key=lambda x: x.confidence_score, reverse=True)

    if debug:
        print(f"=== GENERATED GUESSES with {LLM_MODEL} ===")
        for guess in response.guesses:
            print(f"{guess.answer} (confidence: {guess.confidence_score}) - {guess.explanation}")

    return __filter_invalid_guesses(response.guesses, pattern)
