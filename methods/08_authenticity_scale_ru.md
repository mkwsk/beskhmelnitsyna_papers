---
schema_version: "2.0"
id: authenticity_scale_ru
title: "Authenticity Scale, русская версия"
short_title: "Authenticity Scale"
aliases:
  - "Шкала аутентичности Вуд и соавт."
  - "Authentic Living / Accepting External Influence / Self-Alienation"
construct: "Аутентичность"
domain: "аутентичность"
status_in_research: "reserve"
priority: "reserve"
recommended_use: "альтернатива аспекта самоактуализации"
language: "ru"
version: "русская валидация Нартовой-Бочавер и соавт., 2021"
authors_original:
  - "Wood et al."
authors_adaptation:
  - "С.К. Нартова-Бочавер"
  - "соавторы"
year_original: 2008
year_adaptation: 2021
item_count: 11
scale_count: 3
response_format: "likert_1_7"
estimated_time_min: "3-5"
license_status: "unclear"
full_items_stored: false
items_text_policy: "source_required"
items_file: "items/authenticity_scale_ru_items.csv"
key_file: "keys/authenticity_scale_ru_keys.csv"
scoring_status: "external_key_required"
form_variable_prefix: "auth"
response_options:
  - {value: 1}
  - {value: 2}
  - {value: 3}
  - {value: 4}
  - {value: 5}
  - {value: 6}
  - {value: 7}
scale_codes:
  - {code: authentic_living, title: "Authentic Living"}
  - {code: external_influence, title: "Accepting External Influence"}
  - {code: self_alienation, title: "Self-Alienation"}
source_primary: "Wood et al. The Authenticity Scale."
source_secondary:
  - "Nartova-Bochaver et al. Russian validation of the Authenticity Scale"
notes_for_vkr: "Резервная альтернатива, если самоактуализация задается через аутентичность."
---

# Authenticity Scale, русская версия

## Назначение

Шкала сохранена как резервная альтернатива: она может быть полезна, если самоактуализация операционализируется через аутентичность.

## Пункты и ключ

- Пункты: `items/authenticity_scale_ru_items.csv`.
- Ключ: `keys/authenticity_scale_ru_keys.csv`.

## Подсчет

Методика имеет 3 субшкалы. Точный ключ, реверсирование и возможность общего показателя нужно сверить по русской публикации перед подключением к автоматическому расчету.

```text
if scoring_status != "complete": skip_auto_scoring(authenticity_scale_ru)
```

## Ограничения

- Не входит в актуальную батарею.
- Требуется сверка полного текста и ключа.
