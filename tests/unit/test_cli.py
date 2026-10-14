
import json
from pathlib import Path

from price_alert.cli import main


def create_inputs(tmp_path: Path) -> tuple[Path, Path]:
    prices_file = tmp_path / "prices.csv"
    prices_file.write_text(
        "date,instrument,close\n"
        "2026-01-01,ABC,100\n"
        "2026-01-02,ABC,120\n",
        encoding="utf-8",
    )

    rules_file = tmp_path / "rules.json"
    rules_file.write_text(
        json.dumps([
            {
                "id": "R1",
                "instrument": "ABC",
                "type": "level",
                "direction": "above",
                "level": 110,
            }
        ]),
        encoding="utf-8",
    )

    return prices_file, rules_file


def test_cli_success(tmp_path, monkeypatch, capsys):
    prices_file, rules_file = create_inputs(tmp_path)

    monkeypatch.setattr(
        "sys.argv",
        [
            "price-alert",
            "--prices", str(prices_file),
            "--rules", str(rules_file),
        ],
    )

    exit_code = main()

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "R1" in captured.out
    assert "2026-01-02" in captured.out
    assert captured.err == ""


def test_cli_missing_csv_returns_error(
    tmp_path, monkeypatch, capsys
):
    _, rules_file = create_inputs(tmp_path)
    missing_file = tmp_path / "missing.csv"

    monkeypatch.setattr(
        "sys.argv",
        [
            "price-alert",
            "--prices", str(missing_file),
            "--rules", str(rules_file),
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error:" in captured.err


def test_cli_invalid_json_returns_error(
    tmp_path, monkeypatch, capsys
):
    prices_file, _ = create_inputs(tmp_path)
    rules_file = tmp_path / "invalid.json"
    rules_file.write_text("{ invalid json", encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "price-alert",
            "--prices", str(prices_file),
            "--rules", str(rules_file),
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error:" in captured.err


def test_cli_empty_valid_inputs_print_no_alerts(
    tmp_path, monkeypatch, capsys
):
    prices_file = tmp_path / "prices.csv"
    prices_file.write_text(
        "date,instrument,close\n"
        "2026-01-01,ABC,100\n"
        "2026-01-02,ABC,101\n",
        encoding="utf-8",
    )

    rules_file = tmp_path / "rules.json"
    rules_file.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "price-alert",
            "--prices", str(prices_file),
            "--rules", str(rules_file),
        ],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "No alerts detected." in captured.out
