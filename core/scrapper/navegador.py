from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import logging
from config.logger import setup_logger

setup_logger()
logger = logging.getLogger(__name__)

def get_chrome_driver(headless=True, disable_gpu=True, colab_mode=False):
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
