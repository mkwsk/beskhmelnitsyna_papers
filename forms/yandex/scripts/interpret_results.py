from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

PREFIX_MAP = {
    "samoal_lazukin_kalina_": "samoal_",
    "gse_schwarzer_jerusalem_ru_": "gse_",
    "core_self_evaluation_scale_ru_": "cse_",
    "rosenberg_self_esteem_scale_ru_": "rses_",
    "gavrilova_professional_self_realization_": "gav_",
}

COLUMN_RENAMES = {
    "cse_neg_rev": "cse_negative",
    "cse_neg_rev_raw": "cse_negative_raw",
    "cse_neg_rev_answered_count": "cse_negative_answered_count",
    "cse_neg_rev_complete": "cse_negative_complete",
}


class CliError(Exception):
    """User-facing command line error without a Python traceback."""


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as error:
        raise CliError(f"Cannot read JSON {path}: {error}") from error


def read_csv(path: Path) -> List[Dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    except Exception as error:
        raise CliError(f"Cannot read CSV {path}: {error}") from error


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
    fields = ordered_columns(rows)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_answers(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise CliError(f"Answers file not found: {path}")
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
    raise CliError("Unsupported answers format. Use CSV or JSON list/object with answers/items.")


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


def norm_text(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().replace("ё", "е").split())


def mapping_lookup(mapping: Dict[str, Any]) -> Dict[str, str]:
    lookup: Dict[str, str] = {}
    for field in mapping.get("fields") or []:
        code = str(field.get("code") or "")
        if not code:
            continue
        lookup[code] = code
        question_id = field.get("question_id")
        if question_id not in (None, ""):
            lookup[str(question_id)] = code
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


def choice_score(value: Any, payload: Dict[str, Any], direction: str) -> int | None:
    value = unwrap(value)
    if value in (None, ""):
        return None
    try:
        raw = int(value)
    except Exception:
        raw = None

    if raw is None:
        text = norm_text(value)
        for index, item in enumerate(payload.get("items") or [], start=1):
            label = norm_text(item.get("label", ""))
            if text == label:
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


def normalize_ab(value: Any) -> str:
    text = norm_text(unwrap(value))
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


def safe_float(value: Any, default: float = 1.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def maybe_int(value: float) -> int | float:
    return int(value) if float(value).is_integer() else value


def short_name(name: str) -> str:
    result = name
    for old, new in PREFIX_MAP.items():
        if result.startswith(old):
            result = new + result[len(old):]
            break
    return COLUMN_RENAMES.get(result, result)


def question_map(bundle: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    result = {}
    for question in bundle.get("api", {}).get("questions", []):
        if question.get("kind") == "question" and question.get("method_id"):
            result[str(question.get("code"))] = question
    return result


def method_map(bundle: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(method.get("id")): method for method in bundle.get("methods", []) if method.get("id")}


def method_item_columns(bundle: Dict[str, Any]) -> set[str]:
    result = set()
    for method in bundle.get("methods") or []:
        for item in method.get("items") or []:
            variable = item.get("variable") or item.get("code")
            if variable:
                result.add(str(variable))
    return result


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


def add_scale_quality(out: Dict[str, Any], prefix: str, answered: int, expected: int) -> None:
    out[f"{prefix}_answered_count"] = answered
    out[f"{prefix}_complete"] = bool(expected and answered == expected)


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
            add_scale_quality(out, prefix, answered, len(keyed))
            if multiplier and multiplier != 1.0:
                out[f"{prefix}_percent"] = round(score / 15 * 100, 2)
            continue

        direct_items = normalize_number_list(key.get("direct_items"))
        reverse_items = normalize_number_list(key.get("reverse_items"))
        expected_items = direct_items + reverse_items
        if not expected_items:
            continue

        total = 0
        answered = 0
        for number in expected_items:
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
        add_scale_quality(out, prefix, answered, len(expected_items))

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
    expected: Dict[str, int] = {}
    for code, question in questions.items():
        method_id = question.get("method_id")
        if method_id in handled_methods:
            continue
        scoring = question.get("scoring") or {}
        scale = scoring.get("scale_code") or "total"
        direction = scoring.get("direction") or "direct"
        score = choice_score(values.get(code), question.get("payload") or {}, direction)
        prefix = f"{method_id}_{scale}"
        expected[prefix] = expected.get(prefix, 0) + 1
        if score is None:
            continue
        totals[prefix] = totals.get(prefix, 0) + score
        counts[prefix] = counts.get(prefix, 0) + 1

    for key, value in totals.items():
        out[key] = value
        add_scale_quality(out, key, counts.get(key, 0), expected.get(key, 0))

    return out


def normalize_column_names(row: Dict[str, Any], *, long_names: bool) -> Dict[str, Any]:
    if long_names:
        return dict(row)
    out: Dict[str, Any] = {}
    for key, value in row.items():
        out[short_name(key)] = value
    return out


def score_rows(
    bundle: Dict[str, Any],
    rows: List[Dict[str, Any]],
    mapping: Dict[str, Any] | None = None,
    *,
    scores_only: bool = False,
    long_names: bool = False,
) -> List[Dict[str, Any]]:
    questions = question_map(bundle)
    methods = method_map(bundle)
    item_columns = method_item_columns(bundle)
    result = []

    for row in rows:
        mapped_row = apply_mapping(row, mapping)
        scored = score_row(mapped_row, questions, methods)
        if scores_only:
            scored = {key: value for key, value in scored.items() if key not in item_columns}
        result.append(normalize_column_names(scored, long_names=long_names))

    return result


def scores_only_rows(scored_rows: List[Dict[str, Any]], bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
    item_columns = method_item_columns(bundle)
    short_item_columns = {short_name(name) for name in item_columns}
    return [
        {key: value for key, value in row.items() if key not in item_columns and key not in short_item_columns}
        for row in scored_rows
    ]


def is_score_column(name: str) -> bool:
    if name.endswith(("_raw", "_percent", "_answered_count", "_complete")):
        return True
    return bool(re.search(r"^(samoal|gse|cse|rses|gav)_", name))


def scoring_report(scored_rows: List[Dict[str, Any]], bundle: Dict[str, Any]) -> Dict[str, Any]:
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
        "incomplete_by_score_column": {
            name: sum(1 for row in scored_rows if row.get(name) is False)
            for name in score_columns
            if name.endswith("_complete")
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Interpret exported answers using compiled form bundle")
    parser.add_argument("--bundle", type=Path, default=Path("output/compiled_form_bundle.json"))
    parser.add_argument("--answers", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, default=None, help="Optional exports/form_mapping.json for manually exported CSV")
    parser.add_argument("--out", type=Path, default=Path("output/interpreted_results.csv"))
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--scores-only", action="store_true", help="Drop raw method item answers from output")
    parser.add_argument("--long-names", action="store_true", help="Keep full method_id prefixes in score columns")
    args = parser.parse_args()

    try:
        bundle = read_json(args.bundle)
        rows = load_answers(args.answers)
        mapping = read_json(args.mapping) if args.mapping else None
        scored = score_rows(bundle, rows, mapping, scores_only=args.scores_only, long_names=args.long_names)
        write_csv(args.out, scored)
        print(f"Saved {len(scored)} interpreted rows to {args.out}")
        if args.report:
            write_json(args.report, scoring_report(scored, bundle))
            print(f"Scoring report saved to {args.report}")
        return 0
    except CliError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
