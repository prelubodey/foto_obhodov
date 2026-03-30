import requests
import os
import logging

# Настройки API Макс берутся из переменных окружения
TOKEN = os.environ.get("MAX_TOKEN")
CHAT_ID_RAW = os.environ.get("MAX_CHAT_ID", "").strip().strip('"').strip("'")
BASE_URL = "https://platform-api.max.ru"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_photo_to_max(file_path, text="Обнаружен человек!"):
    """
    Загружает изображение и отправляет его в чат Макс.
    """
    if not TOKEN or not CHAT_ID_RAW:
        logging.error("❌ Ошибка: MAX_TOKEN или MAX_CHAT_ID не настроены в .env!")
        return False

    if not os.path.exists(file_path):
        logging.error(f"Файл {file_path} не найден!")
        return False

    headers = {
        "Authorization": TOKEN
    }

    try:
        # ШАГ 1: Получение URL для загрузки
        logging.info(f"Инициализация загрузки для {file_path}...")
        upload_init_res = requests.post(
            f"{BASE_URL}/uploads",
            params={"v": "1.0.0", "type": "image"},
            headers=headers,
            timeout=10
        )
        upload_init_res.raise_for_status()
        upload_url = upload_init_res.json()["url"]

        # ШАГ 2: Загрузка файла
        file_name = os.path.basename(file_path)
        with open(file_path, 'rb') as f:
            files = {'data': (file_name, f)}
            upload_res = requests.post(upload_url, files=files, timeout=30)
        
        upload_res.raise_for_status()
        photo_data = upload_res.json()

        # ШАГ 3: Отправка сообщения с вложением
        message_data = {
            "text": text,
            "attachments": [
                {
                    "type": "image",
                    "payload": {
                        "photos": photo_data["photos"]
                    }
                }
            ],
            "link": None,
            "format": "markdown"
        }

        # --- ПОПЫТКА 1: Стандартная (через user_id в params) ---
        logging.info(f"Попытка №1: Отправка через user_id в params на {CHAT_ID_RAW}")
        response = requests.post(
            f"{BASE_URL}/messages",
            params={"v": "1.0.0", "user_id": CHAT_ID_RAW},
            headers=headers,
            json=message_data,
            timeout=10
        )

        if response.status_code == 200:
            logging.info(f"✅ Фото успешно отправлено.")
            return True

        # --- ПОПЫТКА 2: Если 404, пробуем chat_id вместо user_id ---
        logging.warning(f"⚠️ Ошибка {response.status_code}. Попытка №2: замена user_id на chat_id...")
        response = requests.post(
            f"{BASE_URL}/messages",
            params={"v": "1.0.0", "chat_id": CHAT_ID_RAW},
            headers=headers,
            json=message_data,
            timeout=10
        )
        if response.status_code == 200:
            logging.info(f"✅ Фото успешно отправлено через chat_id.")
            return True

        # --- ПОПЫТКА 3: Передача ID в теле JSON (наиболее надежно) ---
        logging.warning(f"⚠️ Ошибка {response.status_code}. Попытка №3: передача ID внутри JSON...")
        message_data["user_id"] = CHAT_ID_RAW
        response = requests.post(
            f"{BASE_URL}/messages",
            params={"v": "1.0.0"},
            headers=headers,
            json=message_data,
            timeout=10
        )
        if response.status_code == 200:
            logging.info(f"✅ Фото успешно отправлено через JSON тело.")
            return True

        logging.error(f"❌ Все попытки отправки провалены: {response.status_code} - {response.text}")
        return False

    except Exception as e:
        logging.error(f"⚠️ Произошла ошибка при работе с Макс API: {e}")
        return False
