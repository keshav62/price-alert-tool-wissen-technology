
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from price_alert.models.price import Price


REQUIRED_COLUMNS = {"date", "instrument", "close"}


class PriceCSVError(ValueError):
    """Raised when a price CSV file contains invalid data."""


def load_prices(file_path: str | Path) -> list[Price]:
    """
    Load prices from a CSV file, validate records,
    and return them in chronological order.

    Expected columns:
        date,instrument,close

    Raises:
        FileNotFoundError: If the file does not exist.
        PriceCSVError: If the CSV structure or data is invalid.
    """
    path = Path(file_path)
    prices: list[Price] = []
    seen_records: set[tuple[date, str]] = set()

    try:
        with path.open(
            mode="r",
            encoding="utf-8-sig",
            newline="",
        ) as csv_file:
            reader = csv.DictReader(csv_file)

            if reader.fieldnames is None:
                raise PriceCSVError("CSV file is empty or missing a header.")

            # Remove surrounding whitespace from header names.
            headers = [
                header.strip() if header else ""
                for header in reader.fieldnames
            ]

            if len(headers) != len(set(headers)):
                raise PriceCSVError("CSV contains duplicate column names.")

            missing_columns = REQUIRED_COLUMNS - set(headers)

            if missing_columns:
                missing = ", ".join(sorted(missing_columns))
                raise PriceCSVError(
                    f"Missing required CSV columns: {missing}"
                )

            # Use normalized headers when accessing row values.
            reader.fieldnames = headers

            for row in reader:
                line_number = reader.line_num

                # Reject rows with extra or missing CSV fields.
                if None in row or any(
                    row.get(column) is None
                    for column in REQUIRED_COLUMNS
                ):
                    raise PriceCSVError(
                        f"Invalid number of fields at line {line_number}."
                    )

                raw_date = row["date"].strip()
                instrument = row["instrument"].strip().upper()
                raw_close = row["close"].strip()

                if not raw_date:
                    raise PriceCSVError(
                        f"Missing date at line {line_number}."
                    )

                if not instrument:
                    raise PriceCSVError(
                        f"Missing instrument at line {line_number}."
                    )

                if not raw_close:
                    raise PriceCSVError(
                        f"Missing closing price at line {line_number}."
                    )

                try:
                    trading_date = date.fromisoformat(raw_date)
                except ValueError as exc:
                    raise PriceCSVError(
                        f"Invalid date '{raw_date}' at line {line_number}; "
                        "expected YYYY-MM-DD."
                    ) from exc

                try:
                    close = Decimal(raw_close)
                except InvalidOperation as exc:
                    raise PriceCSVError(
                        f"Invalid closing price '{raw_close}' "
                        f"at line {line_number}."
                    ) from exc

                if not close.is_finite() or close <= 0:
                    raise PriceCSVError(
                        f"Closing price must be finite and positive "
                        f"at line {line_number}."
                    )

                # One closing price per instrument per trading day.
                record_key = (trading_date, instrument)

                if record_key in seen_records:
                    raise PriceCSVError(
                        f"Duplicate price for {instrument} on "
                        f"{trading_date} at line {line_number}."
                    )

                seen_records.add(record_key)

                prices.append(
                    Price(
                        date=trading_date,
                        instrument=instrument,
                        close=close,
                    )
                )

    except csv.Error as exc:
        raise PriceCSVError(f"Unable to parse CSV file: {exc}") from exc

    # Sort chronologically; use instrument as a deterministic tie-breaker.
    prices.sort(key=lambda price: (price.date, price.instrument))

    return prices
