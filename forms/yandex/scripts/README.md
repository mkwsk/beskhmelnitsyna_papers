# Скрипты для Яндекс.Форм

Все команды выполняются из папки `forms/yandex`.

Главная логика:

```text
vkr_main_form.json + methods_manifest.json + methods/*.md + items/*.csv + keys/*.csv
        -> compile_form_json.py
        -> output/compiled_form_bundle.json
        -> validate_definition.py
        -> create_form.py
        -> exports/form_mapping.json
        -> ручная проверка формы
        -> export_research_results.py
        -> exports/research_results/stat_dataset.csv
```

## Скрипты текущего пайплайна

### `validate_definition.py`

Проверяет исходный JSON формы или уже собранный бандл.

```bash
python scripts/validate_definition.py form_definition/vkr_main_form.json
python scripts/validate_definition.py output/compiled_form_bundle.json
```

Проверяет неизвестную схему, пустые вопросы, дубли кодов, пустые подписи, пустые варианты ответов и placeholder-тексты вроде `TODO`.

### `compile_form_json.py`

Собирает полный бандл формы.

```bash
python scripts/compile_form_json.py --out output/compiled_form_bundle.json
```

Входы:

```text
form_definition/vkr_main_form.json
methods_manifest.json
../../methods/*.md
../../methods/items/*.csv
../../methods/keys/*.csv
```

Выход:

```text
output/compiled_form_bundle.json
```

Важное поведение:

- не берет старые JSON-секции из `form_definition/sections`;
- не добавляет декоративные разделители;
- не пропускает placeholder-тексты в итоговую форму;
- для forced-choice методик использует варианты `text_a` и `text_b`;
- для шкал Лайкерта требует текст пункта в `text`.

### `create_form.py`

Создает форму в Яндекс.Формах из собранного бандла.

```bash
python scripts/create_form.py output/compiled_form_bundle.json --output exports/form_mapping.json
```

Создать и сразу опубликовать:

```bash
python scripts/create_form.py output/compiled_form_bundle.json --publish --output exports/form_mapping.json
```

Выход:

```text
exports/form_mapping.json
```

Этот файл хранит `survey_id`, payload формы, список созданных вопросов и связь локального кода вопроса с ID вопроса в Яндекс.Формах.

`create_form.py` не выставляет обязательность вопросов. Это нужно сделать вручную в интерфейсе Яндекс.Форм.

### `publish_form.py`

Управляет публикацией уже созданной формы.

```bash
python scripts/publish_form.py <survey_id> publish
python scripts/publish_form.py <survey_id> unpublish
```

Обычно можно обойтись `create_form.py --publish`.

### `export_research_results.py`

Главный скрипт после сбора данных. Выгружает ответы через API, нормализует колонки и считает шкалы.

```bash
python scripts/export_research_results.py
```

Эта команда уже делает полный расчет. После нее отдельно запускать `interpret_results.py` обычно не нужно.

Можно указать ID формы явно:

```bash
python scripts/export_research_results.py --survey-id <survey_id> --out-dir exports/research_results
```

Если нужно только выгрузить ответы без подсчета шкал:

```bash
python scripts/export_research_results.py --survey-id <survey_id> --no-interpret
```

Выходы в `exports/research_results/`:

```text
answers_raw.json
answers_by_code.csv
codebook.csv
interpreted_results.csv
stat_dataset.csv
scoring_report.json
```

### `export_answer_report_md.py`

Скачивает один ответ по ID и формирует Markdown-отчет.

В отчет входят:

- социологические данные;
- вычисленные баллы по каждой шкале с краткой интерпретацией;
- сырые ответы по всем полям.

```bash
python scripts/export_answer_report_md.py --answer-id <answer_id>
```

Можно явно указать ID формы и путь для Markdown-файла:

```bash
python scripts/export_answer_report_md.py \
  --survey-id <survey_id> \
  --answer-id <answer_id> \
  --out exports/research_results/answer_reports/answer_<answer_id>.md
```

По умолчанию скрипт берет `survey_id` из `exports/form_mapping.json`, бандл из `output/compiled_form_bundle.json`, а результат сохраняет в `exports/research_results/answer_reports/answer_<answer_id>.md`.

### `interpret_results.py`

Считает шкалы по уже имеющейся таблице ответов.

Если `export_research_results.py` уже был запущен, для статистики обычно достаточно файла:

```text
exports/research_results/stat_dataset.csv
```

Повторный расчет по нормализованной CSV-таблице:

```bash
python scripts/interpret_results.py \
  --bundle output/compiled_form_bundle.json \
  --answers exports/research_results/answers_by_code.csv \
  --out output/stat_dataset.csv \
  --scores-only
```

Ручная выгрузка из интерфейса Яндекс.Форм:

```bash
python scripts/interpret_results.py \
  --bundle output/compiled_form_bundle.json \
  --mapping exports/form_mapping.json \
  --answers exports/yandex_manual_export.csv \
  --out output/interpreted_results.csv \
  --report output/scoring_report.json
```

Только база для статистики, без сырых пунктов методик:

```bash
python scripts/interpret_results.py \
  --bundle output/compiled_form_bundle.json \
  --mapping exports/form_mapping.json \
  --answers exports/yandex_manual_export.csv \
  --out output/stat_dataset.csv \
  --scores-only
```

`exports/yandex_manual_export.csv` - пример имени файла. Его нужно заменить на реальное имя ручной выгрузки. Если такого файла нет, команда закономерно завершится ошибкой `Answers file not found`.

Полезные флаги:

```text
--mapping       сопоставить ручную выгрузку с локальными кодами
--report        сохранить JSON-отчет о подсчете
--scores-only   убрать сырые пункты методик
--long-names    оставить полные префиксы method_id в колонках
```

### `yf_client.py`

Внутренний клиент API. Отдельно запускать не нужно.

Использует переменные окружения:

```text
FORMS_TOKEN
ORG_ID
ORG_HEADER
AUTH_SCHEME
FORMS_PUBLIC_API
```

Подробности в `../docs/env_variables.md`.

## Удаленные устаревшие скрипты

Из рабочего пайплайна убраны старые ручные заготовки:

```text
export_answers.py
score_export_template.py
score_responses.py
```

Их заменяют:

```text
export_research_results.py
interpret_results.py
export_answer_report_md.py
```

## Проверка перед созданием формы

Минимальный набор команд:

```bash
python scripts/validate_definition.py form_definition/vkr_main_form.json
python scripts/compile_form_json.py --out output/compiled_form_bundle.json
python scripts/validate_definition.py output/compiled_form_bundle.json
```

Если все три команды прошли успешно, можно создавать форму.

## Проверка после сбора данных

```bash
python scripts/export_research_results.py
```

После выполнения открыть:

```text
exports/research_results/scoring_report.json
exports/research_results/stat_dataset.csv
```

В `scoring_report.json` проверить, что шкальные колонки создались и нет массовых пропусков. `stat_dataset.csv` использовать для дальнейшей статистической обработки.
