from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from yf_client import YandexFormsClient


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_sections(definition_path: Path) -> List[Dict[str, Any]]:
    definition = load_json(definition_path)
    base = definition_path.parent
    sections = []
    for rel in definition.get("section_files", []):
        section = load_json(base / rel)
        section["_source_file"] = rel
        sections.append(section)
    return sections


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Yandex Form from local JSON definition")
    parser.add_argument("definition", type=Path, help="Path to form_definition/vkr_main_form.json")
    parser.add_argument("--publish", action="store_true", help="Publish form after creation")
    parser.add_argument("--output", type=Path, default=Path("exports/form_mapping.json"), help="Where to save local-to-Yandex mapping")
    args = parser.parse_args()

    definition = load_json(args.definition)
    sections = iter_sections(args.definition)
    client = YandexFormsClient()

    survey_id = client.create_survey(definition["survey_payload"])
    print(f"Created survey {survey_id}")

    created = []
    for section in sections:
        for item in section.get("questions", []):
            payload = item["payload"]
            question_id = client.add_question(survey_id, payload)
            print(f"Added {item.get('qid')} -> {question_id}")
            created.append({
                "local_qid": item.get("qid"),
                "yandex_question_id": question_id,
                "page": section.get("page", 1),
                "section_id": section.get("section_id"),
                "title": section.get("title"),
                "payload": payload,
                "required": item.get("required"),
                "scoring": item.get("scoring"),
            })

    # Move questions to pages. First page stays as is; for every new page the first item creates a page.
    seen_pages = {1}
    positions: Dict[int, int] = {}
    for item in created:
        page = int(item.get("page") or 1)
        positions[page] = positions.get(page, 0) + 1
        qid = item["yandex_question_id"]
        if page == 1:
            continue
        payload = {"page": page, "position": positions[page]}
        if page not in seen_pages:
            payload["create_page"] = True
            seen_pages.add(page)
        client.move_question(survey_id, qid, payload)
        print(f"Moved {item['local_qid']} to page {page}, position {positions[page]}")

    if args.publish:
        client.publish(survey_id)
        print(f"Published survey {survey_id}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({
        "survey_id": survey_id,
        "published": args.publish,
        "questions": created,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Mapping saved to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
