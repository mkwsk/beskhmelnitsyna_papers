from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

from interpret_results import load_answers, method_map, question_map, read_json, score_row

PREFIX_MAP = {
    "samoal_lazukin_kalina_": "samoal_",
    "gse_schwarzer_jerusalem_ru_": "gse_",
    "core_self_evaluation_scale_ru_": "cse_",
    "rosenberg_self_esteem_scale_ru_": "rses_",
}

COLUMN_RENAMES = {
    "cse_neg_rev": "cse_negative",
    "cse_neg_rev_raw": "cse_negative_raw",
    "cse_neg_rev_answered": "cse_negative_answered",
}


class CliError(Exception):
    pass


def norm_text(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().replace("ё", "е").split())


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ordered_columns(rows: Iterable[Dict[str, Any]]) -> List[str]:
    columns: List[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                columns.append(key)
    return columns


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = ordered_columns(rows)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def mapping_lookup(mapping: Dict[str, Any]) -> Dict[str, str]:
    lookup: Dict[str, str] = {}
    for field in mapping.get("fields") or []:
        code = str(field.get("code") or "")
        if not code:
            continue
        lookup[code] = code
        qid = field.get("question_id")
        if qid not in (None, ""):
            lookup[str(qid)] = code
        label = (field.get("payload") or {}).get("label")
        if label:
            lookup[norm_text(label)] = code
    return lookup


def apply_mapping(row: Dict[str, Any], mapping: Dict[str, Any] | None) -> Dict[str, Any]:
    if not mapping:
        return dict(row)
    lookup = mapping_lookup(mapping)
    if not lookup:
        return dict(row)
    out: Dict[str, Any] = {}
    for key, value in row.items():
        mapped = lookup.get(str(key)) or lookup.get(norm_text(key)) or str(key)
        if mapped not in out or out[mapped] in (None, ""):
            out[mapped] = value
    return out


def short_name(name: str) -> str:
    result = name
    for old, new in PREFIX_MAP.items():
        if result.startswith(old):
            result = new + result[len(old):]
            break
    return COLUMN_RENAMES.get(result, result)


def method_item_columns(bundle: Dict[str, Any]) -> set[str]:
    result = set()
    for method in bundle.get("methods") or []:
        for item in method.get("items") or []:
            variable = item.get("variable") or item.get("code")
            if variable:
                result.add(str(variable))
    return result


def normalize_score_columns(row: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, value in row.items():
        out[short_name(key)] = value
    if out.get("rses_total") not in (None, "") and "rses_total_0_3" not in out:
        try:
            answered = float(out.get("rses_total_answered") or 10)
            out["rses_total_0_3"] = int(float(out["rses_total"]) - answered)
        except Exception:
            pass
    return out


def score_rows(bundle: Dict[str, Any], rows: List[Dict[str, Any]], mapping: Dict[str, Any] | None, scores_only: bool) -> List[Dict[str, Any]]:
    questions = question_map(bundle)
    methods = method_map(bundle)
    item_columns = method_item_columns(bundle)
    result = []
    for row in rows:
        mapped_row = apply_mapping(row, mapping)
        scored = normalize_score_columns(score_row(mapped_row, questions, methods))
        if scores_only:
            scored = {key: value for key, value in scored.items() if key not in item_columns}
        result.append(scored)
    return result


def is_score_column(name: str) -> bool:
    if name.endswith(("_raw", "_percent", "_answered", "_answered_count", "_complete")):
        return True
    return bool(re.search(r"^(samoal|gse|cse|rses)_", name))


def report(scored_rows: List[Dict[str, Any]], bundle: Dict[str, Any]) -> Dict[str, Any]:
    columns = ordered_columns(scored_rows)
    score_columns = [name for name in columns if is_score_column(name)]
    return {
        "rows": len(scored_rows),
        "methods": [method.get("id") for method in bundle.get("methods") or []],
        "score_columns": score_columns,
        "missing_by_score_column": {
            name: sum(1 for row in scored_rows if row.get(name) in (None, ""))
            for name in score_columns
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score exported Yandex Forms answers by method keys")
    parser.add_argument("--bundle", type=Path, default=Path("output/compiled_form_bundle.json"))
    parser.add_argument("--answers", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("output/scored_responses.csv"))
    parser.add_argument("--mapping", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--scores-only", action="store_true")
    args = parser.parse_args()
    try:
        bundle = read_json(args.bundle)
        rows = load_answers(args.answers)
        mapping = read_json(args.mapping) if args.mapping else None
        scored = score_rows(bundle, rows, mapping, args.scores_only)
        write_csv(args.out, scored)
        print(f"Saved {len(scored)} scored rows to {args.out}")
        if args.report:
            write_json(args.report, report(scored, bundle))
            print(f"Scoring report saved to {args.report}")
        return 0
    except (CliError, OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
