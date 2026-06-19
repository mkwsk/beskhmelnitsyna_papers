---
schema_version: "2.0"
id: sat_self_actualization_test_ru
title: "Самоактуализационный тест, САТ"
short_title: "САТ"
aliases:
  - "CAT"
  - "Самоактуализационный тест А. Шострома"
construct: "Самоактуализация личности"
domain: "самоактуализация"
status_in_research: "reserve"
priority: "reserve"
recommended_use: "резерв; использовать только при сильном обосновании"
language: "ru"
version: "адаптация Ю.Е. Алешиной, Л.Я. Гозмана, М.В. Загика, М.В. Кроз"
authors_original:
  - "Everett Shostrom"
authors_adaptation:
  - "Ю.Е. Алешина"
  - "Л.Я. Гозман"
  - "М.В. Загик"
  - "М.В. Кроз"
year_original: 1963
year_adaptation: 1987
item_count: 126
scale_count: 14
response_format: "forced_choice_ab"
estimated_time_min: "30-35"
license_status: "unclear"
full_items_stored: false
items_text_policy: "source_required"
items_file: "items/sat_self_actualization_test_ru_items.csv"
key_file: "items/sat_self_actualization_test_ru_key.csv"
scoring_status: "external_key_required"
form_variable_prefix: "sat"
response_options:
  - {value: "a", label: "вариант а"}
  - {value: "b", label: "вариант б"}
scale_codes:
  - {code: time, title: "Ориентация во времени"}
  - {code: support, title: "Поддержка"}
  - {code: aux, title: "12 дополнительных шкал"}
source_primary: "Shostrom E. Personal Orientation Inventory."
source_secondary:
  - "Материалы Psylab по САТ"
  - "HR-Portal: Самоактуализационный тест"
notes_for_vkr: "Родственный POI-инструмент; слишком длинный для текущей онлайн-батареи."
---

# Самоактуализационный тест, САТ

## Назначение

САТ сохранен в архиве как родственный инструмент POI-традиции. В актуальную батарею не включен, потому что длинный и требует сильного обоснования.

## Подсчет

Формат ответов - forced choice A/B. Каждый ответ, совпадающий с ключом шкалы, дает 1 балл. Полный ключ и текст пунктов нужно сверить с руководством или выбранным источником.

```text
if scoring_status != "complete": skip_auto_scoring(sat_self_actualization_test_ru)
```

## Ограничения

- 126 пунктов, высокий риск утомления в онлайн-опросе.
- Измеряет общую, а не профессиональную самоактуализацию.
- Ключ и правовой статус требуют сверки.
