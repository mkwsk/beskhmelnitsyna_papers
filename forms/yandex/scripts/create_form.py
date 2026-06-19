from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from yf_client import YandexFormsClient, YandexFormsError

TRUTHY = {"1", "true", "yes", "y", "да"}
FALSY = {"0", "false", "no", "n", "нет"}

REQUIRED_MARKER_KEYS = {
    "required",
    "is_required",
    "isRequired",
    "answer_required",
    "answerRequired",
    "mandatory",
    "is_mandatory",
    "isMandatory",
}


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


def response_json(response: Any) -> Any:
    if not response.content:
        return {}
    try:
        return response.json()
    except ValueError:
        return {"raw": response.text}


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


def with_required_flags(payload: Dict[str, Any], required: bool, *, strict_required: bool = True) -> Dict[str, Any]:
    result = dict(payload)
    result["required"] = required

    if strict_required and required:
        validation = result.get("validation")
        if not isinstance(validation, dict):
            validation = {}
        validation["required"] = True
        result["validation"] = validation
    elif "validation" in result and isinstance(result["validation"], dict):
        validation = dict(result["validation"])
        validation.pop("required", None)
        if validation:
            result["validation"] = validation
        else:
            result.pop("validation", None)

    return result


def prepare_payload(question: Dict[str, Any], *, strict_required: bool = True) -> Dict[str, Any]:
    payload = dict(question["payload"])
    if not is_answerable(question):
        return payload
    return with_required_flags(payload, required_value(question), strict_required=strict_required)


def required_patch_payloads(required: bool) -> List[Tuple[str, Dict[str, Any]]]:
    """Return minimal payload variants for the required flag.

    Some API calls may accept extra fields without a hard error but ignore them in the
    real form. Minimal PATCH bodies make it easier to test which flag name actually
    changes the question settings.
    """

    validation = {"required": required}
    return [
        ("required", {"required": required}),
        ("required_with_validation", {"required": required, "validation": validation}),
        ("is_required", {"is_required": required}),
        ("isRequired", {"isRequired": required}),
        ("answer_required", {"answer_required": required}),
        ("answerRequired", {"answerRequired": required}),
        ("mandatory", {"mandatory": required}),
        ("settings.required", {"settings": {"required": required}}),
        ("params.required", {"params": {"required": required}}),
        ("payload.required", {"payload": {"required": required}}),
    ]


def contains_truthy_required_marker(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in REQUIRED_MARKER_KEYS and item is True:
                return True
            if contains_truthy_required_marker(item):
                return True
    elif isinstance(value, list):
        return any(contains_truthy_required_marker(item) for item in value)
    return False


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


def patch_question(client: YandexFormsClient, survey_id: str, question_id: int, payload: Dict[str, Any]) -> Any:
    response = client._request(
        "PATCH",
        f"/surveys/{survey_id}/questions/{question_id}/",
        json=payload,
        expected=(200, 204),
    )
    return response_json(response)


def fetch_question(client: YandexFormsClient, survey_id: str, question_id: int) -> Any:
    response = client._request(
        "GET",
        f"/surveys/{survey_id}/questions/{question_id}/",
        expected=(200,),
    )
    return response_json(response)


def repair_required_after_moves(
    client: YandexFormsClient,
    survey_id: str,
    created: List[Dict[str, Any]],
    *,
    debug_dir: Path | None = None,
) -> None:
    """Re-apply required flags after all questions have reached their final pages."""

    for item in created:
        if not is_answerable(item):
            continue
        if not item.get("required"):
            continue

        accepted_modes: List[str] = []
        rejected_modes: Dict[str, str] = {}
        returned_required_modes: List[str] = []
        responses: Dict[str, Any] = {}

        for mode, payload in required_patch_payloads(True):
            try:
                response = patch_question(client, survey_id, item["question_id"], payload)
            except YandexFormsError as error:
                rejected_modes[mode] = str(error)
                continue

            accepted_modes.append(mode)
            responses[mode] = response
            if contains_truthy_required_marker(response):
                returned_required_modes.append(mode)

        if not accepted_modes:
            raise CliError(
                "Could not re-apply required=yes after moving question "
                f"{item.get('code')} to page {item.get('page')}. "
                "Every known required flag PATCH variant was rejected by the API."
            )

        try:
            fetched_question = fetch_question(client, survey_id, item["question_id"])
        except YandexFormsError as error:
            fetched_question = {"error": str(error)}

        if debug_dir:
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_path = debug_dir / f"{item['question_id']}_{item['code']}.json"
            debug_path.write_text(
                json.dumps(
                    {
                        "code": item.get("code"),
                        "question_id": item.get("question_id"),
                        "accepted_modes": accepted_modes,
                        "rejected_modes": rejected_modes,
                        "returned_required_modes": returned_required_modes,
                        "responses": responses,
                        "fetched_question": fetched_question,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

        item["required_patch_modes"] = accepted_modes
        item["required_patch_rejections"] = rejected_modes
        item["required_returned_modes"] = returned_required_modes
        item["required_repaired_after_move"] = True
        item["strict_required"] = bool(returned_required_modes) or contains_truthy_required_marker(fetched_question)
        print(
            f"Re-applied required flag for {item['code']} "
            f"(accepted modes: {', '.join(accepted_modes)})"
        )


def create_from_bundle(
    bundle_path: Path,
    *,
    publish: bool,
    output: Path,
    required_debug_dir: Path | None = None,
) -> int:
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
            "required_repaired_after_move": False,
            "strict_required": bool((payload.get("validation") or {}).get("required", False)) if isinstance(payload.get("validation"), dict) else False,
            "required_patch_modes": [],
            "required_patch_rejections": {},
            "required_returned_modes": [],
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

    repair_required_after_moves(client, survey_id, created, debug_dir=required_debug_dir)

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
    if required_debug_dir:
        print(f"Required flag API debug saved to {required_debug_dir}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Yandex Form from compiled bundle")
    parser.add_argument("bundle", type=Path, help="Path to output/compiled_form_bundle.json")
    parser.add_argument("--publish", action="store_true", help="Publish form after creation")
    parser.add_argument("--output", type=Path, default=Path("exports/form_mapping.json"), help="Where to save local-to-Yandex mapping")
    parser.add_argument(
        "--required-debug-dir",
        type=Path,
        default=None,
        help="Optional directory for raw API responses from required-flag PATCH attempts",
    )
    args = parser.parse_args()
    try:
        return create_from_bundle(
            args.bundle,
            publish=args.publish,
            output=args.output,
            required_debug_dir=args.required_debug_dir,
        )
    except CliError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    except YandexFormsError as error:
        print(f"ERROR: Yandex Forms API request failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
