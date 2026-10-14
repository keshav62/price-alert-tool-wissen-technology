
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Alert:
    date: date
    rule_id: str
    instrument: str
    message: str
