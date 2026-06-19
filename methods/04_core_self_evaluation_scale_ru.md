---
schema_version: "2.0"
id: core_self_evaluation_scale_ru
title: "Шкала базового самооценивания Core Self-Evaluation Scale, CSEs(Ru)"
short_title: "CSEs(Ru)"
aliases:
  - "Core Self-Evaluation Scale"
  - "ШБСО"
construct: "Базовое самооценивание как интегральный личностный ресурс"
domain: "самооценка"
status_in_research: "included"
priority: "primary"
recommended_use: "основная методика актуальной батареи"
language: "ru"
version: "русскоязычная версия Маничева, Лепехина, Ильиной, 2022"
authors_original:
  - "T.A. Judge"
  - "A. Erez"
  - "J.E. Bono"
  - "C.J. Thoresen"
authors_adaptation:
  - "С.А. Маничев"
  - "Н.Н. Лепехин"
  - "О.Н. Ильина"
year_original: 2003
year_adaptation: 2022
item_count: 10
scale_count: 3
response_format: "likert_1_5"
estimated_time_min: "2-4"
license_status: "open"
full_items_stored: true
items_text_policy: "stored_in_items_csv"
items_file: "items/core_self_evaluation_scale_ru_items.csv"
key_file: "keys/core_self_evaluation_scale_ru_keys.csv"
scoring_status: "complete"
form_variable_prefix: "cse"
response_options:
  - {value: 1, label: "полностью не согласна", score_direct: 1, score_reverse: 5}
  - {value: 2, label: "скорее не согласна", score_direct: 2, score_reverse: 4}
  - {value: 3, label: "затрудняюсь ответить", score_direct: 3, score_reverse: 3}
  - {value: 4, label: "скорее согласна", score_direct: 4, score_reverse: 2}
  - {value: 5, label: "полностью согласна", score_direct: 5, score_reverse: 1}
scale_codes:
  - {code: positive, title: "Позитивное базовое самооценивание", score_type: sum, item_count: 5, range_raw: "5-25"}
  - {code: neg_rev, title: "Обратная субшкала после реверса", score_type: sum, item_count: 5, range_raw: "5-25"}
  - {code: total, title: "Общий балл БСО", score_type: sum, item_count: 10, range_raw: "10-50"}
source_primary: "Judge et al. The Core Self-Evaluations Scale, 2003."
source_secondary:
  - "Маничев С.А., Лепехин Н.Н., Ильина О.Н., 2022."
notes_for_vkr: "Широкий интегральный показатель. Полный текст 10 пунктов хранится в items/core_self_evaluation_scale_ru_items.csv."
---

# Шкала базового самооценивания Core Self-Evaluation Scale, CSEs(Ru)

## Назначение в ВКР

Методика используется для оценки базового самооценивания как интегрального личностного ресурса.

## Пункты и ключ

- Пункты: `items/core_self_evaluation_scale_ru_items.csv`.
- Ключ: `keys/core_self_evaluation_scale_ru_keys.csv`.

## Подсчет баллов

```text
reverse_score = 6 - raw_answer
cse_positive = sum(q01 q03 q05 q07 q09)
cse_neg_rev = sum(reverse(q02 q04 q06 q08 q10))
cse_total = cse_positive + cse_neg_rev
```

## Интерпретация

Высокий общий балл означает более выраженное позитивное базовое самооценивание. В ВКР важно отдельно описывать, что CSEs(Ru) шире классической самооценки и частично пересекается с GSE.

## Ограничения

- Частично пересекается с GSE и RSES.
- Не является клинической диагностикой.
