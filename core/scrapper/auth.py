import logging
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from typing import Tuple
import logging
from config.logger import setup_logger

setup_logger() 
logger = logging.getLogger(__name__)
# Emojis: ✅ ❌ ⚠️ 📂 💾 ℹ️️ 🚀 📦 📊 🎨 🖊️ 📌 ➡️ 🎯 🏷️ 📏

def login_generic(
    driver: WebDriver,
    url: str,
    username: str,
    password: str,
    selectors: dict,
    success_check: Tuple[str,str]
) -> None:
    """
    Perform a generic login process on a web page using Selenium.

    The function navigates to the provided login URL, locates the username,
    password, and submit fields based on the given selectors, enters the
    credentials, and submits the form. After submission, it waits until an
    element defined in `success_check` is located to confirm successful login.
    If any step fails, the exception is logged.

    Args:
        driver (WebDriver): A Selenium WebDriver instance used to navigate
            and interact with the login page.
        url (str): The URL of the login page.
        username (str): The username credential for login.
        password (str): The password credential for login.
        selectors (dict): A dictionary containing Selenium locator tuples for
            the login fields. Expected keys:
                - "username": Locator for the username input field.
                - "password": Locator for the password input field.
                - "submit": Locator for the submit button.
        success_check (Tuple[str, str]): A Selenium locator tuple used to
            verify that the login succeeded by waiting for the presence of a
            specific element.

    Returns:
        None

    Raises:
        Exception: If navigation, field interaction, submission, or the
        success check fails. The exception is logged before being raised.
    """
    try:
        logger.info("🔁 Navegando a página de login...")
        driver.get(url)
        time.sleep(3)

        logger.info("🔎 Esperando campo de usuario...")
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((selectors["username"]))
        )
        logger.debug("ℹ️️ Campo usuario encontrado")

        password_field = driver.find_element(*selectors["password"])
        logger.debug("ℹ️️ Campo contraseña encontrado")

        username_field.send_keys(username)
        logger.debug("🧾 Usuario ingresado")

        password_field.send_keys(password)
        logger.debug("🧾 Contraseña ingresada")

        submit_button = driver.find_element(*selectors["submit"])
        logger.debug("ℹ️️ Botón de ingreso encontrado")

        submit_button.click()
        logger.info("📌 Credenciales ingresadas")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(success_check)
        )
        logger.info("✅ Login exitoso")

    except Exception as e:
        logger.exception("❌ Fallo durante el login")
