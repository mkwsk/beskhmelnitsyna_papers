from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ALLOWED_PAYLOAD_KEYS = {
    "type", "label", "placeholder", "multiline", "widget", "items", "rows", "columns",
    "data_source", "header", "required",
}


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def validate_payload(code: str, payload: Dict[str, Any], errors: List[str]) -> None:
    if "type" not in payload:
        errors.append(f"{code}: payload has no type")
    if "label" not in payload:
        errors.append(f"{code}: payload has no label")
    extra = set(payload) - ALLOWED_PAYLOAD_KEYS
    if extra:
        errors.append(f"{code}: unknown payload keys: {sorted(extra)}")


def validate_form_definition(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if data.get("schema_version") != "form-definition-v1":
        errors.append("schema_version must be form-definition-v1")
    if "survey_payload" not in data:
        errors.append("survey_payload is required")
    if "section_files" in data:
        errors.append("section_files should not be used here; tests are loaded from methods_manifest.json")
    for block_name in ("screening", "demographics"):
        block = data.get(block_name)
        if not isinstance(block, list):
            errors.append(f"{block_name} must be a list")
            continue
        for item in block:
            if "code" not in item:
                errors.append(f"{block_name}: item without code")
            if "label" not in item:
                errors.append(f"{block_name}: {item.get('code')} has no label")
    return errors


def validate_bundle(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if data.get("schema_version") != "vkr-yandex-forms-bundle-v1":
        errors.append("schema_version must be vkr-yandex-forms-bundle-v1")
    questions = data.get("api", {}).get("questions")
    if not isinstance(questions, list) or not questions:
        errors.append("api.questions must be a non-empty list")
        return errors
    codes = set()
    for question in questions:
        code = question.get("code")
        if not code:
            errors.append("question without code")
            continue
        if code in codes:
            errors.append(f"duplicate question code: {code}")
        codes.add(code)
        validate_payload(code, question.get("payload", {}), errors)
    return errors


def validate(path: Path) -> List[str]:
    data = load_json(path)
    schema = data.get("schema_version")
    if schema == "form-definition-v1":
        return validate_form_definition(data)
    if schema == "vkr-yandex-forms-bundle-v1":
        return validate_bundle(data)
    return [f"Unknown schema_version: {schema}"]


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/validate_definition.py <form_definition_or_bundle.json>")
        return 2
    errors = validate(Path(sys.argv[1]))
    if errors:
        print("Definition has errors:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Definition looks OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
