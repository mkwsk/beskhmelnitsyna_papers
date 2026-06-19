from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List

DIVIDER = "──────────────── ✦ ────────────────"


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def scalar(value: str) -> Any:
    value = value.strip()
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def inline_dict(text: str) -> Dict[str, Any]:
    text = text.strip().strip("{}").strip()
    if not text:
        return {}
    parts: List[str] = []
    buf: List[str] = []
    quote = ""
    for ch in text:
        if ch in {'"', "'"}:
            quote = "" if quote == ch else ch if not quote else quote
        if ch == "," and not quote:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf).strip())
    result: Dict[str, Any] = {}
    for part in parts:
        if ":" in part:
            key, value = part.split(":", 1)
            result[key.strip()] = scalar(value)
    return result


def front_matter(text: str) -> Dict[str, Any]:
    match = re.match(r"---\s*\n(.*?)\n---", text, flags=re.S)
    if not match:
        return {}
    block = match.group(1)
    try:
        import yaml  # type: ignore
        return yaml.safe_load(block) or {}
    except Exception:
        pass
    data: Dict[str, Any] = {}
    current = ""
    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not raw.startswith(" ") and ":" in raw:
            key, value = raw.split(":", 1)
            current = key.strip()
            data[current] = scalar(value) if value.strip() else []
        elif current and raw.strip().startswith("- "):
            item = raw.strip()[2:].strip()
            data.setdefault(current, []).append(inline_dict(item) if item.startswith("{") else scalar(item))
    return data


def csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def expand_range(row: Dict[str, str]) -> List[Dict[str, str]]:
    m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", row.get("item_range", ""))
    if not m:
        return []
    prefix = row.get("variable_prefix", "q")
    result = []
    for number in range(int(m.group(1)), int(m.group(2)) + 1):
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
        return expand_range(rows[0])
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
        })
    return result


def response_options(meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    if meta.get("response_options"):
        return list(meta["response_options"])
    fmt = str(meta.get("response_format") or "")
    if fmt == "likert_1_5":
        labels = ["полностью не согласна", "скорее не согласна", "затрудняюсь ответить", "скорее согласна", "полностью согласна"]
        return [{"value": i + 1, "label": label, "score_direct": i + 1} for i, label in enumerate(labels)]
    if fmt == "forced_choice_ab":
        return [{"value": "A", "label": "A"}, {"value": "B", "label": "B"}]
    labels = ["абсолютно неверно", "скорее всего не верно", "скорее всего верно", "совершенно верно"]
    return [{"value": i + 1, "label": label, "score_direct": i + 1} for i, label in enumerate(labels)]


def option_items(options: Iterable[Dict[str, Any]], row: Dict[str, str]) -> List[Dict[str, str]]:
    result = []
    for option in options:
        value = option.get("value")
        label = str(option.get("label", value))
        if value == "A" and row.get("text_a"):
            label = f"A. {row['text_a']}"
        if value == "B" and row.get("text_b"):
            label = f"B. {row['text_b']}"
        result.append({"label": label})
    return result


def load_method(root: Path, entry: Dict[str, Any]) -> Dict[str, Any]:
    source = root / entry["source"]
    meta = front_matter(source.read_text(encoding="utf-8-sig"))
    meta.setdefault("id", entry.get("id"))
    meta["source_file"] = str(source)
    meta["include_in_form"] = bool(entry.get("include_in_form", True))
    meta["answerable_items_per_page"] = int(entry.get("answerable_items_per_page") or 0)
    meta["response_options"] = response_options(meta)
    meta["items"] = normalize_items(csv_rows(root / str(meta.get("items_file", ""))))
    meta["keys"] = csv_rows(root / str(meta.get("key_file", ""))) if meta.get("key_file") else []
    return meta


def text_block(code: str, label: str, page: int, *, header: bool = False, kind: str = "comment") -> Dict[str, Any]:
    return {
        "code": code,
        "page": page,
        "kind": kind,
        "payload": {"type": "comment", "label": label, "header": header},
    }


def comment(code: str, label: str, page: int, *, header: bool = True) -> Dict[str, Any]:
    return text_block(code, label, page, header=header)


def separator(code: str, page: int) -> Dict[str, Any]:
    return text_block(code, DIVIDER, page, header=False, kind="separator")


def field_question(field: Dict[str, Any], page: int) -> Dict[str, Any]:
    payload = {"type": field.get("type", "string"), "label": field.get("label", field.get("code", ""))}
    for key in ("placeholder", "widget", "items", "multiline"):
        if key in field:
            payload[key] = field[key]
    return {"code": field.get("code"), "page": page, "kind": "question", "required": bool(field.get("required", True)), "payload": payload}


def method_question(method: Dict[str, Any], row: Dict[str, str], page: int) -> Dict[str, Any]:
    code = row.get("variable") or f"{method['id']}_{row.get('item_code', '')}"
    text = row.get("text") or f"TODO: добавить текст пункта {row.get('item_number')} методики {method.get('short_title') or method.get('id')}"
    return {
        "code": code,
        "page": page,
        "kind": "question",
        "required": str(row.get("required", "yes")).lower() not in {"no", "false", "0"},
        "method_id": method["id"],
        "payload": {"type": "enum", "label": text, "widget": "radio", "items": option_items(method["response_options"], row)},
        "scoring": {"scale_code": row.get("scale_code") or "total", "direction": row.get("scoring_direction") or "direct", "keyed_value": row.get("keyed_value") or None},
    }


def build_questions(definition: Dict[str, Any], methods: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[str]]:
    questions: List[Dict[str, Any]] = []
    warnings: List[str] = []
    page = 1
    intro = definition.get("intro", {})
    questions.append(comment("intro_header", (intro.get("title", "") + "\n\n" + "\n\n".join(intro.get("body", []))).strip(), page))
    for field in definition.get("screening", []):
        questions.append(field_question(field, page))
    page += 1
    questions.append(separator("demographics_separator", page))
    questions.append(comment("demographics_header", "Социально-демографические данные", page))
    for field in definition.get("demographics", []):
        questions.append(field_question(field, page))
    for method in methods:
        if not method.get("include_in_form"):
            continue
        items = method.get("items") or []
        if not items:
            warnings.append(f"{method.get('id')}: не найдены пункты")
            continue
        page += 1
        title = method.get("short_title") or method.get("title") or method.get("id")
        questions.append(separator(f"{method['id']}_separator", page))
        questions.append(comment(f"{method['id']}_header", f"{title}\n\nВыберите один вариант ответа для каждого пункта.", page))
        split = int(method.get("answerable_items_per_page") or 0)
        count = 0
        part = 1
        for row in items:
            if split and count >= split:
                page += 1
                part += 1
                count = 0
                questions.append(separator(f"{method['id']}_part_{part:02d}_separator", page))
                questions.append(comment(f"{method['id']}_part_{part:02d}_header", f"{title}. Продолжение, часть {part}.", page))
            q = method_question(method, row, page)
            if "TODO" in q["payload"].get("label", ""):
                warnings.append(f"{method['id']}:{q['code']}: нет полного текста пункта")
            questions.append(q)
            count += 1
    page += 1
    closing = definition.get("closing", {})
    questions.append(separator("closing_separator", page))
    questions.append(comment("closing_header", (closing.get("title", "") + "\n\n" + "\n\n".join(closing.get("body", []))).strip(), page))
    return questions, warnings


def archive_root(zip_path: Path) -> tuple[tempfile.TemporaryDirectory[str], Path]:
    tmp = tempfile.TemporaryDirectory()
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(tmp.name)
    root = Path(tmp.name)
    if (root / "methods").is_dir():
        return tmp, root / "methods"
    children = [p for p in root.iterdir() if p.is_dir()]
    if len(children) == 1:
        child = children[0]
        if (child / "methods").is_dir():
            return tmp, child / "methods"
        return tmp, child
    return tmp, root


def compile_bundle(definition_path: Path, manifest_path: Path, out_path: Path, methods_root: Path) -> Dict[str, Any]:
    definition = read_json(definition_path)
    manifest = read_json(manifest_path)
    methods = [load_method(methods_root, item) for item in manifest.get("methods", [])]
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
    parser.add_argument("--archive", type=Path, default=None, help="Optional zip archive with method markdown and items/keys directories")
    args = parser.parse_args()
    tmp = None
    if args.archive:
        tmp, methods_root = archive_root(args.archive)
    else:
        manifest = read_json(args.manifest)
        methods_root = (args.manifest.parent / manifest.get("methods_root", "../../methods")).resolve()
    try:
        bundle = compile_bundle(args.definition, args.manifest, args.out, methods_root)
    finally:
        if tmp:
            tmp.cleanup()
    print(f"Compiled {len(bundle['api']['questions'])} questions into {args.out}")
    for warning in bundle.get("warnings", []):
        print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
