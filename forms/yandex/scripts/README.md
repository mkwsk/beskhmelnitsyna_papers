# Скрипты для Яндекс.Форм

Команды ниже выполняются из папки `forms/yandex`.

## Общая схема

1. Проверить нетестовую часть формы.
2. Скомпилировать методики из `methods/` в один JSON-бандл.
3. Проверить бандл.
4. Создать форму из бандла.
5. После сбора ответов посчитать шкалы по тому же бандлу.

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

Для отвечаемых вопросов `required=yes` теперь передается в API в двух местах: как `required: true` и как `validation.required: true`. Это нужно, чтобы обязательные вопросы блокировали переход на следующий лист. Если API отклонит расширенное поле `validation.required`, скрипт автоматически повторит создание вопроса в старом режиме и напечатает предупреждение.

В `exports/form_mapping.json` для каждого вопроса сохраняются два признака: `required` и `strict_required`. Если у вопроса `required=true`, но `strict_required=false`, такую форму нужно проверить вручную перед рассылкой.

## export_answers.py

Выгружает ответы из формы.

```bash
python scripts/export_answers.py <survey_id> --json exports/answers.json --csv exports/answers.csv
```

## interpret_results.py

Считает результаты по выгрузке ответов, используя ключи из `compiled_form_bundle.json`.

```bash
python scripts/interpret_results.py --bundle output/compiled_form_bundle.json --answers exports/answers.csv --out output/interpreted_results.csv
```

## Устаревший шаблон score_export_template.py

`score_export_template.py` оставлен как простой ручной шаблон. Для новой схемы лучше использовать `interpret_results.py`, потому что он берет ключи из бандла.
