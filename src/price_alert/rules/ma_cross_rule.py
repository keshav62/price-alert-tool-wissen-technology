
from price_alert.indicators.moving_average import (
    calculate_moving_average,
)
from price_alert.models.alert import Alert
from price_alert.models.price import Price
from price_alert.models.rule import Rule
from price_alert.rules.base import BaseRule


class MACrossRule(BaseRule):
    """Detect short and long moving-average crossovers."""

    def evaluate(self, prices: list[Price], rule: Rule) -> list[Alert]:
        if rule.type != "ma_cross":
            raise ValueError("MACrossRule only supports 'ma_cross' rules.")

        if rule.short is None or rule.long is None:
            raise ValueError("MA crossover rule requires short and long windows.")

        if (
            type(rule.short) is not int
            or type(rule.long) is not int
            or rule.short <= 0
            or rule.long <= 0
            or rule.short >= rule.long
        ):
            raise ValueError(
                "MA windows must be positive integers with short < long."
            )

        if rule.direction not in ("above", "below"):
            raise ValueError("Direction must be 'above' or 'below'.")

        instrument_prices = sorted(
            (
                price
                for price in prices
                if price.instrument == rule.instrument
            ),
            key=lambda price: price.date,
        )

        closes = [price.close for price in instrument_prices]

        short_ma = calculate_moving_average(closes, rule.short)
        long_ma = calculate_moving_average(closes, rule.long)

        alerts: list[Alert] = []

        for index in range(1, len(instrument_prices)):
            previous_short = short_ma[index - 1]
            previous_long = long_ma[index - 1]
            current_short = short_ma[index]
            current_long = long_ma[index]

            # Both averages must exist on both observations.
            if any(
                value is None
                for value in (
                    previous_short,
                    previous_long,
                    current_short,
                    current_long,
                )
            ):
                continue

            if rule.direction == "above":
                crossed = (
                    previous_short <= previous_long
                    and current_short > current_long
                )
            else:
                crossed = (
                    previous_short >= previous_long
                    and current_short < current_long
                )

            if crossed:
                alerts.append(
                    Alert(
                        date=instrument_prices[index].date,
                        rule_id=rule.id,
                        instrument=rule.instrument,
                        message=(
                            f"MA crossover {rule.direction} "
                            f"(short={format(current_short, 'f')}, "
                            f"long={format(current_long, 'f')})"
                        ),
                    )
                )

        return alerts
