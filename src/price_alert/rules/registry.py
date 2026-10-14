
from price_alert.rules.base import BaseRule
from price_alert.rules.level_rule import LevelRule
from price_alert.rules.ma_cross_rule import MACrossRule


class RuleRegistry:
    """Resolve rule types to their implementations."""

    def __init__(self) -> None:
        self._rules: dict[str, BaseRule] = {
            "level": LevelRule(),
            "ma_cross": MACrossRule(),
        }

    def get(self, rule_type: str) -> BaseRule:
        """Return the implementation for a supported rule type."""
        try:
            return self._rules[rule_type]
        except KeyError:
            raise ValueError(
                f"Unsupported rule type: {rule_type!r}"
            ) from None
