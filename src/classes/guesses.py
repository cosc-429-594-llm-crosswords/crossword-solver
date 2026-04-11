from llama_index.core.bridge.pydantic import BaseModel, Field


class Guess(BaseModel):
    answer: str = Field(
        description="The answer to the clue, fitting the specified length and any known letters. The answer should be in uppercase and should not contain spaces or punctuation."
    )
    confidence_score: int = Field(
        description="A confidence score between 0 and 100 indicating the likelihood that this answer is correct."
    )
    explanation: str = Field(
        description="A brief explanation of how the clue leads to this answer."
    )


class Guesses(BaseModel):
    guesses: list[Guess] = Field(
        description="A list of five unique guesses matching the clue and pattern."
    )
