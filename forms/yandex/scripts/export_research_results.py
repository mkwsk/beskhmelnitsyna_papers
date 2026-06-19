from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
from urllib.parse import urlparse

from yf_client import YandexFormsClient, YandexFormsError


class CliError(Exception):
    """User-facing command line error without a Python traceback."""


def read_json(path: Path, *, required: bool = True) -> Dict[str, Any]:
    if not path.exists():
        if required:
            raise CliError(f"JSON file not found: {path}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as error:
        raise CliError(f"Invalid JSON: {path}\n{error.msg} at line {error.lineno}, column {error.colno}") from error


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_next_path(next_url: str | None) -> str | None:
    if not next_url:
        return None
    parsed = urlparse(next_url)
    if parsed.scheme and parsed.netloc:
        path = parsed.path
        if parsed.query:
            path += f"?{parsed.query}"
    else:
        path = next_url
    if path.startswith("/v1/"):
        path = path[3:]
    return path


def fetch_answers_page(client: YandexFormsClient, survey_id: str, *, page_size: int, next_url: str | None = None) -> Dict[str, Any]:
    path = normalize_next_path(next_url) or f"/surveys/{survey_id}/answers?page_size={page_size}"
    response = client._request("GET", path, expected=(200,))
    return response.json()


def fetch_all_answers(client: YandexFormsClient, survey_id: str, *, page_size: int) -> Dict[str, Any]:
    result: Dict[str, Any] = {"survey_id": survey_id, "columns": None, "answers": []}
    next_url: str | None = None
    while True:
        page = fetch_answers_page(client, survey_id, page_size=page_size, next_url=next_url)
        if result["columns"] is None:
            result["columns"] = page.get("columns") or []
        result["answers"].extend(page.get("answers") or [])
        next_info = page.get("next") or {}
        next_url = next_info.get("next_url") or next_info.get("url") or page.get("next_url")
        if not next_url:
            break
    return result


def value_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(value_to_text(item) for item in value if value_to_text(item) != "")
    if isinstance(value, dict):
        if "label" in value:
            return str(value.get("label") or "")
        if "value" in value:
            return value_to_text(value.get("value"))
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def answer_item_value(item: Any) -> str:
    if isinstance(item, dict):
        if "value" in item:
            return value_to_text(item.get("value"))
        if "answer" in item:
            return value_to_text(item.get("answer"))
    return value_to_text(item)


def norm_text(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def build_code_lookup(bundle: Dict[str, Any], mapping: Dict[str, Any]) -> tuple[Dict[str, str], Dict[str, str]]:
    by_id: Dict[str, str] = {}
    by_label: Dict[str, str] = {}

    for field in mapping.get("fields") or []:
        code = str(field.get("code") or "")
        if not code:
            continue
        question_id = field.get("question_id")
        if question_id not in (None, ""):
            by_id[str(question_id)] = code
        payload = field.get("payload") or {}
        label = norm_text(payload.get("label"))
        if label:
            by_label[label] = code

    for question in bundle.get("api", {}).get("questions", []):
        code = str(question.get("code") or "")
        payload = question.get("payload") or {}
        label = norm_text(payload.get("label"))
        if code and label:
            by_label.setdefault(label, code)

    return by_id, by_label


def column_candidates(column: Dict[str, Any]) -> tuple[list[str], list[str]]:
    ids = []
    labels = []
    for key in ("id", "question_id", "questionId", "field_id", "fieldId"):
        value = column.get(key)
        if value not in (None, ""):
            ids.append(str(value))
    for key in ("text", "label", "title", "name"):
        value = column.get(key)
        if value not in (None, ""):
            labels.append(norm_text(value))
    return ids, labels


def fallback_code(column: Dict[str, Any], index: int) -> str:
    for key in ("id", "question_id", "field_id"):
        value = column.get(key)
        if value not in (None, ""):
            return f"field_{value}"
    return f"field_{index:03d}"


def resolve_columns(columns: Iterable[Dict[str, Any]], by_id: Dict[str, str], by_label: Dict[str, str]) -> List[str]:
    used: Dict[str, int] = {}
    result: List[str] = []
    for index, column in enumerate(columns, start=1):
        code = ""
        ids, labels = column_candidates(column)
        for item in ids:
            if item in by_id:
                code = by_id[item]
                break
        if not code:
            for item in labels:
                if item in by_label:
                    code = by_label[item]
                    break
        if not code:
            code = fallback_code(column, index)
        used[code] = used.get(code, 0) + 1
        result.append(code if used[code] == 1 else f"{code}_{used[code]}")
    return result


def answer_row(answer: Dict[str, Any], field_codes: List[str]) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "answer_id": answer.get("id") or answer.get("answer_id") or "",
        "created": answer.get("created") or answer.get("created_at") or "",
    }
    data = answer.get("data") or []
    if isinstance(data, dict):
        for key, value in data.items():
            row[str(key)] = answer_item_value(value)
    elif isinstance(data, list):
        for code, item in zip(field_codes, data):
            row[code] = answer_item_value(item)
    return row


def write_csv(path: Path, rows: List[Dict[str, Any]], preferred_fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["answer_id", "created"] + preferred_fields
    extras = sorted({key for row in rows for key in row} - set(fieldnames))
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames + extras)
        writer.writeheader()
        writer.writerows(rows)


def write_codebook(path: Path, columns: List[Dict[str, Any]], field_codes: List[str]) -> None:
    rows = []
    for index, (column, code) in enumerate(zip(columns, field_codes), start=1):
        rows.append({
            "order": index,
            "variable": code,
            "column_id": column.get("id") or column.get("question_id") or "",
            "column_text": column.get("text") or column.get("label") or column.get("title") or "",
        })
    write_csv(path, rows, ["order", "variable", "column_id", "column_text"])


def write_interpreted(bundle: Dict[str, Any], rows: List[Dict[str, Any]], out_path: Path) -> None:
    from interpret_results import method_map, question_map, score_row, write_csv as write_scored_csv

    questions = question_map(bundle)
    methods = method_map(bundle)
    scored = [score_row(row, questions, methods) for row in rows]
    write_scored_csv(out_path, scored)
    print(f"Interpreted CSV saved to {out_path}")


def resolve_survey_id(args: argparse.Namespace, mapping: Dict[str, Any]) -> str:
    if args.survey_id:
        return str(args.survey_id)
    survey_id = mapping.get("survey_id")
    if survey_id:
        return str(survey_id)
    raise CliError("Survey id is not set. Pass --survey-id or provide exports/form_mapping.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Yandex Forms research answers and calculate method scores")
    parser.add_argument("--survey-id", default=None, help="Yandex Forms survey id. If omitted, read from --mapping")
    parser.add_argument("--bundle", type=Path, default=Path("output/compiled_form_bundle.json"), help="Compiled form bundle")
    parser.add_argument("--mapping", type=Path, default=Path("exports/form_mapping.json"), help="Mapping saved by create_form.py")
    parser.add_argument("--out-dir", type=Path, default=Path("exports/research_results"), help="Output directory")
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--no-interpret", action="store_true", help="Only export raw answers and normalized CSV")
    args = parser.parse_args()

    try:
        bundle = read_json(args.bundle, required=not args.no_interpret)
        mapping = read_json(args.mapping, required=False)
        survey_id = resolve_survey_id(args, mapping)

        client = YandexFormsClient()
        export_data = fetch_all_answers(client, survey_id, page_size=args.page_size)
        columns = export_data.get("columns") or []
        by_id, by_label = build_code_lookup(bundle, mapping)
        field_codes = resolve_columns(columns, by_id, by_label)
        rows = [answer_row(answer, field_codes) for answer in export_data.get("answers") or []]

        raw_path = args.out_dir / "answers_raw.json"
        csv_path = args.out_dir / "answers_by_code.csv"
        codebook_path = args.out_dir / "codebook.csv"
        interpreted_path = args.out_dir / "interpreted_results.csv"

        write_json(raw_path, export_data)
        write_csv(csv_path, rows, field_codes)
        write_codebook(codebook_path, columns, field_codes)
        print(f"Raw JSON saved to {raw_path}")
        print(f"Answers CSV saved to {csv_path}")
        print(f"Codebook saved to {codebook_path}")

        if not args.no_interpret:
            write_interpreted(bundle, rows, interpreted_path)
        print(f"Exported {len(rows)} answers")
        return 0
    except (CliError, YandexFormsError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
