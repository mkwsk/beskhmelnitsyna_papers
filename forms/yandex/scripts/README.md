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

После успешного запуска скрипт печатает идентификатор созданной формы:

```text
Created survey <survey_id>
Mapping saved to exports\form_mapping.json
```

Файл `exports/form_mapping.json` нужен для связи локальных кодов вопросов с вопросами, созданными в Яндекс.Формах. Его полезно сохранить рядом с выгрузками. В этом же файле хранится `survey_id` формы.

Перед реальной публикацией нужно вручную открыть форму в интерфейсе Яндекс.Форм и проверить страницы, обязательность вопросов, тексты шкал и отсутствие `TODO`.

## Где брать `survey_id`

`survey_id` - это идентификатор формы в API Яндекс.Форм. Он нужен для команд публикации, снятия с публикации и выгрузки ответов.

Основной способ - взять его из результата `create_form.py`.

При создании формы скрипт пишет в консоль строку вида:

```text
Created survey 12345678
```

В этом примере `12345678` и есть `survey_id`.

Второй способ - открыть файл `exports\form_mapping.json`, который создает `create_form.py`:

```bat
type exports\form_mapping.json
```

В начале файла будет поле:

```json
{
  "survey_id": "12345678",
  "published": false,
  "questions": []
}
```

Быстро вывести только `survey_id` можно так:

```bat
python -c "import json; print(json.load(open('exports/form_mapping.json', encoding='utf-8'))['survey_id'])"
```

Если форма была создана вручную в интерфейсе Яндекс.Форм, а не через `create_form.py`, идентификатор нужно взять из адресной строки редактора формы. Обычно это числовой или строковый идентификатор формы в URL. В интерфейсе Яндекса адрес может меняться, поэтому ориентир простой: нужен именно ID формы, который API подставляет в путь `/surveys/<survey_id>/...`.

Если файл `exports\form_mapping.json` потерян, но форма создавалась через скрипт, проще всего найти `survey_id` в консольном выводе запуска, в истории терминала или в URL формы в браузере. В текущем наборе скриптов отдельной команды для поиска уже созданных форм пока нет.

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

Где `<survey_id>` - идентификатор формы. Его можно взять из вывода `create_form.py`, из файла `exports/form_mapping.json` или из URL формы в интерфейсе Яндекс.Форм.

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
