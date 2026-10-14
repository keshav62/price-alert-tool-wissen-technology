
from price_alert.models.alert import Alert
from price_alert.models.price import Price
from price_alert.models.rule import Rule
from price_alert.rules.registry import RuleRegistry


class RuleEvaluator:
    """Evaluate an individual alert rule."""

    def __init__(self, registry: RuleRegistry | None = None) -> None:
        self._registry = registry or RuleRegistry()

    def evaluate(
        self,
        prices: list[Price],
        rule: Rule,
    ) -> list[Alert]:
        implementation = self._registry.get(rule.type)
        return implementation.evaluate(prices, rule)
