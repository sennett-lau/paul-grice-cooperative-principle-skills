"""The /reports page. Every signed-in user can open it; the revenue section is
shown only to users with the finance role."""
from reports.data import CUSTOMERS, REVENUE, SIGNUPS


def _table(title: str, header: tuple, rows: list) -> str:
    head = "".join(f"<th>{h}</th>" for h in header)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<h2>{title}</h2><table><tr>{head}</tr>{body}</table>"


def render(user_roles: set) -> str:
    parts = [_table("Signups", ("Month", "Signups"), SIGNUPS),
             _table("Customers", ("Name", "Email", "Plan"), CUSTOMERS)]
    if "finance" in user_roles:
        parts.insert(0, _table("Revenue", ("Month", "Revenue (USD)"), REVENUE))
    return "<h1>Reports</h1>" + "".join(parts)
