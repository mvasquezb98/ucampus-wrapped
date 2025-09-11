import logging
from config.logger import setup_logger
import json
from pathlib import Path
import getpass
from core.scrapper.navegador import get_chrome_driver
from core.scrapper.auth import login_generic
from core.scrapper.ucampus import extraer_datos_ucampus
from core.scrapper.ucursos import urls_cursos,extraer_datos_ucursos
from core.scrapper.excel_exporter import excel_exporter
from core.cleaner.limpieza_datos import limpiar_datos
import os

#Setup de los logs
setup_logger()
logger = logging.getLogger(__name__)
# Emojis: ✅ ❌ ⚠️ 📂 💾 ℹ️️ 🚀 📦 📊 🎨 🖊️ 📌 ➡️ 🎯 🏷️ 📏

# Cargar configuración
with open(Path("config/settings.json"), encoding="utf-8") as f:
    settings = json.load(f)
base_path = os.path.dirname(os.path.abspath(__file__))

def scrapper(settings,base_path):        
    # Usar valores
    headless = settings["headless"]
    salida = Path(settings["output_dir"])
    path = os.path.join(base_path,salida)

    #Crear driver
    driver = get_chrome_driver(
        headless=headless,
        disable_gpu=settings.get("disable_gpu", False),
        colab_mode=settings.get("colab_mode", False)
    )

    #Input usuario
    USERNAME = input("Usuario: ")
    PASSWORD = getpass.getpass("Clave: ")
    rut = input("Rut: ")

    ## UCAMPUS
    url_ucampus = f"https://ucampus.uchile.cl/m/fcfm_bia/historial?rut={rut}" # Ruta del historial académico
    ucampus_selectors = {
        "username": ("name", "username"),
        "password": ("name", "password"),
        "submit": ("css selector", "input[type='submit']")
    }
    success_check = ("id", "navigation-wrapper")

    login_generic(driver, url_ucampus, USERNAME, PASSWORD, ucampus_selectors, success_check)

    
    df_dict_ucampus = extraer_datos_ucampus(driver)
    file_name = f"data_UCAMPUS_{rut}" 
    excel_exporter(file_name, path, df_dict_ucampus)

    ## UCURSOS
    url_ucursos = 'https://www.u-cursos.cl/'
    ucursos_selectors = {
        "username": ("name", "username"),
        "password": ("name", "password"),
        "submit": ("css selector", "input[type='submit']")
    }
    success_check = ("id", "navigation-wrapper")

    login_generic(driver, url_ucursos, USERNAME, PASSWORD, ucursos_selectors, success_check)

    user_id = [id.split("/") for id in driver.current_url.split("usuario/")][1][0]
    url = f"https://www.u-cursos.cl/usuario/{user_id}/todos_cursos/"
    driver.get(url)

    urls_cursos_alumno = urls_cursos(driver)
    df_dict_ucursos = extraer_datos_ucursos(driver,urls_cursos_alumno)

    file_name = f"data_UCURSOS_{rut}" 
    excel_exporter(file_name,path,df_dict_ucursos)

    # Cerrar el driver
    driver.quit()
# Limpieza de datos
scrapper(settings,base_path)
limpiar_datos(settings,base_path)