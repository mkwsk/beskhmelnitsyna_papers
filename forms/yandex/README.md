# Заготовка Яндекс.Форм для ВКР

Эта директория содержит JSON-заготовку формы и Python-скрипты для работы с API Яндекс Форм.

PowerShell-скриптов и `.cmd`-оберток в текущей версии нет. Рабочий интерфейс управления - Python-скрипты из папки `scripts/`.

## Состав директории

```text
forms/yandex/
├── form_definition/
│   ├── vkr_main_form.json       # основная форма
│   ├── sections/                # секции основной формы
│   └── reserve/                 # резервные методики
├── scripts/                     # Python-скрипты управления
├── docs/                        # заметки по API
├── exports/                     # локальные выгрузки, не хранить в Git
├── .env.example                 # пример настроек API
├── requirements.txt             # зависимости Python
└── README.md                    # этот файл
```

## Основная форма

Главный файл: `form_definition/vkr_main_form.json`.

Секции основной формы лежат в `form_definition/sections/`:

- `00_welcome.json` - приветствие и информированное согласие;
- `01_screening.json` - критерии участия;
- `02_demographics.json` - социально-демографический блок;
- `10_gse_schwarzer_jerusalem_ru.json` - GSE;
- `20_rosenberg_self_esteem_scale_ru.json` - RSES;
- `30_gavrilova_professional_self_realization.json` - методика Гавриловой;
- `99_finish.json` - завершающий экран.

Резервные методики лежат в `form_definition/reserve/` и по умолчанию не загружаются в основную форму.

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

Установка зависимостей на Linux / macOS:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Установка зависимостей на Windows через `cmd.exe`:

```bat
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Если позже в репозиторий будет добавлен переносимый Python, команды можно будет заменить на запуск конкретного `python.exe` из папки репозитория.

## Настройка `.env`

Скопировать пример:

Windows `cmd.exe`:

```bat
copy .env.example .env
```

Linux / macOS:

```bash
cp .env.example .env
```

Заполнить `.env`:

```text
FORMS_TOKEN=...
ORG_ID=...
ORG_HEADER=X-Org-Id
AUTH_SCHEME=OAuth
FORMS_PUBLIC_API=https://api.forms.yandex.net/v1
```

Для организации Yandex Cloud вместо `X-Org-Id` может использоваться:

```text
ORG_HEADER=X-Cloud-Org-Id
```

Подробная инструкция, откуда брать `FORMS_TOKEN`, `ORG_ID`, `ORG_HEADER`, `AUTH_SCHEME` и `FORMS_PUBLIC_API`, лежит в `docs/env_variables.md`.

Краткие заметки по заголовкам API лежат в `docs/yandex_forms_api_notes.md`.

## Проверка JSON

```bash
python scripts/validate_definition.py form_definition/vkr_main_form.json
```

Проверка должна завершиться без ошибок. Если есть `TODO`, это не техническая ошибка JSON, но это блокер перед реальной публикацией.

## Создание формы через API

Создать черновик без публикации:

```bash
python scripts/create_form.py form_definition/vkr_main_form.json --output exports/form_mapping.json
```

Создать и сразу опубликовать:

```bash
python scripts/create_form.py form_definition/vkr_main_form.json --publish --output exports/form_mapping.json
```

После загрузки обязательно открыть форму в Яндекс.Формах вручную и проверить:

1. порядок страниц;
2. обязательность вопросов;
3. ветвление для несогласия и неподходящих критериев;
4. отсутствие `TODO`-плейсхолдеров;
5. корректность текстов и шкал.

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

## Структура JSON-секции

Каждая секция содержит массив `questions`. Для каждого вопроса есть:

- `qid` - локальный код переменной для базы;
- `payload` - то, что отправляется в API Яндекс Форм;
- `required` - локальная пометка для контроля, в API сейчас не отправляется;
- `scoring` - локальные правила подсчета, в API сейчас не отправляются.

Скрипт `create_form.py` отправляет в API только `payload`, чтобы не передать лишние локальные поля.
