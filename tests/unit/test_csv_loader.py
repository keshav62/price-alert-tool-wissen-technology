"""Tests for the CSV price loader using fixture files.

Fixtures live under tests/fixtures/ and are resolved relative to this
test file so that the test suite works regardless of the current
working directory.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from price_alert.data.csv_loader import PriceCSVError, load_prices
from price_alert.models.price import Price


# ── Fixture directory ────────────────────────────────────────────────

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def fixture(name: str) -> Path:
    """Return the absolute path to a fixture file."""
    return FIXTURES_DIR / name


# ── Helper ───────────────────────────────────────────────────────────

def write_csv(tmp_path: Path, content: str) -> Path:
    """Create a temporary CSV file for inline test data."""
    file_path = tmp_path / "prices.csv"
    file_path.write_text(content, encoding="utf-8")
    return file_path


# =====================================================================
# Valid fixtures
# =====================================================================


class TestValidBasic:
    """valid_basic.csv — one instrument, five rows."""

    def test_loads_all_rows(self):
        prices = load_prices(fixture("valid_basic.csv"))
        assert len(prices) == 5

    def test_correct_types(self):
        prices = load_prices(fixture("valid_basic.csv"))
        for price in prices:
            assert isinstance(price, Price)
            assert isinstance(price.date, date)
            assert isinstance(price.instrument, str)
            assert isinstance(price.close, Decimal)

    def test_first_row_values(self):
        prices = load_prices(fixture("valid_basic.csv"))
        assert prices[0] == Price(
            date=date(2026, 9, 1),
            instrument="INFY",
            close=Decimal("1520.50"),
        )

    def test_sorted_by_date(self):
        prices = load_prices(fixture("valid_basic.csv"))
        dates = [p.date for p in prices]
        assert dates == sorted(dates)


class TestValidMultipleInstruments:
    """valid_multiple_instruments.csv — three instruments, overlapping dates."""

    def test_loads_all_rows(self):
        prices = load_prices(fixture("valid_multiple_instruments.csv"))
        assert len(prices) == 9

    def test_contains_expected_instruments(self):
        prices = load_prices(fixture("valid_multiple_instruments.csv"))
        instruments = {p.instrument for p in prices}
        assert instruments == {"INFY", "TCS", "WIPRO"}

    def test_sorted_by_date_then_instrument(self):
        prices = load_prices(fixture("valid_multiple_instruments.csv"))
        keys = [(p.date, p.instrument) for p in prices]
        assert keys == sorted(keys)


class TestValidUnsortedDates:
    """valid_unsorted_dates.csv — rows arrive in random order."""

    def test_output_is_sorted(self):
        prices = load_prices(fixture("valid_unsorted_dates.csv"))
        dates = [p.date for p in prices]
        assert dates == sorted(dates)

    def test_all_rows_present(self):
        prices = load_prices(fixture("valid_unsorted_dates.csv"))
        assert len(prices) == 5


class TestValidDecimalPrices:
    """valid_decimal_prices.csv — high-precision and edge-case decimals."""

    def test_prices_use_decimal(self):
        prices = load_prices(fixture("valid_decimal_prices.csv"))
        for price in prices:
            assert isinstance(price.close, Decimal)

    def test_precision_preserved(self):
        prices = load_prices(fixture("valid_decimal_prices.csv"))
        closes = {p.close for p in prices}
        assert Decimal("1520.123456") in closes
        assert Decimal("0.01") in closes
        assert Decimal("99999.99") in closes


class TestValidInstrumentCase:
    """valid_instrument_case.csv — mixed-case instrument names."""

    def test_all_normalized_to_upper(self):
        prices = load_prices(fixture("valid_instrument_case.csv"))
        for price in prices:
            assert price.instrument == "INFY"

    def test_all_rows_loaded(self):
        prices = load_prices(fixture("valid_instrument_case.csv"))
        assert len(prices) == 4


class TestValidSingleRow:
    """valid_single_row.csv — exactly one data row."""

    def test_single_row(self):
        prices = load_prices(fixture("valid_single_row.csv"))
        assert len(prices) == 1
        assert prices[0] == Price(
            date=date(2026, 9, 1),
            instrument="INFY",
            close=Decimal("1520.50"),
        )


class TestValidHeaderOnly:
    """valid_header_only.csv — header with no data rows."""

    def test_returns_empty_list(self):
        prices = load_prices(fixture("valid_header_only.csv"))
        assert prices == []


class TestValidLargeDataset:
    """valid_large_dataset.csv — 500 deterministic rows."""

    def test_row_count(self):
        prices = load_prices(fixture("valid_large_dataset.csv"))
        assert len(prices) == 500

    def test_sorted_by_date_then_instrument(self):
        prices = load_prices(fixture("valid_large_dataset.csv"))
        keys = [(p.date, p.instrument) for p in prices]
        assert keys == sorted(keys)

    def test_all_prices_positive(self):
        prices = load_prices(fixture("valid_large_dataset.csv"))
        assert all(p.close > 0 for p in prices)

    def test_contains_multiple_instruments(self):
        prices = load_prices(fixture("valid_large_dataset.csv"))
        instruments = {p.instrument for p in prices}
        assert len(instruments) >= 2


# =====================================================================
# Invalid fixtures — parametrized
# =====================================================================


class TestInvalidStructural:
    """Fixtures that violate CSV structure or header requirements."""

    @pytest.mark.parametrize(
        "filename, match",
        [
            ("invalid_empty.csv", "empty|missing"),
            ("invalid_missing_header.csv", "Missing required"),
            ("invalid_missing_date_column.csv", "Missing required"),
            ("invalid_missing_instrument_column.csv", "Missing required"),
            ("invalid_missing_close_column.csv", "Missing required"),
            ("invalid_duplicate_headers.csv", "duplicate column"),
        ],
        ids=[
            "empty_file",
            "missing_header",
            "missing_date_column",
            "missing_instrument_column",
            "missing_close_column",
            "duplicate_headers",
        ],
    )
    def test_raises_price_csv_error(self, filename, match):
        with pytest.raises(PriceCSVError, match=f"(?i){match}"):
            load_prices(fixture(filename))


class TestInvalidDates:
    """Fixtures with malformed or impossible dates."""

    @pytest.mark.parametrize(
        "filename",
        [
            "invalid_date_format.csv",
            "invalid_impossible_date.csv",
        ],
        ids=[
            "malformed_date",
            "impossible_date",
        ],
    )
    def test_raises_price_csv_error(self, filename):
        with pytest.raises(PriceCSVError, match="(?i)date"):
            load_prices(fixture(filename))


class TestInvalidInstrument:
    """Fixture with blank instrument."""

    def test_empty_instrument_raises(self):
        with pytest.raises(PriceCSVError, match="(?i)instrument"):
            load_prices(fixture("invalid_empty_instrument.csv"))


class TestInvalidClosingPrice:
    """Fixtures with various invalid closing prices."""

    @pytest.mark.parametrize(
        "filename",
        [
            "invalid_empty_close.csv",
            "invalid_non_numeric_close.csv",
            "invalid_zero_close.csv",
            "invalid_negative_close.csv",
            "invalid_nan_close.csv",
            "invalid_infinite_close.csv",
        ],
        ids=[
            "empty",
            "non_numeric",
            "zero",
            "negative",
            "nan",
            "infinite",
        ],
    )
    def test_raises_price_csv_error(self, filename):
        with pytest.raises(PriceCSVError):
            load_prices(fixture(filename))


class TestInvalidDuplicateRecord:
    """Fixture with duplicate (date, instrument) combination."""

    def test_raises_price_csv_error(self):
        with pytest.raises(PriceCSVError, match="(?i)duplicate"):
            load_prices(fixture("invalid_duplicate_record.csv"))


class TestInvalidFieldCount:
    """Fixtures with wrong number of fields in a data row."""

    @pytest.mark.parametrize(
        "filename",
        [
            "invalid_extra_field.csv",
            "invalid_missing_field.csv",
        ],
        ids=["extra_field", "missing_field"],
    )
    def test_raises_price_csv_error(self, filename):
        with pytest.raises(PriceCSVError, match="(?i)field"):
            load_prices(fixture(filename))


# =====================================================================
# Edge cases using tmp_path (inline data)
# =====================================================================


class TestMissingFile:
    """FileNotFoundError for non-existent path."""

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_prices(tmp_path / "nonexistent.csv")


class TestInlineValidation:
    """Quick inline tests preserved from the original test suite."""

    def test_load_valid_csv(self, tmp_path):
        fp = write_csv(
            tmp_path,
            "date,instrument,close\n"
            "2026-09-01,INFY,1520.50\n"
            "2026-09-02,TCS,3902.25\n",
        )
        prices = load_prices(fp)
        assert len(prices) == 2
        assert prices[0] == Price(
            date(2026, 9, 1), "INFY", Decimal("1520.50")
        )
        assert prices[1].instrument == "TCS"

    def test_instrument_is_normalized(self, tmp_path):
        fp = write_csv(
            tmp_path,
            "date,instrument,close\n"
            "2026-09-01, infy ,1520.50\n",
        )
        prices = load_prices(fp)
        assert prices[0].instrument == "INFY"

    @pytest.mark.parametrize(
        "bad_date",
        ["not-a-date", "2026-13-01"],
    )
    def test_invalid_date_raises_error(self, tmp_path, bad_date):
        fp = write_csv(
            tmp_path,
            f"date,instrument,close\n{bad_date},INFY,1520.50\n",
        )
        with pytest.raises(PriceCSVError, match="(?i)date"):
            load_prices(fp)

    @pytest.mark.parametrize(
        "bad_close",
        ["abc", "NaN", "Infinity", "0", "-10"],
    )
    def test_invalid_close_raises_error(self, tmp_path, bad_close):
        fp = write_csv(
            tmp_path,
            f"date,instrument,close\n2026-09-01,INFY,{bad_close}\n",
        )
        with pytest.raises(PriceCSVError):
            load_prices(fp)
