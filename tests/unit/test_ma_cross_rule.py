
from datetime import date
from decimal import Decimal

import pytest

from price_alert.models.price import Price
from price_alert.models.rule import Rule
from price_alert.rules.ma_cross_rule import MACrossRule


def make_prices(values: list[str]) -> list[Price]:
    return [
        Price(
            date=date(2026, 1, index + 1),
            instrument="ABC",
            close=Decimal(value),
        )
        for index, value in enumerate(values)
    ]


def make_rule(direction: str = "above") -> Rule:
    return Rule(
        id="MA1",
        instrument="ABC",
        type="ma_cross",
        direction=direction,
        short=2,
        long=3,
    )


def test_detects_upward_crossover():
    # Short MA: 9, 11, 13, 15
    # Long MA: unavailable, unavailable, 10, 12, 14
    # At the fifth observation, short MA crosses above long MA.
    prices = make_prices(["10", "10", "10", "14", "16"])

    alerts = MACrossRule().evaluate(prices, make_rule("above"))

    assert len(alerts) == 1
    assert alerts[0].date == date(2026, 1, 4)
    assert alerts[0].rule_id == "MA1"
    assert alerts[0].instrument == "ABC"


def test_no_alert_without_crossover():
    prices = make_prices(["10", "10", "10", "10", "10"])

    assert MACrossRule().evaluate(prices, make_rule()) == []


def test_ignores_other_instruments():
    prices = [
        *make_prices(["10", "10", "10"]),
        Price(date(2026, 1, 4), "XYZ", Decimal("100")),
    ]

    assert MACrossRule().evaluate(prices, make_rule()) == []


@pytest.mark.parametrize(
    "short,long",
    [(0, 3), (-1, 3), (3, 3), (4, 3), (True, 3)],
)
def test_rejects_invalid_windows(short, long):
    rule = Rule(
        id="MA1",
        instrument="ABC",
        type="ma_cross",
        direction="above",
        short=short,
        long=long,
    )

    with pytest.raises(ValueError):
        MACrossRule().evaluate(make_prices(["10", "20", "30"]), rule)


def test_rejects_wrong_rule_type():
    rule = Rule(
        id="L1",
        instrument="ABC",
        type="level",
        direction="above",
        level=Decimal("20"),
    )

    with pytest.raises(ValueError):
        MACrossRule().evaluate(make_prices(["10", "20"]), rule)
