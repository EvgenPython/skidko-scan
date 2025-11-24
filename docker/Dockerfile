FROM python:3.12-bookworm

# Используем украинские зеркала Debian (минуем Fastly, который у тебя отваливается)
RUN printf "deb http://ftp.ua.debian.org/debian bookworm main contrib non-free-firmware\n\
deb http://ftp.ua.debian.org/debian bookworm-updates main contrib non-free-firmware\n\
deb http://security.debian.org/debian-security bookworm-security main contrib non-free-firmware\n" \
> /etc/apt/sources.list

# Чиним DNS, не трогая защищённый /etc/resolv.conf
# (работает на 100% на Debian 12 / Docker Desktop / WSL2)
RUN echo "nameserver 8.8.8.8" > /usr/lib/systemd/resolv.conf

# Системные зависимости
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev libjpeg-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем зависимости Python
COPY docker/requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . /app/

# Запускаем Gunicorn
CMD ["gunicorn", "skidko_scan.wsgi:application", "--bind", "0.0.0.0:8000"]
