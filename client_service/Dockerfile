FROM node:14-alpine as build

WORKDIR /app

# Копируем файлы package.json и package-lock.json для установки зависимостей
COPY package.json package-lock.json ./

# Устанавливаем зависимости
RUN npm install

# Копируем остальные файлы проекта в контейнер
COPY . .

# Собираем React-приложение
RUN npm run build

# Используем образ nginx для создания production-образа
FROM nginx:alpine

# Копируем собранные файлы React-приложения из предыдущего этапа сборки
COPY --from=build /app/build /usr/share/nginx/html

# При необходимости, можно добавить дополнительные настройки для nginx, например, конфигурацию
# COPY nginx.conf /etc/nginx/nginx.conf

# Указываем порт, который будет прослушивать контейнер
EXPOSE 80

# Команда для запуска nginx в контейнере
CMD ["nginx", "-g", "daemon off;"]