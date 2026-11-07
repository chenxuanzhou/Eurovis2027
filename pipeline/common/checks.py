"""Tiny check runner used by every dataset's validate.py and by pipeline/validate.py."""
from __future__ import annotations


class Checker:
    def __init__(self, title: str):
        self.title = title
        self.failed: list[str] = []
        self.pending: list[str] = []
        print(f"\n## {title}")

    def check(self, name: str, ok: bool, detail: str = "") -> bool:
        print(f"[{'ok ' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))
        if not ok:
            self.failed.append(name)
        return ok

    def wait(self, name: str, why: str) -> None:
        print(f"[PENDING] {name}  ({why})")
        self.pending.append(name)
