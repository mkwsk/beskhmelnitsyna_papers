# Материалы ВКР Бесхмельницыной

Репозиторий приведен к более аккуратной структуре: каталог методик отделен от заготовки Яндекс.Форм и скриптов для работы с API.

## Структура

```text
.
├── methods/                 # карточки методик, источники и полный каталог
├── forms/
│   └── yandex/              # JSON-заготовка Яндекс.Форм и API-скрипты
├── CHANGELOG.md             # что было изменено при объединении
└── README.md                # этот файл
```

## Каталог методик

Основной вход в каталог: [`methods/README.md`](methods/README.md).

Ключевые файлы:

- [`methods/00_index.md`](methods/00_index.md) - быстрый навигатор по методикам;
- [`methods/metodiki_vkr_katalog_full.md`](methods/metodiki_vkr_katalog_full.md) - полный объединенный каталог;
- [`methods/template.md`](methods/template.md) - шаблон карточки методики;
- [`methods/91_decision_for_supervisor.md`](methods/91_decision_for_supervisor.md) - краткое решение для согласования с куратором;
- [`methods/92_sources.md`](methods/92_sources.md) - список основных источников.

## Заготовка Яндекс.Форм

Заготовка формы и скрипты API лежат в [`forms/yandex/`](forms/yandex/).

Главный файл формы: [`forms/yandex/form_definition/vkr_main_form.json`](forms/yandex/form_definition/vkr_main_form.json).

Проверка определения формы:

```bash
cd forms/yandex
python scripts/validate_definition.py form_definition/vkr_main_form.json
```

Установка зависимостей для работы с API:

```bash
cd forms/yandex
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Создание формы:

```bash
python scripts/create_form.py form_definition/vkr_main_form.json --output exports/form_mapping.json
```

## Важное ограничение

В JSON-заготовке пунктов методик часть формулировок оставлена как `TODO`. Перед реальной публикацией формы нужно вставить точные формулировки из выбранных первоисточников и проверить правовой статус использования материалов.
