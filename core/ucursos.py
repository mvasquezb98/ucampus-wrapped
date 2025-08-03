import pandas as pd
from selenium.webdriver.common.by import By
import time
import openpyxl

def urls_cursos(driver):
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
    return(urls_cursos_alumno)

def extraer_datos_ucursos(driver,urls_cursos_alumno):
  notas_data = []
  acta_data = []

  for curso_url in urls_cursos_alumno:
      link_notas = curso_url + 'notas/alumno'
      link_acta = curso_url + 'actas/'

      #### NOTAS ####
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
                    print(f"⚠️ Could not extract row: {e}")
          else:
              print(f"⚠️ Tabla de notas no encontrada en {link_notas}")
      except Exception as e:
          print(f"❌ Error cargando página de notas: {e}")

      #### ACTA ####
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
                  print(f"⚠️ Error parsing row in acta: {e}")
      except Exception as e:
          print(f"❌ Error cargando página de acta: {e}")

  # Convertir a DataFrames
  df_notas = pd.DataFrame(notas_data)
  df_actas = pd.DataFrame(acta_data)
  # Guardar en Excel con varias hojas
  with pd.ExcelWriter("datos_ucursos.xlsx", engine="openpyxl") as writer:
      df_notas.to_excel(writer, sheet_name="Notas_ucursos", index=False)
      df_actas.to_excel(writer, sheet_name="Actas_ucursos", index=False)
  print("✅ Datos exportados correctamente a 'datos_ucursos.xlsx'")
  return(df_notas,df_actas)