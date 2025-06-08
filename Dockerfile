# Базовий образ з Python 3.10
FROM python:3.10-slim

# Робоча директорія в контейнері
WORKDIR /app

# Копіюємо всі файли проєкту в контейнер
COPY . .

# Відкриваємо порти для HTTP (3000) і UDP (5000)
EXPOSE 3000
EXPOSE 5000/udp

# Запускаємо головний скрипт
CMD ["python", "main.py"]
