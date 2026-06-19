---
schema_version: "2.0"
id: pgis_ii_ru
title: "PGIS-II, русскоязычная модификация"
short_title: "PGIS-II"
aliases:
  - "Инициатива личностного роста"
construct: "Инициатива личностного роста"
domain: "самоактуализация"
status_in_research: "reserve"
priority: "reserve"
recommended_use: "альтернатива аспекта самоактуализации"
language: "ru"
version: "русскоязычная модификация; уточнить публикацию"
authors_original:
  - "C. Robitschek"
authors_adaptation:
  - "уточнить по выбранной русской публикации"
year_original: 2012
year_adaptation: 2018
item_count: 16
scale_count: 3
response_format: "likert"
estimated_time_min: "4-6"
license_status: "unclear"
full_items_stored: false
items_text_policy: "source_required"
items_file: "items/pgis_ii_ru_items.csv"
key_file: "keys/pgis_ii_ru_keys.csv"
scoring_status: "external_key_required"
form_variable_prefix: "pgis"
response_options: []
scale_codes:
  - {code: awareness, title: "Осознанность саморазвития"}
  - {code: intentional_behavior, title: "Преднамеренное поведение"}
  - {code: total, title: "Инициатива личностного роста"}
source_primary: "Robitschek, 2012."
source_secondary:
  - "Скворцова: русскоязычная модификация PGIS-II"
notes_for_vkr: "Резервная альтернатива, если фокус на саморазвитии и субъектности."
---

# PGIS-II, русскоязычная модификация

## Назначение

PGIS-II сохранена как резервная альтернатива самоактуализации через саморазвитие и субъектность.

## Пункты и ключ

- Пункты: `items/pgis_ii_ru_items.csv`.
- Ключ: `keys/pgis_ii_ru_keys.csv`.

## Подсчет

Точные пункты, формат ответа и ключ нужно сверить по выбранной публикации.

```text
if scoring_status != "complete": skip_auto_scoring(pgis_ii_ru)
```

## Ограничения

- Не входит в актуальную батарею.
- Требуется сверка полного текста, ключа и шкалы ответа.
