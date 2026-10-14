
from price_alert.engine.evaluator import RuleEvaluator
from price_alert.models.alert import Alert
from price_alert.models.price import Price
from price_alert.models.rule import Rule


class AlertEngine:
    """Evaluate configured rules and collect ordered alerts."""

    def __init__(self, evaluator: RuleEvaluator | None = None) -> None:
        self._evaluator = evaluator or RuleEvaluator()

    def run(
        self,
        prices: list[Price],
        rules: list[Rule],
    ) -> list[Alert]:
        alerts: list[Alert] = []

        for rule in rules:
            alerts.extend(self._evaluator.evaluate(prices, rule))

        return sorted(
            alerts,
            key=lambda alert: (alert.date, alert.rule_id),
        )
