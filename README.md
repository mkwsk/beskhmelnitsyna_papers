# Материалы ВКР Бесхмельницыной

Рабочий репозиторий для материалов магистерской ВКР по теме взаимосвязи самооценки с уровнем профессиональной самоактуализации женщин-предпринимателей.

Сейчас репозиторий содержит два основных блока:

- `methods/` - каталог психодиагностических методик, источники и решение по батарее;
- `forms/yandex/` - заготовка Яндекс.Формы и Python-скрипты для работы с API.

PowerShell-оберток в текущей версии нет. Скрипты управления формой написаны на Python.

## Структура репозитория

```text
.
├── methods/                 # карточки методик, каталог, источники
├── forms/
│   └── yandex/              # JSON формы и Python-скрипты для API Яндекс Форм
├── CHANGELOG.md             # история изменений
├── .gitignore               # исключения для Git
└── README.md                # этот файл
```

## Блок `methods/`

Основной вход в каталог: [`methods/README.md`](methods/README.md).

Полезные файлы:

- [`methods/00_index.md`](methods/00_index.md) - быстрый навигатор по методикам;
- [`methods/metodiki_vkr_katalog_full.md`](methods/metodiki_vkr_katalog_full.md) - полный объединенный каталог;
- [`methods/template.md`](methods/template.md) - шаблон карточки методики;
- [`methods/91_decision_for_supervisor.md`](methods/91_decision_for_supervisor.md) - краткое решение для согласования с куратором;
- [`methods/92_sources.md`](methods/92_sources.md) - список основных источников.

В каталоге есть как основные, так и резервные методики. Часть пунктов не хранится в репозитории полностью, если статус распространения методики неясен.

## Блок `forms/yandex/`

Основная инструкция: [`forms/yandex/README.md`](forms/yandex/README.md).

Главный файл формы: [`forms/yandex/form_definition/vkr_main_form.json`](forms/yandex/form_definition/vkr_main_form.json).

Секции формы лежат в [`forms/yandex/form_definition/sections/`](forms/yandex/form_definition/sections/). Резервные методики лежат в [`forms/yandex/form_definition/reserve/`](forms/yandex/form_definition/reserve/) и по умолчанию не входят в основную форму.

Python-скрипты лежат в [`forms/yandex/scripts/`](forms/yandex/scripts/):

- `validate_definition.py` - проверка JSON-определения формы;
- `create_form.py` - создание формы через API;
- `publish_form.py` - публикация и снятие с публикации;
- `export_answers.py` - выгрузка ответов;
- `score_export_template.py` - шаблон подсчета баллов по выгрузке.

## Быстрый запуск скриптов

Перейти в папку формы:

```bash
cd forms/yandex
```

Создать окружение и установить зависимости:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

На Windows в `cmd.exe`:

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

На Linux / macOS:

```bash
cp .env.example .env
```

Заполнить `.env` токеном и идентификатором организации. Подробная инструкция по переменным лежит в [`forms/yandex/docs/env_variables.md`](forms/yandex/docs/env_variables.md), краткие заметки по API - в [`forms/yandex/docs/yandex_forms_api_notes.md`](forms/yandex/docs/yandex_forms_api_notes.md).

Проверить JSON формы:

```bash
python scripts/validate_definition.py form_definition/vkr_main_form.json
```

Создать черновик формы:

```bash
python scripts/create_form.py form_definition/vkr_main_form.json --output exports/form_mapping.json
```

## Важные ограничения

1. В JSON-заготовке часть пунктов методик оставлена как `TODO`. Перед публикацией формы нужно вставить точные формулировки из выбранных первоисточников.
2. Перед реальным сбором данных нужно вручную проверить форму в интерфейсе Яндекс.Форм.
3. `.env`, выгрузки ответов и локальное виртуальное окружение не должны попадать в Git.
4. Встроенный/portable интерпретатор Python пока не добавлен в репозиторий. Текущие команды предполагают, что команда `python` уже доступна в среде запуска.
