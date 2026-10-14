
from datetime import date
from decimal import Decimal

from price_alert.models.price import Price
from price_alert.models.rule import Rule
from price_alert.models.alert import Alert


def test_price_model():
    price = Price(
        date=date(2026, 9, 1),
        instrument="INFY",
        close=Decimal("1520.50"),
    )

    assert price.instrument == "INFY"
    assert price.close == Decimal("1520.50")


def test_level_rule_model():
    rule = Rule(
        id="r1",
        instrument="INFY",
        type="level",
        direction="below",
        level=Decimal("1500"),
    )

    assert rule.id == "r1"
    assert rule.level == Decimal("1500")


def test_alert_model():
    alert = Alert(
        date=date(2026, 9, 3),
        rule_id="r1",
        instrument="INFY",
        message="level below 1500",
    )

    assert alert.rule_id == "r1"
    assert alert.instrument == "INFY"
