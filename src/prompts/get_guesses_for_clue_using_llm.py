from functools import cache

from llama_index.core.prompts import RichPromptTemplate
from llama_index.llms.ollama import Ollama

from src.classes.clue import Clue
from src.classes.guesses import Guess, Guesses
from src.constants import LLM_MODEL

PROMPT_TEMPLATE = RichPromptTemplate(
    """
You are an expert crossword solver whose goal is to generate valid guesses for a crossword clue based on the clue's text and known letter constraints.
Each guess should be accompanied by a confidence score between 0 and 100, as well as a brief explanation of how it satisfies the clue and letter constraints.
The sum of the confidence scores for all guesses should not exceed 100, and higher confidence scores should be assigned to guesses that better satisfy the clue and letter constraints according to the rules outlined below.
It is acceptable to return fewer than five guesses if there are not enough valid options that meet the criteria, but do not return any guesses that violate the rules.
It is better to return fewer high-quality guesses than to include low-quality guesses that do not satisfy the clue and letter constraints well.

### CROSSWORD RULES
The following are rules for generating valid guesses from most to least important. Prioritize guesses that satisfy more of these rules, and assign higher confidence scores to those guesses accordingly.
1. RELEVANCE: The guesses should directly relate to the whole clue, not just a part of it, and should be commonly associated with the clue's wording and theme. DO NOT include guesses that are only remotely related to the clue or require multiple leaps of logic to connect them to the clue's meaning.
2. LETTER CONSTRAINT MATCHING: Guesses must fit the specified letter constraints, matching known letters in their exact positions and having the correct length. The constraints are always correct and should be strictly followed.
3. INTEGRITY: DO NOT include spaces, numbers, or punctuation. Guesses must be valid, correctly spelled dictionary words.
4. GRAMMATICAL CONSISTENCY: Guesses must match the clue's grammatical requirements, including tense, part of speech, and number (singular/plural).
5. UNIQUENESS: All five guesses must be distinct from each other, providing a variety of plausible answers rather than minor variations on the same word.
6. SIMPLICITY: Guesses should be straightforward and not require convoluted reasoning or obscure knowledge to connect them to the clue. Simpler, more direct guess should also have higher confidence scores than more complex, less direct guesses.
7. MAXIMUM CONFIDENCE SCORE: The sum of the confidence scores for all guesses should not exceed 100. Assign higher confidence scores to guesses that better satisfy the above rules, and ensure that the total does not exceed this limit.


### Input Variables
The following is the clue your are trying to solve:

{{ clue_text }}

The answer has {{ letter_constraint_length }} letters, with the following known letter constraints:

{{ letter_constraint_text }}

### OUTPUT FORMAT
Return up to five guesses, each with a confidence score and a brief explanation of how it satisfies the clue and letter constraints.

### Example Output
Clue: "A black and white animal"
Pattern: "_ _ _ _ _"
Number of letters: 5
[
    {
        "answer": "ZEBRA",
        "confidence_score": 60,
        "explanation": "ZEBRA is a strong guess for this clue because it is a well-known animal that is characterized by its distinctive black and white striped coat."
    },
    {
        "answer": "PANDA",
        "confidence_score": 40,
        "explanation": "PANDA is a valid guess for this clue because it is a well-known animal that is characterized by its distinctive black and white fur. However, PANDA is less likely than ZEBRA because it is not as commonly associated with the phrase 'black and white animal' and may require a slightly more specific knowledge of animals to connect it to the clue."
    }
]
""".strip()
)


@cache
def __get_llm() -> Ollama:
    llm = Ollama(
        model=LLM_MODEL,
        request_timeout=1200.0,
        context_window=1000,
        temperature=0.1,
        json_mode=True,
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


def filter_invalid_guesses(guesses: list[Guess], pattern: list[str]) -> list[Guess]:
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

    return filter_invalid_guesses(response.guesses, pattern)
