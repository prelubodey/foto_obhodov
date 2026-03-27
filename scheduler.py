import schedule
import time
import logging
from main import run_once
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def job():
    logging.info(f"Запуск запланированного сканирования в {datetime.now()}")
    try:
        run_once()
    except Exception as e:
        logging.error(f"Ошибка во время выполнения задания: {e}")

# Планируем запуск каждый день в 09:00
# Важно: В Docker-контейнере должна быть установлена таймзона Europe/Moscow
schedule.every().day.at("09:00").do(job)

logging.info("Планировщик запущен. Ожидание 09:00 по местному времени (МСК)...")

# Тестовый запуск при старте контейнера (опционально, можно убрать)
# job()

while True:
    schedule.run_pending()
    time.sleep(60)
