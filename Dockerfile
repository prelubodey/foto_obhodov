# Используем официальный образ Python для aarch64 (NanoPi)
FROM python:3.9-slim

# Настройка часового пояса МСК
ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Установка системных зависимостей для OpenCV и работы с NPU
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    wget \
    python3-opencv \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- УСТАНОВКА RKNN-TOOLKIT-LITE2 ---
# Прямая загрузка через git-lfs на GitHub часто выдает 404 для wget.
# Попробуем загрузить файл из официального репозитория через другой путь (blob -> raw) или из стабильного зеркала.
# Актуальная ссылка на версию 2.3.0 из master ветки rknn-toolkit2
RUN wget https://github.com/airockchip/rknn-toolkit2/raw/refs/heads/master/rknn-toolkit-lite2/packages/rknn_toolkit_lite2-2.3.0-cp39-cp39-linux_aarch64.whl \
    && pip install rknn_toolkit_lite2-2.3.0-cp39-cp39-linux_aarch64.whl \
    && rm rknn_toolkit_lite2-2.3.0-cp39-cp39-linux_aarch64.whl

# Копируем исходный код проекта
COPY . .

# Команда запуска планировщика
CMD ["python", "scheduler.py"]
