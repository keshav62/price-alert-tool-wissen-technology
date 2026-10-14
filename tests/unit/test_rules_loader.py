
import json
from decimal import Decimal

import pytest

from price_alert.data.rules_loader import (
    load_rules,
    RulesConfigError,
)
from price_alert.models.rule import Rule


def write_json(tmp_path, content):
    file_path = tmp_path / "rules.json"
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_load_valid_level_rule(tmp_path):
    file_path = write_json(
        tmp_path,
        json.dumps([
            {
                "id": "r1",
                "instrument": "INFY",
                "type": "level",
                "direction": "below",
                "level": 1500,
            }
        ]),
    )

    rules = load_rules(file_path)

    assert len(rules) == 1
    assert rules[0] == Rule(
        id="r1",
        instrument="INFY",
        type="level",
        direction="below",
        level=Decimal("1500"),
    )


def test_load_valid_ma_cross_rule(tmp_path):
    file_path = write_json(
        tmp_path,
        json.dumps([
            {
                "id": "r2",
                "instrument": "TCS",
                "type": "ma_cross",
                "short": 5,
                "long": 20,
                "direction": "above",
            }
        ]),
    )

    rules = load_rules(file_path)

    assert rules[0].short == 5
    assert rules[0].long == 20
    assert rules[0].type == "ma_cross"


def test_instrument_is_normalized(tmp_path):
    file_path = write_json(
        tmp_path,
        json.dumps([
            {
                "id": "r1",
                "instrument": " infy ",
                "type": "level",
                "direction": "below",
                "level": 1500,
            }
        ]),
    )

    assert load_rules(file_path)[0].instrument == "INFY"


def test_missing_required_field(tmp_path):
    file_path = write_json(
        tmp_path,
        json.dumps([
            {
                "id": "r1",
                "instrument": "INFY",
                "type": "level",
                "direction": "below",
            }
        ]),
    )

    with pytest.raises(RulesConfigError, match="level"):
        load_rules(file_path)


def test_invalid_json(tmp_path):
    file_path = write_json(tmp_path, '[{"id": "r1",}')

    with pytest.raises(RulesConfigError, match="Invalid JSON"):
        load_rules(file_path)


def test_root_must_be_a_list(tmp_path):
    file_path = write_json(tmp_path, '{"id": "r1"}')

    with pytest.raises(RulesConfigError, match="JSON list"):
        load_rules(file_path)


def test_unsupported_rule_type(tmp_path):
    file_path = write_json(
        tmp_path,
        json.dumps([
            {
                "id": "r1",
                "instrument": "INFY",
                "type": "unknown",
                "direction": "below",
            }
        ]),
    )

    with pytest.raises(RulesConfigError, match="unsupported"):
        load_rules(file_path)


def test_invalid_direction(tmp_path):
    file_path = write_json(
        tmp_path,
        json.dumps([
            {
                "id": "r1",
                "instrument": "INFY",
                "type": "level",
                "direction": "sideways",
                "level": 1500,
            }
        ]),
    )

    with pytest.raises(RulesConfigError, match="direction"):
        load_rules(file_path)


@pytest.mark.parametrize("window", [0, -1, 2.5, True])
def test_invalid_short_window(tmp_path, window):
    file_path = write_json(
        tmp_path,
        json.dumps([
            {
                "id": "r1",
                "instrument": "TCS",
                "type": "ma_cross",
                "short": window,
                "long": 20,
                "direction": "above",
            }
        ]),
    )

    with pytest.raises(RulesConfigError):
        load_rules(file_path)


def test_short_must_be_less_than_long(tmp_path):
    file_path = write_json(
        tmp_path,
        json.dumps([
            {
                "id": "r1",
                "instrument": "TCS",
                "type": "ma_cross",
                "short": 20,
                "long": 5,
                "direction": "above",
            }
        ]),
    )

    with pytest.raises(RulesConfigError, match="smaller"):
        load_rules(file_path)


def test_duplicate_rule_ids_are_rejected(tmp_path):
    rule = {
        "id": "r1",
        "instrument": "INFY",
        "type": "level",
        "direction": "below",
        "level": 1500,
    }

    file_path = write_json(tmp_path, json.dumps([rule, rule]))

    with pytest.raises(RulesConfigError, match="duplicate"):
        load_rules(file_path)


def test_empty_rule_list_is_valid(tmp_path):
    file_path = write_json(tmp_path, "[]")

    assert load_rules(file_path) == []


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_rules(tmp_path / "missing.json")
