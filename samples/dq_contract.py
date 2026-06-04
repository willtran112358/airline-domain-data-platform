"""SQ analytics — silver/gold DQ contract (CRITICAL blocks publish)."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"


@dataclass
class DQRule:
    name: str
    severity: Severity
    passed: bool
    detail: str = ""


def check_pnr_not_null(rows: list[dict]) -> DQRule:
    bad = [r for r in rows if not r.get("pnr_locator")]
    return DQRule("pnr_locator_not_null", Severity.CRITICAL, len(bad) == 0, f"{len(bad)} null PNR")


def check_fare_non_negative(rows: list[dict]) -> DQRule:
    bad = [r for r in rows if r.get("base_fare_amount") is not None and float(r["base_fare_amount"]) < 0]
    return DQRule("base_fare_non_negative", Severity.CRITICAL, len(bad) == 0, f"{len(bad)} negative fare")


def run_contract(rows: list[dict]) -> None:
    rules = [check_pnr_not_null(rows), check_fare_non_negative(rows)]
    critical = [r for r in rules if not r.passed and r.severity == Severity.CRITICAL]
    for r in rules:
        print(f"[{'PASS' if r.passed else 'FAIL'}] {r.severity.value} {r.name}: {r.detail}")
    if critical:
        raise SystemExit(1)


if __name__ == "__main__":
    run_contract([
        {"pnr_locator": "5KQZ2A", "base_fare_amount": "1280.00"},
        {"pnr_locator": None, "base_fare_amount": "50.00"},
    ])
