USERS = {
    1: {"id": 1, "name": "Ana", "plan": "pro"},
    2: {"id": 2, "name": "Ben", "plan": "free"},
    3: {"id": 3, "name": "Chen", "plan": "team"},
}


def get_user(user_id: int):
    """The user with this id, or None if there is none."""
    return USERS.get(user_id)
