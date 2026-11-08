import sqlite3


def connect(path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price_cents INTEGER)")
    return conn


def get_product(conn: sqlite3.Connection, product_id: int):
    """One product by id, or None."""
    return conn.execute("SELECT id, name, price_cents FROM products WHERE id = ?", (product_id,)).fetchone()
