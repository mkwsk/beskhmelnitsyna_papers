from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Dict, List

from yf_client import YandexFormsClient


DIVIDER = "──────────────── ✦ ────────────────"


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_answerable_item(item: Dict[str, Any]) -> bool:
    payload = item.get("payload", {})
    return item.get("kind") != "comment" and payload.get("type") != "comment"


def get_section_layout(definition: Dict[str, Any], section: Dict[str, Any]) -> Dict[str, Any]:
    layouts = definition.get("section_layout", {})
    section_id = section.get("section_id")
    source_file = section.get("_source_file")
    return dict(layouts.get(section_id) or layouts.get(source_file) or {})


def replace_first_comment_label(items: List[Dict[str, Any]], label: str) -> None:
    for item in items:
        if not is_answerable_item(item):
            payload = item.setdefault("payload", {})
            if payload.get("type") == "comment":
                payload["label"] = label
                payload["header"] = True
                return


def format_part_label(template: str, *, section: Dict[str, Any], part: int, start_item: int, end_item: int) -> str:
    return template.format(
        divider=DIVIDER,
        section_title=section.get("title", ""),
        section_id=section.get("section_id", ""),
        part=part,
        start_item=start_item,
        end_item=end_item,
    )


def build_form_items(definition_path: Path) -> List[Dict[str, Any]]:
    definition = load_json(definition_path)
    base = definition_path.parent
    form_items: List[Dict[str, Any]] = []
    page = 1

    for rel in definition.get("section_files", []):
        section = load_json(base / rel)
        section["_source_file"] = rel
        layout = get_section_layout(definition, section)
        items = copy.deepcopy(section.get("questions", []))

        intro_label = layout.get("intro_label")
        if intro_label:
            replace_first_comment_label(items, intro_label)

        split_every = int(layout.get("answerable_items_per_page") or 0)
        part_label_template = layout.get(
            "part_label_template",
            "{divider}\n\nПродолжение блока: {section_title}\n\nЧасть {part}. Вопросы {start_item}-{end_item}.",
        )

        current_page = page
        answerable_in_part = 0
        answerable_total = 0
        part = 1

        for item in items:
            if split_every and is_answerable_item(item) and answerable_in_part >= split_every:
                part += 1
                current_page += 1
                answerable_in_part = 0
                start_item = answerable_total + 1
                end_item = start_item + split_every - 1
                header_item = {
                    "qid": f"{section.get('section_id')}_part_{part:02d}_header",
                    "kind": "comment",
                    "payload": {
                        "type": "comment",
                        "label": format_part_label(
                            part_label_template,
                            section=section,
                            part=part,
                            start_item=start_item,
                            end_item=end_item,
                        ),
                        "header": True,
                    },
                }
                form_items.append({
                    "item": header_item,
                    "section": section,
                    "page": current_page,
                    "synthetic": True,
                })

            form_items.append({
                "item": item,
                "section": section,
                "page": current_page,
                "synthetic": False,
            })

            if is_answerable_item(item):
                answerable_in_part += 1
                answerable_total += 1

        page = current_page + 1

    return form_items


def iter_sections(definition_path: Path) -> List[Dict[str, Any]]:
    """Compatibility helper: returns sections in section_files order.

    The actual page layout is built by build_form_items(), because some long sections
    can be split into several pages through section_layout.
    """

    definition = load_json(definition_path)
    base = definition_path.parent
    sections = []
    for page_index, rel in enumerate(definition.get("section_files", []), start=1):
        section = load_json(base / rel)
        section["_source_file"] = rel
        section["_resolved_page"] = page_index
        sections.append(section)
    return sections


def prepare_payload(item: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(item["payload"])
    if is_answerable_item(item):
        payload["required"] = True
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Yandex Form from local JSON definition")
    parser.add_argument("definition", type=Path, help="Path to form_definition/vkr_main_form.json")
    parser.add_argument("--publish", action="store_true", help="Publish form after creation")
    parser.add_argument("--output", type=Path, default=Path("exports/form_mapping.json"), help="Where to save local-to-Yandex mapping")
    args = parser.parse_args()

    definition = load_json(args.definition)
    form_items = build_form_items(args.definition)
    client = YandexFormsClient()

    survey_id = client.create_survey(definition["survey_payload"])
    print(f"Created survey {survey_id}")

    created = []
    for entry in form_items:
        item = entry["item"]
        section = entry["section"]
        payload = prepare_payload(item)
        question_id = client.add_question(survey_id, payload)
        print(f"Added {item.get('qid')} -> {question_id}")
        created.append({
            "local_qid": item.get("qid"),
            "yandex_question_id": question_id,
            "page": entry.get("page"),
            "section_id": section.get("section_id"),
            "title": section.get("title"),
            "payload": payload,
            "required": bool(payload.get("required", False)),
            "synthetic": bool(entry.get("synthetic", False)),
            "scoring": item.get("scoring"),
        })

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
