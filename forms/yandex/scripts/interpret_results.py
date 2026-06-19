from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


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
        if "value" in value:
            return value["value"]
        if "label" in value:
            return value["label"]
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


def normalize_number_list(text: str | None) -> List[int]:
    if not text:
        return []
    result = []
    for item in re.split(r"[\s,;]+", str(text).strip()):
        if not item:
            continue
        match = re.match(r"^(\d+)", item)
        if match:
            result.append(int(match.group(1)))
    return result


def parse_keyed_items(text: str | None) -> List[Tuple[int, str]]:
    if not text:
        return []
    result: List[Tuple[int, str]] = []
    for item in re.split(r"[\s,;]+", str(text).strip()):
        if not item:
            continue
        match = re.match(r"^(\d+)\s*([A-Za-zА-Яа-я])$", item)
        if match:
            result.append((int(match.group(1)), normalize_ab(match.group(2))))
    return result


def normalize_ab(value: Any) -> str:
    text = str(unwrap(value) or "").strip().lower()
    if not text:
        return ""
    text = text.replace("вариант", "").strip()
    if text.startswith(("a", "а")):
        return "a"
    if text.startswith(("b", "б")):
        return "b"
    match = re.search(r"(^|\s|\.)(([abаб]))(\.|\)|\s|$)", text)
    if match:
        letter = match.group(2)
        return "a" if letter in {"a", "а"} else "b"
    return text[:1]


def safe_float(value: Any, default: float = 1.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def maybe_int(value: float) -> int | float:
    return int(value) if float(value).is_integer() else value


def question_map(bundle: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    result = {}
    for question in bundle.get("api", {}).get("questions", []):
        if question.get("kind") == "question" and question.get("method_id"):
            result[str(question.get("code"))] = question
    return result


def method_map(bundle: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(method.get("id")): method for method in bundle.get("methods", []) if method.get("id")}


def item_maps(method: Dict[str, Any]) -> Tuple[Dict[int, str], Dict[str, int]]:
    number_to_variable: Dict[int, str] = {}
    variable_to_number: Dict[str, int] = {}
    for item in method.get("items") or []:
        try:
            number = int(item.get("item_number") or item.get("number"))
        except Exception:
            continue
        variable = str(item.get("variable") or item.get("code") or "")
        if not variable:
            continue
        number_to_variable[number] = variable
        variable_to_number[variable] = number
    return number_to_variable, variable_to_number


def score_method_by_keys(method: Dict[str, Any], values: Dict[str, Any], questions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    keys = method.get("keys") or []
    if not keys:
        return out
    method_id = str(method.get("id"))
    number_to_variable, _ = item_maps(method)
    for key in keys:
        scale = str(key.get("scale_code") or "total")
        prefix = f"{method_id}_{scale}"
        multiplier = safe_float(key.get("normalize_multiplier"), 1.0)
        keyed = parse_keyed_items(key.get("keyed_items"))
        if keyed:
            raw = 0
            answered = 0
            for number, expected in keyed:
                variable = number_to_variable.get(number)
                if not variable:
                    continue
                value = values.get(variable)
                if value in (None, ""):
                    continue
                answered += 1
                if normalize_ab(value) == expected:
                    raw += 1
            score = raw * multiplier
            out[f"{prefix}_raw"] = raw
            out[prefix] = maybe_int(score)
            out[f"{prefix}_answered"] = answered
            if multiplier and multiplier != 1.0:
                out[f"{prefix}_percent"] = round(score / 15 * 100, 2)
            continue

        direct_items = normalize_number_list(key.get("direct_items"))
        reverse_items = normalize_number_list(key.get("reverse_items"))
        if not direct_items and not reverse_items:
            continue
        total = 0
        answered = 0
        for number in direct_items + reverse_items:
            variable = number_to_variable.get(number)
            question = questions.get(variable)
            if not variable or not question:
                continue
            direction = "reverse" if number in reverse_items else "direct"
            score = choice_score(values.get(variable), question.get("payload") or {}, direction)
            if score is None:
                continue
            total += score
            answered += 1
        score = total * multiplier
        out[f"{prefix}_raw"] = total
        out[prefix] = maybe_int(score)
        out[f"{prefix}_answered"] = answered
    return out


def score_row(row: Dict[str, Any], questions: Dict[str, Dict[str, Any]], methods: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    values = response_values(row)
    out: Dict[str, Any] = dict(values)
    handled_methods = set()

    for method_id, method in methods.items():
        scores = score_method_by_keys(method, values, questions)
        if scores:
            out.update(scores)
            handled_methods.add(method_id)

    totals: Dict[str, int] = {}
    counts: Dict[str, int] = {}
    for code, question in questions.items():
        method_id = question.get("method_id")
        if method_id in handled_methods:
            continue
        scoring = question.get("scoring") or {}
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
    methods = method_map(bundle)
    rows = load_answers(args.answers)
    scored = [score_row(row, questions, methods) for row in rows]
    write_csv(args.out, scored)
    print(f"Saved {len(scored)} interpreted rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
