import os
import time
import shutil
import logging
from pathlib import Path
from max_api import upload_photo_to_max, send_album_to_max
from ultralytics import YOLO

# --- КОНФИГУРАЦИЯ ---
SOURCE_DIR = "/mnt/userdata/camera" # Путь к папке с фото (монтируется в Docker)
MODEL_NAME = "yolov8n.pt"           # Модель YOLO (Nano, скачивается автоматически)
CONFIDENCE = 0.5                     # Порог уверенности (0.0 - 1.0)
EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALBUM_SIZE = 10                      # Максимальное количество фото в одном сообщении

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("camera_scanner.log"),
        logging.StreamHandler()
    ]
)

def run_once():
    """Разовый запуск сканирования с групповой отправкой фото."""
    logging.info(f"Загрузка модели {MODEL_NAME}...")
    try:
        model = YOLO(MODEL_NAME)
    except Exception as e:
        logging.error(f"Ошибка при загрузке модели: {e}")
        return

    logging.info(f"Начинаю сканирование папки: {SOURCE_DIR}")
    
    found_photos_tokens = [] # Здесь будем копить токены загруженных фото
    
    try:
        base_path = Path(SOURCE_DIR)
        if not base_path.exists():
            logging.error(f"Папка {SOURCE_DIR} не существует!")
            return

        # Находим все изображения во всех подпапках
        all_images = [
            f for f in base_path.rglob("*") 
            if f.suffix.lower() in EXTENSIONS and f.is_file()
        ]

        if all_images:
            logging.info(f"Найдено новых файлов для проверки: {len(all_images)}")

            for img_path in sorted(all_images, key=lambda x: x.stat().st_mtime):
                img_str_path = str(img_path)
                
                try:
                    # Детекция человека (класс 0)
                    results = model(img_str_path, conf=CONFIDENCE, verbose=False)
                    is_person = any(0 in r.boxes.cls for r in results)

                    if is_person:
                        logging.info(f"👤 ЧЕЛОВЕК ОБНАРУЖЕН: {img_path.name}. Загрузка на сервер...")
                        
                        # Загружаем фото и получаем токены
                        upload_res = upload_photo_to_max(img_str_path)
                        if upload_res:
                            found_photos_tokens.append(upload_res)
                            logging.info(f"✅ Фото загружено (в очереди: {len(found_photos_tokens)})")

                    # Если накопили на альбом (10 штук), отправляем сразу
                    if len(found_photos_tokens) >= ALBUM_SIZE:
                        send_album_to_max(found_photos_tokens)
                        found_photos_tokens = [] # Очищаем очередь

                    # В любом случае удаляем файл после обработки
                    img_path.unlink()
                    
                except Exception as e:
                    logging.error(f"Ошибка при обработке {img_path.name}: {e}")

            # После завершения цикла проверяем, не осталось ли в очереди недоотправленных фото
            if found_photos_tokens:
                logging.info(f"Отправка оставшихся {len(found_photos_tokens)} фото...")
                send_album_to_max(found_photos_tokens)
                found_photos_tokens = []

        # Очистка пустых папок
        for folder in sorted(base_path.glob("**/"), reverse=True):
            if folder != base_path and folder.is_dir() and not any(folder.iterdir()):
                try:
                    folder.rmdir()
                    logging.info(f"🧹 Удалена пустая папка: {folder.relative_to(base_path)}")
                except:
                    pass

        logging.info("--- Сканирование завершено ---")

    except Exception as e:
        logging.error(f"Глобальная ошибка при сканировании: {e}")

if __name__ == "__main__":
    run_once()
