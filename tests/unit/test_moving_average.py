
from decimal import Decimal

import pytest

from price_alert.indicators.moving_average import (
    calculate_moving_average,
)


def D(value: str) -> Decimal:
    return Decimal(value)


def test_calculates_simple_moving_average():
    prices = [D("10"), D("20"), D("30"), D("40")]

    result = calculate_moving_average(prices, 3)

    assert result == [None, None, D("20"), D("30")]


def test_window_of_one_returns_original_prices():
    prices = [D("10"), D("20"), D("30")]

    assert calculate_moving_average(prices, 1) == prices


def test_window_equal_to_price_count():
    prices = [D("10"), D("20"), D("30")]

    assert calculate_moving_average(prices, 3) == [
        None,
        None,
        D("20"),
    ]


def test_window_larger_than_price_count():
    prices = [D("10"), D("20")]

    assert calculate_moving_average(prices, 3) == [None, None]


def test_empty_prices():
    assert calculate_moving_average([], 3) == []


@pytest.mark.parametrize("window", [0, -1, 1.5, True, "3"])
def test_rejects_invalid_window(window):
    with pytest.raises(ValueError):
        calculate_moving_average([D("10"), D("20")], window)
