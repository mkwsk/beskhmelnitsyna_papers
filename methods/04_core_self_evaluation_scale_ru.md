---
schema_version: "2.0"
id: core_self_evaluation_scale_ru
title: "Шкала базового самооценивания Core Self-Evaluation Scale, CSEs(Ru)"
short_title: "CSEs(Ru)"
aliases:
  - "Core Self-Evaluation Scale"
  - "ШБСО"
  - "Шкала базового самооценивания"
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
full_items_stored: false
items_text_policy: "source_required"
items_file: "items/core_self_evaluation_scale_ru_items.csv"
key_file: ""
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
  - {code: negative_reversed, title: "Негативное базовое самооценивание после реверса", score_type: sum, item_count: 5, range_raw: "5-25"}
  - {code: total, title: "Общий балл БСО", score_type: sum, item_count: 10, range_raw: "10-50"}
source_primary: "Judge et al. The Core Self-Evaluations Scale, 2003."
source_secondary:
  - "Маничев С.А., Лепехин Н.Н., Ильина О.Н. Русскоязычная версия Шкалы базового самооценивания (Core Self-Evaluation Scale): психометрическая проверка и перспективы использования // Вестник СПбГУ. Психология. 2022. Т. 12. Вып. 3. С. 285-308."
notes_for_vkr: "Широкий интегральный показатель; в интерпретации разводить с GSE и RSES."
---

# Шкала базового самооценивания Core Self-Evaluation Scale, CSEs(Ru)

## Назначение в ВКР

Методика используется для оценки базового самооценивания как интегрального личностного ресурса. В актуальной батарее ее нужно интерпретировать не как простую самооценку, а как более широкий конструкт.

## Теоретическое основание

Конструкт Core Self-Evaluations включает самооценку, обобщенную самоэффективность, эмоциональную стабильность и локус контроля. В теме ВКР показатель может быть связан с предпринимательской устойчивостью и проактивностью, но требует разведения с GSE и RSES.

## Источники и психометрия

Русскоязычная проверка: Маничев, Лепехин, Ильина, 2022. Выборка N = 917 работников организаций 18-60 лет. Зафиксирована двухфакторная структура: позитивное и негативное базовое самооценивание; показана удовлетворительная надежность и связи с самооценкой, субъективным контролем, самоэффективностью, нейротизмом и вовлеченностью.

## Пункты

Машиночитаемая карта пунктов: `items/core_self_evaluation_scale_ru_items.csv`.

Тексты пунктов брать из статьи/приложения русской версии или из разрешенного источника.

## Подсчет баллов

```text
reverse_score = 6 - raw_answer
cse_positive = q01 + q03 + q05 + q07 + q09
cse_negative_reversed = reverse(q02) + reverse(q04) + reverse(q06) + reverse(q08) + reverse(q10)
cse_total = cse_positive + cse_negative_reversed
```

## Интерпретация

Высокий общий балл означает более выраженное позитивное базовое самооценивание. В ВКР важно отдельно описывать, что CSEs(Ru) шире классической самооценки и частично пересекается с GSE.

## Ограничения

- Частично пересекается с GSE и RSES.
- Не следует использовать как полную замену классической самооценки без пояснения.
- Не является клинической диагностикой.
