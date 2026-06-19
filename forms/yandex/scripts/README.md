# Скрипты для Яндекс.Форм

Эта папка содержит Python-скрипты для проверки JSON-заготовки формы, загрузки формы в Яндекс.Формы через API, публикации, выгрузки ответов и первичного подсчета баллов.

Команды ниже предполагают, что ты находишься в папке:

```bat
forms\yandex
```

На Windows можно запускать так:

```bat
python scripts\validate_definition.py form_definition\vkr_main_form.json
```

Если используется виртуальное окружение в `.venv`, то так:

```bat
.venv\Scripts\python.exe scripts\validate_definition.py form_definition\vkr_main_form.json
```

На Linux / macOS можно запускать так:

```bash
python scripts/validate_definition.py form_definition/vkr_main_form.json
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

Если есть ошибки, скрипт выведет список проблем и завершится с кодом `1`.

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

Файл `exports/form_mapping.json` нужен для связи локальных кодов вопросов с вопросами, созданными в Яндекс.Формах. Его полезно сохранить рядом с выгрузками.

Перед реальной публикацией нужно вручную открыть форму в интерфейсе Яндекс.Форм и проверить страницы, обязательность вопросов, тексты шкал и отсутствие `TODO`.

## `publish_form.py`

Публикует или снимает с публикации уже созданную форму.

Что делает:

- принимает `survey_id` формы;
- выполняет действие `publish` или `unpublish`;
- отправляет соответствующий запрос в API.

Требует заполненный `.env`.

Опубликовать форму:

```bat
python scripts\publish_form.py <survey_id> publish
```

Снять форму с публикации:

```bat
python scripts\publish_form.py <survey_id> unpublish
```

Где `<survey_id>` - идентификатор формы. Его можно взять из вывода `create_form.py` или из файла `exports/form_mapping.json`.

## `export_answers.py`

Выгружает ответы из Яндекс.Форм.

Что делает:

- принимает `survey_id` формы;
- постранично забирает ответы через API;
- может сохранить полную выгрузку в JSON;
- может сохранить плоскую таблицу в CSV;
- если не указаны `--json` и `--csv`, печатает JSON в консоль.

Требует заполненный `.env`.

Выгрузить ответы в JSON и CSV:

```bat
python scripts\export_answers.py <survey_id> --json exports\answers.json --csv exports\answers.csv
```

Изменить размер страницы API-запроса:

```bat
python scripts\export_answers.py <survey_id> --page-size 50 --json exports\answers.json --csv exports\answers.csv
```

Вывести JSON прямо в консоль:

```bat
python scripts\export_answers.py <survey_id>
```

CSV сохраняется в кодировке `utf-8-sig`, чтобы его проще было открыть в Excel.

## `score_export_template.py`

Шаблон для подсчета баллов по CSV-выгрузке.

Что делает:

- читает CSV;
- считает `gse_total` по 10 пунктам GSE;
- считает `rses_total` по 10 пунктам RSES с учетом обратных пунктов;
- считает черновой `gav_total_raw_all_items` как сумму всех 51 пунктов Гавриловой;
- сохраняет новый CSV с добавленными колонками.

Этот скрипт не обращается к API и не требует `.env`.

Пример запуска:

```bat
python scripts\score_export_template.py exports\answers.csv exports\answers_scored.csv
```

Важное ограничение: скрипт ожидает, что колонки в CSV называются локальными кодами вопросов, например:

```text
gse_q01, rses_q01, gav_q01
```

После выгрузки из API Яндекс.Формы могут дать колонкам названия по текстам вопросов. В этом случае перед подсчетом нужно переименовать колонки по `exports/form_mapping.json` или доработать скрипт импорта.

Для методики Гавриловой сейчас заполнен только общий черновой подсчет по всем пунктам. Ключи по компонентам `goal`, `resource`, `phenomenological` нужно добавить после сверки с первоисточником.

## `yf_client.py`

Служебный модуль для работы с API Яндекс.Форм.

Что делает:

- читает переменные окружения из `.env`;
- собирает заголовки `Authorization` и заголовок организации;
- отправляет HTTP-запросы к API;
- предоставляет методы для создания формы, добавления вопросов, перемещения вопросов, публикации, снятия с публикации и выгрузки ответов.

Напрямую обычно не запускается. Его используют скрипты:

```text
create_form.py
publish_form.py
export_answers.py
```

## Типовой порядок работы

1. Заполнить `.env`.
2. Проверить JSON формы.
3. Создать форму как черновик.
4. Открыть форму в интерфейсе Яндекс.Форм и проверить вручную.
5. Опубликовать форму.
6. После сбора данных выгрузить ответы.
7. Подготовить CSV к подсчету и запустить шаблон подсчета.

Команды:

```bat
python scripts\validate_definition.py form_definition\vkr_main_form.json
python scripts\create_form.py form_definition\vkr_main_form.json --output exports\form_mapping.json
python scripts\publish_form.py <survey_id> publish
python scripts\export_answers.py <survey_id> --json exports\answers.json --csv exports\answers.csv
python scripts\score_export_template.py exports\answers.csv exports\answers_scored.csv
```
