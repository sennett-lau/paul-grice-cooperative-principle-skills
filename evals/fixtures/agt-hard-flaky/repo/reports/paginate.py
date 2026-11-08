def paginate(items: list, page: int, per_page: int = 20) -> dict:
    """One page of items (pages start at 1) plus the total page count."""
    if page < 1 or per_page < 1:
        raise ValueError("page and per_page must be at least 1")
    pages = max(1, -(-len(items) // per_page))
    start = (page - 1) * per_page
    return {"items": items[start:start + per_page], "page": page, "pages": pages}
