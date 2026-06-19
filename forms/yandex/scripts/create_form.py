from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from yf_client import YandexFormsClient, YandexFormsError

TRUTHY = {"1", "true", "yes", "y", "да"}
FALSY = {"0", "false", "no", "n", "нет"}


class CliError(Exception):
    """User-facing command line error without a Python traceback."""



def require_file(path: Path, description: str, *, missing_hint: str | None = None) -> None:
    if not path.exists():
        message = f"{description} not found: {path}"
        if missing_hint:
            message += f"\n{missing_hint}"
        raise CliError(message)
    if not path.is_file():
        raise CliError(f"{description} is not a file: {path}")



def load_json(path: Path, *, description: str, missing_hint: str | None = None) -> Dict[str, Any]:
    require_file(path, description, missing_hint=missing_hint)
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as error:
        raise CliError(
            f"{description} is not valid JSON: {path}\n"
            f"{error.msg} at line {error.lineno}, column {error.colno}"
        ) from error
    except OSError as error:
        raise CliError(f"Cannot read {description}: {path}\n{error}") from error



def bool_flag(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in TRUTHY:
        return True
    if normalized in FALSY:
        return False
    return default



def is_answerable(question: Dict[str, Any]) -> bool:
    payload = question.get("payload", {})
    return question.get("kind") != "comment" and payload.get("type") != "comment"



def required_value(question: Dict[str, Any]) -> bool:
    return bool_flag(question.get("required"), default=True)



def prepare_payload(question: Dict[str, Any], *, strict_required: bool = True) -> Dict[str, Any]:
    payload = dict(question["payload"])
    if not is_answerable(question):
        return payload

    required = required_value(question)
    payload["required"] = required

    if strict_required and required:
        validation = payload.get("validation")
        if not isinstance(validation, dict):
            validation = {}
        validation["required"] = True
        payload["validation"] = validation

    return payload



def add_question(
    client: YandexFormsClient,
    survey_id: str,
    question: Dict[str, Any],
) -> Tuple[int, Dict[str, Any]]:
    payload = prepare_payload(question, strict_required=True)
    try:
        return client.add_question(survey_id, payload), payload
    except YandexFormsError as error:
        if is_answerable(question) and required_value(question) and "validation" in payload:
            raise CliError(
                "Yandex Forms API rejected strict required validation for "
                f"{question.get('code')}. Form was not published because "
                "required=yes must block moving to the next page."
            ) from error
        raise



def create_from_bundle(bundle_path: Path, *, publish: bool, output: Path) -> int:
    bundle = load_json(
        bundle_path,
        description="compiled form bundle",
        missing_hint="Run first: python scripts/compile_form_json.py --out output/compiled_form_bundle.json",
    )
    if bundle.get("schema_version") != "vkr-yandex-forms-bundle-v1":
        raise CliError(
            "Input file is not a compiled bundle.\n"
            "Run: python scripts/compile_form_json.py --out output/compiled_form_bundle.json"
        )

    api = bundle.get("api") or {}
    survey_payload = api.get("survey") or {}
    questions: List[Dict[str, Any]] = api.get("questions") or []
    if not questions:
        raise CliError("Compiled bundle has no api.questions")

    client = YandexFormsClient()
    survey_id = client.create_survey(survey_payload)
    print(f"Created survey {survey_id}")

    created = []
    for question in questions:
        yandex_question_id, payload = add_question(client, survey_id, question)
        print(f"Added {question.get('code')} -> {yandex_question_id}")
        created.append({
            "code": question.get("code"),
            "question_id": yandex_question_id,
            "page": int(question.get("page") or 1),
            "kind": question.get("kind"),
            "method_id": question.get("method_id"),
            "payload": payload,
            "required": bool(payload.get("required", False)),
            "strict_required": bool((payload.get("validation") or {}).get("required", False)) if isinstance(payload.get("validation"), dict) else False,
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
    try:
        return create_from_bundle(args.bundle, publish=args.publish, output=args.output)
    except CliError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    except YandexFormsError as error:
        print(f"ERROR: Yandex Forms API request failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
