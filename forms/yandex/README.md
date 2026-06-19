# Заготовка Яндекс.Форм для ВКР

Эта директория содержит JSON-заготовку формы и Python-скрипты для работы с API Яндекс Форм.

PowerShell-скриптов и `.cmd`-оберток в текущей версии нет. Рабочий интерфейс управления - Python-скрипты из папки `scripts/`.

## Основная форма

Главный файл: `form_definition/vkr_main_form.json`.

Актуальная батарея тестов в основной форме:

| Порядок | Блок | Файл секции |
|---:|---|---|
| 1 | Самоактуализация - САМОАЛ, Лазукин-Калина | `reserve/80_samoal_placeholder.json` |
| 2 | Самоэффективность - GSE Шварцера-Ерусалема, адаптация Ромека | `sections/10_gse_schwarzer_jerusalem_ru.json` |
| 3 | Самооценивание - CSEs(Ru), Шкала базового самооценивания | `reserve/50_core_self_evaluation_scale_ru.json` |
| 4 | Самоуважение / самооценка - Шкала Розенберга | `sections/20_rosenberg_self_esteem_scale_ru.json` |

Полный порядок секций, которые реально загружаются скриптом `create_form.py`, задается только полем `section_files` в `form_definition/vkr_main_form.json`.

Сейчас там указаны:

- `sections/00_welcome.json` - приветствие и информированное согласие;
- `sections/01_screening.json` - критерии участия;
- `sections/02_demographics.json` - социально-демографический блок;
- `reserve/80_samoal_placeholder.json` - САМОАЛ;
- `sections/10_gse_schwarzer_jerusalem_ru.json` - GSE;
- `reserve/50_core_self_evaluation_scale_ru.json` - CSEs(Ru);
- `sections/20_rosenberg_self_esteem_scale_ru.json` - RSES;
- `sections/99_finish.json` - завершающий экран.

В папке `sections/` могут оставаться дополнительные JSON-файлы от прежней версии батареи. Они не попадают в форму, если не перечислены в `section_files`.

## Важное ограничение по пунктам методик

Точные формулировки пунктов методик с неясным статусом распространения не внесены в JSON. Вместо них стоят `TODO`-плейсхолдеры.

Перед публикацией формы нужно:

1. заменить все `TODO` на точные пункты из выбранных первоисточников;
2. проверить правовой статус использования методик;
3. открыть форму в интерфейсе Яндекс.Форм и проверить страницы, шкалы и обязательность вопросов.

## Подготовка Python

Текущая версия предполагает, что команда `python` уже доступна в среде запуска. Встроенный/portable Python в репозиторий пока не добавлен.

Создание окружения:

```bash
python -m venv .venv
```

Установка зависимостей на Windows через `cmd.exe`:

```bat
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Установка зависимостей на Linux / macOS:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

## Настройка `.env`

Скопировать пример:

```bat
copy .env.example .env
```

Заполнить `.env`:

```text
FORMS_TOKEN=...
ORG_ID=...
ORG_HEADER=X-Org-Id
AUTH_SCHEME=OAuth
FORMS_PUBLIC_API=https://api.forms.yandex.net/v1
```

Подробная инструкция, откуда брать `FORMS_TOKEN`, `ORG_ID`, `ORG_HEADER`, `AUTH_SCHEME` и `FORMS_PUBLIC_API`, лежит в `docs/env_variables.md`.

## Скрипты

Подробное описание всех скриптов, их назначения и примеры запуска лежат в `scripts/README.md`.

Кратко:

| Скрипт | Назначение |
|---|---|
| `scripts/validate_definition.py` | Проверяет локальную JSON-заготовку формы. |
| `scripts/create_form.py` | Создает форму через API из локального JSON-описания. |
| `scripts/publish_form.py` | Публикует или снимает с публикации уже созданную форму. |
| `scripts/export_answers.py` | Выгружает ответы из Яндекс.Форм в JSON и/или CSV. |
| `scripts/score_export_template.py` | Шаблон подсчета баллов по CSV-выгрузке. |
| `scripts/yf_client.py` | Служебный клиент API, напрямую обычно не запускается. |

## Проверка JSON

```bash
python scripts/validate_definition.py form_definition/vkr_main_form.json
```

Проверка должна завершиться без ошибок. Если есть `TODO`, это не техническая ошибка JSON, но это блокер перед реальной публикацией.

## Создание формы через API

```bash
python scripts/create_form.py form_definition/vkr_main_form.json --output exports/form_mapping.json
```

Создать и сразу опубликовать:

```bash
python scripts/create_form.py form_definition/vkr_main_form.json --publish --output exports/form_mapping.json
```

После загрузки обязательно открыть форму в Яндекс.Формах вручную и проверить порядок страниц, обязательность вопросов, ветвление, отсутствие `TODO`-плейсхолдеров и корректность шкал.

## Публикация и снятие с публикации

```bash
python scripts/publish_form.py <survey_id> publish
python scripts/publish_form.py <survey_id> unpublish
```

## Выгрузка ответов

```bash
python scripts/export_answers.py <survey_id> --json exports/answers.json --csv exports/answers.csv
```

## Подсчет баллов по выгрузке

```bash
python scripts/score_export_template.py exports/answers.csv exports/answers_scored.csv
```

Скрипт подсчета является шаблоном. Перед использованием его нужно сверить с финальными ключами методик и с тем, как именно Яндекс.Формы выгружают названия колонок.
