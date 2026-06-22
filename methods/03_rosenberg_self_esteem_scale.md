---
schema_version: "2.0"
id: rosenberg_self_esteem_scale_ru
title: "Шкала самооценки Розенберга"
short_title: "RSES"
aliases:
  - "Rosenberg Self-Esteem Scale"
  - "Шкала самоуважения Розенберга"
construct: "Глобальная самооценка / самоуважение"
domain: "самооценка"
status_in_research: "included"
priority: "primary"
recommended_use: "основная методика актуальной батареи"
language: "ru"
version: "рабочая русскоязычная версия; ответы в форме кодируются 1-4"
authors_original:
  - "Morris Rosenberg"
authors_adaptation:
  - "русскоязычный академический источник для финальной ссылки требует закрепления"
year_original: 1965
year_adaptation: 0
item_count: 10
scale_count: 1
response_format: "likert_1_4"
estimated_time_min: "2-4"
license_status: "unclear"
full_items_stored: true
items_text_policy: "stored_in_items_csv"
items_file: "items/rosenberg_self_esteem_scale_ru_items.csv"
key_file: "keys/rosenberg_self_esteem_scale_ru_keys.csv"
scoring_status: "complete"
form_variable_prefix: "rses"
response_options:
  - {value: 1, label: "полностью не согласна", score_direct: 1, score_reverse: 4}
  - {value: 2, label: "не согласна", score_direct: 2, score_reverse: 3}
  - {value: 3, label: "согласна", score_direct: 3, score_reverse: 2}
  - {value: 4, label: "полностью согласна", score_direct: 4, score_reverse: 1}
scale_codes:
  - {code: total, title: "Глобальная самооценка / самоуважение", score_type: sum, item_count: 10, range_raw: "10-40"}
source_primary: "Rosenberg M. Society and the Adolescent Self-image. Princeton University Press, 1965."
source_secondary:
  - "StatBlank: Шкала самоуважения Розенберга - источник рабочих русскоязычных формулировок"
  - "Золотарева: русскоязычная валидационная публикация по RSES; в аудите использована для сверки направлений пунктов и замечания о шкалировании 0-3"
notes_for_vkr: "Включена для измерения глобальной самооценки. Ключ направлений согласован, но для финальной ВКР нужно закрепить точное библиографическое описание русскоязычной академической версии."
audit_note: "По аудиту ключ направлений согласован: прямые 1,3,4,7,10; обратные 2,5,6,8,9. В репозитории используется кодирование 1-4; при сопоставлении с источниками 0-3 нужно пересчитать total_0_3 = total_1_4 - 10."
---

# Шкала самооценки Розенберга

## Назначение в ВКР

Методика используется как показатель глобальной самооценки / самоуважения.

## Пункты и ключ

- Пункты: `items/rosenberg_self_esteem_scale_ru_items.csv`.
- Ключ: `keys/rosenberg_self_esteem_scale_ru_keys.csv`.

## Подсчет баллов

Прямые пункты: 1, 3, 4, 7, 10. Обратные пункты: 2, 5, 6, 8, 9.

В текущей форме используется кодирование ответов 1-4. Для него применяется реверс:

```text
reverse_score = 5 - raw_answer
rses_total_1_4 = sum direct plus reversed items
```

Диапазон итогового балла при этой конвенции: 10-40.

Если для анализа или сопоставления с публикацией нужна конвенция 0-3, общий балл переводится так:

```text
rses_total_0_3 = rses_total_1_4 - 10
```

Диапазон итогового балла после пересчета: 0-30. Направления ключа при этом не меняются.

## Источники и трассируемость

Основной первоисточник методики: Rosenberg M. Society and the Adolescent Self-image. Princeton University Press, 1965.

Рабочие русскоязычные формулировки в текущем item-файле взяты из открытого источника StatBlank. По аудиту направления прямых и обратных пунктов совпадают с русскоязычной валидационной публикацией Золотаревой, но для финальной ВКР нужно внести точное библиографическое описание выбранной академической русскоязычной версии.

## Интерпретация

Более высокий балл означает более выраженную глобальную самооценку. Для анализа ВКР предпочтительно использовать сырой общий балл как непрерывную переменную.

## Ограничения

- Нужно развести интерпретацию RSES и CSEs(Ru).
- Не является клинической диагностикой.
- Нельзя смешивать шкалирование 1-4 и 0-3 без пересчета итогового балла.
