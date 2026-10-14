
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


RuleType = Literal["level", "ma_cross"]
Direction = Literal["above", "below"]


@dataclass(frozen=True)
class Rule:
    id: str
    instrument: str
    type: RuleType
    direction: Direction
    level: Decimal | None = None
    short: int | None = None
    long: int | None = None
