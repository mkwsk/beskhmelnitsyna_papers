# Подсчет шкал по выгрузке ответов

Скрипт `forms/yandex/scripts/score_responses.py` превращает выгрузку ответов Яндекс.Форм в таблицу шкал, пригодную для статистической обработки.

Расчет идет не по вручную зашитым формулам, а по ключам из скомпилированного бандла `output/compiled_form_bundle.json`. Бандл собирается из карточек методик, файлов `methods/items/*_items.csv` и ключей `methods/keys/*_keys.csv`.

## Базовый порядок работы

Команды выполняются из каталога `forms/yandex`.

Сначала собрать бандл формы:

```bash
python scripts/compile_form_json.py --out output/compiled_form_bundle.json
```

Если ответы выгружены через `export_research_results.py`, они уже будут нормализованы по кодам переменных:

```bash
python scripts/export_research_results.py
python scripts/score_responses.py \
  --bundle output/compiled_form_bundle.json \
  --answers exports/research_results/answers_by_code.csv \
  --out output/scored_responses.csv \
  --report output/scoring_report.json
```

Если ответы выгружены вручную из интерфейса Яндекс.Форм и в колонках стоят идентификаторы или тексты вопросов, нужно передать mapping-файл, который создает `create_form.py`:

```bash
python scripts/score_responses.py \
  --bundle output/compiled_form_bundle.json \
  --mapping exports/form_mapping.json \
  --answers exports/answers.csv \
  --out output/scored_responses.csv \
  --report output/scoring_report.json
```

Для дальнейшей статистики можно убрать сырые ответы на пункты методик и оставить только метаданные, социально-демографические поля и рассчитанные шкалы:

```bash
python scripts/score_responses.py \
  --bundle output/compiled_form_bundle.json \
  --answers exports/research_results/answers_by_code.csv \
  --out output/stat_dataset.csv \
  --scores-only
```

## Что появляется в выходной таблице

Для САМОАЛ рассчитываются 11 шкал профиля. Для каждой шкалы добавляются сырой балл, нормированный балл и процент:

```text
samoal_time, samoal_time_raw, samoal_time_percent
samoal_values, samoal_values_raw, samoal_values_percent
samoal_human_nature, samoal_cognition, samoal_creativity
samoal_autonomy, samoal_spontaneity, samoal_self_understanding
samoal_autosympathy, samoal_contact, samoal_communication_flexibility
```

Общий показатель САМОАЛ специально не агрегируется автоматически, потому что в карточке методики зафиксировано: способ общего показателя нужно согласовать отдельно. Для статистической проверки сейчас безопаснее использовать профиль шкал.

Для остальных методик добавляются:

```text
gse_total
cse_positive
cse_negative
cse_total
rses_total
rses_total_0_3
```

Также добавляются технические поля контроля полноты: `*_answered`, `*_answered_count`, `*_complete`.

## Отчет

Файл `scoring_report.json` содержит:

- количество обработанных строк;
- список методик из бандла;
- список рассчитанных шкальных колонок;
- количество пропусков по каждой шкальной колонке.

Это нужно, чтобы быстро увидеть, не сломалась ли выгрузка из-за переименования колонок или неполного заполнения формы.
