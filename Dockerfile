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
# Теперь устанавливаем локально из файла .whl, включенного в проект
COPY rknn_toolkit_lite2-2.3.2-cp39-cp39-manylinux_2_17_aarch64.manylinux2014_aarch64.whl .
RUN pip install rknn_toolkit_lite2-2.3.2-cp39-cp39-manylinux_2_17_aarch64.manylinux2014_aarch64.whl \
    && rm rknn_toolkit_lite2-2.3.2-cp39-cp39-manylinux_2_17_aarch64.manylinux2014_aarch64.whl

# Копируем исходный код проекта
COPY . .

# Команда запуска планировщика
CMD ["python", "scheduler.py"]
