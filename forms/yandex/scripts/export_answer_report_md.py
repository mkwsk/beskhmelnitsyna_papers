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


META_FIELDS = {
    "answer_id": "ID ответа",
    "created": "Дата и время отправки",
}


METHOD_INTERPRETATIONS = {
    "gse_schwarzer_jerusalem_ru": "Чем выше балл, тем более выражена общая самоэффективность: субъективная уверенность в способности справляться с трудностями.",
    "rosenberg_self_esteem_scale_ru": "Чем выше балл, тем более выражена глобальная самооценка / самоуважение. Для ВКР показатель лучше использовать как непрерывный балл.",
    "core_self_evaluation_scale_ru": "Чем выше балл, тем более выражено позитивное базовое самооценивание как интегральный личностный ресурс.",
    "samoal_lazukin_kalina": "Чем выше балл, тем сильнее выражен соответствующий аспект самоактуализации. Для ВКР лучше интерпретировать профиль шкал, а не ставить клинические ярлыки.",
    "gavrilova_professional_self_realization": "Чем выше балл, тем сильнее выражен соответствующий компонент профессиональной самореализации.",
}


SCALE_INTERPRETATIONS = {
    ("core_self_evaluation_scale_ru", "positive"): "Высокий балл означает более выраженную позитивную оценку собственных возможностей.",
    ("core_self_evaluation_scale_ru", "neg_rev"): "Шкала обратная: после реверса высокий балл означает меньшую выраженность негативного самооценивания.",
    ("core_self_evaluation_scale_ru", "total"): "Высокий общий балл означает более выраженное позитивное базовое самооценивание.",
    ("gavrilova_professional_self_realization", "goal"): "Высокий балл означает большую выраженность ценностно-целевого компонента: ясность и значимость профессиональных целей.",
    ("gavrilova_professional_self_realization", "resource"): "Высокий балл означает большую выраженность ресурсного компонента: переживание наличия возможностей для профессиональной реализации.",
    ("gavrilova_professional_self_realization", "phenomenological"): "Высокий балл означает большую выраженность феноменологического компонента: субъективное переживание профессиональной реализованности.",
    ("gavrilova_professional_self_realization", "total"): "Высокий общий балл означает более высокий уровень профессиональной самореализации.",
}


class ReportError(CliError):
    """User-facing report generation error."""


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
    header_line = "| " + " | ".join(md_escape(item) for item in headers) + " |"
    sep_line = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(md_escape(value_text(item)) for item in row) + " |" for row in rows]
    return "\n".join([header_line, sep_line] + body)


def answer_identity(answer: Dict[str, Any]) -> str:
    for key in ("id", "answer_id", "answerId", "uid"):
        value = answer.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def find_answer(answers: List[Dict[str, Any]], answer_id: str) -> Dict[str, Any]:
    expected = str(answer_id)
    for answer in answers:
        if answer_identity(answer) == expected:
            return answer
    examples = [answer_identity(answer) for answer in answers[:10] if answer_identity(answer)]
    suffix = f" Examples: {', '.join(examples)}" if examples else ""
    raise ReportError(f"Answer id not found: {answer_id}. Loaded answers: {len(answers)}.{suffix}")


def question_lookup(bundle: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for question in bundle.get("api", {}).get("questions", []):
        if question.get("kind") != "question":
            continue
        code = str(question.get("code") or "")
        if code:
            result[code] = question
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
            label = str(field.get("label") or code)
            fields.append((code, label))

    if not fields:
        fields = [(code, question_label(questions.get(code), code)) for code in row if code.startswith("soc_")]

    return [(label, row.get(code, "")) for code, label in fields]


def method_item_order(bundle: Dict[str, Any]) -> List[str]:
    result: List[str] = []
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
    result: List[Tuple[str, str, Any]] = []
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
        if code in known:
            continue
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


def range_position_comment(value: Any, range_raw: Any) -> str:
    number = numeric(value)
    score_range = parse_range(range_raw)
    if number is None or not score_range:
        return ""
    low, high = score_range
    part = (number - low) / (high - low)
    if part < 0.34:
        zone = "нижней"
    elif part < 0.67:
        zone = "средней"
    else:
        zone = "верхней"
    return f" Значение находится в {zone} части возможного диапазона {value_text(low)}-{value_text(high)}."


def interpretation_for(method: Dict[str, Any], scale: Dict[str, Any], value: Any, percent: Any) -> str:
    method_id = str(method.get("id") or "")
    code = scale_code(scale)
    text = SCALE_INTERPRETATIONS.get((method_id, code))
    if not text:
        title = scale_title(method, scale)
        base = METHOD_INTERPRETATIONS.get(method_id, "Чем выше балл, тем более выражен показатель шкалы.")
        if method_id == "samoal_lazukin_kalina":
            text = f"Чем выше балл, тем сильнее выражена шкала '{title}'."
        else:
            text = base
    if percent not in (None, ""):
        text += f" Нормированный показатель: {value_text(percent)}%."
    text += range_position_comment(value, scale.get("range_raw"))
    return text


def score_sections(bundle: Dict[str, Any], scored: Dict[str, Any]) -> List[str]:
    sections: List[str] = []
    for method in bundle.get("methods") or []:
        method_id = str(method.get("id") or "")
        rows = []
        for scale in scales_for_method(method):
            code = scale_code(scale)
            prefix = f"{method_id}_{code}"
            value = scored.get(prefix)
            raw = scored.get(f"{prefix}_raw")
            percent = scored.get(f"{prefix}_percent")
            answered = scored.get(f"{prefix}_answered_count")
            complete = scored.get(f"{prefix}_complete")
            if value in (None, "") and raw in (None, ""):
                continue
            rows.append(
                [
                    scale_title(method, scale),
                    value_text(value),
                    value_text(raw),
                    value_text(percent),
                    value_text(answered),
                    value_text(complete),
                    interpretation_for(method, scale, value, percent),
                ]
            )
        if rows:
            sections.append(f"### {method_title(method)}\n\n" + table(["Шкала", "Балл", "Сырой балл", "%", "Ответов", "Полнота", "Интерпретация"], rows))
    return sections


def build_markdown(bundle: Dict[str, Any], survey_id: str, answer_id: str, row: Dict[str, Any], scored: Dict[str, Any]) -> str:
    questions = question_lookup(bundle)
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

    parts = [
        f"# Отчет по ответу {md_escape(answer_id)}",
        "",
        table(
            ["Поле", "Значение"],
            [
                ["ID формы", survey_id],
                ["ID ответа", row.get("answer_id") or answer_id],
                ["Дата отправки", row.get("created", "")],
                ["Отчет сформирован", generated_at],
            ],
        ),
        "",
        "## 1. Социологические данные",
        "",
        table(["Поле", "Значение"], demographic_rows(bundle, row, questions)),
        "",
        "## 2. Вычисленные баллы по шкалам",
        "",
    ]

    sections = score_sections(bundle, scored)
    if sections:
        parts.append("\n\n".join(sections))
    else:
        parts.append("Баллы не рассчитаны. Проверьте, что в бандле есть методики, пункты и ключи обработки.")

    parts.extend(
        [
            "",
            "## 3. Сырые данные",
            "",
            table(["Код", "Вопрос / поле", "Ответ"], raw_rows(bundle, row, questions)),
            "",
        ]
    )
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
