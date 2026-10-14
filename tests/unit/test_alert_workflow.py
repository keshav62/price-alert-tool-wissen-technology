
from datetime import date
from decimal import Decimal

from price_alert.engine.alert_engine import AlertEngine
from price_alert.models.price import Price
from price_alert.models.rule import Rule


def test_engine_evaluates_rules_and_sorts_alerts():
    prices = [
        Price(date(2026, 1, 1), "ABC", Decimal("10")),
        Price(date(2026, 1, 2), "ABC", Decimal("25")),
        Price(date(2026, 1, 3), "ABC", Decimal("35")),
    ]

    rules = [
        Rule(
            id="Z_RULE",
            instrument="ABC",
            type="level",
            direction="above",
            level=Decimal("20"),
        ),
        Rule(
            id="A_RULE",
            instrument="ABC",
            type="level",
            direction="above",
            level=Decimal("20"),
        ),
        Rule(
            id="B_RULE",
            instrument="ABC",
            type="level",
            direction="above",
            level=Decimal("30"),
        ),
    ]

    alerts = AlertEngine().run(prices, rules)

    assert [
        (alert.date, alert.rule_id)
        for alert in alerts
    ] == [
        (date(2026, 1, 2), "A_RULE"),
        (date(2026, 1, 2), "Z_RULE"),
        (date(2026, 1, 3), "B_RULE"),
    ]


def test_engine_returns_empty_list_when_no_rules():
    prices = [
        Price(date(2026, 1, 1), "ABC", Decimal("10")),
        Price(date(2026, 1, 2), "ABC", Decimal("11")),
    ]

    assert AlertEngine().run(prices, []) == []
