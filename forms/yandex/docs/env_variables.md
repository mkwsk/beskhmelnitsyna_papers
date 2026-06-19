# Переменные `.env` для API Яндекс Форм

Этот файл объясняет, откуда брать значения для переменных из `forms/yandex/.env`:

```text
FORMS_TOKEN=
ORG_ID=
ORG_HEADER=X-Org-Id
AUTH_SCHEME=OAuth
FORMS_PUBLIC_API=https://api.forms.yandex.net/v1
```

Файл `.env` должен лежать в директории `forms/yandex/`. Его нужно создать из примера:

```bat
copy .env.example .env
```

На Linux / macOS:

```bash
cp .env.example .env
```

`.env` нельзя добавлять в Git, потому что внутри будет токен доступа.

## 1. FORMS_TOKEN

`FORMS_TOKEN` - это токен пользователя, от имени которого скрипты будут работать с API Яндекс Форм.

Есть два варианта токена:

1. OAuth-токен - основной вариант для Яндекс 360 для бизнеса и для Yandex Cloud Organization.
2. IAM-токен - вариант только для Yandex Cloud Organization.

Для обычного сценария лучше начинать с OAuth-токена.

### Как получить OAuth-токен

1. Открыть страницу Яндекс OAuth: `https://oauth.yandex.ru`.
2. Нажать `Создать`.
3. Выбрать вариант `Для доступа к API или отладки`.
4. Указать название приложения, например `vkr-yandex-forms-api`.
5. Указать почту для связи.
6. Добавить права доступа:
   - `forms:write` - изменение настроек форм, создание, удаление и редактирование;
   - `forms:read` - просмотр настроек форм и чтение данных.
7. Создать приложение.
8. Открыть созданное приложение и скопировать `ClientID`.
9. Сформировать ссылку:

```text
https://oauth.yandex.ru/authorize?response_type=token&client_id=<CLIENT_ID>
```

10. Перейти по ссылке под тем аккаунтом Яндекса, от имени которого будут создаваться и редактироваться формы.
11. Скопировать выданный OAuth-токен.

В `.env` записать только сам токен, без слова `OAuth`:

```text
FORMS_TOKEN=<OAUTH_TOKEN>
AUTH_SCHEME=OAuth
```

### Как получить IAM-токен

IAM-токен нужен только если формы работают через Yandex Cloud Organization и ты сознательно выбираешь авторизацию через IAM.

В этом случае:

```text
FORMS_TOKEN=<IAM_TOKEN>
AUTH_SCHEME=Bearer
ORG_HEADER=X-Cloud-Org-Id
```

Важно: IAM-токен живет ограниченное время. По документации Яндекса он действует не больше 12 часов, после чего API вернет `401 Unauthorized`. Для постоянной работы удобнее OAuth-токен.

Сервисный аккаунт Yandex Cloud для API Яндекс Форм использовать нельзя. Запросы должны выполняться от имени пользователя.

## 2. ORG_ID

`ORG_ID` - это идентификатор организации, к которой относится форма.

Где взять:

1. Открыть Яндекс Трекер: `https://tracker.yandex.ru`.
2. Перейти в `Администрирование`.
3. Открыть раздел `Организации`.
4. Скопировать значение поля `Идентификатор`.

В `.env` записать только само значение идентификатора:

```text
ORG_ID=<ORGANIZATION_ID>
```

Не нужно писать `X-Org-Id:` или `X-Cloud-Org-Id:` внутри `ORG_ID`.

## 3. ORG_HEADER

`ORG_HEADER` - это имя HTTP-заголовка, в котором скрипт отправляет `ORG_ID`.

Для организации Яндекс 360 для бизнеса:

```text
ORG_HEADER=X-Org-Id
```

Для Yandex Cloud Organization:

```text
ORG_HEADER=X-Cloud-Org-Id
```

Если сомневаешься, начни с:

```text
ORG_HEADER=X-Org-Id
```

Если API отвечает ошибкой по организации, проверь, не относится ли форма к Yandex Cloud Organization.

## 4. AUTH_SCHEME

`AUTH_SCHEME` - это первое слово в заголовке авторизации.

Для OAuth-токена:

```text
AUTH_SCHEME=OAuth
```

Скрипт соберет заголовок так:

```text
Authorization: OAuth <FORMS_TOKEN>
```

Для IAM-токена:

```text
AUTH_SCHEME=Bearer
```

Скрипт соберет заголовок так:

```text
Authorization: Bearer <FORMS_TOKEN>
```

## 5. FORMS_PUBLIC_API

`FORMS_PUBLIC_API` - базовый адрес API Яндекс Форм.

Обычно менять не нужно:

```text
FORMS_PUBLIC_API=https://api.forms.yandex.net/v1
```

Эта переменная нужна, чтобы скрипты не хранили адрес API внутри каждого файла жестко. Если Яндекс изменит адрес или появится тестовый контур, можно будет изменить только `.env`.

## 6. Готовые примеры `.env`

### Яндекс 360 для бизнеса, OAuth

```text
FORMS_TOKEN=<OAUTH_TOKEN>
ORG_ID=<YANDEX_360_ORG_ID>
ORG_HEADER=X-Org-Id
AUTH_SCHEME=OAuth
FORMS_PUBLIC_API=https://api.forms.yandex.net/v1
```

### Yandex Cloud Organization, OAuth

```text
FORMS_TOKEN=<OAUTH_TOKEN>
ORG_ID=<YANDEX_CLOUD_ORG_ID>
ORG_HEADER=X-Cloud-Org-Id
AUTH_SCHEME=OAuth
FORMS_PUBLIC_API=https://api.forms.yandex.net/v1
```

### Yandex Cloud Organization, IAM

```text
FORMS_TOKEN=<IAM_TOKEN>
ORG_ID=<YANDEX_CLOUD_ORG_ID>
ORG_HEADER=X-Cloud-Org-Id
AUTH_SCHEME=Bearer
FORMS_PUBLIC_API=https://api.forms.yandex.net/v1
```

## 7. Как проверить доступ без запуска наших скриптов

Для Яндекс 360 и OAuth в `cmd.exe`:

```bat
curl -X GET "https://api.forms.yandex.net/v1/users/me/" ^
  -H "Authorization: OAuth <FORMS_TOKEN>" ^
  -H "X-Org-Id: <ORG_ID>"
```

Для Yandex Cloud Organization и OAuth:

```bat
curl -X GET "https://api.forms.yandex.net/v1/users/me/" ^
  -H "Authorization: OAuth <FORMS_TOKEN>" ^
  -H "X-Cloud-Org-Id: <ORG_ID>"
```

Для Yandex Cloud Organization и IAM:

```bat
curl -X GET "https://api.forms.yandex.net/v1/users/me/" ^
  -H "Authorization: Bearer <FORMS_TOKEN>" ^
  -H "X-Cloud-Org-Id: <ORG_ID>"
```

Если ответ пришел без `401` и `403`, доступ в целом работает.

## 8. Типовые ошибки

### `401 Unauthorized`

Возможные причины:

- неверный токен;
- токен скопирован с пробелом или лишними символами;
- для OAuth в `AUTH_SCHEME` ошибочно указано `Bearer`;
- для IAM в `AUTH_SCHEME` ошибочно указано `OAuth`;
- IAM-токен истек.

### `403 Forbidden`

Возможные причины:

- у пользователя нет прав на работу с формами в организации;
- OAuth-приложению не добавлены права `forms:write` и `forms:read`;
- пользователь авторизовался не тем аккаунтом;
- форма находится в другой организации.

### Ошибка по организации

Проверить:

- правильно ли указан `ORG_ID`;
- выбран ли правильный `ORG_HEADER`;
- не перепутаны ли Яндекс 360 и Yandex Cloud Organization.

## 9. Как эти переменные использует проект

Скрипты читают переменные из `.env` через `python-dotenv`.

Клиент API собирает базовый адрес и заголовки так:

```python
base_url = FORMS_PUBLIC_API
headers = {
    "Authorization": f"{AUTH_SCHEME} {FORMS_TOKEN}",
    ORG_HEADER: ORG_ID,
}
```

То есть в `.env` нужно хранить части заголовков отдельно, а не готовые строки целиком.
