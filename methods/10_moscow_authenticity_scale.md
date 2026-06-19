---
schema_version: "2.0"
id: moscow_authenticity_scale
title: "Московская шкала аутентичности, MAS"
short_title: "MAS"
aliases:
  - "Moscow Authenticity Scale"
construct: "Аутентичность"
domain: "аутентичность"
status_in_research: "reserve"
priority: "reserve"
recommended_use: "короткий скрининг или дополнительная методика"
language: "ru"
version: "Нартова-Бочавер и соавт., 2021"
authors_original:
  - "С.К. Нартова-Бочавер"
  - "соавторы"
authors_adaptation: []
year_original: 2021
year_adaptation: 2021
item_count: 5
scale_count: 1
response_format: "likert_1_5"
estimated_time_min: "1-2"
license_status: "unclear"
full_items_stored: false
items_text_policy: "source_required"
items_file: "items/moscow_authenticity_scale_items.csv"
key_file: "items/moscow_authenticity_scale_key.csv"
scoring_status: "external_key_required"
form_variable_prefix: "mas"
response_options:
  - {value: 1}
  - {value: 2}
  - {value: 3}
  - {value: 4}
  - {value: 5}
scale_codes:
  - {code: total, title: "Общая аутентичность"}
source_primary: "Nartova-Bochaver et al. Moscow Authenticity Scale. Psychology in Russia: State of the Art. 2021."
source_secondary: []
notes_for_vkr: "Очень короткая шкала; как полная замена самоактуализации слишком узкая."
---

# Московская шкала аутентичности, MAS

## Назначение

MAS сохранена как короткий резервный скрининг аутентичности. Она может быть полезна как дополнительная шкала, но слишком узкая для полной замены самоактуализации.

## Подсчет

Предполагается общий показатель по 5 пунктам, но точный ключ и возможность реверсирования нужно сверить по статье перед автоматическим расчетом.

```text
if scoring_status != "complete": skip_auto_scoring(moscow_authenticity_scale)
```

## Ограничения

- Не входит в актуальную батарею.
- Очень короткая и узкая шкала.
- Требуется сверка текста пунктов и ключа.
