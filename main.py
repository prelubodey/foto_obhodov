import os
import time
import shutil
import logging
from pathlib import Path
from max_api import send_photo_to_max
from rknn_yolo import RKNNYoloDetector

# --- КОНФИГУРАЦИЯ ---
SOURCE_DIR = "/mnt/userdata/camera" # Путь к папке с фото
MODEL_PATH = "yolov8n.rknn"         # Путь к модели RKNN
CONFIDENCE = 0.5                     # Порог уверенности (0.0 - 1.0)
CHECK_INTERVAL = 10                  # Интервал проверки папки (секунды)
EXTENSIONS = {".jpg", ".jpeg", ".png"}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("camera_scanner.log"),
        logging.StreamHandler()
    ]
)

def download_model_if_missing():
    """Инструкция пользователю, если модель отсутствует."""
    if not os.path.exists(MODEL_PATH):
        logging.warning(f"Файл модели {MODEL_PATH} не найден!")
        logging.info("Пожалуйста, скачайте или сконвертируйте модель yolov8n в формат .rknn для RK3568.")
        # Можно добавить ссылку на репозиторий с готовыми моделями или скрипт скачивания
        return False
    return True

def process_camera_folder():
    """Основной цикл сканирования."""
    logging.info("Инициализация детектора NPU...")
    detector = RKNNYoloDetector(MODEL_PATH, conf_threshold=CONFIDENCE)
    
    logging.info(f"Начинаю мониторинг папки: {SOURCE_DIR}")
    
    try:
        while True:
            base_path = Path(SOURCE_DIR)
            if not base_path.exists():
                logging.error(f"Папка {SOURCE_DIR} не существует!")
                time.sleep(60)
                continue

            # Находим все изображения во всех подпапках
            all_images = [
                f for f in base_path.rglob("*") 
                if f.suffix.lower() in EXTENSIONS and f.is_file()
            ]

            if all_images:
                logging.info(f"Найдено новых файлов для проверки: {len(all_images)}")

                for img_path in sorted(all_images, key=lambda x: x.stat().st_mtime):
                    img_str_path = str(img_path)
                    logging.info(f"Проверка: {img_str_path}")
                    
                    try:
                        # Детекция человека на NPU
                        if detector.has_person(img_str_path):
                            logging.info(f"👤 ЧЕЛОВЕК ОБНАРУЖЕН! Отправка в Макс...")
                            # Отправляем фото
                            success = send_photo_to_max(img_str_path, text=f"Обнаружен человек! \nФайл: {img_path.name}")
                            
                        # В любом случае удаляем файл после обработки, 
                        # чтобы не проверять его повторно и очищать место
                        img_path.unlink()
                        logging.info(f"🗑️ Удален обработанный файл: {img_path.name}")
                        
                    except Exception as e:
                        logging.error(f"Ошибка при обработке {img_path.name}: {e}")

            # После обработки всех файлов проверяем пустые подпапки и удаляем их
            for folder in base_path.iterdir():
                if folder.is_dir() and not any(folder.iterdir()):
                    try:
                        folder.rmdir()
                        logging.info(f"🧹 Удалена пустая папка: {folder.name}")
                    except Exception as e:
                        logging.error(f"Не удалось удалить папку {folder}: {e}")

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        logging.info("Скрипт остановлен пользователем.")
    finally:
        detector.release()
        logging.info("Ресурсы NPU освобождены.")

if __name__ == "__main__":
    if download_model_if_missing():
        process_camera_folder()
    else:
        logging.error("Запуск невозможен без файла модели.")
