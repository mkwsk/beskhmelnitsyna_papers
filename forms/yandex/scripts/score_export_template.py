from __future__ import annotations

"""
Шаблон подсчета баллов.

Этот файл ожидает CSV, где колонки называются локальными qid: gse_q01, rses_q01, gav_q01 и т.д.
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
RSES_MAP = {
    "Полностью не согласна": 1,
    "Не согласна": 2,
    "Согласна": 3,
    "Полностью согласна": 4,
}
RSES_REVERSE = {"rses_q02", "rses_q05", "rses_q06", "rses_q08", "rses_q09"}
GAV_MAP = {"Нет": 0, "Отчасти верно": 1, "Да": 2}


def reverse(value: int, min_score: int, max_score: int) -> int:
    return min_score + max_score - value


def score_row(row: Dict[str, str]) -> Dict[str, str]:
    out = dict(row)
    try:
        out["gse_total"] = str(sum(GSE_MAP[row[f"gse_q{i:02d}"]] for i in range(1, 11)))
    except KeyError:
        out["gse_total"] = ""

    try:
        rses_total = 0
        for i in range(1, 11):
            key = f"rses_q{i:02d}"
            raw = RSES_MAP[row[key]]
            rses_total += reverse(raw, 1, 4) if key in RSES_REVERSE else raw
        out["rses_total"] = str(rses_total)
    except KeyError:
        out["rses_total"] = ""

    # TODO: заполнить ключи Гавриловой по статье.
    # Пока считаем только общий сырой балл по всем 51 пунктам.
    try:
        out["gav_total_raw_all_items"] = str(sum(GAV_MAP[row[f"gav_q{i:02d}"]] for i in range(1, 52)))
    except KeyError:
        out["gav_total_raw_all_items"] = ""
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
    for col in ["gse_total", "rses_total", "gav_total_raw_all_items"]:
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
