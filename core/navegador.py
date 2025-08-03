# Solo en GoogleColab
# chrome_options.add_argument('--no-sandbox') # Para desactivar el sandbox de seguridad de Chrome, porque da errores al intentar crearlo en entornos limitados.
# chrome_options.add_argument('--disable-dev-shm-usage') # Para que chrome use el disco normal en vez de la memoria compartida de la carpeta /dev/shm que es limitada y se puede caer.
# chrome_options.add_argument('--disable-gpu') #  Le dice a Chrome que no intente usar la tarjeta gráfica (GPU) para renderizar páginas.

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def get_chrome_driver(headless=True, disable_gpu=True, colab_mode=False):
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
    return driver
