import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

def login_generic(driver, url, username, password, selectors, success_check):
    try:
        logger.info("🔁 Navegando a página de login...")
        driver.get(url)
        time.sleep(3)

        logger.info("🔎 Esperando campo de usuario...")
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((selectors["username"]))
        )
        logger.info("✅ Campo usuario encontrado")

        password_field = driver.find_element(*selectors["password"])
        logger.info("✅ Campo contraseña encontrado")

        username_field.send_keys(username)
        logger.info("🧾 Usuario ingresado")

        password_field.send_keys(password)
        logger.info("🧾 Contraseña ingresada")

        submit_button = driver.find_element(*selectors["submit"])
        logger.info("✅ Botón de ingreso encontrado")

        submit_button.click()
        logger.info("🚀 Formulario enviado")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(success_check)
        )
        logger.info("✅ Login exitoso")

    except Exception as e:
        logger.exception("❌ Fallo durante el login")
