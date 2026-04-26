import dataclasses

from src.constants import CLUE_ID, DIRECTIONS


@dataclasses.dataclass
class Clue:
    text: str
    length: int
    number: int
    direction: DIRECTIONS
    row: int = 0
    col: int = 0

    @property
    def id(self) -> CLUE_ID:
        return (self.number, self.direction)

    def __hash__(self):
        return hash(self.id)
