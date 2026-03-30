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

    # В этой версии мы попробуем передавать CHAT_ID как строку в параметрах,
    # чтобы избежать искажения чисел на уровне библиотеки requests или API.
    CHAT_ID = CHAT_ID_RAW

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

        # Пытаемся отправить, используя строковый ID и проверяя сформированный URL
        # Некоторые API принимают ID пользователя и в params, и в теле.
        # Мы попробуем передать его в params как строку.
        params = {
            "v": "1.0.0",
            "user_id": CHAT_ID
        }

        logging.info(f"Отправка сообщения на Chat ID: {CHAT_ID}")
        
        response = requests.post(
            f"{BASE_URL}/messages",
            params=params,
            headers=headers,
            json=message_data,
            timeout=10
        )

        if response.status_code == 200:
            logging.info(f"✅ Фото {file_name} успешно отправлено в Макс (Chat ID: {CHAT_ID}).")
            return True
        else:
            # Если 404, пробуем альтернативный способ: передать user_id прямо в JSON
            if response.status_code == 404:
                logging.warning(f"⚠️ Ошибка 404 при отправке на {CHAT_ID}. Пробую передать ID в теле запроса...")
                message_data["user_id"] = CHAT_ID # Попытка №2
                response = requests.post(
                    f"{BASE_URL}/messages",
                    params={"v": "1.0.0"},
                    headers=headers,
                    json=message_data,
                    timeout=10
                )
                if response.status_code == 200:
                    logging.info(f"✅ Успешно отправлено (через JSON тело).")
                    return True

            logging.error(f"❌ Ошибка отправки сообщения: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logging.error(f"⚠️ Произошла ошибка при работе с Макс API: {e}")
        return False
