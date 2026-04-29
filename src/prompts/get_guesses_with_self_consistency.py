from functools import cache

from llama_index.core.prompts import RichPromptTemplate
from llama_index.llms.ollama import Ollama

from src.classes.clue import Clue
from src.classes.guesses import Guess, Guesses
from src.constants import DEFAULT_MAX_GUESSES, DEFAULT_NUM_SAMPLES, LLM_MODEL

PROMPT_TEMPLATE = RichPromptTemplate(
    """
You are a crossword expert. Provide up to five different guesses that fit the clue and pattern.
Constraints:
- Clue: {{ clue_text }}
- Length: {{ pattern_length }} letters

{{ pattern_text }}

Final Output:
Return only your guesses in ALL CAPS, a confidence score (0-100), and an explanation. Every letter used must be in the English alphabet. 
No spaces, numbers, or punctuation in guesses. 
Do not hallucinate. Every guess MUST be a real word and MUST have a reasonable explanation that fits the guess.
If a letter in the word has an accent mark on it, but has a common alternative in the English alphabet, use the English letter instead.
If abbreviate, abbreviation, abbr., or abbrev. are not specified in the clue, then DO NOT abbreviate the guess to fit the pattern.
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
        top_p=1,
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


def __get_guesses_for_clue_using_llm(
    clue: Clue, pattern: list[str], debug: bool = False
) -> list[Guess]:
    try:
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
                print(
                    f"{guess.answer} (confidence: {guess.confidence_score}) - {guess.explanation}"
                )

        return __filter_invalid_guesses(response.guesses, pattern)
    except Exception:
        return []


def get_guesses_with_self_consistency(
    clue,
    pattern: list[str],
    num_samples: int = DEFAULT_NUM_SAMPLES,
    max_guesses: int = DEFAULT_MAX_GUESSES,
    debug: bool = False,
) -> list[Guess]:
    all_runs: list[list[Guess]] = []

    for i in range(num_samples):
        if debug:
            print(f"  [Self-consistency] Sample {i + 1}/{num_samples}...")
        run_guesses = __get_guesses_for_clue_using_llm(clue, pattern, debug=debug)

        all_runs.append(run_guesses)

    answer_scores: dict[str, list[float]] = {}
    answer_explanations: dict[str, str] = {}

    for run in all_runs:
        for guess in run:
            key = guess.answer.upper().strip()
            if key not in answer_scores:
                answer_scores[key] = []
                answer_explanations[key] = guess.explanation
            answer_scores[key].append(guess.confidence_score)

    aggregated: list[Guess] = []
    for answer, scores in answer_scores.items():
        mean_confidence = int(round(sum(scores) / num_samples, 0))

        aggregated.append(
            Guess(
                answer=answer,
                confidence_score=mean_confidence,
                explanation=answer_explanations[answer],
            )
        )

    aggregated.sort(key=lambda g: g.confidence_score, reverse=True)
    top_guesses = aggregated[:max_guesses]

    if debug:
        print(
            f"  [Self-consistency] Aggregated {len(answer_scores)} unique answers → top {len(top_guesses)}:"
        )
        for g in top_guesses:
            freq_count = len(answer_scores[g.answer.upper().strip()])
            print(
                f"    {g.answer} | score={g.confidence_score} | appeared in {freq_count}/{num_samples} runs"
            )

    return top_guesses
