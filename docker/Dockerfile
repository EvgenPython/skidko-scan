FROM python:3.12-slim

# Устанавливаем зависимости системы
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev libjpeg-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY docker/requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . /app/

# Для web по умолчанию запускаем Gunicorn
CMD ["gunicorn", "skidko_scan.wsgi:application", "--bind", "0.0.0.0:8000"]
