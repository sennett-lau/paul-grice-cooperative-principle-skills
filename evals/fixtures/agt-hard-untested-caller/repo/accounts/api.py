from accounts.store import get_user


def user_endpoint(user_id: int) -> tuple:
    """(status, body) for GET /users/<id>."""
    user = get_user(user_id)
    return 200, {"name": user["name"], "plan": user["plan"]}
