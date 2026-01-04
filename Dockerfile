FROM python:3.11-slim

# Установка локали
RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/*
RUN locale-gen ru_RU.UTF-8
ENV LANG=ru_RU.UTF-8
ENV LC_ALL=ru_RU.UTF-8

# Установка системных зависимостей для LDAP и PostgreSQL
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libldap2-dev \
    libsasl2-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем локальные пакеты
#COPY offline_packages /app/offline_packages

# Устанавливаем зависимости из локального источника
COPY requirements.txt .

# Устанавливаем зависимости *из интернета* (временно)
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .

# Указываем команду запуска
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]