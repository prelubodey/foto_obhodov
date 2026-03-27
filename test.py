import requests

def send_message():
    token = "f9LHodD0cOJ3sZU5I6lEDWPRsJYkTGQNgXt-FemScOPTCCcLO1gzlyPrRLPmBDeEr5lbP8jiaf5uQMYvQkR7"
    # Можно также использовать https://botapi.max.ru/messages [6]
    url = "https://platform-api.max.ru/messages" 
    
    params = {
        "v": "1.0.0",
        "user_id": 11380703  # ID пользователя как число [3]
    }
    
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    
    # Полное соответствие схеме NewMessageBody [1, 2]
    data = {
        "text": "Проверка связи! Запрос сформирован по инструкции.",
        "attachments": [], 
        "link": None,
        "format": "markdown" # Опционально, если хотите использовать разметку [5]
    }

    response = requests.post(url, headers=headers, params=params, json=data)
    
    print(f"Статус: {response.status_code}")
    print(f"Ответ: {response.text}")

if __name__ == "__main__":
    send_message()