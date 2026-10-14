from decimal import Decimal

from price_alert.models.alert import Alert
from price_alert.models.price import Price
from price_alert.models.rule import Rule
from price_alert.rules.base import BaseRule


class LevelRule(BaseRule):
    """Detect when a closing price crosses a configured level."""

    def evaluate(
        self,
        prices: list[Price],
        rule: Rule,
    ) -> list[Alert]:
        if rule.type != "level":
            raise ValueError("LevelRule only supports 'level' rules.")

        if rule.level is None:
            raise ValueError("Level rule requires a threshold.")

        if rule.direction not in ("above", "below"):
            raise ValueError("Direction must be 'above' or 'below'.")

        if not rule.level.is_finite() or rule.level <= 0:
            raise ValueError("Level must be finite and positive.")

        # Select only the configured instrument and sort its history.
        instrument_prices = sorted(
            (
                price
                for price in prices
                if price.instrument == rule.instrument
            ),
            key=lambda price: price.date,
        )

        alerts: list[Alert] = []
        level: Decimal = rule.level

        # A crossing requires both a previous and current price.
        for previous, current in zip(
            instrument_prices,
            instrument_prices[1:],
        ):
            if rule.direction == "below":
                crossed = (
                    previous.close >= level
                    and current.close < level
                )
            else:
                crossed = (
                    previous.close <= level
                    and current.close > level
                )

            if crossed:
                alerts.append(
                    Alert(
                        date=current.date,
                        rule_id=rule.id,
                        instrument=rule.instrument,
                        message=(
                            f"level {rule.direction} "
                            f"{format(level, 'f')}"
                        ),
                    )
                )

        return alerts