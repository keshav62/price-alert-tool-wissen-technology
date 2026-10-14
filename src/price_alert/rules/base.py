from abc import ABC, abstractmethod

from price_alert.models.alert import Alert
from price_alert.models.price import Price
from price_alert.models.rule import Rule


class BaseRule(ABC):
    """Common interface for all alert rule implementations."""

    @abstractmethod
    def evaluate(
        self,
        prices: list[Price],
        rule: Rule,
    ) -> list[Alert]:
        """Evaluate a rule against price history."""
        raise NotImplementedError