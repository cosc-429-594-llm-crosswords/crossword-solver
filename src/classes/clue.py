import dataclasses

from src.constants import CLUE_ID, DIRECTIONS


# This class store all the important information for a given clue
@dataclasses.dataclass
class Clue:
    text: str
    length: int
    number: int
    direction: DIRECTIONS
    row: int = 0
    col: int = 0

    # The clue id is a combination of the clue number and direction.
    # Note, all combinations of clue numbers and directions are not valid.
    @property
    def id(self) -> CLUE_ID:
        return (self.number, self.direction)

    def __hash__(self):
        return hash(self.id)
