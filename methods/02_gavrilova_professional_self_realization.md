---
schema_version: "2.0"
id: gavrilova_professional_self_realization
title: "Методика Тип и уровень профессиональной самореализации Е.А. Гавриловой"
short_title: "Методика Гавриловой"
aliases:
  - "Тип и уровень профессиональной самореализации"
construct: "Профессиональная самореализация личности"
domain: "профессиональная самореализация"
status_in_research: "reserve"
priority: "reserve"
recommended_use: "резервная методика"
language: "ru"
version: "Е.А. Гаврилова, 2015"
authors_original:
  - "Е.А. Гаврилова"
authors_adaptation: []
year_original: 2015
year_adaptation: 2015
item_count: 51
scale_count: 4
response_format: "yes_partial_no"
estimated_time_min: "10-15"
license_status: "citation_only"
full_items_stored: false
items_text_policy: "not_stored_public_repo"
items_file: "items/gavrilova_professional_self_realization_items.csv"
key_file: "keys/gavrilova_professional_self_realization_keys.csv"
scoring_status: "external_key_required"
form_variable_prefix: "gav"
response_options:
  - {value: 2, label: "да"}
  - {value: 1, label: "отчасти верно"}
  - {value: 0, label: "нет"}
scale_codes:
  - {code: goal, title: "Ценностно-целевой компонент"}
  - {code: resource, title: "Ресурсный компонент"}
  - {code: phenomenological, title: "Феноменологический компонент"}
  - {code: total, title: "Общий уровень"}
source_primary: "Гаврилова Е.А. Психодиагностическая методика Тип и уровень профессиональной самореализации: разработка, описание и психометрия // Вестник ТвГУ. Серия Педагогика и психология. 2015. С. 19-34."
source_secondary: []
notes_for_vkr: "Резервная методика по профессиональной самореализации; ключ требуется сверить с первоисточником."
---

# Методика Тип и уровень профессиональной самореализации Е.А. Гавриловой

## Назначение

Методика сохранена в архиве как резерв по профессиональной самореализации.

## Пункты и ключ

- Пункты: `items/gavrilova_professional_self_realization_items.csv`.
- Ключ: `keys/gavrilova_professional_self_realization_keys.csv`.

## Подсчет

Ответы кодируются как `да = 2`, `отчасти верно = 1`, `нет = 0`. Точный ключ пунктов нужно сверить с первоисточником перед автоматическим расчетом.

```text
if scoring_status != "complete": skip_auto_scoring(gavrilova_professional_self_realization)
```

## Ограничения

- Не входит в актуальную батарею.
- Для подключения к форме нужна ручная сверка первоисточника.
