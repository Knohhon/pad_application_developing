FROM python:3.12

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY . .

# Настройка миграций
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]