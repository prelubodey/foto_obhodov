import requests
import os
import logging

# Настройки API Макс берутся из переменных окружения
TOKEN = os.environ.get("MAX_TOKEN")
CHAT_ID_RAW = os.environ.get("MAX_CHAT_ID", "").strip().strip('"').strip("'")
BASE_URL = "https://platform-api.max.ru"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def upload_photo_to_max(file_path):
    """
    Загружает изображение на сервер Макс и возвращает словарь с токенами фото.
    """
    if not TOKEN:
        logging.error("❌ Ошибка: MAX_TOKEN не настроен в .env!")
        return None

    if not os.path.exists(file_path):
        logging.error(f"Файл {file_path} не найден!")
        return None

    headers = {"Authorization": TOKEN}

    try:
        # ШАГ 1: Получение URL для загрузки
        upload_init_res = requests.post(
            f"{BASE_URL}/uploads",
            params={"v": "1.0.0", "type": "image"},
            headers=headers,
            timeout=15
        )
        upload_init_res.raise_for_status()
        upload_url = upload_init_res.json()["url"]

        # ШАГ 2: Загрузка бинарных данных
        file_name = os.path.basename(file_path)
        with open(file_path, 'rb') as f:
            # Согласно test2.py поле должно называться 'data'
            files = {'data': (file_name, f)}
            upload_res = requests.post(upload_url, files=files, timeout=30)
        
        upload_res.raise_for_status()
        # Возвращаем результат загрузки (содержит tokens)
        return upload_res.json()

    except Exception as e:
        logging.error(f"⚠️ Ошибка при загрузке фото {file_path}: {e}")
        return None

def send_album_to_max(photo_results, text="Обнаружены люди!"):
    """
    Отправляет группу фотографий (до 10 штук) одним сообщением.
    photo_results - список словарей, полученных из upload_photo_to_max
    """
    if not TOKEN or not CHAT_ID_RAW:
        logging.error("❌ Ошибка: MAX_TOKEN или MAX_CHAT_ID не настроены!")
        return False

    if not photo_results:
        return False

    headers = {"Authorization": TOKEN}

    try:
        # Формируем список вложений
        attachments = []
        for res in photo_results:
            if "photos" in res:
                attachments.append({
                    "type": "image",
                    "payload": {
                        "photos": res["photos"]
                    }
                })

        if not attachments:
            logging.warning("⚠️ Нет корректных токенов для отправки альбома.")
            return False

        message_data = {
            "chat_id": CHAT_ID_RAW,
            "text": text,
            "attachments": attachments,
            "link": None,
            "format": "markdown"
        }

        logging.info(f"Отправка альбома из {len(attachments)} фото в чат: {CHAT_ID_RAW}")
        
        response = requests.post(
            f"{BASE_URL}/messages",
            params={"v": "1.0.0", "chat_id": CHAT_ID_RAW},
            headers=headers,
            json=message_data,
            timeout=20
        )

        if response.status_code == 200:
            logging.info(f"✅ Альбом успешно отправлен.")
            return True
        else:
            logging.error(f"❌ Ошибка отправки альбома: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logging.error(f"⚠️ Ошибка при отправке альбома в Макс API: {e}")
        return False

# Для обратной совместимости (если где-то вызывается старая функция)
def send_photo_to_max(file_path, text="Обнаружен человек!"):
    res = upload_photo_to_max(file_path)
    if res:
        return send_album_to_max([res], text)
    return False
