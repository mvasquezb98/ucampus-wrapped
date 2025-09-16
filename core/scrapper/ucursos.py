import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
import time
import logging
from config.logger import setup_logger

setup_logger() 
logger = logging.getLogger(__name__)
# Emojis: ✅ ❌ ⚠️ 📂 💾 ℹ️️ 🚀 📦 📊 🎨 🖊️ 📌 ➡️ 🎯 🏷️ 📏📋

def urls_cursos(driver: WebDriver) -> list[str]:
    """
    Extract the list of course URLs for a student from a web page using Selenium.

    The function scans all table cells with class "objetoflex string",
    verifies which ones contain a \\<div\\> element with class "cargo cargo-alumno"
    (indicating that the course belongs to the student), and retrieves the
    hyperlink (\\<a\\>) inside the same cell.

    Args:
        driver (WebDriver): A Selenium WebDriver instance pointing to the page
            where the student's courses are listed.

    Returns:
        list[str]: A list of course URLs extracted from the page.

    Raises:
        Exception: Propagates any unexpected Selenium errors during element
        search or attribute extraction.
    """
    logger.info("📋 Iniciando extracción de urls de u-cursos")
    urls_cursos_alumno = []

    # Encuentra todos los td que contienen los cursos
    tds = driver.find_elements(By.CSS_SELECTOR, "td.objetoflex.string")

    for td in tds:
        try:
            # Solo si contiene un div con clase 'cargo cargo-alumno'
            cargo_div = td.find_element(By.CSS_SELECTOR, "div.cargo.cargo-alumno")

            # Ahora buscamos el <a> en el mismo td
            a_tag = td.find_element(By.TAG_NAME, "a")
            href = a_tag.get_attribute("href")

            if href:
                urls_cursos_alumno.append(href)
        except:
            continue  # Si no hay div.cargo.cargo-alumno, lo ignora
    
    logger.info(f"✅ {len(urls_cursos_alumno)} urls de u-cursos obtenidos")
    return(urls_cursos_alumno)

def data_notas(
    driver: WebDriver,
    urls_cursos_alumno: list[str]
) -> pd.DataFrame:
    """
    Extract evaluation names and grades from each course page and return them
    as a pandas DataFrame.

    For every course URL provided, the function navigates to the corresponding
    grades page (appending 'notas/alumno' to the URL), locates the table that
    contains evaluations and their averages, and extracts the relevant rows.
    Each extracted row includes the course URL, the evaluation name, and the
    corresponding grade. Results are aggregated into a DataFrame.

    Args:
        driver (WebDriver): A Selenium WebDriver instance used to navigate the
            course pages.
        urls_cursos_alumno (list[str]): List of URLs for the student's courses.

    Returns:
        pandas.DataFrame: A DataFrame containing the extracted data with the
        following columns:
            - "Curso URL" (str): The course URL where the evaluation was found.
            - "Evaluación" (str): The name of the evaluation.
            - "Promedio" (str): The grade or score of the evaluation.

    Raises:
        Exception: If a page cannot be loaded, if the grades table cannot be
        found, or if row extraction fails. Exceptions are logged and re-raised.
    """
    logger.info("📦Recuperando notas obtenidas por ramo")
    notas_data = []
    for curso_url in urls_cursos_alumno:
        link_notas = curso_url + 'notas/alumno'
        try:
            driver.get(link_notas)
            time.sleep(2)

            # Encuentra la tabla correcta
            tables = driver.find_elements(By.TAG_NAME, "table")
            target_table = next(
                (table for table in tables
                if "Evaluación" in [th.text.strip() for th in table.find_elements(By.TAG_NAME, "th")]
                and any("Prom" in th.text.strip() for th in table.find_elements(By.TAG_NAME, "th"))),
                None
            )

            if target_table:
                rows = target_table.find_elements(By.XPATH, ".//tbody/tr[not(contains(@class, 'separador'))]")
                for row in rows:
                    try:
                        cols = row.find_elements(By.TAG_NAME, "td")
                        evaluacion = cols[0].find_element(By.TAG_NAME, "h1").text.strip()
                        promedio = cols[-1].find_element(By.TAG_NAME, "span").text.strip()
                        notas_data.append({
                            "Curso URL": curso_url,
                            "Evaluación": evaluacion,
                            "Promedio": promedio
                        })
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Could not extract row: {e}")
            else:
                logger.warning(f"⚠️ Tabla de notas no encontrada en {link_notas}")
        
        except Exception as e:
            logger.warning(f"⚠️ Error cargando página de notas")
    logger.info(f"ℹ️️ Total de notas registradas: {len(notas_data)}")
    logger.info(f"✅ Recuperación de notas finalizada")
    return(pd.DataFrame(notas_data))

def data_actas(
    driver: WebDriver,
    urls_cursos_alumno: list[str]
) -> pd.DataFrame:
    """
    Extract acta (record) information from each course page and return it as a
    pandas DataFrame.

    For every course URL provided, the function navigates to the corresponding
    acta page (constructed by appending 'actas/' to the course URL), locates
    the detail table, and extracts row data. Each row typically contains an
    indicator (label) and its associated value. If a row has only one cell,
    the value is recorded as an empty string. All results are aggregated into
    a single DataFrame.

    Args:
        driver (WebDriver): A Selenium WebDriver instance used to navigate the
            course pages.
        urls_cursos_alumno (list[str]): List of course URLs belonging to the
            student.

    Returns:
        pandas.DataFrame: A DataFrame with one row per indicator containing the
        following columns:
            - "Curso URL" (str): The course URL where the acta information was found.
            - "Indicador" (str): The label or indicator extracted from the table row.
            - "Valor" (str): The value associated with the indicator.

    Raises:
        Exception: If a page cannot be loaded, the acta table is not found,
        or row extraction fails. Exceptions are logged before being raised.
    """
    logger.info("📦 Recuperando estadísticas de las actas")
    acta_data = []
    for curso_url in urls_cursos_alumno:
        link_acta = curso_url + 'actas/'
        try:
            driver.get(link_acta)
            time.sleep(2)

            table = driver.find_element(By.CSS_SELECTOR, "table.detalle")
            rows = table.find_elements(By.TAG_NAME, "tr")

            for row in rows:
                try:
                    cols = row.find_elements(By.TAG_NAME, "th") + row.find_elements(By.TAG_NAME, "td")
                    if len(cols) == 1:
                        label = cols[0].text.strip()
                        value = ""
                    elif len(cols) >= 2:
                        label = cols[0].text.strip()
                        value = cols[1].text.strip()
                    else:
                        continue
                    acta_data.append({
                        "Curso URL": curso_url,
                        "Indicador": label,
                        "Valor": value
                    })
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing row in acta")
        except Exception as e:
            logger.warning(f"⚠️ Error cargando página de acta")
    logger.info(f"ℹ️️ Total de actas registradas: {len(acta_data)}")
    logger.info(f"✅ Recuperación de estadísticas de actas finalizada")
    return(pd.DataFrame(acta_data))        
    
def extraer_datos_ucursos(
    driver: WebDriver,
    urls_cursos_alumno: list[str]
) -> dict[str, pd.DataFrame]:
    """
    Extract grades and acta data from U-Cursos and return them in a dictionary
    of DataFrames.

    The function orchestrates the execution of `data_notas` and `data_actas`
    to retrieve evaluations (grades and averages) and acta details
    (indicators and values) for all student courses provided in the URL list.
    Results are returned in a dictionary with descriptive keys. If the
    extraction process fails, an empty or partially filled dictionary is
    returned.

    Args:
        driver (WebDriver): A Selenium WebDriver instance pointing to U-Cursos.
        urls_cursos_alumno (list[str]): List of URLs for the student's courses.

    Returns:
        dict[str, pandas.DataFrame]: A dictionary containing:
            - "Notas_ucursos": DataFrame with evaluations and averages per course.
            - "Actas_ucursos": DataFrame with acta indicators and values per course.

        Returns an empty or partially filled dictionary if extraction fails.

    Raises:
        Exception: If either the notes or acta extraction fails. The exception
        is logged and the dictionary with available data (possibly empty) is returned.
    """
    logger.info("🚀 Inicio webscrapping de u-cursos")
    df_dict = {}
    try:
        df_notas = data_notas(driver,urls_cursos_alumno)
        df_actas = data_actas(driver,urls_cursos_alumno)

        df_dict = {
            "Notas_ucursos": df_notas,
            "Actas_ucursos": df_actas
        }
        logger.info("✅ Extracción de datos de u-cursos completada")
        return(df_dict)
    except Exception as e:
        logger.exception(f"❌ Error al extraer datos de u-cursos: {e}")
        return(df_dict)