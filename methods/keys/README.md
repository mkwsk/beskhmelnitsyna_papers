# Ключи методик

Этот каталог хранит канонические ключи подсчета для карточек из `methods/*.md`.

Разделение такое:

- `methods/items/*_items.csv` - пункты и переменные формы;
- `methods/keys/*_keys.csv` - шкалы, направления подсчета и правила начисления баллов;
- поле `key_file` в каждой карточке должно ссылаться на файл из `methods/keys/`.

## Формат `*_keys.csv`

```csv
method_id,scale_code,scale_title,item_number,item_code,variable,response_format,scoring_direction,keyed_value,score_if_match,reverse_min,reverse_max,weight,normalize_multiplier,scoring_status,source_note
```

`scoring_direction` принимает значения: `direct`, `reverse`, `keyed`, `derived`, `external_key_required`.

`scoring_status` принимает значения: `complete`, `complete_key_without_item_texts`, `external_key_required`.

Для скриптов канонический ключ находится в `key_file`. Колонки с ключом в `items.csv` считаются устаревшими подсказками и не должны быть единственным источником подсчета.
