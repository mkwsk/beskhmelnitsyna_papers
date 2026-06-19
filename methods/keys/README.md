# Ключи методик

Этот каталог хранит канонические ключи подсчета для карточек из `methods/*.md`.

Разделение такое:

- `methods/items/*_items.csv` - пункты и переменные формы;
- `methods/keys/*_keys.csv` - шкалы, направления подсчета и правила начисления баллов;
- поле `key_file` в каждой карточке должно ссылаться на файл из `methods/keys/`.

## Формат `*_keys.csv`

Основной формат ключей - одна строка на вычисляемую шкалу:

```csv
method_id,scale_code,scale_title,direct_items,reverse_items,keyed_items,response_format,reverse_min,reverse_max,normalize_multiplier,score_expression,scoring_status,source_note
```

- `direct_items` - номера прямых пунктов через пробел;
- `reverse_items` - номера обратных пунктов через пробел;
- `keyed_items` - пары вида `1B 11A` для forced-choice A/B;
- `reverse_min` и `reverse_max` - диапазон реверса для шкал Лайкерта;
- `normalize_multiplier` - множитель нормирования, если шкалы нужно привести к общему диапазону;
- `score_expression` - краткое текстовое правило расчета;
- `scoring_status` - `complete`, `needs_review` или `external_key_required`.

Для скриптов канонический ключ находится в `key_file`. Колонки с ключом в `items.csv` считаются устаревшими подсказками и не должны быть единственным источником подсчета.
