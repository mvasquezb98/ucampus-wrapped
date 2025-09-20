from config.integrity_checks import check_project_schema
check_project_schema()

import logging
from config.logger import setup_logger
import json
from pathlib import Path
from core.cleaner.limpieza_datos import limpiar_datos
import os
from core.scrapper.webscrapper import scrapper
import pandas as pd
from core.visuals.boleta_acta_milagrosa import create_receipt_with_shadow_and_barcode

#Setup de los logs
setup_logger()
logger = logging.getLogger(__name__)
# Emojis: ✅ ❌ ⚠️ 📂 💾 ℹ️️ 🚀 📦 📊 🎨 🖊️ 📌 ➡️ 🎯 🏷️ 📏

# Cargar configuración
with open(Path("config/settings.json"), encoding="utf-8") as f:
    settings = json.load(f)
base_path = os.path.dirname(os.path.abspath(__file__))


# Extracción de datos
rut = scrapper(settings,base_path)

#Limpieza de datos
limpiar_datos(settings,base_path,rut)

df = pd.read_excel("data/clean_data_" + rut + ".xlsx",sheet_name="Acta_Milagrosa")
create_receipt_with_shadow_and_barcode(df, texture_path = "assets/textures/texture2.jpg", barcode_text = "Acta Milagrosa", output_path = "data/receipt" + "_" + rut + ".png")