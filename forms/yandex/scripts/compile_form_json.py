from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
import zipfile
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List

DIVIDER = "──────────────── ✦ ────────────────"


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def parse_inline_dict(text: str) -> Dict[str, Any]:
    text = text.strip().strip("{}").strip()
    if not text:
        return {}
    result: Dict[str, Any] = {}
    parts = []
    current = []
    in_quote = False
    quote = ""
    for ch in text:
        if ch in {'"', "'"}:
            if not in_quote:
                in_quote = True
                quote = ch
            elif quote == ch:
                in_quote = False
        if ch == "," and not in_quote:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current).strip())
    for part in parts:
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        result[key.strip()] = clean_scalar(value)
    return result


def parse_front_matter(text: str) -> Dict[str, Any]:
    match = re.match(r"---\s*\n(.*?)\n---", text, flags=re.S)
    if not match:
        return {}
    block = match.group(1)
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(block)
        return data or {}
    except Exception:
        pass

    data: Dict[str, Any] = {}
    current_key = ""
    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            current_key = key.strip()
            value = value.strip()
            if value:
                data[current_key] = clean_scalar(value)
            else:
                data[current_key] = []
            continue
        stripped = line.strip()
        if current_key and stripped.startswith("- "):
            item = stripped[2:].strip()
            if item.startswith("{") and item.endswith("}"):
                data.setdefault(current_key, []).append(parse_inline_dict(item))
            else:
                data.setdefault(current_key, []).append(clean_scalar(item))
    return data


def load_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def range_items(row: Dict[str, str]) -> List[Dict[str, str]]:
    item_range = row.get("item_range", "")
    prefix = row.get("variable_prefix", "q")
    m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", item_range)
    if not m:
        return []
    start, end = int(m.group(1)), int(m.group(2))
    result = []
    for number in range(start, end + 1):
        result.append({
            "item_number": str(number),
            "item_code": f"q{number:03d}",
            "variable": f"{prefix}{number:03d}",
            "text": "",
            "text_a": "TODO A",
            "text_b": "TODO B",
            "scale_code": "total",
            "scoring_direction": "direct",
            "required": "yes",
        })
    return result


def normalize_items(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if len(rows) == 1 and rows[0].get("item_range"):
        return range_items(rows[0])
    result = []
    for row in rows:
        result.append({
            "item_number": row.get("item_number") or row.get("number") or row.get("№") or "",
            "item_code": row.get("item_code") or row.get("code") or row.get("Код вопроса") or "",
            "variable": row.get("variable") or row.get("code") or row.get("Код вопроса") or "",
            "text": row.get("text") or row.get("Текст вопроса / утверждения") or row.get("Текст утверждения") or "",
            "text_a": row.get("text_a") or "",
            "text_b": row.get("text_b") or "",
            "scale_code": row.get("scale_code") or row.get("scale") or row.get("Шкала") or "total",
            "keyed_value": row.get("keyed_value") or "",
            "scoring_direction": row.get("scoring_direction") or row.get("key") or row.get("Тип ключа") or "direct",
            "required": row.get("required") or row.get("Обязательный") or "yes",
            "source_note": row.get("source_note") or row.get("note") or row.get("Примечание") or "",
        })
    return result


def default_response_options(meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    options = meta.get("response_options") or []
    if options:
        return list(options)
    response_format = str(meta.get("response_format") or "")
    if response_format == "likert_1_5":
        return [
            {"value": 1, "label": "полностью не согласна", "score_direct": 1},
            {"value": 2, "label": "скорее не согласна", "score_direct": 2},
            {"value": 3, "label": "затрудняюсь ответить", "score_direct": 3},
            {"value": 4, "label": "скорее согласна", "score_direct": 4},
            {"value": 5, "label": "полностью согласна", "score_direct": 5},
        ]
    if response_format == "forced_choice_ab":
        return [
            {"value": "A", "label": "A", "score_direct": 1},
            {"value": "B", "label": "B", "score_direct": 0},
        ]
    return [
        {"value": 1, "label": "абсолютно неверно", "score_direct": 1},
        {"value": 2, "label": "скорее всего не верно", "score_direct": 2},
        {"value": 3, "label": "скорее всего верно", "score_direct": 3},
        {"value": 4, "label": "совершенно верно", "score_direct": 4},
    ]


def option_items(options: Iterable[Dict[str, Any]], row: Dict[str, str] | None = None) -> List[Dict[str, str]]:
    row = row or {}
    items = []
    for option in options:
        label = str(option.get("label", option.get("value", "")))
        value = option.get("value", label)
        if value == "A" and row.get("text_a"):
            label = f"A. {row['text_a']}"
        elif value == "B" and row.get("text_b"):
            label = f"B. {row['text_b']}"
        items.append({"label": label})
    return items


def comment(code: str, label: str, page: int) -> Dict[str, Any]:
    return {
        "code": code,
        "page": page,
        "kind": "comment",
        "payload": {"type": "comment", "label": label, "header": True},
    }


def field_to_question(field: Dict[str, Any], page: int) -> Dict[str, Any]:
    payload = {
        "type": field.get("type", "string"),
        "label": field.get("label", field.get("code", "")),
    }
    for key in ("placeholder", "widget", "items", "multiline"):
        if key in field:
            payload[key] = field[key]
    return {
        "code": field.get("code"),
        "page": page,
        "kind": "question",
        "required": bool(field.get("required", True)),
        "payload": payload,
    }


def method_item_to_question(method: Dict[str, Any], row: Dict[str, str], page: int) -> Dict[str, Any]:
    code = row.get("variable") or f"{method['id']}_{row.get('item_code', '')}"
    text = row.get("text") or f"TODO: добавить текст пункта {row.get('item_number')} методики {method.get('short_title') or method.get('id')}"
    payload = {
        "type": "enum",
        "label": text,
        "widget": "radio",
        "items": option_items(method["response_options"], row),
    }
    return {
        "code": code,
        "page": page,
        "kind": "question",
        "required": str(row.get("required", "yes")).lower() not in {"no", "false", "0"},
        "method_id": method["id"],
        "payload": payload,
        "scoring": {
            "scale_code": row.get("scale_code") or "total",
            "direction": row.get("scoring_direction") or "direct",
            "keyed_value": row.get("keyed_value") or None,
        },
    }


def load_method(methods_root: Path, entry: Dict[str, Any]) -> Dict[str, Any]:
    source = methods_root / entry["source"]
    text = source.read_text(encoding="utf-8-sig")
    meta = parse_front_matter(text)
    meta.setdefault("id", entry.get("id"))
    meta["source_file"] = str(source)
    meta["include_in_form"] = bool(entry.get("include_in_form", True))
    meta["answerable_items_per_page"] = int(entry.get("answerable_items_per_page") or 0)
    meta["response_options"] = default_response_options(meta)
    items_file = meta.get("items_file")
    key_file = meta.get("key_file")
    meta["items"] = normalize_items(load_csv(methods_root / str(items_file))) if items_file else []
    meta["keys"] = load_csv(methods_root / str(key_file)) if key_file else []
    return meta


def build_questions(definition: Dict[str, Any], methods: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[str]]:
    questions: List[Dict[str, Any]] = []
    warnings: List[str] = []
    page = 1
    intro = definition.get("intro", {})
    intro_text = intro.get("title", "") + "\n\n" + "\n\n".join(intro.get("body", []))
    questions.append(comment("intro_header", intro_text.strip(), page))
    for field in definition.get("screening", []):
        questions.append(field_to_question(field, page))

    page += 1
    questions.append(comment("demographics_header", f"{DIVIDER}\n\nСоциально-демографические данные", page))
    for field in definition.get("demographics", []):
        questions.append(field_to_question(field, page))

    for method in methods:
        if not method.get("include_in_form"):
            continue
        items = method.get("items") or []
        if not items:
            warnings.append(f"{method.get('id')}: не найдены пункты методики")
            continue
        page += 1
        title = method.get("short_title") or method.get("title") or method.get("id")
        questions.append(comment(f"{method['id']}_header", f"{DIVIDER}\n\n{title}\n\nВыберите один вариант ответа для каждого пункта.", page))
        split_every = int(method.get("answerable_items_per_page") or 0)
        count_in_page = 0
        part = 1
        for row in items:
            if split_every and count_in_page >= split_every:
                page += 1
                part += 1
                count_in_page = 0
                questions.append(comment(f"{method['id']}_part_{part:02d}_header", f"{DIVIDER}\n\n{title}. Продолжение, часть {part}.", page))
            q = method_item_to_question(method, row, page)
            if "TODO" in q["payload"].get("label", ""):
                warnings.append(f"{method['id']}:{q['code']}: нет полного текста пункта")
            questions.append(q)
            count_in_page += 1

    page += 1
    closing = definition.get("closing", {})
    closing_text = closing.get("title", "") + "\n\n" + "\n\n".join(closing.get("body", []))
    questions.append(comment("closing_header", f"{DIVIDER}\n\n{closing_text.strip()}", page))
    return questions, warnings


def compile_bundle(definition_path: Path, manifest_path: Path, out_path: Path) -> Dict[str, Any]:
    definition = read_json(definition_path)
    manifest = read_json(manifest_path)
    methods_root = (manifest_path.parent / manifest.get("methods_root", "../../methods")).resolve()
    methods = [load_method(methods_root, entry) for entry in manifest.get("methods", [])]
    questions, warnings = build_questions(definition, methods)
    bundle = {
        "schema_version": "vkr-yandex-forms-bundle-v1",
        "compiled_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": {
            "form_definition": str(definition_path),
            "methods_manifest": str(manifest_path),
            "methods_root": str(methods_root),
        },
        "form_definition": definition,
        "methods": methods,
        "api": {
            "survey": definition.get("survey_payload", {"name": definition.get("name", "VKR form")}),
            "questions": questions,
        },
        "warnings": warnings,
    }
    write_json(out_path, bundle)
    return bundle


def extract_archive(path: Path) -> tempfile.TemporaryDirectory[str] | None:
    if not path or not path.exists() or path.is_dir():
        return None
    if path.suffix.lower() != ".zip":
        raise ValueError("Архив должен быть zip-файлом")
    tmp = tempfile.TemporaryDirectory()
    with zipfile.ZipFile(path) as archive:
        archive.extractall(tmp.name)
    return tmp


def main() -> int:
    base = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Compile form_definition + markdown methods into one JSON bundle")
    parser.add_argument("--definition", type=Path, default=base / "form_definition" / "vkr_main_form.json")
    parser.add_argument("--manifest", type=Path, default=base / "methods_manifest.json")
    parser.add_argument("--out", type=Path, default=base / "output" / "compiled_form_bundle.json")
    parser.add_argument("--archive", type=Path, default=None, help="Optional zip with methods; if given, manifest paths are resolved inside extracted archive")
    args = parser.parse_args()

    tmp = extract_archive(args.archive) if args.archive else None
    try:
        bundle = compile_bundle(args.definition, args.manifest, args.out)
    finally:
        if tmp:
            tmp.cleanup()
    print(f"Compiled {len(bundle['api']['questions'])} questions into {args.out}")
    if bundle.get("warnings"):
        print("Warnings:")
        for warning in bundle["warnings"]:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
