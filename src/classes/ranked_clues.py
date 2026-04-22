from llama_index.core.bridge.pydantic import BaseModel, Field


class RankedClue(BaseModel):
    number: int = Field(description="The clue number as it appears in the crossword puzzle.")
    direction: str = Field(description="The direction of the clue, either 'across' or 'down'.")
    difficulty_score: int = Field(
        description="A difficulty score between 0 and 100 indicating how difficult the clue is to solve. Higher scores indicate greater difficulty."
    )
    explanation: str = Field(
        description="A brief explanation of why this clue is considered difficult, based on factors such as ambiguity, wordplay, or obscurity."
    )


class RankedClues(BaseModel):
    ranked_clues: list[RankedClue] = Field(
        description="A list of clues ranked by their difficulty score, with the most difficult clue first."
    )

class RankedCluesCopy(BaseModel):
    ranked_clues: list[RankedClue] = Field(
        description="A list of clues ranked by their difficulty score, with the least difficult clue first."
    )
