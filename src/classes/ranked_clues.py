from llama_index.core.bridge.pydantic import BaseModel, Field


class RankedClue(BaseModel):
    number: int = Field(description="The clue number as it appears in the crossword puzzle.")
    direction: str = Field(description="The direction of the clue, either 'across' or 'down'.")
    explanation: str = Field(
        description="A brief explanation of why this clue is considered difficult, based on factors such as ambiguity, wordplay, or obscurity."
    )
    vagueness_score: int = Field(
        description="A vagueness score between 0 and 100 indicating how vague the clue is. Higher scores indicate greater vagueness. Clues are more vague when they have multiple plausible interpretations or potential multiple correct answers, making it harder for solvers to determine the intended meaning."
    )
    complex_score: int = Field(
        description="A complexity score between 0 and 100 indicating how complex the clue is to solve. Higher scores indicate greater complexity. Clues are more complex when they require multiple steps of reasoning, involve intricate wordplay, or require knowledge of obscure references, making them more challenging for solvers to decipher."
    )


class RankedClues(BaseModel):
    ranked_clues: list[RankedClue] = Field(
        description="A list of clues ranked by their difficulty score, with the least difficult clue first."
    )
