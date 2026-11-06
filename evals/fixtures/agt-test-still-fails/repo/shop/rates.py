import json
import urllib.request

RATES_URL = "https://rates.internal.example/v1/{currency}"


def fetch_rate(currency: str) -> float:
    """Live exchange rate from USD, from the internal rates service."""
    with urllib.request.urlopen(RATES_URL.format(currency=currency), timeout=3) as resp:
        return float(json.load(resp)["rate"])
