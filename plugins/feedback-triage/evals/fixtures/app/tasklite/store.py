import json
import os

DEFAULT_PATH = os.path.expanduser("~/.tasklite.json")


def load(path=DEFAULT_PATH):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def save(tasks, path=DEFAULT_PATH):
    with open(path, "w") as f:
        json.dump(tasks, f)


def next_id(tasks):
    return max([t["id"] for t in tasks] or [0]) + 1
