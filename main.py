from config.integrity_checks import check_project_schema
check_project_schema()

import logging
from config.logger import setup_logger
import json
from pathlib import Path
from core.cleaner.limpieza_datos import limpiar_datos
import os
from core.scrapper.webscrapper import scrapper

#Setup de los logs
setup_logger()
logger = logging.getLogger(__name__)
# Emojis: ✅ ❌ ⚠️ 📂 💾 ℹ️️ 🚀 📦 📊 🎨 🖊️ 📌 ➡️ 🎯 🏷️ 📏

# Cargar configuración
with open(Path("config/settings.json"), encoding="utf-8") as f:
    settings = json.load(f)
base_path = os.path.dirname(os.path.abspath(__file__))


# Extracción de datos
scrapper(settings,base_path)
#Limpieza de datos
limpiar_datos(settings,base_path)