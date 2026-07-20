#!/usr/bin/env python3
"""binary_validator.py — reduce a set of acceptance predicates to a single bit.

A step is SUCCESS only if EVERY predicate passed. There is no partial credit.
This mirrors the Master Contract's binary classification rule.
"""
from __future__ import annotations
import json
import sys


def classify(predicate_results: list[dict]) -> str:
    if not predicate_results:
        return "FAILURE"
    return "SUCCESS" if all(p.get("passed") is True for p in predicate_results) else "FAILURE"


if __name__ == "__main__":
    data = json.load(sys.stdin)
    print(classify(data.get("predicate_results", [])))
