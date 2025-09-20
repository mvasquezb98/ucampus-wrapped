from pathlib import Path
import getpass
from core.scrapper.navegador import get_chrome_driver
from core.scrapper.auth import login_generic
from core.scrapper.ucampus import extraer_datos_ucampus
from core.scrapper.ucursos import urls_cursos,extraer_datos_ucursos
from core.scrapper.excel_exporter import excel_exporter
import os
import logging
from config.logger import setup_logger
from selenium.webdriver.common.by import By


#Setup de los logs
setup_logger()
logger = logging.getLogger(__name__)
# Emojis: ✅ ❌ ⚠️ 📂 💾 ℹ️️ 🚀 📦 📊 🎨 🖊️ 📌 ➡️ 🎯 🏷️ 📏

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
    facultad = input("Facultad (fcfm o medicina): ")

    ## UCAMPUS
    
    url_ucampus = f"https://ucampus.uchile.cl/m/fcfm_bia/historial?rut={rut}" # Ruta del historial académico
    if facultad == "medicina":
        url_ucampus = f"https://ucampus.uchile.cl/m/medicina_bia/historial?rut={rut}" # Ruta del historial académico
    
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

    # find all elements with a class attribute
    elements = driver.find_elements(By.XPATH, "//*[@class]")

    usuario_classes = set()
    for el in elements:
        for c in el.get_attribute("class").split(): #type: ignore
            if c.startswith("usuario"):
                usuario_classes.add(c)
    usuario_classes = list(usuario_classes)
    user_id = usuario_classes[0].split(".")[1]
    
    #user_id = [id.split("/") for id in driver.current_url.split("usuario/")][1][0]
    url = f"https://www.u-cursos.cl/usuario/{user_id}/todos_cursos/"
    driver.get(url)

    urls_cursos_alumno = urls_cursos(driver)
    df_dict_ucursos = extraer_datos_ucursos(driver,urls_cursos_alumno)

    file_name = f"data_UCURSOS_{rut}" 
    excel_exporter(file_name,path,df_dict_ucursos)
    
    # Cerrar el driver
    driver.quit()
    return(str(rut))