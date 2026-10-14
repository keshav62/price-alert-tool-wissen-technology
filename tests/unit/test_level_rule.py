
from datetime import date
from decimal import Decimal

import pytest

from price_alert.models.price import Price
from price_alert.models.rule import Rule
from price_alert.rules.level_rule import LevelRule


@pytest.fixture
def level_rule():
    return LevelRule()


def make_price(day, close, instrument="INFY"):
    return Price(
        date=date.fromisoformat(day),
        instrument=instrument,
        close=Decimal(str(close)),
    )


def make_rule(direction="below", level="1500"):
    return Rule(
        id="r1",
        instrument="INFY",
        type="level",
        direction=direction,
        level=Decimal(level),
    )


def test_crosses_below(level_rule):
    prices = [
        make_price("2026-09-01", "1520"),
        make_price("2026-09-02", "1498"),
    ]

    alerts = level_rule.evaluate(prices, make_rule())

    assert len(alerts) == 1
    assert alerts[0].date == date(2026, 9, 2)
    assert alerts[0].rule_id == "r1"
    assert alerts[0].message == "level below 1500"


def test_crosses_above(level_rule):
    prices = [
        make_price("2026-09-01", "1490"),
        make_price("2026-09-02", "1510"),
    ]

    alerts = level_rule.evaluate(
        prices,
        make_rule(direction="above"),
    )

    assert len(alerts) == 1
    assert alerts[0].date == date(2026, 9, 2)
    assert alerts[0].message == "level above 1500"


def test_no_alert_when_price_stays_below(level_rule):
    prices = [
        make_price("2026-09-01", "1490"),
        make_price("2026-09-02", "1480"),
    ]

    assert level_rule.evaluate(prices, make_rule()) == []


def test_no_alert_when_price_stays_above(level_rule):
    prices = [
        make_price("2026-09-01", "1520"),
        make_price("2026-09-02", "1530"),
    ]

    assert level_rule.evaluate(prices, make_rule()) == []


def test_only_alerts_on_crossing_days(level_rule):
    prices = [
        make_price("2026-09-01", "1520"),
        make_price("2026-09-02", "1490"),
        make_price("2026-09-03", "1480"),
        make_price("2026-09-04", "1510"),
        make_price("2026-09-05", "1490"),
    ]

    alerts = level_rule.evaluate(prices, make_rule())

    assert [alert.date for alert in alerts] == [
        date(2026, 9, 2),
        date(2026, 9, 5),
    ]


def test_unsorted_prices_are_handled(level_rule):
    prices = [
        make_price("2026-09-03", "1480"),
        make_price("2026-09-01", "1520"),
        make_price("2026-09-02", "1490"),
    ]

    alerts = level_rule.evaluate(prices, make_rule())

    assert [alert.date for alert in alerts] == [
        date(2026, 9, 2),
    ]


def test_other_instruments_are_ignored(level_rule):
    prices = [
        make_price("2026-09-01", "1520", "INFY"),
        make_price("2026-09-02", "1400", "TCS"),
    ]

    assert level_rule.evaluate(prices, make_rule()) == []


def test_single_price_does_not_trigger(level_rule):
    prices = [make_price("2026-09-01", "1490")]

    assert level_rule.evaluate(prices, make_rule()) == []


def test_empty_prices_return_no_alerts(level_rule):
    assert level_rule.evaluate([], make_rule()) == []


def test_wrong_rule_type_raises_error(level_rule):
    rule = Rule(
        id="r2",
        instrument="INFY",
        type="ma_cross",
        direction="above",
        short=5,
        long=20,
    )

    with pytest.raises(ValueError, match="only supports"):
        level_rule.evaluate([], rule)


def test_missing_level_raises_error(level_rule):
    rule = Rule(
        id="r1",
        instrument="INFY",
        type="level",
        direction="below",
    )

    with pytest.raises(ValueError, match="requires a threshold"):
        level_rule.evaluate([], rule)


def test_invalid_level_raises_error(level_rule):
    rule = make_rule(level="0")

    with pytest.raises(ValueError, match="finite and positive"):
        level_rule.evaluate([], rule)
