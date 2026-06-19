from __future__ import annotations

"""
Шаблон подсчета баллов.

Этот файл ожидает CSV, где колонки называются локальными qid:
samoal_q001, gse_q01, cse_q01, rses_q01 и т.д.
После выгрузки из API может понадобиться переименовать колонки по exports/form_mapping.json.
"""

import argparse
import csv
from pathlib import Path
from typing import Dict, List

GSE_MAP = {
    "неверно": 1,
    "скорее неверно": 2,
    "скорее верно": 3,
    "совершенно верно": 4,
}

CSE_MAP = {
    "Совершенно не согласна": 1,
    "Скорее не согласна": 2,
    "Затрудняюсь ответить": 3,
    "Скорее согласна": 4,
    "Полностью согласна": 5,
}
CSE_REVERSE = {"cse_q02", "cse_q04", "cse_q06", "cse_q08", "cse_q10"}
CSE_POSITIVE = {"cse_q01", "cse_q03", "cse_q05", "cse_q07", "cse_q09"}

RSES_MAP = {
    "Полностью не согласна": 1,
    "Не согласна": 2,
    "Согласна": 3,
    "Полностью согласна": 4,
}
RSES_REVERSE = {"rses_q02", "rses_q05", "rses_q06", "rses_q08", "rses_q09"}


def reverse(value: int, min_score: int, max_score: int) -> int:
    return min_score + max_score - value


def score_row(row: Dict[str, str]) -> Dict[str, str]:
    out = dict(row)

    # САМОАЛ: ключи шкал нужно добавить после переноса точного ключа из источника.
    samoal_values = [row.get(f"samoal_q{i:03d}", "") for i in range(1, 101)]
    out["samoal_answered_count"] = str(sum(1 for value in samoal_values if value))
    out["samoal_total"] = ""

    try:
        out["gse_total"] = str(sum(GSE_MAP[row[f"gse_q{i:02d}"]] for i in range(1, 11)))
    except KeyError:
        out["gse_total"] = ""

    try:
        cse_positive = 0
        cse_negative = 0
        for i in range(1, 11):
            key = f"cse_q{i:02d}"
            raw = CSE_MAP[row[key]]
            scored = reverse(raw, 1, 5) if key in CSE_REVERSE else raw
            if key in CSE_POSITIVE:
                cse_positive += scored
            else:
                cse_negative += scored
        out["cse_positive"] = str(cse_positive)
        out["cse_negative"] = str(cse_negative)
        out["cse_total"] = str(cse_positive + cse_negative)
    except KeyError:
        out["cse_positive"] = ""
        out["cse_negative"] = ""
        out["cse_total"] = ""

    try:
        rses_total = 0
        for i in range(1, 11):
            key = f"rses_q{i:02d}"
            raw = RSES_MAP[row[key]]
            rses_total += reverse(raw, 1, 4) if key in RSES_REVERSE else raw
        out["rses_total"] = str(rses_total)
    except KeyError:
        out["rses_total"] = ""

    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("output_csv", type=Path)
    args = parser.parse_args()

    with args.input_csv.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = [score_row(row) for row in reader]
        fieldnames: List[str] = list(reader.fieldnames or [])

    for col in [
        "samoal_answered_count",
        "samoal_total",
        "gse_total",
        "cse_positive",
        "cse_negative",
        "cse_total",
        "rses_total",
    ]:
        if col not in fieldnames:
            fieldnames.append(col)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Scored CSV saved to {args.output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
