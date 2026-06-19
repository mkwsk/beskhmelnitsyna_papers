# Краткие заметки по API Яндекс Форм

Официальная база URL в примерах Яндекса:

```text
https://api.forms.yandex.net/v1
```

Основные методы, которые использует эта заготовка:

```text
POST /surveys/                                  - создать форму
POST /surveys/{survey_id}/questions/            - добавить вопрос
POST /surveys/{survey_id}/questions/{id}/move/  - переместить вопрос / создать страницу
POST /surveys/{survey_id}/publish/              - опубликовать форму
POST /surveys/{survey_id}/unpublish             - снять с публикации
GET  /surveys/{survey_id}/answers               - выгрузить ответы
```

Авторизация:

```text
Authorization: OAuth <token>
X-Org-Id: <org_id>
```

или для Yandex Cloud Organization:

```text
Authorization: Bearer <iam_token>
X-Cloud-Org-Id: <cloud_org_id>
```

В этой заготовке по умолчанию используется OAuth.
