import pandas as pd
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, NoSuchElementException
from selenium.webdriver.remote.webdriver import WebDriver
import logging
from config.logger import setup_logger

setup_logger() 
logger = logging.getLogger(__name__)
# Emojis: ✅ ❌ ⚠️ 📂 💾 ℹ️️ 🚀 📦 📊 🎨 🖊️ 📌 ➡️ 🎯 🏷️ 📏

def datos_indicadores(driver: WebDriver) -> pd.DataFrame:
    """
    Extract student indicators from the web page and return them as a DataFrame. 
    
    The function searches for the HTML section with id "indicadores", collects
    all <dt> (indicator labels) and <dd> (indicator values) pairs, and organizes
    them into a dictionary. The dictionary is then converted into a DataFrame
    with two columns: "Indicador" and "Valor". An additional field
    "id_indicador" is added for identification. If the extraction fails, an
    empty DataFrame is returned.
    
    Args:
        driver (WebDriver): A Selenium WebDriver instance pointing to the page
            that contains the student's indicators.

    Returns:
        pandas.DataFrame: A DataFrame with two columns:
            - "Indicador" (str): The name of the indicator.
            - "Valor" (str): The corresponding value.
        Returns an empty DataFrame if indicators cannot be loaded.

    Raises:
        Exception: If Selenium cannot locate or process the indicators section.
        The exception is logged and an empty DataFrame is returned.
        """
    logger.info("📦 Recuperando indicadores")
    indicadores= {}
    df_indicadores = pd.DataFrame()
    # Indicadores del estudiante
    try:
        indicadores_dl = driver.find_element(By.ID, "indicadores")
        dt_tags = indicadores_dl.find_elements(By.TAG_NAME, "dt")
        dd_tags = indicadores_dl.find_elements(By.TAG_NAME, "dd")
        for dt, dd in zip(dt_tags, dd_tags):
            indicadores[dt.text.strip()] = dd.text.strip()
        indicadores['id_indicador'] = 1
        logger.info("✅ Carga Exitosa: Indicadores")
        df_indicadores = pd.DataFrame(indicadores.items(), columns=["Indicador", "Valor"])
        return(df_indicadores)
    except Exception:
        logger.exception("⚠️ Error al cargar Indicadores del Estudiante")
        return(df_indicadores)

def datos_resumen(driver: WebDriver) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extract the academic summary from the web page and return it as two DataFrames.

    The function accesses the "resumen" section of the student’s academic record,
    ensures its visibility, and parses the table to extract both semester-level
    indicators (CRA, CAR) and detailed course information (course name, credits,
    and grade). Results are returned as two DataFrames: one summarizing each
    semester and another listing individual courses.

    Args:
        driver (WebDriver): A Selenium WebDriver instance pointing to the page
            containing the academic summary table.

    Returns:
        tuple[pandas.DataFrame, pandas.DataFrame]:
            - The first DataFrame contains semester-level data with the columns:
                * "Periodo" (str): Academic period or semester identifier.
                * "CRA" (str): Student’s CRA (academic performance metric).
                * "CAR" (str): Student’s CAR (career progression metric).
            - The second DataFrame contains course-level data with the columns:
                * "Periodo" (str): Academic period when the course was taken.
                * "Curso" (str): Course code or name.
                * "Creditos" (float): Number of credits for the course.
                * "Nota" (str): Grade received in the course.

    Raises:
        Exception: If the "resumen" section or its table cannot be accessed or parsed.
        In such cases, the exception is logged and two empty DataFrames are returned.
    """
    logger.info("📦 Recuperando resumen de ramos cursados por semestre")
    df_semestre = pd.DataFrame()
    df_cursos = pd.DataFrame()
    try:
        # Forzar visibilidad si está oculto por CSS
        driver.execute_script("document.getElementById('resumen').style.display = 'block';")
        logger.info("ℹ️️ Div 'resumen' visible. Extrayendo tabla...")
        resumen = driver.find_element(By.ID,"resumen")
        tabla = resumen.find_element(By.TAG_NAME, "table")
        filas = tabla.find_elements(By.TAG_NAME, "tr")
        datos = []
        cursos = {}

        for fila in filas:
            columnas = fila.find_elements(By.TAG_NAME, "td")
            if not columnas:
                continue  # saltar encabezados

            periodo = columnas[0].text.strip()
            cra_car = columnas[1].text.strip().split("\n")
            cra = cra_car[0]
            car = cra_car[1] #columnas[2].text.strip()

            semestre =[]

            for col in columnas[3:]:
                texto = col.text.strip()
                if texto and texto != '\xa0':
                    cursos_semestre = texto.split(" - ")
                    cursos_semestre = cursos_semestre[0].split()+[cursos_semestre[1]]
                    resumen_semestre = {}
                    resumen_semestre["Curso"] = cursos_semestre[0]
                    resumen_semestre["Créditos"] = float(cursos_semestre[1])
                    resumen_semestre["Nota"] = cursos_semestre[2]
                    semestre.append(resumen_semestre)
            cursos[periodo] = semestre
            datos.append({
                "Periodo": periodo,
                "CRA": cra,
                "CAR": car
            })
        filas = []

        for periodo, ramos in cursos.items():
            for ramo in ramos:
                filas.append({
                    "Periodo": periodo,
                    "Curso": ramo["Curso"],
                    "Creditos": ramo["Créditos"],
                    "Nota": ramo["Nota"]
                })
        logger.info(f"ℹ️️ Extraídas {len(datos)} filas.")

        df_cursos = pd.DataFrame(filas)
        df_semestre = pd.DataFrame(datos)
        logger.info("✅ Carga Exitosa: Resumen notas")
        return(df_semestre,df_cursos)
    except Exception:
        logger.exception("⚠️ Error al cargar resumen")
        return(df_semestre,df_cursos)

def datos_labores_docentes(driver: WebDriver) -> pd.DataFrame:
    """
    Extract the table of teaching activities (courses taught by the instructor)
    from the web page and return it as a structured DataFrame.

    The function waits for the "cursos_dictados" section to appear, retrieves the
    associated table, and parses its rows and columns. It cleans and restructures
    the data by normalizing column names, extracting the academic year, splitting
    the course column into separate name and code fields, and reordering columns
    for readability. Rows corresponding to separators or incomplete data are
    removed. If extraction fails, an empty DataFrame is returned.

    Args:
        driver (WebDriver): A Selenium WebDriver instance pointing to the page
            containing the instructor's teaching activities.

    Returns:
        pandas.DataFrame: A DataFrame with the following columns:
            - "Año" (str or int): Academic year of the course.
            - "Semestre" (str): Semester during which the course was taught.
            - "Nombre" (str): Name of the course.
            - "Código" (str): Course code.
            - "Cargo" (str): Instructor's role in the course.

        Returns an empty DataFrame if the data cannot be extracted.

    Raises:
        Exception: If Selenium cannot locate or parse the teaching activities
        table. The exception is logged and an empty DataFrame is returned.
    """
    logger.info("📦 Recuperando cursos dictados")
    df_dictados = pd.DataFrame()
    try:
        # Esperar a que el h2 con id "cursos_dictados" esté presente
        wait = WebDriverWait(driver, 10)
        header = wait.until(EC.presence_of_element_located((By.ID, "cursos_dictados")))

        # Obtener la tabla que viene justo después
        tabla = header.find_element(By.XPATH, 'following-sibling::table[1]')

        # Obtener los encabezados de la tabla
        encabezados = [th.text.strip() for th in tabla.find_elements(By.TAG_NAME, "th")]

        # Obtener filas del cuerpo de la tabla
        filas = tabla.find_elements(By.XPATH, ".//tbody/tr[td]")  # Evita los separadores

        datos = []
        for fila in filas:
            celdas = fila.find_elements(By.TAG_NAME, "td")
            fila_datos = [celda.text.strip() for celda in celdas]
            datos.append(fila_datos)

        # Convertir a DataFrame
        df_dictados = pd.DataFrame(datos, columns=encabezados)

        # Rename columns just in case they're weirdly named
        df_dictados.columns = [col.strip() for col in df_dictados.columns]

        # Step 1: Rename first column to 'Nº' if needed
        if df_dictados.columns[0] != "Nº":
            df_dictados.columns.values[0] = "Nº"

        # Step 2: Create a new 'Año' column
        año_col = []
        current_year = None

        for val in df_dictados["Nº"]:
            if str(val).isdigit():
                if len(str(val))==4:
                    current_year = val
                    año_col.append(current_year)
                else:  # Save the year from the separator row
                    año_col.append(None)

        # Step 3: Assign 'Año' column and drop rows that are separators
        df_dictados["Año"] = año_col
        df_dictados = df_dictados[df_dictados["Nº"].apply(lambda x: str(x).isdigit())].reset_index(drop=True)

        # Step 4: Drop the "Nº" column
        df_dictados.drop(columns=["Nº"], inplace=True)
        # Step 1: Split 'Curso' into two parts using newline character
        curso_split = df_dictados["Curso"].str.split("\n", expand=True)

        # Step 2: Assign to new columns 'Nombre' and 'Código'
        df_dictados["Nombre"] = curso_split[0]
        df_dictados["Código"] = curso_split[1]

        # Step 3: Drop the original 'Curso' column if no longer needed
        df_dictados.drop(columns=["Curso"], inplace=True)

        # Optional: Reorder columns for better readability
        df_dictados = df_dictados[["Año", "Semestre", "Nombre", "Código", "Cargo"]]
        df_dictados.dropna(inplace=True)
        logger.info("✅ Carga Exitosa: Labores docentes")
        return(df_dictados)
    except Exception:
        logger.exception("⚠️ Error al cargar labores docentes")
        return(df_dictados)

def datos_examenes_y_titulo(driver: WebDriver) -> pd.DataFrame:
    """
    Extract information about degree and/or title exams from the web page and
    return it as a DataFrame.

    The function waits for the section titled "Exámenes de Grado y/o Título" to
    appear, locates the corresponding table, and extracts its rows. Each row is
    parsed into a record containing the exam or title name, the date, the grade,
    and the advisor professor. The results are returned as a pandas DataFrame.
    If the section or table cannot be found, an empty DataFrame is returned.

    Args:
        driver (WebDriver): A Selenium WebDriver instance pointing to the page
            containing the "Exámenes de Grado y/o Título" section.

    Returns:
        pandas.DataFrame: A DataFrame with the following columns:
            - "Examen / Título" (str): Name of the exam or title.
            - "Fecha" (str): Date of the exam.
            - "Nota" (str): Grade obtained.
            - "Profesor Guía" (str): Name of the advisor professor.

        Returns an empty DataFrame if the data cannot be extracted.

    Raises:
        Exception: If Selenium cannot locate or parse the section or its table.
        The exception is logged and an empty DataFrame is returned.
    """
    logger.info("📦 Recuperando sección Exámenes de Grado y/o Título")
    df_examenes = pd.DataFrame()
    try:
        # Esperar hasta que aparezca el <h2> con el texto exacto
        titulo_h2 = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//h2[normalize-space()="Exámenes de Grado y/o Título"]'))
        )

        # Obtener la siguiente tabla
        tabla_examenes = titulo_h2.find_element(By.XPATH, 'following-sibling::table[1]')

        # Obtener las filas del cuerpo de la tabla
        filas = tabla_examenes.find_elements(By.XPATH, './/tbody/tr')

        # Procesar datos en una lista de diccionarios
        datos = []
        for fila in filas:
            columnas = fila.find_elements(By.TAG_NAME, 'td')
            datos.append({
                "Examen / Título": columnas[0].text.strip().replace("\n", " "),
                "Fecha": columnas[1].text.strip(),
                "Nota": columnas[2].text.strip(),
                "Profesor Guía": columnas[3].text.strip()
            })

        # Convertir a DataFrame
        df_examenes = pd.DataFrame(datos)
        logger.info("✅ Carga Exitosa: Exámenes de Grado y/o Título")
        return(df_examenes)
    except Exception:
        logger.exception("⚠️ Error al cargar Exámenes de Grado y/o Título")
        return(df_examenes)

def datos_UB(driver: WebDriver) -> pd.DataFrame:
    """
    Extract scholarship unit (UB) assignment data from U-Campus and return it
    as a consolidated DataFrame.

    The function navigates to the "Unidades Becarias" page, iterates over all
    available years in the year dropdown menu, and extracts the corresponding
    tables of UB assignments. For each year, the data is collected, stored in
    a DataFrame, and combined into a single result with an additional "Año"
    column indicating the academic year. If an error occurs, an empty or
    partially filled DataFrame is returned.

    Args:
        driver (WebDriver): A Selenium WebDriver instance pointing to the
            U-Campus page for "Unidades Becarias".

    Returns:
        pandas.DataFrame: A DataFrame containing the extracted UB assignment
        data with the following columns:
            - All original columns from the UB assignment tables (varies by system).
            - "Año" (str): The academic year associated with the assignment.

        Returns an empty or partially filled DataFrame if extraction fails.

    Raises:
        Exception: If navigation, dropdown interaction, or table parsing fails.
        The exception is logged and a DataFrame with available data (possibly
        empty) is returned.
    """
    logger.info("📦 Recuperando historial de pagos de UB")
    url = "https://ucampus.uchile.cl/m/fcfm_unidades_becarias/becas_alumno"
    df_final = pd.DataFrame()
    try:
        logger.info("🔁 Navegando a página de Unidades Becarias...")
        wait = WebDriverWait(driver, 10)
        driver.get(url)

        wait.until(EC.presence_of_element_located((By.ID, "ano_chosen")))

        year_select = driver.find_element(By.ID, "ano")
        year_values = [opt.get_attribute("value") for opt in year_select.find_elements(By.TAG_NAME, "option")]

        for year_value in year_values:
            logger.info(f"📆 Extrayendo datos del año {year_value}...")

            try:
                dropdown = wait.until(EC.element_to_be_clickable((By.ID, "ano_chosen")))
                dropdown.click()
            except ElementClickInterceptedException:
                logger.warning("⚠️ Dropdown interceptado, usando JavaScript click.")
                dropdown = driver.find_element(By.ID, "ano_chosen")
                driver.execute_script("arguments[0].click();", dropdown)

            time.sleep(0.5)

            year_options = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.chosen-results li")))
            year_option = next((li for li in year_options if li.text.strip() == year_value), None)

            if not year_option:
                logger.warning(f"⚠️ No se encontró la opción para el año {year_value}.")
                continue

            try:
                year_option.click()
            except ElementClickInterceptedException:
                logger.warning("⚠️ Año interceptado, usando JavaScript click.")
                driver.execute_script("arguments[0].click();", year_option)

            time.sleep(1.5)

            h2 = wait.until(EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'UBs Asignadas')]")))
            table = h2.find_element(By.XPATH, "following-sibling::table[1]")

            headers = [th.text.strip() for th in table.find_elements(By.TAG_NAME, "th")]
            rows = table.find_elements(By.XPATH, ".//tbody/tr")

            data = []
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) < len(headers):
                    continue
                data.append([col.text.strip() for col in cols])

            df = pd.DataFrame(data, columns=headers)
            df["Año"] = year_value
            df_final = pd.concat([df_final, df], ignore_index=True)
        logger.info("✅ Carga Exitosa: Historial de pagos de UB")
        return(df_final)

    except Exception as e:
        logger.exception(f"⚠️ Error general al navegar en Unidades Becarias: {e}")
        return(df_final)

def datos_UB_eliminados(driver: WebDriver) -> pd.DataFrame:
    """
    Extract data about eliminated scholarship units (UBs) from U-Campus and
    return it as a consolidated DataFrame.

    The function navigates to the "Unidades Becarias" page, iterates over all
    available years in the year dropdown, and searches for the section titled
    "UBs Eliminadas". If the section is present, it extracts the table rows and
    builds a DataFrame for that year. All yearly results are combined into a
    single DataFrame with an additional "Año" column. If no eliminated UBs are
    found for a given year, that year is skipped. If an error occurs, an empty
    or partially filled DataFrame is returned.

    Args:
        driver (WebDriver): A Selenium WebDriver instance pointing to the
            U-Campus "Unidades Becarias" page.

    Returns:
        pandas.DataFrame: A DataFrame containing eliminated UB data with the
        following columns:
            - All original columns extracted from the "UBs Eliminadas" tables.
            - "Año" (str): The academic year associated with the record.

        Returns an empty or partially filled DataFrame if extraction fails.

    Raises:
        Exception: If navigation, dropdown interaction, or table parsing fails.
        The exception is logged and a DataFrame with available data (possibly
        empty) is returned.
    """
    logger.info("📦 Recuperando historial de UB eliminadas")
    df_final = pd.DataFrame()
    url = "https://ucampus.uchile.cl/m/fcfm_unidades_becarias/becas_alumno"
    try:
        logger.info("🔁 Navegando a página de Unidades Becarias...")
        wait = WebDriverWait(driver, 10)
        driver.get(url)
        wait.until(EC.presence_of_element_located((By.ID, "ano_chosen")))
    
        year_select = driver.find_element(By.ID, "ano")
        year_values = [opt.get_attribute("value") for opt in year_select.find_elements(By.TAG_NAME, "option")]

        for year_value in year_values:
            logger.info(f"📆 Extrayendo datos del año {year_value}...")

            try:
                dropdown = wait.until(EC.element_to_be_clickable((By.ID, "ano_chosen")))
                dropdown.click()
            except ElementClickInterceptedException:
                logger.warning("⚠️ Dropdown interceptado, usando JavaScript click.")
                dropdown = driver.find_element(By.ID, "ano_chosen")
                driver.execute_script("arguments[0].click();", dropdown)

            time.sleep(0.5)

            year_options = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.chosen-results li")))
            year_option = next((li for li in year_options if li.text.strip() == year_value), None)

            if not year_option:
                logger.warning(f"⚠️ No se encontró la opción para el año {year_value}.")
                continue

            try:
                year_option.click()
            except ElementClickInterceptedException:
                logger.warning("⚠️ Año interceptado, usando JavaScript click.")
                driver.execute_script("arguments[0].click();", year_option)

            time.sleep(1.5)

            try:
                h2 = wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//h2[contains(text(), 'UBs Eliminadas')]")
                ))
                table = h2.find_element(By.XPATH, "following-sibling::table[1]")
            except (TimeoutException, NoSuchElementException):
                logger.warning(f"⚠️ No hay tabla de UBs Eliminadas para el año {year_value}.")
                continue

            headers = [th.text.strip() for th in table.find_elements(By.TAG_NAME, "th")]
            rows = table.find_elements(By.XPATH, ".//tbody/tr")

            data = []
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) < len(headers):
                    continue
                data.append([col.text.strip() for col in cols])

            df = pd.DataFrame(data, columns=headers)
            df["Año"] = year_value
            df_final = pd.concat([df_final, df], ignore_index=True)
        logger.info("✅ Carga Exitosa: UB's eliminadas") 
        return(df_final)

    except Exception as e:
        logger.exception(f"❌ Error general al navegar en Unidades Becarias: {e}")
        return(df_final)

def datos_recuento(driver: WebDriver) -> pd.DataFrame:
    """
    Extract the "Recuento de UDs" (unit/credit count) table from U-Campus and
    return it as a pandas DataFrame.

    The function navigates to the recuento page, waits for the main table with
    class "excel" to load, and parses its content. Each <tbody> in the table
    represents a different academic plan, identified by its "id" attribute.
    The function collects all rows, prepends the plan name to each record, and
    organizes the results into a DataFrame with a "Plan" column plus the
    original table headers.

    Args:
        driver (WebDriver): A Selenium WebDriver instance pointing to the page
            containing the recuento de UDs.

    Returns:
        pandas.DataFrame: A DataFrame containing the recuento de UDs data with
        the following columns:
            - "Plan" (str): The academic plan identifier (from the <tbody> id).
            - Additional columns as provided by the table headers (<th>).

        Returns an empty DataFrame if no data is found or if extraction fails.

    Raises:
        Exception: If navigation or table parsing fails. The exception is logged
        and an empty DataFrame is returned.
    """
    logger.info("📦 Recuperando Recuento de UDs")
    url = "https://ucampus.uchile.cl/m/fcfm_bia/recuento_uds"
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)

        # Esperar tabla principal con clase "excel"
        tabla = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "excel")))

        # Obtener encabezados
        encabezados = [th.text.strip() for th in tabla.find_elements(By.TAG_NAME, "th")]

        # Añadir columna 'Plan' al inicio
        encabezados = ["Plan"] + encabezados

        datos = []
        # Iterar sobre los <tbody> de la tabla (uno por plan)
        tbodies = tabla.find_elements(By.TAG_NAME, "tbody")
        for tbody in tbodies:
            plan = tbody.get_attribute("id")  # Usamos el id del tbody como nombre del plan
            filas = tbody.find_elements(By.TAG_NAME, "tr")
            for fila in filas:
                columnas = [td.text.strip() for td in fila.find_elements(By.TAG_NAME, "td")]
                if columnas:  # Evitar filas vacías
                    datos.append([plan] + columnas)

        if not datos:
            logger.info("⚠️ No se encontraron datos en la tabla.")
            return(pd.DataFrame())

        df = pd.DataFrame(datos, columns=encabezados)
        logger.info("✅ Datos de recuento extraídos correctamente.")
        return(df)

    except Exception as e:
        logger.exception(f"❌ Error al obtener el recuento de UDs: {e}")
        return(pd.DataFrame())

def extraer_datos_ucampus(driver: WebDriver) -> dict[str, pd.DataFrame]:
    """
    Extract all available academic data from U-Campus and return it as a
    dictionary of DataFrames.

    The function orchestrates multiple specialized scraping routines to
    collect information about the student, including indicators, semester
    summaries, course grades, teaching activities, degree/title exams,
    scholarship units (assigned and eliminated), and unit counts. Each data
    source is parsed into a pandas DataFrame, and all results are grouped into
    a single dictionary with descriptive keys.

    Args:
        driver (WebDriver): A Selenium WebDriver instance authenticated and
            pointing to U-Campus.

    Returns:
        dict[str, pandas.DataFrame]: A dictionary where each key maps to a
        DataFrame with specific academic data:
            - "indicadores": Personal indicators of the student.
            - "notas": Detailed grades by course.
            - "semestre": Semester-level summaries (CRA, CAR).
            - "docencia": Teaching activities (courses taught).
            - "titulo": Degree and/or title exam results.
            - "UB": Assigned scholarship units by year.
            - "UB_eliminadas": Eliminated scholarship units by year.
            - "recuento": Unit/credit counts by academic plan.

        Returns an empty or partially filled dictionary if extraction fails.

    Raises:
        Exception: If any of the extraction processes fail. The exception is
        logged and a dictionary with available data (possibly empty) is returned.
    """
    logger.info("🚀 Inicio webscrapping de ucampus")

    df_dict = {}
    try:
        dict_indicadores = datos_indicadores(driver)
        df_cursos, df_semestre = datos_resumen(driver) # type: ignore
        df_dictados = datos_labores_docentes(driver)
        df_examenes = datos_examenes_y_titulo(driver)
        df_UB = datos_UB(driver)
        df_UB_eliminados = datos_UB_eliminados(driver)
        df_recuento = datos_recuento(driver)
        df_dict={
            "indicadores": dict_indicadores,
            "notas": df_cursos,
            "semestre": df_semestre,
            "docencia": df_dictados,
            "titulo": df_examenes,
            "UB": df_UB,
            "UB_eliminadas": df_UB_eliminados,
            "recuento": df_recuento
        }
        logger.info("✅ Extracción de datos de ucampus completada")
        return(df_dict)
    except Exception as e:
        logger.exception(f"❌ Error al extraer datos de ucampus: {e}")
        return(df_dict)
