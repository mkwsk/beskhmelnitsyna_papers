from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from yf_client import YandexFormsClient


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def is_answerable(question: Dict[str, Any]) -> bool:
    payload = question.get("payload", {})
    return question.get("kind") != "comment" and payload.get("type") != "comment"


def prepare_payload(question: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(question["payload"])
    if is_answerable(question):
        payload["required"] = bool(question.get("required", True))
    return payload


def create_from_bundle(bundle_path: Path, *, publish: bool, output: Path) -> int:
    bundle = load_json(bundle_path)
    if bundle.get("schema_version") != "vkr-yandex-forms-bundle-v1":
        raise SystemExit(
            "Input file is not a compiled bundle. Run: "
            "python scripts/compile_form_json.py --out output/compiled_form_bundle.json"
        )

    api = bundle.get("api") or {}
    survey_payload = api.get("survey") or {}
    questions: List[Dict[str, Any]] = api.get("questions") or []
    if not questions:
        raise SystemExit("Compiled bundle has no api.questions")

    client = YandexFormsClient()
    survey_id = client.create_survey(survey_payload)
    print(f"Created survey {survey_id}")

    created = []
    for question in questions:
        payload = prepare_payload(question)
        yandex_question_id = client.add_question(survey_id, payload)
        print(f"Added {question.get('code')} -> {yandex_question_id}")
        created.append({
            "code": question.get("code"),
            "question_id": yandex_question_id,
            "page": int(question.get("page") or 1),
            "kind": question.get("kind"),
            "method_id": question.get("method_id"),
            "payload": payload,
            "required": bool(payload.get("required", False)),
            "scoring": question.get("scoring"),
        })

    seen_pages = {1}
    positions: Dict[int, int] = {}
    for item in created:
        page = int(item.get("page") or 1)
        positions[page] = positions.get(page, 0) + 1
        if page == 1:
            continue
        move_payload: Dict[str, Any] = {"page": page, "position": positions[page]}
        if page not in seen_pages:
            move_payload["create_page"] = True
            seen_pages.add(page)
        client.move_question(survey_id, item["question_id"], move_payload)
        print(f"Moved {item['code']} to page {page}, position {positions[page]}")

    if publish:
        client.publish(survey_id)
        print(f"Published survey {survey_id}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "survey_id": survey_id,
        "published": publish,
        "fields": created,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Mapping saved to {output}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Yandex Form from compiled bundle")
    parser.add_argument("bundle", type=Path, help="Path to output/compiled_form_bundle.json")
    parser.add_argument("--publish", action="store_true", help="Publish form after creation")
    parser.add_argument("--output", type=Path, default=Path("exports/form_mapping.json"), help="Where to save local-to-Yandex mapping")
    args = parser.parse_args()
    return create_from_bundle(args.bundle, publish=args.publish, output=args.output)


if __name__ == "__main__":
    raise SystemExit(main())
