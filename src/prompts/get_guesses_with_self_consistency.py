from functools import cache

import requests
from llama_index.core.prompts import RichPromptTemplate
from llama_index.llms.ollama import Ollama

from src.classes.clue import Clue
from src.classes.guesses import Guess, Guesses
from src.constants import (
    DEFAULT_MAX_GUESSES,
    DEFAULT_NUM_SAMPLES,
    LETTERS,
    LLM_MODEL,
    SUGGESTION_CHAR_THRESHOLD,
    UNKNOWN_LETTER,
)
from src.helpers.sanitize_guess import sanitize_guess

PROMPT_TEMPLATE = RichPromptTemplate(
    """\
You are a crossword expert. Provide up to five potential answers for the following clue.

<Constraints>
- Clue: {{ clue_text }}
- Length: {{ pattern_length }} letters
- Pattern:
{{ pattern_text }}
</Constraints>

<Instructions>
1. **READ THE CLUE CAREFULLY.** Consider all interpretations, including literal meanings, synonyms, and wordplay.
2. **INDEPENDENT BRAINSTORM:** Before looking at suggestions, generate your own list of valid English words that fit the length, pattern, and thematic essence of the clue.
3. **API EVALUATION:** Review the provided Suggestions list if it is available. If the list is empty or the words are logically weak, rely on your internal brainstormed words. 
4. **FINAL SELECTION:** Pick words that most logically fit. If the clue has a QUESTION MARK (?), prioritize puns, literalisms (e.g., "Stocking stuffer" = SANTA), or double meanings. Look for the "hidden gem" in the list that fits the theme perfectly.
5. **ACCENT HANDLING:** If a word has an accent mark (e.g., É), use the standard English alphabet equivalent (e.g., E).
</Instructions>

<Guidelines>
1. **VALIDITY:** Every guess MUST be a real English word or a common crossword abbreviation.
2. **EXACT LENGTH:** Every word MUST be exactly {{ pattern_length }} letters long.
3. **NO ILLEGAL ABBREVIATIONS:** Do not shorten words (e.g., "MUSTA" for "MUSTARD") unless the clue explicitly hints at an abbreviation (using "Abbr.", "Abbrev.", or a shortened word in the clue).
4. **LOGIC:** The explanation must be a full sentence (5+ characters) justifying the connection between the word and the clue.
5. **NO DUPLICATES:** Do not include the same word more than once in your response.
6. **NO ANSWERS IN CLUES:** Clues do not contain the answer within them. Avoid selecting words that are directly mentioned in the clue.
7. **CLEAN OUTPUT:** Ensure that the output answer does not contain spaces, numbers, or special characters.
8. **NO HALLUCINATIONS:** Do not generate words that do not exist or don't make logical sense with the clue.
</Guidelines>

<Suggestions>
{% if suggestions %}
    The following words match the pattern but may not fit the clue. Treat them as secondary references:
    {% for word in suggestions %}
        - {{ word.word }}
    {% endfor %}
{% else %}
    No external suggestions provided. Rely entirely on your expert internal vocabulary.
{% endif %}
</Suggestions>

<Response Format>
Return ONLY a JSON object following this structure:
{
    "target_length": {{ pattern_length }},
    "guesses": [
        {
            "word": "EXAMPLE",
            "confidence": 95, (integer from 0 to 100 indicating confidence level)
            "explanation": "Provide a detailed, logical sentence explaining the wordplay or definition."
        }
    ]
}
""".strip()
)


def __get_suggestions(pattern: list[LETTERS]) -> list[dict[str, str | int]]:
    word_length = len(pattern)
    pattern_str = "".join([letter if letter != UNKNOWN_LETTER else "?" for letter in pattern])
    url = f"https://api.datamuse.com/words?sp={pattern_str}&max=25"

    number_of_known_letters = sum(1 for letter in pattern if letter != UNKNOWN_LETTER)
    if number_of_known_letters < SUGGESTION_CHAR_THRESHOLD:
        return []

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        suggestions = []

        for item in data:
            word = sanitize_guess(item.get("word", ""))
            score = item.get("score", 0)
            if len(word) == word_length:
                suggestions.append({"word": word, "score": score})

        return suggestions
    else:
        print(f"Error fetching suggestions: {response.status_code}")
        return []


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
    valid_guesses = set()
    for guess in guesses:
        if len(guess.answer) != len(pattern):
            continue

        is_valid = True
        for g_char, p_char in zip(guess.answer, pattern, strict=True):
            if p_char != "_" and g_char != p_char:
                is_valid = False
                break

        if is_valid:
            valid_guesses.add(guess)

    return list(valid_guesses)


def __get_guesses_for_clue_using_llm(
    clue: Clue, pattern: list[str], filter: bool, debug: bool, include_suggestions: bool = False
) -> list[Guess]:
    llm = __get_llm()
    pattern_text = __generate_pattern_text(pattern)
    suggestions = __get_suggestions(pattern) if include_suggestions else []

    if debug:
        print(f"=== GENERATE GUESSES with {LLM_MODEL} ===")
        print(
            PROMPT_TEMPLATE.format(
                clue_text=clue.text,
                pattern_length=clue.length,
                pattern_text=pattern_text,
                suggestions=suggestions,
            )
        )

    response: Guesses = llm.structured_predict(
        Guesses,
        PROMPT_TEMPLATE,
        clue_text=clue.text,
        pattern_length=clue.length,
        pattern_text=pattern_text,
        suggestions=suggestions,
    )

    response.guesses.sort(key=lambda x: x.confidence_score, reverse=True)

    if debug:
        print(f"=== GENERATED GUESSES with {LLM_MODEL} ===")
        for guess in response.guesses:
            print(f"{guess.answer} (confidence: {guess.confidence_score}) - {guess.explanation}")

    if filter:
        return __filter_invalid_guesses(response.guesses, pattern)
    else: 
        return(response.guesses)


def get_guesses_with_self_consistency(
    clue,
    pattern: list[str],
    num_samples: int = DEFAULT_NUM_SAMPLES,
    max_guesses: int = DEFAULT_MAX_GUESSES,
    filter: bool = True,
    include_suggestions: bool = False,
    debug: bool = False,
) -> list[Guess]:
    all_runs: list[list[Guess]] = []

    for i in range(num_samples):
        if debug:
            print(f"  [Self-consistency] Sample {i + 1}/{num_samples}...")
        run_guesses = __get_guesses_for_clue_using_llm(
            clue, pattern, filter=filter, debug=debug, include_suggestions=include_suggestions
        )

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
