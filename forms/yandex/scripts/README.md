# Скрипты для Яндекс.Форм

Команды ниже выполняются из папки `forms/yandex`.

## Общая схема

1. Проверить нетестовую часть формы.
2. Скомпилировать методики из `methods/` в один JSON-бандл.
3. Проверить бандл.
4. Создать форму из бандла.
5. В редакторе Яндекс.Форм вручную включить обязательность для нужных вопросов.
6. После сбора ответов выгрузить результаты и посчитать шкалы по тому же бандлу.

## validate_definition.py

Проверяет `form_definition/vkr_main_form.json` или уже собранный `output/compiled_form_bundle.json`.

```bash
python scripts/validate_definition.py form_definition/vkr_main_form.json
python scripts/validate_definition.py output/compiled_form_bundle.json
```

## compile_form_json.py

Собирает нетестовую часть формы и методики из markdown/CSV архива в один JSON.

```bash
python scripts/compile_form_json.py --out output/compiled_form_bundle.json
```

Файл `form_definition/vkr_main_form.json` больше не содержит тестовые блоки. Какие методики включать, задается в `methods_manifest.json`.

## create_form.py

Создает форму из уже скомпилированного бандла.

```bash
python scripts/create_form.py output/compiled_form_bundle.json --output exports/form_mapping.json
```

С публикацией:

```bash
python scripts/create_form.py output/compiled_form_bundle.json --publish --output exports/form_mapping.json
```

Скрипт требует локальные настройки доступа к API в `.env`.

По умолчанию `create_form.py` добавляет в `survey_payload` параметры `access`, `access_type` и `visibility` со значением `public`. Итоговый `survey_payload` сохраняется в `exports/form_mapping.json`.

API Яндекс.Форм не позволяет надежно включить обязательность вопроса. Скрипт не выставляет этот флаг и не сохраняет список обязательных полей. После создания формы нужно вручную включить обязательность для нужных вопросов в редакторе Яндекс.Форм.

## export_research_results.py

Выгружает результаты исследования из Яндекс.Форм, сохраняет сырые ответы, нормализованную таблицу по кодам переменных и рассчитанные шкалы методик.

```bash
python scripts/export_research_results.py
```

По умолчанию скрипт берет `survey_id` из `exports/form_mapping.json`, структуру формы из `output/compiled_form_bundle.json`, а результаты сохраняет в `exports/research_results/`:

```text
answers_raw.json
answers_by_code.csv
codebook.csv
interpreted_results.csv
```

Можно указать форму явно:

```bash
python scripts/export_research_results.py --survey-id <survey_id> --out-dir exports/research_results
```

Если нужно только выгрузить ответы без подсчета шкал:

```bash
python scripts/export_research_results.py --survey-id <survey_id> --no-interpret
```

## export_answers.py

Выгружает ответы из формы в простом старом формате.

```bash
python scripts/export_answers.py <survey_id> --json exports/answers.json --csv exports/answers.csv
```

## interpret_results.py

Считает результаты по выгрузке ответов, используя ключи из `compiled_form_bundle.json`.

```bash
python scripts/interpret_results.py --bundle output/compiled_form_bundle.json --answers exports/answers.csv --out output/interpreted_results.csv
```

## Устаревший шаблон score_export_template.py

`score_export_template.py` оставлен как простой ручной шаблон. Для новой схемы лучше использовать `export_research_results.py`, потому что он сразу выгружает ответы и считает шкалы.
