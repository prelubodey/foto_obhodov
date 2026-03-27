import requests
import os

def send_photo_to_user():
    # Данные из вашего предыдущего запроса
    token = "f9LHodD0cOJ3sZU5I6lEDWPRsJYkTGQNgXt-FemScOPTCCcLO1gzlyPrRLPmBDeEr5lbP8jiaf5uQMYvQkR7"
    user_id = 11380703
    
    # Имя файла в папке скрипта
    file_name = "photo.jpg" 
    file_path = os.path.join(os.path.dirname(__file__), file_name)

    if not os.path.exists(file_path):
        print(f"Ошибка: Файл {file_name} не найден в папке скрипта!")
        return

    headers = {
        "Authorization": token
    }
    base_url = "https://platform-api.max.ru"

    try:
        # ШАГ 1: Получение URL для загрузки изображения [1, 2]
        # Используем параметр type=image согласно спецификации [3, 4]
        upload_init_res = requests.post(
            f"{base_url}/uploads",
            params={"v": "1.0.0", "type": "image"},
            headers=headers
        )
        upload_init_res.raise_for_status()
        upload_url = upload_init_res.json()["url"]

        # ШАГ 2: Загрузка бинарных данных файла [2, 5]
        # Поле в multipart/form-data должно называться "data" [6]
        with open(file_path, 'rb') as f:
            files = {'data': (file_name, f)}
            upload_res = requests.post(upload_url, files=files)
        
        upload_res.raise_for_status()
        photo_data = upload_res.json() # Получаем объект PhotoTokens с картой токенов [7]

        # ШАГ 3: Отправка сообщения с вложением [5, 8]
        # Важно: серверу может потребоваться время на обработку фото [5]
        message_data = {
            "text": "Ваше фото из папки скрипта",
            "attachments": [
                {
                    "type": "image",
                    "payload": {
                        "photos": photo_data["photos"] # Передаем полученную карту токенов [7, 9]
                    }
                }
            ],
            "link": None,
            "format": "markdown"
        }

        response = requests.post(
            f"{base_url}/messages",
            params={"v": "1.0.0", "user_id": user_id},
            headers=headers,
            json=message_data
        )

        print(f"Статус отправки: {response.status_code}")
        print(f"Ответ сервера: {response.text}")

    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    send_photo_to_user()