from functools import cache

from llama_index.llms.ollama import Ollama

from src.classes.guesses import Guesses
from src.constants import LLM_MODEL


@cache
def __get_structured_llm() -> Ollama:
    llm = Ollama(
        model=LLM_MODEL,
        request_timeout=1200.0,
        context_window=1000,
        temperature=0.1,
        json_mode=True,
    )

    return llm.as_structured_llm(Guesses)


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


def __generate_prompt(clue: str, pattern: list[str]) -> str:
    constraints = []
    for i, letter in enumerate(pattern, start=1):
        status = f"is {letter}" if letter != "_" else "is unknown"
        constraints.append(f"The {__get_ordinal(i)} letter {status}.")

    pattern_text = "\n".join(constraints)

    return (
        f"You are a crossword solver. Provide five unique guesses matching the clue and pattern.\n\n"
        f"Constraints:\n"
        f"- Clue: {clue}\n"
        f"- Length: {len(pattern)} letters\n"
        f"{pattern_text}\n\n"
        f"Final Output:\n"
        f"Return only the matching words in ALL CAPS, a confidence score (0-10), and an explanation. "
        f"No spaces or punctuation in guesses."
    )


def get_guesses_for_clue_using_llm(clue: str, pattern: list[str]) -> Guesses:
    structured_llm = __get_structured_llm()
    prompt = __generate_prompt(clue, pattern)

    response: Guesses = structured_llm.complete(prompt).raw
    response.guesses.sort(key=lambda x: x.confidence_score, reverse=True)

    return response
