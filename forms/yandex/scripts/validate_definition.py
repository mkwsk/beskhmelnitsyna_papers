from __future__ import annotations

import json
import sys
from pathlib import Path

ALLOWED_PAYLOAD_KEYS = {
    "type", "label", "placeholder", "multiline", "widget", "items", "rows", "columns",
    "data_source", "header",
}


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as error:
        raise SystemExit(f"ERROR: cannot read JSON {path}: {error}")


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
            extra = set(payload) - ALLOWED_PAYLOAD_KEYS
            if extra:
                errors.append(f"{code}: unknown payload keys: {sorted(extra)}")
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
