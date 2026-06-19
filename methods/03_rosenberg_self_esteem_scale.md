---
schema_version: "2.0"
id: rosenberg_self_esteem_scale_ru
title: "Шкала самооценки Розенберга"
short_title: "RSES"
aliases:
  - "Rosenberg Self-Esteem Scale"
  - "Шкала самоуважения Розенберга"
construct: "Глобальная самооценка / самоуважение"
domain: "самооценка"
status_in_research: "included"
priority: "primary"
recommended_use: "основная методика актуальной батареи"
language: "ru"
version: "русскоязычная версия; конкретный источник формулировок уточнить"
authors_original:
  - "Morris Rosenberg"
authors_adaptation:
  - "уточнить по выбранному источнику"
year_original: 1965
year_adaptation: 0
item_count: 10
scale_count: 1
response_format: "likert_1_4"
estimated_time_min: "2-4"
license_status: "unclear"
full_items_stored: false
items_text_policy: "not_stored_public_repo"
items_file: "items/rosenberg_self_esteem_scale_ru_items.csv"
key_file: ""
scoring_status: "complete"
form_variable_prefix: "rses"
response_options:
  - {value: 1, label: "полностью не согласна", score_direct: 1, score_reverse: 4}
  - {value: 2, label: "не согласна", score_direct: 2, score_reverse: 3}
  - {value: 3, label: "согласна", score_direct: 3, score_reverse: 2}
  - {value: 4, label: "полностью согласна", score_direct: 4, score_reverse: 1}
scale_codes:
  - {code: total, title: "Глобальная самооценка", score_type: sum, item_count: 10, range_raw: "10-40"}
source_primary: "Rosenberg M. Society and the Adolescent Self-image. Princeton University Press, 1965."
source_secondary:
  - "StatBlank: Шкала самооценки Розенберга"
  - "Исследования русскоязычной версии RSES"
notes_for_vkr: "Включена для чистого измерения глобальной самооценки / самоуважения; разводить с CSEs(Ru)."
---

# Шкала самооценки Розенберга

## Назначение в ВКР

Методика используется как показатель глобальной самооценки / самоуважения. В актуальной батарее она нужна, чтобы не сводить самооценку только к широкому интегральному конструкту CSEs(Ru).

## Теоретическое основание

Шкала измеряет глобальное позитивное или негативное отношение человека к себе. Для темы ВКР она прямо соответствует заявленной переменной "самооценка".

## Источники

Основной источник - Rosenberg M., 1965. Для русскоязычной формы нужно выбрать и зафиксировать конкретный источник формулировок. Текст пунктов не хранится в публичном репозитории до проверки источника.

## Пункты

Машиночитаемая карта пунктов: `items/rosenberg_self_esteem_scale_ru_items.csv`.

## Подсчет баллов

Прямые пункты: 1, 3, 4, 7, 10. Обратные пункты: 2, 5, 6, 8, 9.

```text
reverse_score = 5 - raw_answer
rses_total = q01 + reverse(q02) + q03 + q04 + reverse(q05) + reverse(q06) + q07 + reverse(q08) + reverse(q09) + q10
```

## Интерпретация

Более высокий балл означает более позитивное глобальное отношение к себе. Для анализа ВКР предпочтительно использовать сырой общий балл как непрерывную переменную.

## Ограничения

- Нужно выбрать конкретную русскоязычную версию формулировок.
- Нельзя смешивать интерпретацию RSES и CSEs(Ru).
- Не является клинической диагностикой.
