
from collections.abc import Sequence

from price_alert.models.alert import Alert


def format_alert(alert: Alert) -> str:
    """Format one alert as a readable console line."""
    return (
        f"{alert.date.isoformat()} | "
        f"{alert.rule_id} | "
        f"{alert.instrument} | "
        f"{alert.message}"
    )


def print_alerts(alerts: Sequence[Alert]) -> None:
    """Print alerts or a message when no alerts are detected."""
    if not alerts:
        print("No alerts detected.")
        return

    for alert in alerts:
        print(format_alert(alert))
