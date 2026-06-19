from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ALLOWED_PAYLOAD_KEYS = {
    "type", "label", "placeholder", "multiline", "widget", "items", "rows", "columns",
    "data_source", "header",
}


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(definition_path: Path) -> List[str]:
    errors: List[str] = []
    root = definition_path.parent
    definition = load_json(definition_path)
    if "survey_payload" not in definition:
        errors.append("Missing survey_payload")
    if not definition.get("section_files"):
        errors.append("Missing section_files")

    qids = set()
    for rel in definition.get("section_files", []):
        section_path = root / rel
        if not section_path.exists():
            errors.append(f"Section file does not exist: {rel}")
            continue
        section = load_json(section_path)
        if "questions" not in section:
            errors.append(f"No questions in {rel}")
            continue
        for item in section["questions"]:
            qid = item.get("qid")
            if not qid:
                errors.append(f"Question without qid in {rel}")
            elif qid in qids:
                errors.append(f"Duplicate qid: {qid}")
            else:
                qids.add(qid)
            payload = item.get("payload")
            if not isinstance(payload, dict):
                errors.append(f"Question {qid} has no payload")
                continue
            if "type" not in payload or "label" not in payload:
                errors.append(f"Question {qid} payload must contain type and label")
            extra = set(payload) - ALLOWED_PAYLOAD_KEYS
            if extra:
                errors.append(f"Question {qid} has unknown payload keys: {sorted(extra)}")
            if "TODO" in str(payload.get("label", "")):
                errors.append(f"Question {qid} still contains TODO placeholder")
            if item.get("placeholder_item_text") and "TODO" not in payload.get("label", ""):
                errors.append(f"Question {qid} marked as placeholder but label has no TODO")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/validate_definition.py form_definition/vkr_main_form.json", file=sys.stderr)
        return 2
    errors = validate(Path(sys.argv[1]))
    if errors:
        print("Definition has errors:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Definition looks OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
