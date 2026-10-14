
import argparse
import sys
from pathlib import Path

from price_alert.data.csv_loader import load_prices
from price_alert.data.rules_loader import load_rules
from price_alert.engine.alert_engine import AlertEngine
from price_alert.output.console import print_alerts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate price alert rules against historical prices."
    )
    parser.add_argument(
        "--prices",
        required=True,
        help="Path to the prices CSV file.",
    )
    parser.add_argument(
        "--rules",
        required=True,
        help="Path to the alert rules JSON file.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        prices = load_prices(Path(args.prices))
        rules = load_rules(Path(args.rules))

        alerts = AlertEngine().run(prices, rules)
        print_alerts(alerts)

        return 0

    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
