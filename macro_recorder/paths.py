"""Пути хранения данных (AppData) и настройка логирования."""

import os
import logging
from datetime import datetime


def get_base_dir():
    """Корневая папка данных в AppData\\Roaming (fallback на Local/дом)."""
    appdata = os.environ.get("APPDATA")
    if not appdata:
        appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    return os.path.join(appdata, "MacroRecorder")


def setup_logging(log_dir):
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"macro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    logger = logging.getLogger("MacroRecorder")
    logger.setLevel(logging.DEBUG)
    if logger.handlers:
        logger.handlers.clear()

    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    
    # Детальный формат: Время | Уровень | Файл:Строка в Функции | Сообщение
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d in %(funcName)s | %(message)s'
    )
    
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger, log_file