---
schema_version: "2.0"
id: sisa_jones_crandall_ru_candidate
title: "Short Index of Self-Actualization, SISA"
short_title: "SISA"
aliases:
  - "Short Index of Self-Actualization"
  - "Краткий индекс самоактуализации Джонса и Крэндалла"
construct: "Краткий индекс самоактуализации"
domain: "самоактуализация"
status_in_research: "reserve"
priority: "reserve"
recommended_use: "короткая возможная замена САТ/САМОАЛ после согласования"
language: "ru"
version: "русский перевод требует уточнения"
authors_original:
  - "A. Jones"
  - "R. Crandall"
authors_adaptation:
  - "уточнить"
year_original: 1986
year_adaptation: 0
item_count: 15
scale_count: 1
response_format: "likert_1_4"
estimated_time_min: "3-5"
license_status: "unclear"
full_items_stored: false
items_text_policy: "source_required"
items_file: "items/sisa_jones_crandall_ru_candidate_items.csv"
key_file: "keys/sisa_keys.csv"
scoring_status: "external_key_required"
form_variable_prefix: "sisa"
response_options:
  - {value: 1}
  - {value: 2}
  - {value: 3}
  - {value: 4}
scale_codes:
  - {code: total, title: "Краткий индекс самоактуализации"}
source_primary: "Jones A., Crandall R. Validation of a Short Index of Self-Actualization // Personality and Social Psychology Bulletin. 1986."
source_secondary:
  - "Русскоязычные исследования, использующие перевод SISA"
notes_for_vkr: "Близкий короткий аналог самоактуализации, но русская психометрическая база требует проверки."
---

# Short Index of Self-Actualization, SISA

## Назначение

SISA сохранен как короткая возможная замена длинных методик самоактуализации.

## Пункты и ключ

- Пункты: `items/sisa_jones_crandall_ru_candidate_items.csv`.
- Ключ: `keys/sisa_keys.csv`.

## Подсчет

Обычно используется общий балл по 15 пунктам, но ключ и реверсирование нужно сверить по выбранной версии.

```text
if scoring_status != "complete": skip_auto_scoring(sisa_jones_crandall_ru_candidate)
```

## Ограничения

- Не входит в актуальную батарею.
- Русская версия и ключ требуют проверки.
