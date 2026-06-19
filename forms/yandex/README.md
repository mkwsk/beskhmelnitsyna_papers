# Заготовка Яндекс.Форм для ВКР

Директория работает в два этапа.

1. `form_definition/vkr_main_form.json` хранит только нетестовую часть анкеты: приветствие, критерии участия, социально-демографические данные и финальную благодарность.
2. `scripts/compile_form_json.py` берет методики из `methods/` по списку `methods_manifest.json` и собирает один JSON-бандл.

Тесты больше не лежат в `form_definition`. Набор методик меняется через `methods_manifest.json`.

Разделители между блоками компилируются как отдельные текстовые поля, а не добавляются в текст заголовков разделов. Так их проще двигать и править в интерфейсе Яндекс.Форм.

Пункты методик хранятся в `methods/items/*_items.csv`, ключи подсчета - в `methods/keys/*_keys.csv`. Скрипт обработки результатов использует именно ключи из `key_file`, поэтому forced-choice методики вроде САМОАЛ считаются по шкалам, а не как простая сумма вариантов ответа.

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

Для шкал Лайкерта используются прямые и обратные пункты из `direct_items` и `reverse_items`. Для forced-choice A/B используются пары из `keyed_items`, например `1B 11A`.

## Ограничения

- `compiled_form_bundle.json` является локальным описанием формы. Скрипт создает форму и добавляет вопросы последовательно.
- API Яндекс.Форм не позволяет надежно выставить флаг "Обязательный". После создания формы нужно вручную включить обязательность для нужных вопросов в редакторе Яндекс.Форм.
- Если в `methods/items/*.csv` нет полного текста пункта, компилятор создает предупреждение.
- Перед публикацией нужно вручную проверить форму в интерфейсе Яндекс.Форм.
