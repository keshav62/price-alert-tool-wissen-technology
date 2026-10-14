
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from price_alert.models.rule import Rule


class RulesConfigError(ValueError):
    """Raised when the rules configuration is invalid."""


SUPPORTED_TYPES = {"level", "ma_cross"}
SUPPORTED_DIRECTIONS = {"above", "below"}


def load_rules(file_path: str | Path) -> list[Rule]:
    """
    Load, validate, and return alert rules from a JSON file.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        RulesConfigError: If the JSON or any rule is invalid.
    """
    path = Path(file_path)

    try:
        with path.open("r", encoding="utf-8-sig") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise RulesConfigError(
            f"Invalid JSON at line {exc.lineno}, column {exc.colno}: "
            f"{exc.msg}"
        ) from exc

    if not isinstance(data, list):
        raise RulesConfigError(
            "Rules configuration must be a JSON list."
        )

    rules: list[Rule] = []
    seen_ids: set[str] = set()

    for index, item in enumerate(data):
        location = f"Rule at index {index}"

        if not isinstance(item, dict):
            raise RulesConfigError(
                f"{location} must be a JSON object."
            )

        # Validate common fields.
        required_fields = {"id", "instrument", "type", "direction"}
        missing = required_fields - item.keys()

        if missing:
            raise RulesConfigError(
                f"{location} is missing fields: "
                f"{', '.join(sorted(missing))}."
            )

        rule_id = item["id"]
        instrument = item["instrument"]
        rule_type = item["type"]
        direction = item["direction"]

        if not isinstance(rule_id, str) or not rule_id.strip():
            raise RulesConfigError(
                f"{location}: 'id' must be a non-empty string."
            )

        rule_id = rule_id.strip()

        if rule_id in seen_ids:
            raise RulesConfigError(
                f"{location}: duplicate rule ID '{rule_id}'."
            )

        if not isinstance(instrument, str) or not instrument.strip():
            raise RulesConfigError(
                f"{location}: 'instrument' must be a non-empty string."
            )

        instrument = instrument.strip().upper()

        
        if not isinstance(rule_type, str) or rule_type not in SUPPORTED_TYPES:
            raise RulesConfigError(
                f"{location}: unsupported rule type {rule_type!r}."
            )

        if not isinstance(direction, str) or direction not in SUPPORTED_DIRECTIONS:
            raise RulesConfigError(
                f"{location}: direction must be 'above' or 'below'."
            )


        level = None
        short = None
        long = None

        # Validate fields specific to each rule type.
        if rule_type == "level":
            if "level" not in item:
                raise RulesConfigError(
                    f"{location}: level rules require 'level'."
                )

            raw_level = item["level"]

            if isinstance(raw_level, bool) or not isinstance(
                raw_level, (int, float)
            ):
                raise RulesConfigError(
                    f"{location}: 'level' must be a JSON number."
                )

            try:
                level = Decimal(str(raw_level))
            except (InvalidOperation, ValueError) as exc:
                raise RulesConfigError(
                    f"{location}: invalid level value."
                ) from exc

            if not level.is_finite() or level <= 0:
                raise RulesConfigError(
                    f"{location}: 'level' must be finite and positive."
                )

        elif rule_type == "ma_cross":
            if "short" not in item or "long" not in item:
                raise RulesConfigError(
                    f"{location}: ma_cross rules require "
                    "'short' and 'long'."
                )

            short = item["short"]
            long = item["long"]

            # bool is a subclass of int, so use exact type checks.
            if type(short) is not int or type(long) is not int:
                raise RulesConfigError(
                    f"{location}: MA windows must be integers."
                )

            if short <= 0 or long <= 0:
                raise RulesConfigError(
                    f"{location}: MA windows must be positive."
                )

            if short >= long:
                raise RulesConfigError(
                    f"{location}: 'short' must be smaller than 'long'."
                )

        rules.append(
            Rule(
                id=rule_id,
                instrument=instrument,
                type=rule_type,
                direction=direction,
                level=level,
                short=short,
                long=long,
            )
        )

        seen_ids.add(rule_id)

    return rules
