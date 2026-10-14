
import pytest

from price_alert.rules.level_rule import LevelRule
from price_alert.rules.ma_cross_rule import MACrossRule
from price_alert.rules.registry import RuleRegistry


def test_returns_level_rule():
    registry = RuleRegistry()

    assert isinstance(registry.get("level"), LevelRule)


def test_returns_ma_cross_rule():
    registry = RuleRegistry()

    assert isinstance(registry.get("ma_cross"), MACrossRule)


def test_rejects_unsupported_rule_type():
    registry = RuleRegistry()

    with pytest.raises(ValueError, match="Unsupported rule type"):
        registry.get("unknown")
