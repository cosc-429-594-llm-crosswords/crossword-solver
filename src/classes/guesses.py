from llama_index.core.bridge.pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)

from src.helpers.sanitize_guess import sanitize_guess


class Guess(BaseModel):
    explanation: str = Field(
        description="A brief explanation of how the clue leads to this answer."
    )
    confidence_score: int = Field(
        description="A confidence score between 0 and 100 indicating the likelihood that this answer is correct."
    )
    answer: str = Field(
        description="The answer to the clue, fitting the specified length and any known letters. The answer should be in uppercase and should not contain spaces or punctuation."
    )

    @field_validator("answer", mode="after")
    @classmethod
    def clean_guess(cls, guess: str) -> str:
        return sanitize_guess(guess)

    def __hash__(self):
        return hash(self.answer)


class Guesses(BaseModel):
    guesses: list[Guess] = Field(
        description="A list of five unique guesses matching the clue and pattern."
    )
    target_length: int = Field(description="The required length of the word.")

    @model_validator(mode="after")
    def validate_and_normalize(self):
        print(
            f"  [DEBUG] LLM raw guesses: {[(g.answer, g.confidence_score) for g in self.guesses]}"
        )

        valid_guesses = []
        for g in self.guesses:
            if len(g.answer) == self.target_length:
                valid_guesses.append(g)
            else:
                print(
                    f"  [DEBUG] Rejected: '{g.answer}' (Length {len(g.answer)} != {self.target_length})"
                )

        self.guesses = valid_guesses
        total_score = sum(g.confidence_score for g in self.guesses)
        if total_score > 0:
            for guess in self.guesses:
                guess.confidence_score = round((guess.confidence_score / total_score) * 100, 2)
        else:
            print("  [DEBUG] Result: No guesses survived the length filter.")

        return self
