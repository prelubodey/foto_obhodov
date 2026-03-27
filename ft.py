# -*- coding: utf-8 -*-
import asyncio
import os
import shutil
from pathlib import Path
from ultralytics import YOLO
from aiogram import Bot
from aiogram.types import FSInputFile, InputMediaPhoto
# --- НАСТРОЙКИ ---
TOKEN = "8048816288:AAE4cbGOUsIvIT3_7KF1A3Q52rNKXHzYaH4"
CHAT_ID = "106215658"
SOURCE_DIR = "upload"
CONFIDENCE = 0.5

model = YOLO("yolov8n.pt")
bot = Bot(token=TOKEN)


async def send_as_album(file_paths, caption=None):
    """Отправка группы фото"""
    if not file_paths:
        return
    # Убедимся, что все пути - это строки
    media_group = [
        InputMediaPhoto(media=FSInputFile(path), caption=caption if i == 0 else None)
        for i, path in enumerate(file_paths)
    ]
    try:
        await bot.send_media_group(chat_id=CHAT_ID, media=media_group)
        print(f"✅ Отправлен альбом из {len(file_paths)} фото.")
    except Exception as e:
        print(f"❌ Ошибка при отправке альбома: {e}")


async def process_images():
    base_path = Path(SOURCE_DIR)
    extensions = (".jpg", ".jpeg", ".png")

    all_images = sorted(
        [f for f in base_path.rglob("*") if f.suffix.lower() in extensions],
        key=lambda f: f.stat().st_mtime,
    )
    print(f"Найдено файлов для проверки: {len(all_images)}")

    found_files = []

    try:
        for img_path in all_images:
            results = model(img_path, conf=CONFIDENCE, verbose=False)

            is_person = any(0 in r.boxes.cls for r in results)

            if is_person:
                print(f"👤 Человек найден: {img_path}")
                found_files.append(img_path)

            if len(found_files) >= 10:
                # Отправляем альбом с найденными фото
                await send_as_album(found_files)
                found_files = []
                await asyncio.sleep(2)

        # Отправляем и проверяем остатки
        if found_files:
            await send_as_album(found_files)

        print("--- Обработка завершена успешно ---")

    finally:
        print("Начинаю очистку папки upload...")
        for item in base_path.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                print(f"🗑️ Удалено: {item.name}")
            except Exception as e:
                print(f"⚠️ Не удалось удалить {item}: {e}")
        print("✨ Папка upload очищена.")
        await bot.session.close()
        print("🔌 Сессия закрыта.")


if __name__ == "__main__":
    # Рекомендуется установить библиотеку: pip install google-generativeai
    try:
        asyncio.run(process_images())
    except KeyboardInterrupt:
        print("\nСкрипт остановлен пользователем.")
