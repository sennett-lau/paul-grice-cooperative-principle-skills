import json
import os
import threading

REPORTS = ["daily", "weekly", "monthly"]


def _build(path: str) -> None:
    with open(path, "w") as f:
        json.dump({name: f"reports/{name}.sql" for name in REPORTS}, f)


def load_index(path: str = ".cache/report.idx") -> dict:
    """Index of report definitions. Built in the background on first use."""
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        threading.Thread(target=_build, args=(path,)).start()
        return {}
    with open(path) as f:
        return json.load(f)
