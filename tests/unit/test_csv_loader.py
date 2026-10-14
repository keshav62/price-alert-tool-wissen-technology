
import csv
from datetime import date
from decimal import Decimal

import pytest

from price_alert.data.csv_loader import load_prices, PriceCSVError
from price_alert.models.price import Price


def write_csv(tmp_path, content):
    """Create a temporary CSV file for testing."""
    file_path = tmp_path / "prices.csv"
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_load_valid_csv(tmp_path):
    file_path = write_csv(
        tmp_path,
        "date,instrument,close\n"
        "2026-09-01,INFY,1520.50\n"
        "2026-09-02,TCS,3902.25\n",
    )

    prices = load_prices(file_path)

    assert len(prices) == 2
    assert prices[0] == Price(
        date(2026, 9, 1), "INFY", Decimal("1520.50")
    )
    assert prices[1].instrument == "TCS"


def test_prices_are_sorted_chronologically(tmp_path):
    file_path = write_csv(
        tmp_path,
        "date,instrument,close\n"
        "2026-09-03,INFY,1498.00\n"
        "2026-09-01,TCS,3890.00\n"
        "2026-09-01,INFY,1520.50\n",
    )

    prices = load_prices(file_path)

    assert [p.date for p in prices] == [
        date(2026, 9, 1),
        date(2026, 9, 1),
        date(2026, 9, 3),
    ]
    assert [p.instrument for p in prices] == [
        "INFY", "TCS", "INFY"
    ]


def test_instrument_is_normalized(tmp_path):
    file_path = write_csv(
        tmp_path,
        "date,instrument,close\n"
        "2026-09-01, infy ,1520.50\n",
    )

    prices = load_prices(file_path)

    assert prices[0].instrument == "INFY"


def test_missing_column_raises_error(tmp_path):
    file_path = write_csv(
        tmp_path,
        "date,instrument\n"
        "2026-09-01,INFY\n",
    )

    with pytest.raises(PriceCSVError, match="Missing required"):
        load_prices(file_path)


@pytest.mark.parametrize(
    "bad_date",
    ["", "not-a-date", "2026-13-01"],
)
def test_invalid_date_raises_error(tmp_path, bad_date):
    file_path = write_csv(
        tmp_path,
        f"date,instrument,close\n"
        f"{bad_date},INFY,1520.50\n",
    )

    with pytest.raises(PriceCSVError, match="date"):
        load_prices(file_path)


@pytest.mark.parametrize(
    "bad_close",
    ["", "abc", "NaN", "Infinity", "0", "-10"],
)
def test_invalid_close_raises_error(tmp_path, bad_close):
    file_path = write_csv(
        tmp_path,
        "date,instrument,close\n"
        f"2026-09-01,INFY,{bad_close}\n",
    )

    with pytest.raises(PriceCSVError):
        load_prices(file_path)


def test_blank_instrument_raises_error(tmp_path):
    file_path = write_csv(
        tmp_path,
        "date,instrument,close\n"
        "2026-09-01, ,1520.50\n",
    )

    with pytest.raises(PriceCSVError, match="instrument"):
        load_prices(file_path)


def test_duplicate_record_raises_error(tmp_path):
    file_path = write_csv(
        tmp_path,
        "date,instrument,close\n"
        "2026-09-01,INFY,1520.50\n"
        "2026-09-01,INFY,1521.00\n",
    )

    with pytest.raises(PriceCSVError, match="Duplicate"):
        load_prices(file_path)


def test_missing_file_raises_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_prices(tmp_path / "missing.csv")


def test_header_only_csv_returns_empty_list(tmp_path):
    file_path = write_csv(
        tmp_path,
        "date,instrument,close\n",
    )

    assert load_prices(file_path) == []
