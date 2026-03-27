import numpy as np
import cv2
import os
import logging

# Попытка импорта rknnlite. 
# На обычном ПК это упадет с ошибкой, поэтому мы перехватим её для тестирования на ПК.
try:
    from rknnlite.api import RKNNLite
    RKNN_AVAILABLE = True
except ImportError:
    RKNN_AVAILABLE = False
    logging.warning("Библиотека rknnlite не найдена! Работа на NPU недоступна.")

class RKNNYoloDetector:
    def __init__(self, model_path, input_size=640, conf_threshold=0.5):
        self.model_path = model_path
        self.input_size = input_size
        self.conf_threshold = conf_threshold
        self.rknn = None

        if RKNN_AVAILABLE:
            self.rknn = RKNNLite()
            logging.info(f"Загрузка RKNN модели: {model_path}")
            ret = self.rknn.load_rknn(model_path)
            if ret != 0:
                logging.error("Ошибка при загрузке RKNN модели!")
                return
            
            # Инициализация среды инференса
            ret = self.rknn.init_runtime()
            if ret != 0:
                logging.error("Ошибка при инициализации RKNN runtime!")
                return
            logging.info("RKNN Runtime инициализирован.")

    def preprocess(self, img):
        """Подготовка изображения под вход YOLOv8."""
        img_h, img_w = img.shape[:2]
        
        # Ресайз с сохранением соотношения сторон (letterbox)
        scale = min(self.input_size / img_w, self.input_size / img_h)
        new_w, new_h = int(img_w * scale), int(img_h * scale)
        
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        # Создаем полотно 640x640 и вставляем туда наше изображение
        canvas = np.full((self.input_size, self.input_size, 3), 114, dtype=np.uint8)
        top = (self.input_size - new_h) // 2
        left = (self.input_size - new_w) // 2
        canvas[top:top+new_h, left:left+new_w] = resized
        
        # RKNN обычно принимает NHWC, uint8 (без нормализации в float внутри скрипта, если она встроена в RKNN)
        # Если модель ожидает RGB, сконвертируем
        canvas = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        return canvas

    def postprocess(self, outputs):
        """
        Упрощенный постпроцессинг для YOLOv8.
        Нам нужно только проверить наличие человека (class_id=0).
        В типичной YOLOv8 выход имеет форму (1, 84, 8400) - где 84 это 4(bbox) + 80(классы).
        """
        # В зависимости от того, как была сконвертирована модель, выходы могут отличаться.
        # Это пример для стандартной YOLOv8.
        if not outputs:
            return False

        # outputs[0] обычно имеет форму [1, 84, 8400]
        output = outputs[0]
        if len(output.shape) == 3:
            output = output[0] # [84, 8400]

        # Для YOLOv8 класса "person" индекс 4 в 0-й размерности (если первые 4 это боксы)
        # На самом деле классы начинаются с индекса 4. Person = 4
        # Проверим уверенность (confidence) для человека.
        person_scores = output[4] # Вероятности класса 0 (человек)
        
        # Если хотя бы один объект имеет уверенность выше порога
        if np.max(person_scores) > self.conf_threshold:
            return True
        
        return False

    def has_person(self, img_path):
        """Основная функция детекции."""
        if not RKNN_AVAILABLE:
            logging.error("RKNN не доступен для обработки.")
            return False

        img = cv2.imread(img_path)
        if img is None:
            logging.error(f"Не удалось прочитать изображение {img_path}")
            return False

        input_data = self.preprocess(img)
        # Добавляем размерность батча
        input_data = np.expand_dims(input_data, 0)

        # Инференс на NPU
        outputs = self.rknn.inference(inputs=[input_data])
        
        return self.postprocess(outputs)

    def release(self):
        if self.rknn:
            self.rknn.release()
