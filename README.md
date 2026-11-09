# Products API — M4PyHunt

Учебный FastAPI-проект по лекциям в `lectures/`

## Запуск

Нужны Python 3.14+, uv и запущенный Docker Desktop с Linux-контейнерами.
Команды выполняются из корня проекта в PowerShell:

```powershell
uv sync
# Только при первом запуске, если .env ещё нет:
Copy-Item .env.example .env
docker compose up -d --wait postgres mongo
uv run alembic upgrade head
uv run alembic check
uv run uvicorn app.main:app --reload
```

Swagger UI: <http://127.0.0.1:8000/docs>. При `DEBUG=True` приложение создаёт
недостающих пользователей `admin` и `user` с паролями из `.env`. Для входа
используется `POST /auth/obtain_token`. При `DEBUG=False` bootstrap отключён.
Задайте собственный `SECRET_KEY` длиной не менее 64 символов и пароли в `.env`.

Локальный URL, общий для API и Alembic:

```text
postgresql+psycopg://products:products@127.0.0.1:5432/products
```

Учебные реквизиты PostgreSQL и MongoDB заданы в `compose.yaml`. Локальное API
подключается через `127.0.0.1`. Данные сохраняются в томах `postgres_data` и `mongo_data`.
`docker compose stop` и `docker compose down` сохраняют данные;
`docker compose down --volumes` удаляет их. Переменная окружения `DATABASE_URL`
имеет приоритет над `.env`. Перед запуском уберите старый SQLite URL из окружения.

## Расширенные характеристики L9

Основные данные товаров, `specs` и пользователи хранятся в PostgreSQL.
Расширенные характеристики хранятся в коллекции MongoDB `product_attributes`.
Добавьте в существующий `.env` (в `.env.example` значения уже есть):

```dotenv
MONGODB_URL=mongodb://mongo:mongo@127.0.0.1:27017/?authSource=admin
MONGODB_DATABASE=products
```

При запуске приложение проверяет соединение и создаёт уникальный индекс по
`product_id`: одному товару соответствует один документ. Alembic управляет SQL.

| Запрос | Доступ | Поведение |
| --- | --- | --- |
| `GET /products/{id}` и `GET /products` | Активный пользователь | SQL-поля и `attributes`; без документа — `attributes: null` |
| `PUT /products/{id}/attributes` | admin | Создаёт или полностью заменяет характеристики, ответ 200 |
| `PATCH /products/{id}/attributes` | admin | Меняет переданные ключи, сохраняя остальные; без документа — 404 |
| `DELETE /products/{id}/attributes` | admin | Удаляет документ, ответ 204; без документа — 404 |

Пример тела PUT/PATCH:

```json
{"attributes": {"layout": "ANSI", "switch": "brown", "wireless": false}}
```

Товар должен существовать в SQL. Принимаются 1–50 ключей за запрос: строчные
латинские буквы, цифры и `_`, первый символ — буква, длина до 40 символов.
Значения — строки до 200 символов, целые BSON int64, конечные числа и bool.
Вложенные объекты, списки, null и поля `weight_grams`, `color`, `tags` запрещены:
общие характеристики изменяются через SQL `specs`. PUT сохраняет id документа
и `created_at`; PUT/PATCH обновляют `updated_at`. SQL-запись возвращает прежний
`ProductRead`, без `attributes`.

Без `MONGODB_URL` приложение запускается, SQL-запись и `/health` работают,
а составные GET возвращают 503. Если URL задан, ошибка подключения или индекса
прерывает запуск. Потеря соединения во время запроса даёт 503; `attributes: null`
означает только отсутствие документа. `/health` проверяет SQL.

Общей транзакции между базами нет: SQL rollback не отменяет запись MongoDB.
Удаление SQL-товара автоматически не удаляет характеристики. Перед удалением
товара удаляйте его характеристики; при сбое между операциями атомарность
не гарантируется. Конфликт первых PUT повторяется как обновление; если документ
успели удалить перед повтором, API возвращает 409.

## Миграции L8

- `0001` создаёт `users`, `products`, уникальный индекс логина и FK автора товара.
- `0002` добавляет `stock_count`: nullable-колонка → заполнение старых строк нулями
  → `NOT NULL`. В API остаток неотрицательный, по умолчанию `0`.

Таблицы больше не создаются при старте приложения. Перед запуском API всегда
применяйте миграции к выбранной базе. После изменения моделей:

```powershell
uv run alembic revision --autogenerate -m "describe schema change"
# Проверить сгенерированные операции и обработку существующих данных.
uv run alembic upgrade head
uv run alembic current
uv run alembic check
```

Откат `uv run alembic downgrade -1` проверяйте на отдельной учебной базе:
откат `0002` удаляет значения остатков. Ревизии поддерживают и PostgreSQL,
и SQLite; для изменения ограничений SQLite используется batch-режим Alembic.

## Перенос существующих SQLite-данных

Выполняйте до первого запуска API на пустом PostgreSQL. Остановите API и сохраните
исходный файл. Если схема SQLite **точно соответствует 0001** (есть `users`,
`products`, `created_by_id`, ещё нет `stock_count`), можно работать с копией:

```powershell
Copy-Item products.db products.before-alembic.db
Copy-Item products.db products_migrations.db
$env:DATABASE_URL = "sqlite+pysqlite:///./products_migrations.db"
# Только для проверенной существующей схемы; на пустой базе нужен upgrade.
uv run alembic stamp 0001
uv run alembic upgrade head
uv run alembic check
Remove-Item Env:DATABASE_URL
docker compose up -d --wait postgres mongo
uv run alembic upgrade head
uv run python -m scripts.copy_sqlite_to_postgres --source-url "sqlite+pysqlite:///./products_migrations.db"
uv run uvicorn app.main:app --reload
```

Для другой исходной схемы нужен отдельный план перехода, описанный в L8.
Обе базы перед копированием должны быть на `0002`; таблицы назначения — пустыми.
Скрипт сохраняет ID, хеши паролей, JSON и связи, затем корректирует PostgreSQL
sequences, чтобы следующие INSERT получали новые ID. Копирование строк выполняется
одной транзакцией. Повторный запуск на непустой базе отклоняется.
Исходный SQLite-файл не изменяется скриптом копирования.

## Проверки

```powershell
docker compose up -d --wait mongo
uv run pytest -q
```

По умолчанию каждый тест получает отдельный временный SQLite-файл, подготовленный
миграциями, и отдельную Mongo-базу `test_<uuid>`, которая удаляется после теста.
MongoDB должна быть запущена; для другого сервера задайте `TEST_MONGODB_URL`
(по умолчанию используется локальный URL из примера выше). Тесты проверяют API,
валидацию и права, PUT/PATCH/DELETE характеристик, параллельные первые PUT,
уникальный индекс, отключение MongoDB, backfill заполненной SQL-базы, откат и
соответствие схемы моделям (`alembic check`). Проверка переноса в PostgreSQL пропускается.

Для запуска того же набора на PostgreSQL, включая проверку переноса и sequences:

```powershell
docker compose up -d --wait postgres mongo
$env:TEST_DATABASE_URL = "postgresql+psycopg://products:products@127.0.0.1:5432/products"
uv run pytest -q
Remove-Item Env:TEST_DATABASE_URL
```

Тесты создают уникальные временные схемы и удаляют их после выполнения; таблицы
приложения в `public` не затрагиваются. Тесты изоляции настроек дополнительно
используют две отдельные SQLite-базы.
