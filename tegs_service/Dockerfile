# Используем базовый образ Python
FROM python:3.11

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /tags_service

# Копируем файл с зависимостями в контейнер
COPY ./requirements.txt /tags_service/requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir --upgrade -r /tags_service/requirements.txt

# Копируем файлы приложения в контейнер
COPY ./app /tags_service/app

# Указываем команду, которая будет запускать сервер приложения при запуске контейнера
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]