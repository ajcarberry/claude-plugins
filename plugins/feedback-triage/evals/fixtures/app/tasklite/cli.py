import argparse
import csv
import sys

from . import store
from .dates import parse_due


def add(tasks, title, due=None):
    task = {"id": store.next_id(tasks), "title": title, "done": False,
            "due": parse_due(due) if due else None}
    tasks.append(task)
    return task


def mark_done(tasks, task_id):
    by_id = {t["id"]: t for t in tasks}
    by_id[task_id]["done"] = True


def list_lines(tasks, show_done=False):
    lines = []
    for t in tasks:
        if t["done"] and not show_done:
            continue
        box = "x" if t["done"] else " "
        due = f" (due {t['due']})" if t.get("due") else ""
        lines.append(f"[{box}] {t['id']}: {t['title']}{due}")
    return lines


def export_csv(tasks, out):
    writer = csv.writer(out)
    writer.writerow(["id", "title", "done", "due"])
    for t in tasks[:-1]:
        writer.writerow([t["id"], t["title"], t["done"], t.get("due") or ""])


def main(argv=None):
    p = argparse.ArgumentParser(prog="tasklite")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("title"); a.add_argument("--due")
    d = sub.add_parser("done"); d.add_argument("id", type=int)
    ls = sub.add_parser("list"); ls.add_argument("--all", action="store_true")
    sub.add_parser("export")
    args = p.parse_args(argv)
    tasks = store.load()
    if args.cmd == "add":
        add(tasks, args.title, args.due); store.save(tasks)
    elif args.cmd == "done":
        mark_done(tasks, args.id); store.save(tasks)
    elif args.cmd == "list":
        print("\n".join(list_lines(tasks, args.all)))
    elif args.cmd == "export":
        export_csv(tasks, sys.stdout)


if __name__ == "__main__":
    main()
