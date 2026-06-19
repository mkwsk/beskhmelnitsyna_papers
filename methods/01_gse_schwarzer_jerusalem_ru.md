---
schema_version: "2.0"
id: gse_schwarzer_jerusalem_ru
title: "Шкала общей самоэффективности Р. Шварцера и М. Ерусалема"
short_title: "GSE"
aliases:
  - "General Self-Efficacy Scale"
  - "Шкала общей самоэффективности"
construct: "Общая самоэффективность"
domain: "самоэффективность"
status_in_research: "included"
priority: "primary"
recommended_use: "основная методика актуальной батареи"
language: "ru"
version: "русская адаптация В.Г. Ромека"
authors_original:
  - "Ralf Schwarzer"
  - "Matthias Jerusalem"
authors_adaptation:
  - "В.Г. Ромек"
year_original: 1979
year_adaptation: 1996
item_count: 10
scale_count: 1
response_format: "likert_1_4"
estimated_time_min: "2-4"
license_status: "unclear"
full_items_stored: true
items_text_policy: "stored_in_items_csv"
items_file: "items/gse_schwarzer_jerusalem_ru_items.csv"
key_file: "keys/gse_schwarzer_jerusalem_ru_keys.csv"
scoring_status: "complete"
form_variable_prefix: "gse"
response_options:
  - {value: 1, label: "абсолютно неверно", score_direct: 1}
  - {value: 2, label: "скорее всего не верно", score_direct: 2}
  - {value: 3, label: "скорее всего верно", score_direct: 3}
  - {value: 4, label: "совершенно верно", score_direct: 4}
scale_codes:
  - {code: total, title: "Общая самоэффективность", score_type: sum, item_count: 10, range_raw: "10-40"}
source_primary: "Schwarzer R., Jerusalem M. General Self-Efficacy Scale."
source_secondary:
  - "Шварцер Р., Ерусалем М., Ромек В. Русская версия шкалы общей самоэффективности Р. Шварцера и М. Ерусалема // Иностранная психология. 1996. № 7. С. 71-77."
notes_for_vkr: "Короткая шкала общей самоэффективности."
---

# Шкала общей самоэффективности Р. Шварцера и М. Ерусалема

## Назначение в ВКР

Методика используется для оценки общей самоэффективности как личностного ресурса.

## Пункты и ключ

- Пункты: `items/gse_schwarzer_jerusalem_ru_items.csv`.
- Ключ: `keys/gse_schwarzer_jerusalem_ru_keys.csv`.

## Подсчет баллов

Все 10 пунктов прямые.

```text
gse_total = sum(gse_q01:gse_q10)
```

## Интерпретация

Более высокий балл означает более выраженную общую самоэффективность. Для анализа ВКР предпочтительно использовать сырой общий балл как непрерывную переменную.

## Ограничения

- Не измеряет профессиональную самоэффективность напрямую.
- Не является клинической диагностикой.
