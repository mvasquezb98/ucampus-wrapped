from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
import logging
from config.logger import setup_logger

setup_logger()
logger = logging.getLogger(__name__)
# Emojis: ✅ ❌ ⚠️ 📂 💾 ℹ️️ 🚀 📦 📊 🎨 🖊️ 📌 ➡️ 🎯 🏷️ 📏

def get_chrome_driver(
    headless: bool = True,
    disable_gpu: bool = True,
    colab_mode: bool = False
) -> WebDriver:
    """
    Initialize and configure a Selenium Chrome WebDriver instance.

    The function sets Chrome options for headless execution, GPU disabling,
    and Colab/Docker compatibility if needed. It also uses
    `ChromeDriverManager` to automatically download and manage the appropriate
    ChromeDriver version. If initialization fails, the exception is logged and
    re-raised.

    Args:
        headless (bool, optional): Whether to run Chrome in headless mode
            (no visible browser window). Defaults to True.
        disable_gpu (bool, optional): Whether to disable GPU acceleration,
            often required in headless environments. Defaults to True.
        colab_mode (bool, optional): Whether to enable compatibility options
            for restricted environments like Google Colab or Docker
            (`--no-sandbox`, `--disable-dev-shm-usage`). Defaults to False.

    Returns:
        WebDriver: A Selenium Chrome WebDriver instance ready for use.

    Raises:
        Exception: If ChromeDriver initialization fails. The exception is logged
        and then re-raised.
    """
    try:
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless')
        if disable_gpu:
            chrome_options.add_argument('--disable-gpu')
        if colab_mode:
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        logger.info("✅ Chrome driver initialized.")
    except Exception as e:
        logger.exception("❌ Failed to initialize Chrome driver.")
        raise e
    return driver
