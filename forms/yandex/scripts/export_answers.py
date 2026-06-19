from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from yf_client import YandexFormsClient


def get_value(item: Dict[str, Any]) -> Any:
    value = item.get("value")
    if value is None:
        return ""
    if isinstance(value, list):
        # API may return labels or objects depending on question type.
        out = []
        for v in value:
            if isinstance(v, dict):
                out.append(str(v.get("label") or v.get("value") or v))
            else:
                out.append(str(v))
        return ", ".join(out)
    if isinstance(value, dict):
        return value.get("label") or value.get("value") or json.dumps(value, ensure_ascii=False)
    return value


def fetch_all(client: YandexFormsClient, survey_id: str, page_size: int) -> Dict[str, Any]:
    result_all = {"columns": None, "answers": []}
    next_path = None
    while True:
        page = client.fetch_answers_page(survey_id, page_size=page_size, next_path=next_path)
        if result_all["columns"] is None:
            result_all["columns"] = page.get("columns") or []
        result_all["answers"].extend(page.get("answers") or [])
        next_page = page.get("next") or {}
        next_path = next_page.get("next_url")
        if not next_path:
            break
    return result_all


def write_csv(path: Path, data: Dict[str, Any]) -> None:
    columns = data.get("columns") or []
    header = ["answer_id", "created"] + [c.get("text") or c.get("id") for c in columns]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for answer in data.get("answers") or []:
            writer.writerow([answer.get("id"), answer.get("created")] + [get_value(x) for x in answer.get("data") or []])


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Yandex Forms answers to JSON/CSV")
    parser.add_argument("survey_id")
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--json", dest="json_path", type=Path)
    parser.add_argument("--csv", dest="csv_path", type=Path)
    args = parser.parse_args()

    client = YandexFormsClient()
    data = fetch_all(client, args.survey_id, args.page_size)

    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"JSON saved to {args.json_path}")
    if args.csv_path:
        write_csv(args.csv_path, data)
        print(f"CSV saved to {args.csv_path}")
    if not args.json_path and not args.csv_path:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
