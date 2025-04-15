

# Архитектура 

## Описание сервисов

<img src="./media/newarchitecture.png"  style="max-width:512px;width:100%;max-height:512px;height:100%"/>

Ссылки:

- [Frontend](https://REDACTED/team-44/prod-frontend)
- [Backend](https://REDACTED/team-44/prod-backend)


| Сервис      | Описание                                                                                                      |
| ----------- | ------------------------------------------------------------------------------------------------------------- |
| Frontend    | Предоставляет интерфейс для `admin` панели, используя `API` от нашего `backend`, и для `Web Apps` нашего бота |
| TelegramBot | Является клиентской частью приложения. При помощи `Web Apps` предоставляет интерфейс бронирования коворкинга. |
| Backend     | Предоставляет `API` для нашего `frontend` и `webhooks` для `tg bot`                                           |


## Структура сервиса backend

| Папка      | Описание                                                     |
| ---------- | ------------------------------------------------------------ |
| `api`      | Описание и реализация `endpoint` для `API`                   |
| `bot`      | Реализация `tg` бота                                         |
| `utils`    | Вспомогательные структуры и скрипты                          |
| `infra`    | Подключение сторонних сервисов (например `s3`, `postgres`)   |
| `schemas`  | Схемы `pydantic` для структур и логических единиц приложения |
| `services` | Бизнес логика для каждой `feature`                           |


## Схема базы данных

![Схемв Базы данных](./media/База%20данных.png)


## API документация

`Swagger` доступен по ссылке: https://prod-team-44-6dleadsa.REDACTED/api/docs#/

Данные для тестирования админ панели:

| `login`  | `password`  |
| -------- | ----------- |
| admin1   | `qwerty123` |
| admin2   | `qwerty123` |
| admin3   | `qwerty123` |
| admin4   | `qwerty123` |
| admin5   | `qwerty123` |
| admin6   | `qwerty123` |
| admin7   | `qwerty123` |
| admin8   | `qwerty123` |
| admin9   | `qwerty123` |
| admin10  | `qwerty123` |

Чтобы протестировать клиентскую часть проекта, нужно зайти в tg бот:

<img src="./media/Ссылка%20на%20tg%20бота.png" width="256" height="256"/>

Для получения jwt токенов клиентов, введите команду `/get_jwt` в Телеграим бот.

## Tests

Тесты написаны при помощи `tavern`. Их найти можно в [./tests](./tests/README.md).

<img src="./media/Coverage.jpg"  style="max-width:512px;width:100%;max-height:512px;height:100%"/>


### Pipelines
В наших репозиториях для frontend и backend лежат файлы .gitlab-ci.yaml
которые запускают пайплайн для деплоя из репозитория [prod-dev](https://REDACTED/team-44/prod-dev)

Пайплайн на бекенд
https://REDACTED/team-44/prod-backend/-/blob/master/.gitlab-ci.yml

Пайплайн на фронтенд
https://REDACTED/team-44/prod-frontend/-/blob/master/.gitlab-ci.yml