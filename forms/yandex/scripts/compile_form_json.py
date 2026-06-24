from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


class CliError(Exception):
    """User-facing command line error without a Python traceback."""


PLACEHOLDER_PATTERNS = (
    "TODO",
    "PLACEHOLDER",
    "ВСТАВИТЬ ТОЧН",
    "ДОБАВИТЬ ТЕКСТ",
    "...",
)


def read_json(path: Path, name: str) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as error:
        raise CliError(f"Cannot read {name}: {path}\n{error}") from error


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def front_matter(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise CliError(f"Method source not found: {path}")
    match = re.match(r"---\s*\n(.*?)\n---", path.read_text(encoding="utf-8-sig"), flags=re.S)
    if not match:
        return {}
    try:
        import yaml  # type: ignore

        return yaml.safe_load(match.group(1)) or {}
    except Exception:
        data: dict[str, Any] = {}
        for line in match.group(1).splitlines():
            if not line.startswith(" ") and ":" in line:
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip().strip('"')
        return data


def has_placeholder(text: str | None) -> bool:
    value = str(text or "").strip()
    if not value:
        return False
    upper = value.upper()
    return any(pattern in upper for pattern in PLACEHOLDER_PATTERNS)


def clean_required(value: Any, default: str = "yes") -> str:
    if value in (None, ""):
        return default
    return str(value)


def expand_items(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    if len(rows) == 1 and rows[0].get("item_range"):
        match = re.fullmatch(r"(\d+)\s*-\s*(\d+)", rows[0]["item_range"])
        if not match:
            return []
        start, end = map(int, match.groups())
        prefix = rows[0].get("variable_prefix", "q")
        return [
            {
                "item_number": str(n),
                "item_code": f"q{n:03d}",
                "variable": f"{prefix}{n:03d}",
                "text": "",
                "text_a": "",
                "text_b": "",
                "scale_code": "total",
                "scoring_direction": "direct",
                "required": "yes",
            }
            for n in range(start, end + 1)
        ]

    result = []
    for row in rows:
        result.append(
            {
                "item_number": row.get("item_number") or row.get("number") or row.get("№") or "",
                "item_code": row.get("item_code") or row.get("code") or row.get("Код вопроса") or "",
                "variable": row.get("variable") or row.get("code") or row.get("Код вопроса") or "",
                "text": row.get("text") or row.get("Текст вопроса / утверждения") or row.get("Текст утверждения") or "",
                "text_a": row.get("text_a") or "",
                "text_b": row.get("text_b") or "",
                "scale_code": row.get("scale_code") or row.get("scale") or row.get("Шкала") or "total",
                "keyed_value": row.get("keyed_value") or "",
                "scoring_direction": row.get("scoring_direction") or row.get("key") or row.get("Тип ключа") or "direct",
                "required": clean_required(row.get("required") or row.get("Обязательный")),
            }
        )
    return result


def response_options(meta: dict[str, Any]) -> list[dict[str, Any]]:
    if meta.get("response_options"):
        return list(meta["response_options"])
    if meta.get("response_format") == "likert_1_5":
        labels = [
            "полностью не согласна",
            "скорее не согласна",
            "затрудняюсь ответить",
            "скорее согласна",
            "полностью согласна",
        ]
        return [{"value": i + 1, "label": label, "score_direct": i + 1} for i, label in enumerate(labels)]
    if meta.get("response_format") == "forced_choice_ab":
        return [{"value": "A", "label": "A"}, {"value": "B", "label": "B"}]
    labels = ["абсолютно неверно", "скорее всего не верно", "скорее всего верно", "совершенно верно"]
    return [{"value": i + 1, "label": label, "score_direct": i + 1} for i, label in enumerate(labels)]


def load_method(root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    meta = front_matter(root / entry["source"])
    meta.setdefault("id", entry.get("id"))
    meta["include_in_form"] = bool(entry.get("include_in_form", True))
    meta["answerable_items_per_page"] = int(entry.get("answerable_items_per_page") or 0)
    meta["response_options"] = response_options(meta)
    meta["items"] = expand_items(csv_rows(root / str(meta.get("items_file", ""))))
    meta["keys"] = csv_rows(root / str(meta.get("key_file", ""))) if meta.get("key_file") else []
    return meta


def page_text(section: dict[str, Any]) -> str:
    parts = [str(section.get("title") or "").strip()]
    parts += [str(x).strip() for x in section.get("body", []) if str(x).strip()]
    return "\n\n".join(x for x in parts if x)


def comment(code: str, text: str, page: int, header: bool = True, kind: str = "comment") -> dict[str, Any]:
    if not text.strip():
        raise CliError(f"{code}: empty comment text")
    if has_placeholder(text):
        raise CliError(f"{code}: placeholder text is not allowed in the compiled form")
    return {"code": code, "page": page, "kind": kind, "payload": {"type": "comment", "label": text, "header": header}}


def field_question(field: dict[str, Any], page: int) -> dict[str, Any]:
    payload = {"type": field.get("type", "string"), "label": field.get("label", field.get("code", ""))}
    if has_placeholder(payload["label"]):
        raise CliError(f"{field.get('code')}: placeholder text is not allowed")
    for key in ("placeholder", "widget", "items", "multiline", "rows", "columns", "data_source"):
        if key in field:
            payload[key] = field[key]
    return {"code": field.get("code"), "page": page, "kind": "question", "required": bool(field.get("required", True)), "payload": payload}


def is_forced_choice(method: dict[str, Any]) -> bool:
    values = {str(option.get("value", "")).strip().lower() for option in method.get("response_options") or []}
    return {"a", "b"}.issubset(values)


def method_question(method: dict[str, Any], row: dict[str, str], page: int) -> dict[str, Any]:
    method_id = str(method["id"])
    item_number = str(row.get("item_number") or "").strip()
    code = row.get("variable") or f"{method_id}_{row.get('item_code', '')}"
    forced_choice = is_forced_choice(method)

    options = []
    for option in method["response_options"]:
        value = option.get("value")
        label = str(option.get("label", option.get("value")))
        if value == "A":
            if not row.get("text_a"):
                raise CliError(f"{method_id}:{code}: missing text_a for forced-choice option A")
            label = f"A. {row['text_a']}"
        if value == "B":
            if not row.get("text_b"):
                raise CliError(f"{method_id}:{code}: missing text_b for forced-choice option B")
            label = f"B. {row['text_b']}"
        if has_placeholder(label):
            raise CliError(f"{method_id}:{code}: placeholder option text is not allowed")
        options.append({"label": label})

    text = str(row.get("text") or "").strip()
    if not text and forced_choice:
        text = f"Пункт {item_number}" if item_number else str(code)
    if not text:
        raise CliError(f"{method_id}:{code}: missing item text")
    if has_placeholder(text):
        raise CliError(f"{method_id}:{code}: placeholder item text is not allowed")

    return {
        "code": code,
        "page": page,
        "kind": "question",
        "required": str(row.get("required", "yes")).lower() not in {"no", "false", "0"},
        "method_id": method_id,
        "payload": {"type": "enum", "label": text, "widget": "radio", "items": options},
        "scoring": {
            "scale_code": row.get("scale_code") or "total",
            "direction": row.get("scoring_direction") or "direct",
            "keyed_value": row.get("keyed_value") or None,
        },
    }


def build_questions(definition: dict[str, Any], methods: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    questions, warnings, page = [], [], 1

    if page_text(definition.get("intro", {})):
        questions.append(comment("intro_header", page_text(definition.get("intro", {})), page))

    for field in definition.get("screening", []):
        questions.append(field_question(field, page))

    info = definition.get("participant_information") or definition.get("information")
    if info:
        page += 1
        questions.append(comment("participant_information_header", page_text(info), page))

    page += 1
    questions.append(comment("demographics_header", "Социально-демографические данные", page))
    questions += [field_question(field, page) for field in definition.get("demographics", [])]

    for method in methods:
        if not method.get("include_in_form"):
            continue
        items = method.get("items") or []
        if not items:
            warnings.append(f"{method.get('id')}: не найдены пункты")
            continue

        page += 1
        title = method.get("short_title") or method.get("title") or method.get("id")
        questions.append(comment(f"{method['id']}_header", f"{title}\n\nВыберите один вариант ответа для каждого пункта.", page))
        split, count, part = int(method.get("answerable_items_per_page") or 0), 0, 1

        for row in items:
            if split and count >= split:
                page, count, part = page + 1, 0, part + 1
                questions.append(comment(f"{method['id']}_part_{part:02d}_header", f"{title}. Продолжение, часть {part}.", page))
            questions.append(method_question(method, row, page))
            count += 1

    page += 1
    if page_text(definition.get("closing", {})):
        questions.append(comment("closing_header", page_text(definition.get("closing", {})), page))

    return questions, warnings


def archive_root(zip_path: Path):
    tmp = tempfile.TemporaryDirectory()
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(tmp.name)
    root = Path(tmp.name)
    children = [x for x in root.iterdir() if x.is_dir()]
    if (root / "methods").is_dir():
        return tmp, root / "methods"
    if len(children) == 1 and (children[0] / "methods").is_dir():
        return tmp, children[0] / "methods"
    return tmp, children[0] if len(children) == 1 else root


def compile_bundle(definition_path: Path, manifest_path: Path, out_path: Path, methods_root: Path):
    definition = read_json(definition_path, "form definition")
    manifest = read_json(manifest_path, "methods manifest")
    methods = [load_method(methods_root, x) for x in manifest.get("methods", [])]
    questions, warnings = build_questions(definition, methods)
    bundle = {
        "schema_version": "vkr-yandex-forms-bundle-v1",
        "compiled_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": {"form_definition": str(definition_path), "methods_manifest": str(manifest_path), "methods_root": str(methods_root)},
        "form_definition": definition,
        "methods": methods,
        "api": {"survey": definition.get("survey_payload", {"name": definition.get("name", "VKR form")}), "questions": questions},
        "warnings": warnings,
    }
    write_json(out_path, bundle)
    return bundle


def main() -> int:
    base = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Compile form definition and method archive into one JSON bundle")
    parser.add_argument("--definition", type=Path, default=base / "form_definition" / "vkr_main_form.json")
    parser.add_argument("--manifest", type=Path, default=base / "methods_manifest.json")
    parser.add_argument("--out", type=Path, default=base / "output" / "compiled_form_bundle.json")
    parser.add_argument("--archive", type=Path, default=None)
    args = parser.parse_args()
    tmp = None
    try:
        if args.archive:
            tmp, methods_root = archive_root(args.archive)
        else:
            manifest = read_json(args.manifest, "methods manifest")
            methods_root = (args.manifest.parent / manifest.get("methods_root", "../../methods")).resolve()
        bundle = compile_bundle(args.definition, args.manifest, args.out, methods_root)
        print(f"Compiled {len(bundle['api']['questions'])} form elements into {args.out}")
        for warning in bundle.get("warnings", []):
            print(f"WARNING: {warning}")
        return 0
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    finally:
        if tmp:
            tmp.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
