FROM python:3.11

WORKDIR /app

# Копируем код вашего приложения
COPY . /app

# Копируем файлы зависимостей и устанавливаем их
COPY requirements.txt /app/

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

# Устанавливаем 'cryptography'
# который требуется для аутентификации с использованием методов 'sha256_password' или 'caching_sha2_password
# Для взаимоействия с BD MySql
RUN pip install cryptography

# Указываем команду запуска
CMD ["python", "main.py"]

