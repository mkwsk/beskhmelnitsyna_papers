# Яндекс.Формы для ВКР

Эта директория отвечает за полный цикл работы с анкетой в Яндекс.Формах:

1. хранение нетестовой части формы;
2. подключение активных методик из каталога `methods/`;
3. сборку единого JSON-бандла;
4. создание формы через API;
5. выгрузку ответов;
6. интерпретацию ответов по ключам методик и подготовку таблицы для статистики.

Команды ниже выполнять из каталога `forms/yandex`.

## Что где лежит

```text
forms/yandex/
├── form_definition/
│   └── vkr_main_form.json        # приветствие, информация, социологические вопросы, благодарность
├── methods_manifest.json         # какие методики добавить в форму
├── scripts/
│   ├── compile_form_json.py       # сборка полного бандла
│   ├── validate_definition.py     # проверка исходной формы и бандла
│   ├── create_form.py             # создание формы через API
│   ├── publish_form.py            # публикация/снятие с публикации
│   ├── export_research_results.py # выгрузка ответов и расчет шкал
│   ├── interpret_results.py       # расчет шкал по уже выгруженной таблице
│   └── yf_client.py               # общий клиент API
├── docs/
├── exports/                       # локальные выгрузки, не коммитить
└── output/                        # собранные бандлы и таблицы, не коммитить
```

Старые ручные JSON-секции методик больше не используются. Форма собирается только из `vkr_main_form.json`, `methods_manifest.json` и файлов каталога `../../methods/`.

## Актуальная батарея

Сейчас в `methods_manifest.json` подключены:

1. `samoal_lazukin_kalina` - САМОАЛ.
2. `gse_schwarzer_jerusalem_ru` - шкала общей самоэффективности.
3. `core_self_evaluation_scale_ru` - CSEs(Ru).
4. `rosenberg_self_esteem_scale_ru` - шкала самооценки Розенберга.

Чтобы изменить батарею, править только `methods_manifest.json` и карточки/CSV в `../../methods/`. Не нужно вручную добавлять тесты в `form_definition/vkr_main_form.json`.

## Подготовка окружения

Linux/macOS:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Windows cmd.exe:

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

В `.env` должны быть токен и ID организации. Подробно: `docs/env_variables.md`.

## Полный пайплайн

### 1. Проверить нетестовую часть формы

```bash
python scripts/validate_definition.py form_definition/vkr_main_form.json
```

Этот файл содержит только приветствие, информацию об исследовании, социально-демографический блок и благодарность. Тестовые методики в этот JSON не добавлять.

### 2. Собрать полный бандл

```bash
python scripts/compile_form_json.py --out output/compiled_form_bundle.json
```

Компилятор читает `vkr_main_form.json`, `methods_manifest.json`, карточки методик, пункты и ключи. Он не должен вставлять в форму декоративные разделители и placeholder-тексты. Если в активной методике нет текста пункта или варианта ответа, сборка должна остановиться с ошибкой.

### 3. Проверить собранный бандл

```bash
python scripts/validate_definition.py output/compiled_form_bundle.json
```

Проверяются наличие вопросов, уникальность кодов, заполненность подписей, заполненность вариантов ответов и отсутствие `TODO`.

### 4. Создать форму

Черновик:

```bash
python scripts/create_form.py output/compiled_form_bundle.json --output exports/form_mapping.json
```

Сразу создать и опубликовать:

```bash
python scripts/create_form.py output/compiled_form_bundle.json --publish --output exports/form_mapping.json
```

`create_form.py` по умолчанию добавляет публичный доступ: `access = public`, `access_type = public`, `visibility = public`.

После создания формы будет сохранен `exports/form_mapping.json`. Этот файл нужен для сопоставления колонок выгрузки с локальными переменными.

### 5. Вручную проверить форму

После создания формы открыть ее в редакторе Яндекс.Форм и проверить:

- порядок страниц;
- тексты;
- все варианты ответов;
- отсутствие пустых пунктов;
- отсутствие `TODO`;
- публичный доступ;
- отправку тестового ответа.

Отдельно включить обязательность вопросов вручную. Через API этот флаг надежно не выставляется, поэтому скрипты его не отправляют и не проверяют.

### 6. Управлять публикацией

```bash
python scripts/publish_form.py <survey_id> publish
python scripts/publish_form.py <survey_id> unpublish
```

При обычном сценарии удобнее использовать `create_form.py --publish`.

### 7. Выгрузить ответы и сразу посчитать шкалы

```bash
python scripts/export_research_results.py
```

По умолчанию скрипт берет `survey_id` из `exports/form_mapping.json`, структуру формы из `output/compiled_form_bundle.json`, выгружает ответы через API, нормализует колонки до локальных кодов и считает шкалы по ключам из бандла.

Эта команда уже делает полный расчет. После нее отдельно запускать `interpret_results.py` обычно не нужно.

Результаты сохраняются в `exports/research_results/`:

```text
answers_raw.json
answers_by_code.csv
codebook.csv
interpreted_results.csv
stat_dataset.csv
scoring_report.json
```

`interpreted_results.csv` содержит сырые ответы и рассчитанные шкалы. `stat_dataset.csv` удобнее для дальнейшей статистики: из него убраны сырые ответы на пункты методик, но оставлены социально-демографические поля и рассчитанные показатели.

### 8. Повторно посчитать шкалы по уже нормализованной CSV

Этот шаг нужен только если нужно пересчитать шкалы без повторной выгрузки из API:

```bash
python scripts/interpret_results.py \
  --bundle output/compiled_form_bundle.json \
  --answers exports/research_results/answers_by_code.csv \
  --out output/stat_dataset.csv \
  --scores-only
```

### 9. Посчитать шкалы по ручной CSV-выгрузке

Если CSV выгружен вручную из интерфейса Яндекс.Форм и колонки не совпадают с локальными кодами, положить файл в `exports/`, например `exports/yandex_manual_export.csv`, и добавить mapping:

```bash
python scripts/interpret_results.py \
  --bundle output/compiled_form_bundle.json \
  --mapping exports/form_mapping.json \
  --answers exports/yandex_manual_export.csv \
  --out output/interpreted_results.csv \
  --report output/scoring_report.json
```

Для статистической базы без сырых пунктов методик:

```bash
python scripts/interpret_results.py \
  --bundle output/compiled_form_bundle.json \
  --mapping exports/form_mapping.json \
  --answers exports/yandex_manual_export.csv \
  --out output/stat_dataset.csv \
  --scores-only
```

`exports/yandex_manual_export.csv` - это пример имени файла. Его нужно заменить на реальное имя ручной выгрузки.

## Какие шкалы появляются в таблице

Для текущего манифеста ожидаются, например:

```text
samoal_time
samoal_values
samoal_human_nature
samoal_cognition
samoal_creativity
samoal_autonomy
samoal_spontaneity
samoal_self_understanding
samoal_autosympathy
samoal_contact
samoal_communication_flexibility
gse_total
cse_positive
cse_negative
cse_total
rses_total
```

Для каждой шкалы дополнительно могут быть технические поля:

```text
*_raw
*_percent
*_answered_count
*_complete
```

Они нужны для контроля полноты заполнения и диагностики проблем выгрузки.

## Частые ошибки

### В форме появился TODO

Значит, в активной карточке или CSV методики остался placeholder. Исправить исходник в `../../methods/`, затем заново собрать бандл.

### Скрипт не находит survey_id

Проверить, что существует `exports/form_mapping.json`, или передать ID явно:

```bash
python scripts/export_research_results.py --survey-id <survey_id>
```

### В статистической таблице пустые шкалы

Проверить:

- совпадают ли колонки с локальными кодами;
- передан ли `--mapping` для ручной выгрузки;
- есть ли ключи в `methods/keys/*_keys.csv`;
- нет ли пропусков в `scoring_report.json`.

### Форма не требует обязательных ответов

Это ожидаемо после API-создания. Обязательность нужно включить вручную в редакторе Яндекс.Форм.
