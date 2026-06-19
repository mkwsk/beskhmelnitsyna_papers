---
schema_version: "2.0"
id: samoal_lazukin_kalina
title: "Опросник диагностики самоактуализации личности, САМОАЛ"
short_title: "САМОАЛ"
aliases:
  - "САМОАЛ Лазукина-Калиной"
  - "Опросник самоактуализации личности"
construct: "Самоактуализация личности"
domain: "самоактуализация"
status_in_research: "included"
priority: "primary"
recommended_use: "основная методика актуальной батареи по решению куратора"
language: "ru"
version: "адаптация А.В. Лазукина, Н.Ф. Калиной, 1998"
authors_original:
  - "Everett Shostrom"
authors_adaptation:
  - "А.В. Лазукин"
  - "Н.Ф. Калина"
year_original: 1963
year_adaptation: 1998
item_count: 100
scale_count: 12
response_format: "forced_choice_ab"
estimated_time_min: "15-25"
license_status: "unclear"
full_items_stored: false
items_text_policy: "not_stored_public_repo"
items_file: "items/samoal_lazukin_kalina_items.csv"
key_file: "keys/samoal_lazukin_kalina_keys.csv"
scoring_status: "complete_key_without_item_texts"
form_variable_prefix: "samoal"
response_options:
  - {value: "a", label: "вариант а"}
  - {value: "b", label: "вариант б"}
scale_codes:
  - {code: time, title: "Ориентация во времени", item_count: 10, normalize_multiplier: 1.5}
  - {code: values, title: "Ценности", item_count: 15, normalize_multiplier: 1.0}
  - {code: human_nature, title: "Взгляд на природу человека", item_count: 10, normalize_multiplier: 1.5}
  - {code: cognition, title: "Потребность в познании", item_count: 10, normalize_multiplier: 1.5}
  - {code: creativity, title: "Креативность", item_count: 15, normalize_multiplier: 1.0}
  - {code: autonomy, title: "Автономность", item_count: 15, normalize_multiplier: 1.0}
  - {code: spontaneity, title: "Спонтанность", item_count: 15, normalize_multiplier: 1.0}
  - {code: self_understanding, title: "Самопонимание", item_count: 10, normalize_multiplier: 1.5}
  - {code: autosympathy, title: "Аутосимпатия", item_count: 15, normalize_multiplier: 1.0}
  - {code: contact, title: "Контактность", item_count: 10, normalize_multiplier: 1.5}
  - {code: communication_flexibility, title: "Гибкость в общении", item_count: 10, normalize_multiplier: 1.5}
  - {code: total, title: "Общий показатель", score_type: "profile_or_sum_after_approval"}
source_primary: "Калина Н.Ф., Лазукин А.В. Вопросник Самоал. Адаптация Самоактуализационного теста // Журнал практического психолога. 1998. № 1."
source_secondary:
  - "Dip-Psi: Опросник диагностики самоактуализации личности, САМОАЛ"
notes_for_vkr: "Включена по решению куратора; методика объемная, не сокращать вручную."
---

# Опросник диагностики самоактуализации личности, САМОАЛ

## Назначение в ВКР

САМОАЛ используется как основной блок самоактуализации в актуальной батарее. Если методика включена, она переносится целиком и обрабатывается по ключу.

## Пункты и ключ

- Пункты: `items/samoal_lazukin_kalina_items.csv`.
- Ключ: `keys/samoal_lazukin_kalina_keys.csv`.
- Переменные формы: `samoal_q001` ... `samoal_q100`.

## Подсчет баллов

Каждый пункт имеет ответ `a` или `b`. Для каждой шкалы хранится набор пар `item_number + keyed_value`.

```text
score(scale, item) = 1 if answer(item) == keyed_value(scale, item) else 0
raw_scale = count(keyed_matches)
normalized_scale = raw_scale * normalize_multiplier
percent_scale = normalized_scale / 15 * 100
```

Шкалы 1, 3, 4, 8, 10 и 11 содержат по 10 пунктов и для сопоставимости умножаются на 1.5. Остальные шкалы содержат по 15 пунктов.

Общий показатель считать только после согласования способа агрегирования.

## Интерпретация

Высокие значения по шкалам показывают большую выраженность соответствующих аспектов самоактуализации. Для ВКР лучше интерпретировать профиль шкал и заранее указать, какие шкалы используются в статистической проверке гипотезы.

## Ограничения

- Очень объемная методика: 100 пунктов, повышенный риск утомления.
- Измеряет общую, а не строго профессиональную самоактуализацию.
- Ручное сокращение недопустимо без отдельного психометрического обоснования.
