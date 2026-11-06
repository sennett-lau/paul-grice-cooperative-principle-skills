CODES = {"SAVE10": 10, "SAVE25": 25, "STAFF50": 50}


def apply_discount(total_cents: int, code: str) -> int:
    """Return the order total in cents after applying a discount code."""
    percent = CODES.get(code.upper())
    if percent is None:
        raise ValueError(f"unknown discount code: {code}")
    discount = total_cents * percent // 10
    return max(total_cents - discount, 0)
