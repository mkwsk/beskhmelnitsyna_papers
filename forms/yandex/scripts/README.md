# Скрипты для Яндекс.Форм

Эта папка содержит Python-скрипты для проверки JSON-заготовки формы, загрузки формы в Яндекс.Формы через API, публикации, выгрузки ответов и первичного подсчета баллов.

Команды ниже предполагают, что ты находишься в папке:

```bat
forms\yandex
```

## Перед запуском

Установить зависимости:

```bat
python -m pip install -r requirements.txt
```

Для скриптов, которые обращаются к API, нужен заполненный файл `.env` в папке `forms/yandex`:

```text
FORMS_TOKEN=...
ORG_ID=...
ORG_HEADER=X-Org-Id
AUTH_SCHEME=OAuth
FORMS_PUBLIC_API=https://api.forms.yandex.net/v1
```

Подробно про эти переменные написано в `../docs/env_variables.md`.

## `validate_definition.py`

Проверяет локальное JSON-описание формы перед загрузкой в API.

Что делает:

- читает основной файл `form_definition/vkr_main_form.json`;
- проверяет наличие `survey_payload` и списка `section_files`;
- проверяет, что все подключенные секции существуют;
- проверяет наличие массива `questions` в каждой секции;
- проверяет уникальность `qid`;
- проверяет, что у каждого вопроса есть `payload`, а в нем есть `type` и `label`;
- проверяет, что в `payload` нет неизвестных локальных полей, которые нельзя отправлять в API.

Этот скрипт не обращается к API и не требует `.env`.

Пример запуска:

```bat
python scripts\validate_definition.py form_definition\vkr_main_form.json
```

Ожидаемый результат:

```text
Definition looks OK
```

## `create_form.py`

Создает форму в Яндекс.Формах из локального JSON-описания.

Что делает:

- читает `form_definition/vkr_main_form.json`;
- читает все секции, перечисленные в `section_files`;
- создает новую форму через API;
- добавляет вопросы из секций;
- раскладывает вопросы по страницам;
- сохраняет файл сопоставления локальных `qid` и ID вопросов в Яндекс.Формах;
- при флаге `--publish` сразу публикует форму.

Требует заполненный `.env`.

Создать черновик формы:

```bat
python scripts\create_form.py form_definition\vkr_main_form.json --output exports\form_mapping.json
```

Создать форму и сразу опубликовать:

```bat
python scripts\create_form.py form_definition\vkr_main_form.json --publish --output exports\form_mapping.json
```

После успешного запуска скрипт печатает идентификатор созданной формы:

```text
Created survey <survey_id>
Mapping saved to exports\form_mapping.json
```

## Где брать `survey_id`

`survey_id` - это идентификатор формы в API Яндекс.Форм. Он нужен для команд публикации, снятия с публикации и выгрузки ответов.

Основной способ - взять его из результата `create_form.py`.

При создании формы скрипт пишет в консоль строку вида:

```text
Created survey 12345678
```

Второй способ - открыть файл `exports\form_mapping.json`, который создает `create_form.py`:

```bat
type exports\form_mapping.json
```

Быстро вывести только `survey_id` можно так:

```bat
python -c "import json; print(json.load(open('exports/form_mapping.json', encoding='utf-8'))['survey_id'])"
```

Если форма была создана вручную в интерфейсе Яндекс.Форм, идентификатор нужно взять из адресной строки редактора формы. Нужен именно ID формы, который API подставляет в путь `/surveys/<survey_id>/...`.

## `publish_form.py`

Публикует или снимает с публикации уже созданную форму.

Примеры:

```bat
python scripts\publish_form.py <survey_id> publish
python scripts\publish_form.py <survey_id> unpublish
```

Требует заполненный `.env`.

## `export_answers.py`

Выгружает ответы из Яндекс.Форм.

Что делает:

- принимает `survey_id` формы;
- постранично забирает ответы через API;
- может сохранить полную выгрузку в JSON;
- может сохранить плоскую таблицу в CSV;
- если не указаны `--json` и `--csv`, печатает JSON в консоль.

Пример:

```bat
python scripts\export_answers.py <survey_id> --json exports\answers.json --csv exports\answers.csv
```

Требует заполненный `.env`.

## `score_export_template.py`

Шаблон для подсчета баллов по CSV-выгрузке.

Что делает для актуальной батареи:

- считает `gse_total` по 10 пунктам GSE;
- считает `cse_positive`, `cse_negative` и `cse_total` по 10 пунктам CSEs(Ru);
- считает `rses_total` по 10 пунктам RSES с учетом обратных пунктов;
- добавляет `samoal_answered_count`;
- оставляет `samoal_total` пустым до переноса ключа САМОАЛ.

Этот скрипт не обращается к API и не требует `.env`.

Пример запуска:

```bat
python scripts\score_export_template.py exports\answers.csv exports\answers_scored.csv
```

Важное ограничение: скрипт ожидает, что колонки в CSV называются локальными кодами вопросов, например:

```text
samoal_q001, gse_q01, cse_q01, rses_q01
```

После выгрузки из API Яндекс.Формы могут дать колонкам названия по текстам вопросов. В этом случае перед подсчетом нужно переименовать колонки по `exports/form_mapping.json` или доработать скрипт импорта.

## `yf_client.py`

Служебный модуль для работы с API Яндекс.Форм.

Что делает:

- читает переменные окружения из `.env`;
- собирает заголовки `Authorization` и заголовок организации;
- отправляет HTTP-запросы к API;
- предоставляет методы для создания формы, добавления вопросов, перемещения вопросов, публикации, снятия с публикации и выгрузки ответов.

Напрямую обычно не запускается. Его используют `create_form.py`, `publish_form.py` и `export_answers.py`.

## Типовой порядок работы

1. Заполнить `.env`.
2. Проверить JSON формы.
3. Создать форму как черновик.
4. Сохранить `survey_id` из вывода команды или из `exports\form_mapping.json`.
5. Открыть форму в интерфейсе Яндекс.Форм и проверить вручную.
6. Опубликовать форму.
7. После сбора данных выгрузить ответы.
8. Подготовить CSV к подсчету и запустить шаблон подсчета.

Команды:

```bat
python scripts\validate_definition.py form_definition\vkr_main_form.json
python scripts\create_form.py form_definition\vkr_main_form.json --output exports\form_mapping.json
python scripts\publish_form.py <survey_id> publish
python scripts\export_answers.py <survey_id> --json exports\answers.json --csv exports\answers.csv
python scripts\score_export_template.py exports\answers.csv exports\answers_scored.csv
```
