from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from export_research_results import (
    CliError,
    answer_row,
    build_code_lookup,
    fetch_all_answers,
    read_json,
    resolve_columns,
    resolve_survey_id,
)
from interpret_results import score_rows
from yf_client import YandexFormsClient, YandexFormsError


META_FIELDS = {"answer_id": "ID ответа", "created": "Дата и время отправки"}

METHOD_INTERPRETATIONS = {
    "gse_schwarzer_jerusalem_ru": "Чем выше балл, тем более выражена общая самоэффективность.",
    "rosenberg_self_esteem_scale_ru": "Чем выше балл, тем более выражена глобальная самооценка / самоуважение.",
    "core_self_evaluation_scale_ru": "Чем выше балл, тем более выражено позитивное базовое самооценивание.",
    "samoal_lazukin_kalina": "Чем выше балл, тем сильнее выражен соответствующий аспект самоактуализации.",
    "gavrilova_professional_self_realization": "Чем выше балл, тем сильнее выражен соответствующий компонент профессиональной самореализации.",
}


class ReportError(CliError):
    pass


def safe_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value).strip())
    return value.strip("._") or "answer"


def md_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "<br>".join(part.strip() for part in text.split("\n"))
    return text.replace("|", "\\|")


def value_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "да" if value else "нет"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def table(headers: List[str], rows: Iterable[Iterable[Any]]) -> str:
    head = "| " + " | ".join(md_escape(item) for item in headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(md_escape(value_text(item)) for item in row) + " |" for row in rows]
    return "\n".join([head, sep] + body)


def answer_identity(answer: Dict[str, Any]) -> str:
    for key in ("id", "answer_id", "answerId", "uid"):
        if answer.get(key) not in (None, ""):
            return str(answer[key])
    return ""


def find_answer(answers: List[Dict[str, Any]], answer_id: str) -> Dict[str, Any]:
    for answer in answers:
        if answer_identity(answer) == str(answer_id):
            return answer
    examples = [answer_identity(answer) for answer in answers[:10] if answer_identity(answer)]
    suffix = f" Examples: {', '.join(examples)}" if examples else ""
    raise ReportError(f"Answer id not found: {answer_id}. Loaded answers: {len(answers)}.{suffix}")


def question_lookup(bundle: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    result = {}
    for question in bundle.get("api", {}).get("questions", []):
        if question.get("kind") == "question" and question.get("code"):
            result[str(question["code"])] = question
    return result


def question_label(question: Dict[str, Any] | None, fallback: str) -> str:
    if not question:
        return META_FIELDS.get(fallback, fallback)
    return str((question.get("payload") or {}).get("label") or fallback)


def demographic_rows(bundle: Dict[str, Any], row: Dict[str, Any], questions: Dict[str, Dict[str, Any]]) -> List[Tuple[str, Any]]:
    fields = []
    for field in bundle.get("form_definition", {}).get("demographics", []):
        code = str(field.get("code") or "")
        if code:
            fields.append((code, str(field.get("label") or code)))
    if not fields:
        fields = [(code, question_label(questions.get(code), code)) for code in row if code.startswith("soc_")]
    return [(label, row.get(code, "")) for code, label in fields]


def method_item_order(bundle: Dict[str, Any]) -> List[str]:
    result = []
    for method in bundle.get("methods") or []:
        for item in method.get("items") or []:
            code = item.get("variable") or item.get("code")
            if code:
                result.append(str(code))
    return result


def raw_rows(bundle: Dict[str, Any], row: Dict[str, Any], questions: Dict[str, Dict[str, Any]]) -> List[Tuple[str, str, Any]]:
    ordered = ["answer_id", "created"]
    ordered.extend(str(field.get("code")) for field in bundle.get("form_definition", {}).get("demographics", []) if field.get("code"))
    ordered.extend(method_item_order(bundle))
    seen = set()
    result = []
    for code in ordered + sorted(str(key) for key in row.keys()):
        if code in seen or code not in row:
            continue
        seen.add(code)
        result.append((code, question_label(questions.get(code), code), row.get(code, "")))
    return result


def method_title(method: Dict[str, Any]) -> str:
    return str(method.get("short_title") or method.get("title") or method.get("id") or "Методика")


def scale_title(method: Dict[str, Any], scale: Dict[str, Any]) -> str:
    return str(scale.get("title") or scale.get("scale_title") or scale.get("code") or scale.get("scale_code") or "Шкала")


def scale_code(scale: Dict[str, Any]) -> str:
    return str(scale.get("code") or scale.get("scale_code") or "total")


def scales_for_method(method: Dict[str, Any]) -> List[Dict[str, Any]]:
    scales = [dict(scale) for scale in (method.get("scale_codes") or [])]
    known = {scale_code(scale) for scale in scales}
    for key in method.get("keys") or []:
        code = str(key.get("scale_code") or "total")
        if code not in known:
            known.add(code)
            scales.append({"code": code, "title": key.get("scale_title") or code})
    return scales


def numeric(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


def parse_range(text: Any) -> Tuple[float, float] | None:
    match = re.search(r"(-?\d+(?:[.,]\d+)?)\s*-\s*(-?\d+(?:[.,]\d+)?)", str(text or ""))
    if not match:
        return None
    low = float(match.group(1).replace(",", "."))
    high = float(match.group(2).replace(",", "."))
    return (low, high) if high > low else None


def value_range(value: Any, bounds: Tuple[float, float] | None) -> str:
    text = value_text(value)
    if not text or not bounds:
        return text
    low, high = bounds
    return f"{text} ({value_text(low)}-{value_text(high)})"


def is_present(value: Any) -> bool:
    return value not in (None, "")


def is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "да"}


def key_for_scale(method: Dict[str, Any], code: str) -> Dict[str, Any]:
    for key in method.get("keys") or []:
        if str(key.get("scale_code") or "total") == code:
            return key
    return {}


def number_list(text: Any) -> List[int]:
    result = []
    for item in re.split(r"[\s,;]+", str(text or "").strip()):
        match = re.match(r"^(\d+)", item)
        if match:
            result.append(int(match.group(1)))
    return result


def response_score_range(method: Dict[str, Any]) -> Tuple[float, float] | None:
    values = []
    for option in method.get("response_options") or []:
        for field in ("score_direct", "value"):
            number = numeric(option.get(field))
            if number is not None:
                values.append(number)
                break
    return (min(values), max(values)) if values else None


def normalize_multiplier(method: Dict[str, Any], scale: Dict[str, Any]) -> float:
    key = key_for_scale(method, scale_code(scale))
    for value in (scale.get("normalize_multiplier"), key.get("normalize_multiplier")):
        number = numeric(value)
        if number is not None:
            return number
    return 1.0


def expected_item_count(method: Dict[str, Any], scale: Dict[str, Any]) -> int | None:
    key = key_for_scale(method, scale_code(scale))
    for value in (scale.get("item_count"), key.get("item_count")):
        number = numeric(value)
        if number is not None:
            return int(number)
    keyed = number_list(key.get("keyed_items"))
    if keyed:
        return len(keyed)
    direct = number_list(key.get("direct_items"))
    reverse = number_list(key.get("reverse_items"))
    if direct or reverse:
        return len(direct) + len(reverse)
    return None


def raw_score_range(method: Dict[str, Any], scale: Dict[str, Any]) -> Tuple[float, float] | None:
    key = key_for_scale(method, scale_code(scale))
    explicit = parse_range(scale.get("range_raw")) or parse_range(key.get("range_raw") or key.get("score_range") or key.get("range"))
    if explicit:
        return explicit
    count = expected_item_count(method, scale)
    if count is None:
        return None
    if number_list(key.get("keyed_items")):
        return 0.0, float(count)
    per_item = response_score_range(method)
    if per_item:
        return per_item[0] * count, per_item[1] * count
    return 0.0, float(count)


def normalized_score_range(method: Dict[str, Any], scale: Dict[str, Any]) -> Tuple[float, float] | None:
    raw = raw_score_range(method, scale)
    if not raw:
        return None
    multiplier = normalize_multiplier(method, scale)
    return raw[0] * multiplier, raw[1] * multiplier


def scale_uses_normalization(method: Dict[str, Any], scale: Dict[str, Any], raw: Any, value: Any, percent: Any) -> bool:
    if abs(normalize_multiplier(method, scale) - 1.0) > 1e-9:
        return True
    if is_present(percent):
        return True
    raw_number = numeric(raw)
    value_number = numeric(value)
    return raw_number is not None and value_number is not None and abs(raw_number - value_number) > 1e-9


def percent_of_maximum(method: Dict[str, Any], scale: Dict[str, Any], value: Any, existing_percent: Any) -> Any:
    if is_present(existing_percent):
        return existing_percent
    score = numeric(value)
    score_range = normalized_score_range(method, scale)
    if score is None or not score_range or score_range[1] == 0:
        return ""
    return round(score / score_range[1] * 100, 2)


def interpretation_for(method: Dict[str, Any], scale: Dict[str, Any]) -> str:
    method_id = str(method.get("id") or "")
    base = METHOD_INTERPRETATIONS.get(method_id, "Чем выше балл, тем более выражен показатель шкалы.")
    if method_id == "samoal_lazukin_kalina":
        return f"Чем выше балл, тем сильнее выражена шкала '{scale_title(method, scale)}'."
    return base


def normalization_memo() -> str:
    return (
        "> Памятка: сырой балл - это результат прямого подсчета по ключу. "
        "Приведенный балл получается после умножения сырого балла на коэффициент нормировки. "
        "Диапазон в скобках после балла показывает минимум и максимум по соответствующей шкале. "
        "`% от максимума` показывает долю приведенного балла от максимального сопоставимого значения шкалы."
    )


def score_sections(bundle: Dict[str, Any], scored: Dict[str, Any]) -> List[str]:
    sections = []
    for method in bundle.get("methods") or []:
        method_id = str(method.get("id") or "")
        rows_data = []
        for scale in scales_for_method(method):
            code = scale_code(scale)
            prefix = f"{method_id}_{code}"
            value = scored.get(prefix)
            raw = scored.get(f"{prefix}_raw")
            percent = scored.get(f"{prefix}_percent")
            if value in (None, "") and raw in (None, ""):
                continue
            rows_data.append({
                "scale": scale,
                "title": scale_title(method, scale),
                "value": value,
                "raw": raw,
                "percent": percent,
                "answered": scored.get(f"{prefix}_answered_count"),
                "complete": scored.get(f"{prefix}_complete"),
            })
        if not rows_data:
            continue

        uses_norm = any(scale_uses_normalization(method, item["scale"], item["raw"], item["value"], item["percent"]) for item in rows_data)
        all_complete = all(is_truthy(item["complete"]) for item in rows_data)
        headers = ["Шкала"]
        headers += ["Сырой балл (значение; мин-макс)", "Приведенный балл (значение; мин-макс)", "% от максимума"] if uses_norm else ["Балл (значение; мин-макс)"]
        if not all_complete:
            headers += ["Ответов", "Полнота"]
        headers += ["Интерпретация"]

        rows = []
        for item in rows_data:
            scale = item["scale"]
            row = [item["title"]]
            if uses_norm:
                row += [
                    value_range(item["raw"], raw_score_range(method, scale)),
                    value_range(item["value"], normalized_score_range(method, scale)),
                    value_text(percent_of_maximum(method, scale, item["value"], item["percent"])),
                ]
            else:
                row += [value_range(item["value"], normalized_score_range(method, scale))]
            if not all_complete:
                row += [value_text(item["answered"]), value_text(item["complete"])]
            row += [interpretation_for(method, scale)]
            rows.append(row)

        parts = [f"### {method_title(method)}"]
        if all_complete:
            parts.append("*Все шкалы методики заполнены полностью.*")
        if uses_norm:
            parts.append("*В таблице используется приведенный балл: шкалы с разным числом пунктов пересчитаны к общей сопоставимой базе.*")
        parts.append(table(headers, rows))
        if uses_norm:
            parts.append(normalization_memo())
        sections.append("\n\n".join(parts))
    return sections


def build_markdown(bundle: Dict[str, Any], survey_id: str, answer_id: str, row: Dict[str, Any], scored: Dict[str, Any]) -> str:
    questions = question_lookup(bundle)
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    parts = [
        f"# Отчет по ответу {md_escape(answer_id)}",
        "",
        table(["Поле", "Значение"], [["ID формы", survey_id], ["ID ответа", row.get("answer_id") or answer_id], ["Дата отправки", row.get("created", "")], ["Отчет сформирован", generated_at]]),
        "",
        "## 1. Социологические данные",
        "",
        table(["Поле", "Значение"], demographic_rows(bundle, row, questions)),
        "",
        "## 2. Вычисленные баллы по шкалам",
        "",
    ]
    sections = score_sections(bundle, scored)
    parts.append("\n\n".join(sections) if sections else "Баллы не рассчитаны. Проверьте, что в бандле есть методики, пункты и ключи обработки.")
    parts.extend(["", "## 3. Сырые данные", "", table(["Код", "Вопрос / поле", "Ответ"], raw_rows(bundle, row, questions)), ""])
    return "\n".join(parts)


def default_out_path(answer_id: str) -> Path:
    return Path("exports/research_results/answer_reports") / f"answer_{safe_filename(answer_id)}.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="Export one Yandex Forms answer by id and build a Markdown report")
    parser.add_argument("--answer-id", required=True, help="Yandex Forms answer id")
    parser.add_argument("--survey-id", default=None, help="Yandex Forms survey id. If omitted, read from --mapping")
    parser.add_argument("--bundle", type=Path, default=Path("output/compiled_form_bundle.json"), help="Compiled form bundle")
    parser.add_argument("--mapping", type=Path, default=Path("exports/form_mapping.json"), help="Mapping saved by create_form.py")
    parser.add_argument("--out", type=Path, default=None, help="Output Markdown file. Default: exports/research_results/answer_reports/answer_<id>.md")
    parser.add_argument("--page-size", type=int, default=100)
    args = parser.parse_args()
    try:
        bundle = read_json(args.bundle)
        mapping = read_json(args.mapping, required=False)
        survey_id = resolve_survey_id(args, mapping)
        client = YandexFormsClient()
        export_data = fetch_all_answers(client, survey_id, page_size=args.page_size)
        answer = find_answer(export_data.get("answers") or [], args.answer_id)
        columns = export_data.get("columns") or []
        by_id, by_label = build_code_lookup(bundle, mapping)
        field_codes = resolve_columns(columns, by_id, by_label)
        row = answer_row(answer, field_codes)
        scored = score_rows(bundle, [row], long_names=True)[0]
        out_path = args.out or default_out_path(args.answer_id)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(build_markdown(bundle, survey_id, args.answer_id, row, scored), encoding="utf-8")
        print(f"Markdown report saved to {out_path}")
        return 0
    except (CliError, YandexFormsError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
