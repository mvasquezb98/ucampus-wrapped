import pandas as pd
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException

import logging
from config.logger import setup_logger
setup_logger()
log = logging.getLogger(__name__)

def datos_indicadores(driver):
  indicadores= {}

  # Indicadores del estudiante
  try:
      indicadores_dl = driver.find_element(By.ID, "indicadores")
      dt_tags = indicadores_dl.find_elements(By.TAG_NAME, "dt")
      dd_tags = indicadores_dl.find_elements(By.TAG_NAME, "dd")
      for dt, dd in zip(dt_tags, dd_tags):
          indicadores[dt.text.strip()] = dd.text.strip()
      indicadores['id_indicador'] = 1
      print("Carga Exitosa: Indicadores")
      df_indicadores = pd.DataFrame(indicadores.items(), columns=["Indicador", "Valor"])
      return(df_indicadores)
  except Exception:
      print("❌ Error al cargar Indicadores del Estudiante")

def datos_resumen(driver):
  try:
    # Forzar visibilidad si está oculto por CSS
    driver.execute_script("document.getElementById('resumen').style.display = 'block';")
    print("✅ Div 'resumen' visible. Extrayendo tabla...")
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
    print(f"✅ Extraídas {len(datos)} filas.")

    df_cursos = pd.DataFrame(filas)
    df_semestre = pd.DataFrame(datos)
    print("Carga Exitosa: Resumen notas")
    return(df_semestre,df_cursos)
  except Exception:
    print("❌ Error al cargar resumen")

def datos_labores_docentes(driver):
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
    print("Carga Exitosa: Labores docentes")
    return(df_dictados)
  except Exception:
    print("❌ Error al cargar labores docentes")

def datos_examenes_y_titulo(driver):
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
    print("Carga Exitosa: Exámenes de Grado y/o Título")
    return(df_examenes)
  except Exception:
    print("❌ Error al cargar Exámenes de Grado y/o Título")

def datos_UB(driver):
    from selenium.common.exceptions import ElementClickInterceptedException
    import pandas as pd
    import time
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    url = "https://ucampus.uchile.cl/m/fcfm_unidades_becarias/becas_alumno"
    try:
        log.info("🔁 Navegando a página de Unidades Becarias...")
        wait = WebDriverWait(driver, 10)
        driver.get(url)

        wait.until(EC.presence_of_element_located((By.ID, "ano_chosen")))
        df_final = pd.DataFrame()

        year_select = driver.find_element(By.ID, "ano")
        year_values = [opt.get_attribute("value") for opt in year_select.find_elements(By.TAG_NAME, "option")]

        for year_value in year_values:
            log.info(f"📆 Extrayendo datos del año {year_value}...")

            try:
                dropdown = wait.until(EC.element_to_be_clickable((By.ID, "ano_chosen")))
                dropdown.click()
            except ElementClickInterceptedException:
                log.warning("⚠️ Dropdown interceptado, usando JavaScript click.")
                dropdown = driver.find_element(By.ID, "ano_chosen")
                driver.execute_script("arguments[0].click();", dropdown)

            time.sleep(0.5)

            year_options = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.chosen-results li")))
            year_option = next((li for li in year_options if li.text.strip() == year_value), None)

            if not year_option:
                log.warning(f"⚠️ No se encontró la opción para el año {year_value}.")
                continue

            try:
                year_option.click()
            except ElementClickInterceptedException:
                log.warning("⚠️ Año interceptado, usando JavaScript click.")
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

        return df_final

    except Exception as e:
        log.exception(f"❌ Error general al navegar en Unidades Becarias: {e}")
        return pd.DataFrame()



def datos_UB_eliminados(driver):
    from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, NoSuchElementException
    import pandas as pd
    import time
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    url = "https://ucampus.uchile.cl/m/fcfm_unidades_becarias/becas_alumno"
    try:
        log.info("🔁 Navegando a página de Unidades Becarias...")
        wait = WebDriverWait(driver, 10)
        driver.get(url)

        wait.until(EC.presence_of_element_located((By.ID, "ano_chosen")))
        df_final = pd.DataFrame()

        year_select = driver.find_element(By.ID, "ano")
        year_values = [opt.get_attribute("value") for opt in year_select.find_elements(By.TAG_NAME, "option")]

        for year_value in year_values:
            log.info(f"📆 Extrayendo datos del año {year_value}...")

            try:
                dropdown = wait.until(EC.element_to_be_clickable((By.ID, "ano_chosen")))
                dropdown.click()
            except ElementClickInterceptedException:
                log.warning("⚠️ Dropdown interceptado, usando JavaScript click.")
                dropdown = driver.find_element(By.ID, "ano_chosen")
                driver.execute_script("arguments[0].click();", dropdown)

            time.sleep(0.5)

            year_options = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.chosen-results li")))
            year_option = next((li for li in year_options if li.text.strip() == year_value), None)

            if not year_option:
                log.warning(f"⚠️ No se encontró la opción para el año {year_value}.")
                continue

            try:
                year_option.click()
            except ElementClickInterceptedException:
                log.warning("⚠️ Año interceptado, usando JavaScript click.")
                driver.execute_script("arguments[0].click();", year_option)

            time.sleep(1.5)

            try:
                h2 = wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//h2[contains(text(), 'UBs Eliminadas')]")
                ))
                table = h2.find_element(By.XPATH, "following-sibling::table[1]")
            except (TimeoutException, NoSuchElementException):
                log.warning(f"⚠️ No hay tabla de UBs Eliminadas para el año {year_value}.")
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

        return df_final

    except Exception as e:
        log.exception(f"❌ Error general al navegar en Unidades Becarias: {e}")
        return pd.DataFrame()

def datos_recuento(driver):
    url = "https://ucampus.uchile.cl/m/fcfm_bia/recuento_uds"
    print("🔁 Navegando a página de Recuento de UDs...")

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
            print("⚠️ No se encontraron datos en la tabla.")
            return pd.DataFrame()

        df = pd.DataFrame(datos, columns=encabezados)
        print("✅ Datos de recuento extraídos correctamente.")
        return df

    except Exception as e:
        print(f"❌ Error al obtener el recuento de UDs: {e}")
        return pd.DataFrame()

def extraer_datos_ucampus(driver):
  dict_indicadores = datos_indicadores(driver)
  df_cursos, df_semestre = datos_resumen(driver) # type: ignore
  df_dictados = datos_labores_docentes(driver)
  df_examenes = datos_examenes_y_titulo(driver)
  df_UB = datos_UB(driver)
  df_UB_eliminados = datos_UB_eliminados(driver)
  df_recuento = datos_recuento(driver)
  return(dict_indicadores, df_cursos, df_semestre, df_dictados, df_examenes, df_UB, df_UB_eliminados, df_recuento)
