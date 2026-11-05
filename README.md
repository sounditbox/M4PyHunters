# Products API — M4PyHunt

Учебный FastAPI-проект по лекциям в `lectures/`. После L8 основная база —
PostgreSQL в Docker Compose, схема управляется Alembic. Python и API запускаются
локально через uv; контейнер API не требуется.

## Запуск

Нужны Python 3.14+, uv и запущенный Docker Desktop с Linux-контейнерами.
Команды выполняются из корня проекта в PowerShell:

```powershell
uv sync
# Только при первом запуске, если .env ещё нет:
Copy-Item .env.example .env
docker compose up -d --wait postgres
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

Учебные реквизиты PostgreSQL заданы в `compose.yaml`. Порт доступен только на
`127.0.0.1`. Данные сохраняются в named volume `postgres_data`.
`docker compose stop` и `docker compose down` сохраняют данные;
`docker compose down --volumes` удаляет их. Переменная окружения `DATABASE_URL`
имеет приоритет над `.env`. Перед запуском уберите старый SQLite URL из окружения.

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
docker compose up -d --wait postgres
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
uv run pytest -q
```

По умолчанию каждый тест получает отдельный временный SQLite-файл, подготовленный
миграциями. Тесты проверяют API, backfill заполненной базы, откат и соответствие
схемы моделям (`alembic check`). Проверка переноса в PostgreSQL пропускается.

Для запуска того же набора на PostgreSQL, включая проверку переноса и sequences:

```powershell
docker compose up -d --wait postgres
$env:TEST_DATABASE_URL = "postgresql+psycopg://products:products@127.0.0.1:5432/products"
uv run pytest -q
Remove-Item Env:TEST_DATABASE_URL
```

Тесты создают уникальные временные схемы и удаляют их после выполнения; таблицы
приложения в `public` не затрагиваются. Тесты изоляции настроек дополнительно
используют две отдельные SQLite-базы.
