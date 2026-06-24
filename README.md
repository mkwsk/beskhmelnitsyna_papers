# Материалы ВКР Бесхмельницыной

Рабочий репозиторий для материалов магистерской ВКР по теме взаимосвязи самооценки с уровнем профессиональной самоактуализации женщин-предпринимателей.

Репозиторий сейчас состоит из двух основных блоков:

- `methods/` - каталог методик, пункты, ключи и источники.
- `forms/yandex/` - нетестовая часть анкеты, сборка формы для Яндекс.Форм, загрузка через API и обработка ответов.

## Актуальная батарея формы

Методики не хранятся внутри `forms/yandex/form_definition/vkr_main_form.json`. Активный набор задается в `forms/yandex/methods_manifest.json`.

Сейчас в манифесте подключены:

1. САМОАЛ.
2. GSE Шварцера-Ерусалема.
3. CSEs(Ru).
4. Шкала самооценки Розенберга.

Главный JSON нетестовой части формы: [`forms/yandex/form_definition/vkr_main_form.json`](forms/yandex/form_definition/vkr_main_form.json).

## Как устроены данные методик

Под архивом тестов в этом репозитории понимается логический markdown/CSV-архив:

- карточки методик: `methods/*.md`;
- пункты методик: `methods/items/*_items.csv`;
- ключи подсчета: `methods/keys/*_keys.csv`;
- активное подключение к форме: `forms/yandex/methods_manifest.json`.

Канонический источник ключа для автоматического подсчета - поле `key_file` в карточке методики. Колонки в `items.csv` используются как описание пунктов и вспомогательная информация, но не должны заменять CSV-ключи.

## Структура репозитория

```text
.
├── methods/                 # карточки методик, пункты, ключи, источники
├── forms/
│   └── yandex/              # форма, API-скрипты, инструкции
├── CHANGELOG.md             # история изменений
├── .gitignore               # локальные файлы и выгрузки
└── README.md                # этот файл
```

## Полный пайплайн

Команды ниже выполняются из каталога `forms/yandex`.

### 1. Подготовить окружение

Linux/macOS:

```bash
cd forms/yandex
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Windows cmd.exe:

```bat
cd forms\yandex
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

После этого заполнить `.env`. Подробности: [`forms/yandex/docs/env_variables.md`](forms/yandex/docs/env_variables.md).

### 2. Проверить исходное описание формы

```bash
python scripts/validate_definition.py form_definition/vkr_main_form.json
```

### 3. Собрать полный JSON-бандл формы

```bash
python scripts/compile_form_json.py --out output/compiled_form_bundle.json
```

Бандл собирается из:

- `form_definition/vkr_main_form.json` - приветствие, информация об исследовании, социологические вопросы, благодарность;
- `methods_manifest.json` - список активных методик;
- `../../methods/*.md`, `../../methods/items/*.csv`, `../../methods/keys/*.csv` - карточки, пункты и ключи методик.

Компилятор больше не вставляет декоративные разделители и не пропускает `TODO` в итоговую форму. Если в активной методике не хватает текста пункта, сборка должна завершиться ошибкой.

### 4. Проверить собранный бандл

```bash
python scripts/validate_definition.py output/compiled_form_bundle.json
```

Валидатор проверяет дубли кодов, пустые подписи, пустые варианты ответов и следы placeholder-текста.

### 5. Создать форму в Яндекс.Формах

Черновик:

```bash
python scripts/create_form.py output/compiled_form_bundle.json --output exports/form_mapping.json
```

Сразу с публикацией:

```bash
python scripts/create_form.py output/compiled_form_bundle.json --publish --output exports/form_mapping.json
```

`exports/form_mapping.json` сохраняет соответствие между локальными кодами вопросов и ID вопросов в Яндекс.Формах. Этот файл нужен для нормализации выгрузки ответов.

Важно: API Яндекс.Форм не позволяет надежно выставлять флаг "Обязательный". После создания формы нужно вручную открыть редактор Яндекс.Форм и включить обязательность для нужных вопросов.

### 6. Ручная проверка перед сбором данных

В редакторе Яндекс.Форм проверить:

- порядок страниц;
- тексты приветствия, информации об исследовании и благодарности;
- все пункты методик;
- отсутствие `TODO`, пустых вопросов и декоративного мусора;
- обязательность вопросов;
- публичный доступ к форме;
- отправку тестового ответа.

### 7. Выгрузить ответы и посчитать шкалы

```bash
python scripts/export_research_results.py
```

По умолчанию скрипт берет `survey_id` из `exports/form_mapping.json`, выгружает ответы через API и сохраняет результаты в `exports/research_results/`.

Выходные файлы:

```text
answers_raw.json          # сырая выгрузка API
answers_by_code.csv       # ответы, переименованные в локальные коды переменных
codebook.csv              # соответствие колонок выгрузки и локальных переменных
interpreted_results.csv   # ответы плюс рассчитанные шкалы
stat_dataset.csv          # база для статистики без сырых пунктов методик
scoring_report.json       # контроль полноты и список рассчитанных шкал
```

### 8. Посчитать шкалы по ручной CSV-выгрузке

Если ответы выгружены не через API-скрипт, а вручную из интерфейса Яндекс.Форм:

```bash
python scripts/interpret_results.py \
  --bundle output/compiled_form_bundle.json \
  --mapping exports/form_mapping.json \
  --answers exports/manual_answers.csv \
  --out output/interpreted_results.csv \
  --report output/scoring_report.json
```

Для базы только под статистику:

```bash
python scripts/interpret_results.py \
  --bundle output/compiled_form_bundle.json \
  --mapping exports/form_mapping.json \
  --answers exports/manual_answers.csv \
  --out output/stat_dataset.csv \
  --scores-only
```

## Основные инструкции

- Методики: [`methods/README.md`](methods/README.md).
- Яндекс.Формы: [`forms/yandex/README.md`](forms/yandex/README.md).
- Скрипты Яндекс.Форм: [`forms/yandex/scripts/README.md`](forms/yandex/scripts/README.md).
- Переменные окружения: [`forms/yandex/docs/env_variables.md`](forms/yandex/docs/env_variables.md).
- Заметки по API: [`forms/yandex/docs/yandex_forms_api_notes.md`](forms/yandex/docs/yandex_forms_api_notes.md).

## Важные ограничения

1. `.env`, локальные выгрузки, `exports/`, `output/` и `.venv/` не должны попадать в Git.
2. Перед реальным сбором данных форму обязательно нужно проверить вручную в интерфейсе Яндекс.Форм.
3. Автоматический подсчет зависит от корректности `methods/keys/*_keys.csv`.
4. Если меняется батарея методик, сначала обновить `methods_manifest.json`, затем заново собрать бандл и создать новую форму.
