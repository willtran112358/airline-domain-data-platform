"""Proposed: lightweight DQ contract runner (no Spark required)."""
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
    return DQRule(
        name="pnr_locator_not_null",
        severity=Severity.CRITICAL,
        passed=len(bad) == 0,
        detail=f"{len(bad)} rows missing PNR",
    )


def check_fare_non_negative(rows: list[dict]) -> DQRule:
    bad = [r for r in rows if r.get("base_fare_amount") is not None and float(r["base_fare_amount"]) < 0]
    return DQRule(
        name="base_fare_non_negative",
        severity=Severity.CRITICAL,
        passed=len(bad) == 0,
        detail=f"{len(bad)} negative fares",
    )


def run_contract(sample_rows: list[dict]) -> None:
    rules = [
        check_pnr_not_null(sample_rows),
        check_fare_non_negative(sample_rows),
    ]
    critical = [r for r in rules if not r.passed and r.severity == Severity.CRITICAL]
    for r in rules:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.severity.value} {r.name}: {r.detail}")
    if critical:
        raise SystemExit(1)


if __name__ == "__main__":
    run_contract(
        [
            {"pnr_locator": "ABC123", "base_fare_amount": "120.00"},
            {"pnr_locator": None, "base_fare_amount": "50.00"},
        ]
    )
