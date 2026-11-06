import re


def slugify(title: str) -> str:
    """URL slug: lowercase ASCII words joined by hyphens."""
    ascii_only = title.encode("ascii", "ignore").decode()
    words = re.findall(r"[a-z0-9]+", ascii_only.lower())
    return "-".join(words)


def truncate(text: str, limit: int) -> str:
    """Cut text to at most `limit` characters, ending with an ellipsis if cut."""
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
