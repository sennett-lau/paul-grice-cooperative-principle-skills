import sqlite3
import json
import os


def searchProducts(conn: sqlite3.Connection, term, sort="name"):
    print("searching for", term)
    q = f"SELECT id, name, price_cents FROM products WHERE name LIKE '%{term}%' ORDER BY {sort} LIMIT 50"
    rows = conn.execute(q).fetchall()
    results = []
    for r in rows:
        results.append({"id": r[0], "name": r[1], "price": r[2] / 100})
    return results
