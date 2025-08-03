import logging
import json
from pathlib import Path
import sys

'''
Explicación:

__file__ 
Es una variable que existe automáticamente en cualquier archivo .py
Representa la ruta completa (o relativa) del archivo actual.

Path(__file__) 
Convierte la ruta del archivo actual (logger.py) en un objeto de tipo Path.

.resolve()
Convierte esa ruta en una ruta absoluta, si es que era relativa.

.parent 
Sube una carpeta.


mkdir()
Crea la carpeta

exist_ok=True
Evita errores si ya está creada la carpeta
'''

def setup_logger():
    # Get settings
    settings_path = Path(__file__).resolve().parent / "settings.json"
    with open(settings_path, encoding="utf-8") as f:
        settings = json.load(f)

    # Read log level from settings.json
    log_level_str = settings.get("log_level", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Prepare log directory and file
    logs_dir = Path(__file__).resolve().parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / "ejecucion.log"

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers if any (avoids duplicates)
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
