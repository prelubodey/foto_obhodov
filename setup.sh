#!/bin/bash

# Скрипт автоматической установки проекта foto_obhodov на NanoPi R3S

set -e

PROJECT_DIR="/root/projects/foto_obhodov"
REPO_URL="https://github.com/prelubodey/foto_obhodov.git"

echo "--- Настройка проекта foto_obhodov ---"

# 1. Создание директории и клонирование (если папки нет)
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Клонирование репозитория в $PROJECT_DIR..."
    mkdir -p /root/projects
    git clone $REPO_URL $PROJECT_DIR
else
    echo "Папка проекта уже существует. Обновление..."
    cd $PROJECT_DIR
    git pull origin main
fi

cd $PROJECT_DIR

# 2. Создание файла .env (если его нет)
if [ ! -f ".env" ]; then
    echo "--- Настройка уведомлений в Макс ---"
    read -p "Введите MAX_TOKEN: " max_token
    read -p "Введите MAX_CHAT_ID: " max_chat_id

    echo "MAX_TOKEN=$max_token" > .env
    echo "MAX_CHAT_ID=$max_chat_id" >> .env
    echo "Файл .env успешно создан."
else
    echo "Файл .env уже существует. Пропускаю настройку токенов."
fi

# 3. Проверка наличия модели
if [ ! -f "yolov8n.rknn" ]; then
    echo "⚠️ ВНИМАНИЕ: Файл модели yolov8n.rknn не найден в $PROJECT_DIR."
    echo "Пожалуйста, скопируйте файл модели в эту папку перед продолжением."
    # Можно добавить паузу или выйти
fi

# 4. Запуск Docker Compose
echo "Запуск Docker-контейнера..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d --build
elif docker compose version &> /dev/null; then
    docker compose up -d --build
else
    echo "❌ Ошибка: docker-compose не найден. Пожалуйста, установите docker."
    exit 1
fi

echo "✅ Установка завершена успешно!"
echo "Логи работы можно посмотреть командой: docker-compose logs -f"
