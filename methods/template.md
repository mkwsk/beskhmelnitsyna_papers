---
schema_version: "2.0"
id: method_id
title: "Полное название методики"
short_title: "Краткое название"
aliases: []
construct: "Что измеряет методика"
domain: "самооценка | самоэффективность | самоактуализация | профессиональная самореализация | аутентичность | другое"
status_in_research: "included | candidate | reserve | excluded"
priority: "primary | secondary | reserve | reference"
recommended_use: "основная методика | дополнительная методика | резерв | не использовать"
language: "ru"
version: "версия / адаптация / год"
authors_original: []
authors_adaptation: []
year_original: 0
year_adaptation: 0
item_count: 0
scale_count: 0
response_format: "likert_1_5 | likert_1_4 | forced_choice_ab | yes_partial_no | other"
estimated_time_min: "0-0"
license_status: "open | citation_only | unclear | restricted"
full_items_stored: false
items_text_policy: "stored | not_stored_public_repo | stored_private_only | source_required"
items_file: "items/method_id_items.csv"
key_file: "items/method_id_key.csv"
scoring_status: "complete | complete_key_without_item_texts | partial | external_key_required | not_applicable"
form_variable_prefix: "method"
response_options: []
scale_codes: []
source_primary: "Библиографическое описание первоисточника"
source_secondary: []
notes_for_vkr: "Краткая методическая пометка для ВКР"
---

# Название методики

## Назначение

Что измеряет методика и какую переменную ВКР она закрывает.

## Источники

Основной источник, источник русской адаптации, дополнительные источники и статус надежности источника.

## Пункты

Машиночитаемый файл пунктов: `items/method_id_items.csv`.

CSV-формат:

```csv
method_id,item_number,item_code,variable,text_a,text_b,text,scale_code,keyed_value,scoring_direction,required,source_note
```

Если правовой статус полного текста неясен, в публичном репозитории хранится структура пунктов, ключи и ссылка на источник, а формулировки добавляются после проверки источника или в приватной копии.

## Подсчет баллов

Для шкал Лайкерта:

```text
score_q01 = raw_q01
score_q02 = reverse(raw_q02, min=1, max=5)
total = sum(score_q01:score_qNN)
```

Для forced choice A/B:

```text
score(scale, item) = 1 if answer == keyed_value else 0
scale_total = sum(score(scale, item_i))
```

## Интерпретация

Что означает высокий и низкий балл, есть ли нормативные уровни, что нельзя выводить по методике.

## Яндекс.Формы и выгрузка

- Префикс переменных: `form_variable_prefix`.
- Ответы: `prefix_q01` ... `prefix_qNN`.
- Шкалы: перечислены в `scale_codes`.
- Пункты не перемешивать.

## Ограничения

Методика не является клинической диагностикой. При отсутствии валидных норм лучше использовать балл как непрерывную переменную.
