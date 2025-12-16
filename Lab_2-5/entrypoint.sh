#!/bin/bash

# Ожидание готовности базы данных
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done

# Применение миграций
alembic upgrade head

# Запуск приложения
exec "$@"