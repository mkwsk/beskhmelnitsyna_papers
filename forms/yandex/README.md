# Заготовка Яндекс.Форм для ВКР

Папка содержит JSON-заготовку формы и Python-скрипты для работы с API Яндекс Форм.

Главная форма: `form_definition/vkr_main_form.json`.

Секции формы лежат отдельно в `form_definition/sections`:

- `00_welcome.json` - приветствие и информированное согласие;
- `01_screening.json` - критерии участия;
- `02_demographics.json` - социально-демографический блок;
- `10_gse_schwarzer_jerusalem_ru.json` - GSE;
- `20_rosenberg_self_esteem_scale_ru.json` - RSES;
- `30_gavrilova_professional_self_realization.json` - методика Гавриловой;
- `99_finish.json` - завершающий экран.

Резервные методики лежат в `form_definition/reserve` и по умолчанию не загружаются.

## Важное ограничение

Точные формулировки пунктов методик с неясным статусом распространения не внесены в JSON. Вместо них стоят TODO-плейсхолдеры. Перед реальной публикацией формы нужно заменить TODO на точные пункты из выбранных первоисточников и проверить правовой статус использования.

## Установка

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Заполни `.env`:

```text
FORMS_TOKEN=...
ORG_ID=...
ORG_HEADER=X-Org-Id
```

Для организации Yandex Cloud можно использовать:

```text
ORG_HEADER=X-Cloud-Org-Id
```

## Проверка заготовки

```bash
python scripts/validate_definition.py form_definition/vkr_main_form.json
```

## Создание формы через API

Черновик без публикации:

```bash
python scripts/create_form.py form_definition/vkr_main_form.json --output exports/form_mapping.json
```

С публикацией:

```bash
python scripts/create_form.py form_definition/vkr_main_form.json --publish --output exports/form_mapping.json
```

После загрузки обязательно открой форму в интерфейсе Яндекс.Форм и проверь:

1. порядок страниц;
2. обязательность вопросов;
3. ветвление для несогласия / неподходящих критериев;
4. отсутствие TODO-плейсхолдеров;
5. корректность текстов и шкал.

## Выгрузка ответов

```bash
python scripts/export_answers.py <survey_id> --json exports/answers.json --csv exports/answers.csv
```

## Публикация и снятие с публикации

```bash
python scripts/publish_form.py <survey_id> publish
python scripts/publish_form.py <survey_id> unpublish
```

## Структура JSON-секции

Каждая секция содержит массив `questions`. Для каждого вопроса есть:

- `qid` - локальный код переменной для базы;
- `payload` - то, что отправляется в API Яндекс Форм;
- `required` - локальная пометка для контроля, в API сейчас не отправляется;
- `scoring` - локальные правила подсчета, в API сейчас не отправляются.

Скрипт `create_form.py` отправляет в API только `payload`, чтобы не передать лишние поля.
