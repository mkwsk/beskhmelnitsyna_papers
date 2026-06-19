# Заготовка Яндекс.Форм для ВКР

Директория работает в два этапа.

1. `form_definition/vkr_main_form.json` хранит только нетестовую часть анкеты: приветствие, критерии участия, социально-демографические данные и финальную благодарность.
2. `scripts/compile_form_json.py` берет методики из `methods/` по списку `methods_manifest.json` и собирает один JSON-бандл.

Тесты больше не лежат в `form_definition`. Набор методик меняется через `methods_manifest.json`.

## Основные файлы

```text
form_definition/vkr_main_form.json
methods_manifest.json
scripts/compile_form_json.py
scripts/create_form.py
scripts/interpret_results.py
output/
exports/
```

## Актуальная батарея

Сейчас подключены:

1. САМОАЛ.
2. GSE Шварцера-Ерусалема.
3. CSEs(Ru).
4. Шкала самооценки Розенберга.

## Быстрый запуск

Команды выполнять из `forms/yandex`.

```bash
python scripts/validate_definition.py form_definition/vkr_main_form.json
python scripts/compile_form_json.py --out output/compiled_form_bundle.json
python scripts/validate_definition.py output/compiled_form_bundle.json
```

## Создание формы

```bash
python scripts/create_form.py output/compiled_form_bundle.json --output exports/form_mapping.json
```

С публикацией:

```bash
python scripts/create_form.py output/compiled_form_bundle.json --publish --output exports/form_mapping.json
```

Для обращения к API нужен локальный `.env`. Подробности лежат в `docs/env_variables.md`.

## Подсчет результатов

```bash
python scripts/interpret_results.py --bundle output/compiled_form_bundle.json --answers exports/answers.csv --out output/interpreted_results.csv
```

## Ограничения

- `compiled_form_bundle.json` является локальным описанием формы. Скрипт создает форму и добавляет вопросы последовательно.
- Если в `methods/items/*.csv` нет полного текста пункта, компилятор создаст предупреждение.
- Перед публикацией нужно вручную проверить форму в интерфейсе Яндекс.Форм.
