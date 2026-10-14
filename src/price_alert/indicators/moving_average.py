
from decimal import Decimal
from collections.abc import Sequence


def calculate_moving_average(
    prices: Sequence[Decimal],
    window: int,
) -> list[Decimal | None]:
    """
    Calculate a simple moving average (SMA).

    The returned list has the same length as prices.
    Entries before a complete window are None.

    Example:
        prices = [10, 20, 30, 40]
        window = 3
        result = [None, None, 20, 30]
    """
    if type(window) is not int or window <= 0:
        raise ValueError("Window must be a positive integer.")

    result: list[Decimal | None] = []
    rolling_sum = Decimal("0")

    for index, price in enumerate(prices):
        rolling_sum += price

        # Remove the price that is outside the current window.
        if index >= window:
            rolling_sum -= prices[index - window]

        if index >= window - 1:
            result.append(rolling_sum / Decimal(window))
        else:
            result.append(None)

    return result
