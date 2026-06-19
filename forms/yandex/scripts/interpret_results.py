from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_answers(path: Path) -> List[Dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        return read_csv(path)
    data = read_json(path)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("answers"), list):
            return data["answers"]
        if isinstance(data.get("items"), list):
            return data["items"]
    raise SystemExit("Unsupported answers format. Use CSV or JSON list/object with answers/items.")


def unwrap(value: Any) -> Any:
    if isinstance(value, dict):
        if "label" in value:
            return value["label"]
        if "value" in value:
            return value["value"]
    if isinstance(value, list):
        return unwrap(value[0]) if value else None
    return value


def response_values(row: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(row.get("data"), dict):
        return {str(k): unwrap(v) for k, v in row["data"].items()}
    if isinstance(row.get("answers"), dict):
        return {str(k): unwrap(v) for k, v in row["answers"].items()}
    return {str(k): unwrap(v) for k, v in row.items()}


def choice_score(value: Any, payload: Dict[str, Any], direction: str) -> int | None:
    value = unwrap(value)
    if value in (None, ""):
        return None
    try:
        raw = int(value)
    except Exception:
        raw = None
    if raw is None:
        text = str(value).strip().lower()
        raw = None
        for index, item in enumerate(payload.get("items") or [], start=1):
            label = str(item.get("label", "")).strip().lower()
            if text == label or text in label:
                raw = index
                break
    if raw is None:
        return None
    if direction == "reverse":
        count = len(payload.get("items") or []) or raw
        return count + 1 - raw
    return raw


def question_map(bundle: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    result = {}
    for question in bundle.get("api", {}).get("questions", []):
        if question.get("kind") == "question" and question.get("method_id"):
            result[str(question.get("code"))] = question
    return result


def score_row(row: Dict[str, Any], questions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    values = response_values(row)
    out: Dict[str, Any] = dict(values)
    totals: Dict[str, int] = {}
    counts: Dict[str, int] = {}
    for code, question in questions.items():
        scoring = question.get("scoring") or {}
        method_id = question.get("method_id")
        scale = scoring.get("scale_code") or "total"
        direction = scoring.get("direction") or "direct"
        score = choice_score(values.get(code), question.get("payload") or {}, direction)
        if score is None:
            continue
        prefix = f"{method_id}_{scale}"
        totals[prefix] = totals.get(prefix, 0) + score
        counts[prefix] = counts.get(prefix, 0) + 1
    for key, value in totals.items():
        out[key] = value
        out[f"{key}_answered"] = counts.get(key, 0)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Interpret exported answers using compiled form bundle")
    parser.add_argument("--bundle", type=Path, default=Path("output/compiled_form_bundle.json"))
    parser.add_argument("--answers", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("output/interpreted_results.csv"))
    args = parser.parse_args()

    bundle = read_json(args.bundle)
    questions = question_map(bundle)
    rows = load_answers(args.answers)
    scored = [score_row(row, questions) for row in rows]
    write_csv(args.out, scored)
    print(f"Saved {len(scored)} interpreted rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
