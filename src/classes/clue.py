import dataclasses

from src.constants import DIRECTIONS


@dataclasses.dataclass
class Clue:
    text: str
    length: int
    number: int
    direction: DIRECTIONS
    row: int
    col: int

    @property
    def id(self) -> tuple[int, DIRECTIONS]:
        return (self.number, self.direction)

    def __hash__(self):
        return hash(self.id)
