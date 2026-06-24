from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ALLOWED_PAYLOAD_KEYS = {
    "type", "label", "placeholder", "multiline", "widget", "items", "rows", "columns",
    "data_source", "header",
}

PLACEHOLDER_MARKERS = (
    "TODO",
    "PLACEHOLDER",
    "ВСТАВИТЬ ТОЧН",
    "ДОБАВИТЬ ТЕКСТ",
)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as error:
        raise SystemExit(f"ERROR: cannot read JSON {path}: {error}")


def has_placeholder(value: Any) -> bool:
    text = str(value or "").strip().upper()
    return any(marker in text for marker in PLACEHOLDER_MARKERS)


def validate_payload(code: str, payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    extra = set(payload) - ALLOWED_PAYLOAD_KEYS
    if extra:
        errors.append(f"{code}: unknown payload keys: {sorted(extra)}")

    label = str(payload.get("label") or "").strip()
    if not label:
        errors.append(f"{code}: empty payload.label")
    if has_placeholder(label):
        errors.append(f"{code}: placeholder text in payload.label")

    if payload.get("type") == "enum":
        items = payload.get("items")
        if not isinstance(items, list) or not items:
            errors.append(f"{code}: enum question must have non-empty items")
        else:
            for index, item in enumerate(items, start=1):
                item_label = str((item or {}).get("label") or "").strip()
                if not item_label:
                    errors.append(f"{code}: empty label in enum item {index}")
                if has_placeholder(item_label):
                    errors.append(f"{code}: placeholder text in enum item {index}")

    return errors


def validate(path: Path) -> list[str]:
    data = load_json(path)
    schema = data.get("schema_version")
    errors: list[str] = []

    if schema == "form-definition-v1":
        if "survey_payload" not in data:
            errors.append("survey_payload is missing")
        if not isinstance(data.get("screening"), list):
            errors.append("screening must be a list")
        if not isinstance(data.get("demographics"), list):
            errors.append("demographics must be a list")
        if "participant_information" in data and not isinstance(data.get("participant_information"), dict):
            errors.append("participant_information must be an object")
        for section_name in ("intro", "participant_information", "closing"):
            section = data.get(section_name) or {}
            if section and has_placeholder(section.get("title")):
                errors.append(f"{section_name}: placeholder in title")
            for index, line in enumerate(section.get("body") or [], start=1):
                if has_placeholder(line):
                    errors.append(f"{section_name}: placeholder in body line {index}")
        for group_name in ("screening", "demographics"):
            for field in data.get(group_name) or []:
                code = str(field.get("code") or "<without_code>")
                if has_placeholder(field.get("label")):
                    errors.append(f"{code}: placeholder in field label")
        return errors

    if schema == "vkr-yandex-forms-bundle-v1":
        questions = data.get("api", {}).get("questions")
        if not isinstance(questions, list) or not questions:
            return ["api.questions must be a non-empty list"]
        codes: set[str] = set()
        for question in questions:
            code = question.get("code")
            if not code:
                errors.append("question without code")
                continue
            if code in codes:
                errors.append(f"duplicate question code: {code}")
            codes.add(code)
            payload = question.get("payload", {})
            errors.extend(validate_payload(str(code), payload))
        return errors

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
