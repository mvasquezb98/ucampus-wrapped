import pandas as pd
import numpy as np
import os
import unicodedata
import logging
from config.logger import setup_logger

setup_logger() 
logger = logging.getLogger(__name__)
# Emojis: ✅ ❌ ⚠️ 📂 💾 ℹ️️ 🚀 📦 📊 🎨 🖊️ 📌 ➡️ 🎯 🏷️ 📏

def load_acta_data(
    file_name: str,
    sheet_name: str
) -> pd.DataFrame:
    """
    Load a specific sheet from an Excel file containing acta data.

    This function builds the path to the Excel file located in the
    ``datos/output`` directory relative to the project root, and attempts
    to read the specified sheet using pandas. If the file or sheet cannot
    be read, it logs the error and returns an empty DataFrame.

    Args:
        file_name (str): Name of the Excel file (e.g., "clean_data.xlsx").
        sheet_name (str): Name of the sheet to load from the Excel file.

    Returns:
        pandas.DataFrame: A DataFrame containing the contents of the
        requested sheet. Returns an empty DataFrame if loading fails.

    Raises:
        Exception: Logs and handles any exception that occurs during
        file access or reading. The exception is not re-raised; instead,
        an empty DataFrame is returned.
    """
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_path,'datos', 'output',file_name)
    
    try:
        data = pd.read_excel(file_path, sheet_name)
        logger.info(f"✅ Datos cargados para identificar Acta Milagrosa ({file_name} - Sheet: {sheet_name}). ")
        return data
    except Exception as e:
        logger.exception(f"❌ Error cargando los datos: {e}")
        return pd.DataFrame()

def limpiar_texto(s: str) -> str:
    """
    Normalize and clean a text string for consistent comparisons.

    The function applies the following transformations:
      - Converts all characters to uppercase.
      - Replaces hyphens with spaces.
      - Removes periods.
      - Strips a leading space if present.
      - Removes diacritical marks (tildes/accents) using Unicode
        normalization.

    Args:
        s (str): Input string to clean.

    Returns:
        str: The cleaned and normalized string.
    """
    # Pasar a mayúsculas
    s = s.upper()
    # Quitar guiones
    s = s.replace("-", " ")
    # Quitar puntos
    s = s.replace(".", "")
    if s[0]==" ":
        s = s[1:]
    # Reemplazar tildes (normalizando Unicode)
    s = ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )
    return s
def create_df_examen() -> pd.DataFrame:
    """
    Build a DataFrame containing only exam records from the "Evaluaciones" sheet.

    This function loads evaluation data, normalizes the evaluation names,
    and filters out records that are not considered exams. It keeps only
    entries that match a predefined list of exam labels, excluding known
    non-exam labels. If multiple exam entries exist for the same course,
    it retains the most recent one by year and semester and selects the
    evaluation label with the shortest text.

    Steps:
        1. Define lists of exam labels and non-exam labels.
        2. Normalize all labels using ``limpiar_texto``.
        3. Load the "Evaluaciones" sheet from ``clean_data.xlsx``.
        4. Drop rows with missing "Promedio".
        5. Rename "Promedio" → "Nota".
        6. Clean the "Evaluación" column using ``limpiar_texto``.
        7. Exclude evaluations matching non-exam patterns.
        8. Keep only evaluations in the predefined exam list.
        9. If multiple exams exist for a course:
           - Sort by year and semester, keeping the latest record.
           - Select the exam entry with the shortest label.
           - Log a warning.

    Returns:
        pandas.DataFrame: A DataFrame containing only exam evaluations
        with at least the following columns:
            - "Curso URL" (str): URL of the course.
            - "Codigo_curso" (str): Course code.
            - "Año" (int): Academic year.
            - "Semestre" (int): Academic semester.
            - "Periodo" (str): Period label.
            - "Evaluación" (str): Normalized exam label.
            - "Nota" (str | float): Exam grade.

        If no exam entries are found, returns an empty DataFrame
        with the expected columns.

    Raises:
        Exception: Any error during file loading is caught and logged.
        In such cases, an empty DataFrame is returned.
    """
    lista_examen = [
        "Examen",
        "Examen 2 no presencial",
        "Examen Adicional",
        "Examen no presencial",
        "Examen Recuperativo",
        "Examen recuperativo",
        "Examen Recuperativo",
        "Examen Recuperativo",
        "Examen Recuperativo",
        "Examen Recuperativo",
        "Examen Recuperativo",
        "Examen v1",
        "Examen v2",
        "Nota Examen",
        "Examen-Promedio"
    ]
    lista_no_examen = [
        "Nota Post ",
        "Nota Post ",
        "Nota Post-",
        "Nota Presentación a ",
        "Nota Presentación ",
        "Notas Controles y ",
        "Promedio Controles y ",
        "Promedio Ponderado presentación a .",
        "Situación pre-",
        "Situación Pre-",
        "Nota de Presentación a ",
        "Nota de presentación a ",
        "-Pregunta1",
        "-Pregunta2",
        "-Pregunta3",
        "-Pregunta4",
        "-P1",
        "-P2",
        "-P3",
        "-P4",
    ]
    lista_examen = [limpiar_texto(x) for x in lista_examen]
    lista_no_examen = [limpiar_texto(x) for x in lista_no_examen]
    pattern = "|".join(lista_no_examen)
    
    df_evaluaciones = pd.DataFrame(columns=["Curso URL","Codigo_curso","Año","Semestre","Periodo","Evaluación","Promedio"])
    
    try:
        df_evaluaciones = load_acta_data(file_name='clean_data.xlsx', sheet_name='Evaluaciones')
    except Exception as e:
         logger.exception(f"❌ Error en la carga de datos: {e}.")
         
    logger.info("📦 Filtrando evaluaciones para los exámenes")     
    df_evaluaciones.dropna(subset=["Promedio"],inplace=True)
    df_examen = df_evaluaciones.copy()
    df_examen.rename(columns={"Promedio": "Nota"}, inplace=True)
    df_examen["Evaluación"] = df_examen["Evaluación"].apply(lambda x: limpiar_texto(x))    
    df_examen = df_examen[~df_examen["Evaluación"].str.contains(pattern, case=False, na=False)]
    df_examen = df_examen[ df_examen["Evaluación"].isin(lista_examen)]   
    if len(df_examen)>len(df_examen["Codigo_curso"].unique()):
                
        df_examen = (
            df_examen.sort_values(["Año", "Semestre"])
                    .drop_duplicates(subset=["Codigo_curso"], keep="last")
        )
        df_examen = (
            df_examen.loc[
                df_examen.groupby("Codigo_curso")["Evaluación"].apply(lambda x: x.str.len().idxmin())
            ]
        )
        logger.info("⚠️ There are multiple exam entries for the same course. Please check the data.")
    logger.info(f"ℹ️️Total de exámenes registrados: {len(df_examen)}")
    logger.info(f"✅ Filtrado de exámenes completado.")
    return(df_examen)

def create_df_nota_presentacion(df_examen) -> pd.DataFrame:
    """
    Build a DataFrame with actual or estimated "Nota de Presentación" for each course.

    This function extracts "Notas de Presentación" (NP) from the *Evaluaciones*
    sheet of ``clean_data.xlsx``, normalizes their labels, and keeps the most
    recent NP entry per course. When the NP is missing, it estimates the value
    using the final course grade (Promedio) and the exam grade (Nota) from the
    *Historial* sheet, based on a weighted formula. Finally, it merges actual
    and estimated NPs into a single column.

    Steps:
        1. Load the "Evaluaciones" sheet to extract NP records.
        2. Normalize evaluation labels with ``limpiar_texto`` and filter those
           matching NP patterns.
        3. Keep the latest NP per course (by year and semester).
        4. Convert "Nota Presentacion" to numeric and drop invalid values.
        5. Load the "Historial" sheet to retrieve final grades (Promedio).
        6. Identify approved courses (exclude R, T, E).
        7. Merge exam notes with historical data and estimate NP with:
           (Promedio - 0.4 * Nota_examen) / 0.6
        8. Merge estimated NP with actual NP when available.
        9. Prefer the actual NP if present; otherwise, keep the estimate.
        10. Round the final NP to two decimals and clean redundant columns.

    Args:
        df_examen (pandas.DataFrame): DataFrame of exam notes with at least:
            - "Curso URL"
            - "Codigo_curso"
            - "Año"
            - "Semestre"
            - "Periodo"
            - "Evaluación"
            - "Nota"

    Returns:
        pandas.DataFrame: A DataFrame with estimated or actual "Nota de Presentación",
        including at least the following columns:
            - "Curso URL" (str): URL of the course.
            - "Codigo_curso" (str): Course code.
            - "Año" (int): Academic year.
            - "Semestre" (int): Academic semester.
            - "Periodo" (str): Period label.
            - "Nota" (float): Exam grade.
            - "Promedio Curso" (str | float): Final grade recorded in actas.
            - "Promedio" (str | float): Final average grade used in calculations.
            - "Nota Presentacion estimada" (float): Actual or estimated NP.

    Raises:
        Exception: Any error during data loading is caught and logged.
        In such cases, the function continues with empty DataFrames and
        returns an empty result.
    """
    pattern_np = (        
        r"(?:"
        r"NOTA\s+(DE\s+)?PRESENTACI[ÓO]N(\s*\(NP\))?(\s+(A\s+)?EXAMEN)?"
        r"|PROMEDIO\s+PONDERADO\s+PRESENTACI[ÓO]N\s+A\s+EXAMEN"
        r"|SITUACION\s+PRE[- ]?EXAMEN"
        r"|NOTA\s+PRE[- ]?EXAMEN"
        r"|PRE[- ]?EXAMEN"
        r")$"
    )
    
    df_evaluaciones = pd.DataFrame(columns=["Curso URL","Codigo_curso","Año","Semestre","Periodo","Evaluación","Promedio"])
    
    try:
        df_evaluaciones = load_acta_data(file_name='clean_data.xlsx', sheet_name='Evaluaciones')
    except Exception as e:
         logger.exception(f"❌ Error en la carga de datos: {e}.")
    
    logger.info("📦 Filtrando evaluaciones para las Notas de Presentación")
    df_nota_presentacion = df_evaluaciones.copy()
    df_nota_presentacion.dropna(subset=["Promedio"],inplace=True)
    df_nota_presentacion.rename(columns={"Evaluación": "Evaluación NP","Promedio": "Nota Presentacion"}, inplace=True)
    df_nota_presentacion["Evaluación NP"] = df_nota_presentacion["Evaluación NP"].apply(lambda x: limpiar_texto(x))
    
    df_nota_presentacion = df_nota_presentacion.loc[
        df_nota_presentacion["Evaluación NP"].astype(str).str.contains(pattern_np, case=False, na=False),
        ["Curso URL","Codigo_curso","Año","Semestre","Periodo","Evaluación NP","Nota Presentacion"]
    ]

    df_nota_presentacion = (
        df_nota_presentacion.sort_values(["Año", "Semestre"])
                            .drop_duplicates(subset=["Codigo_curso"], keep="last")
    )

    df_nota_presentacion["Nota Presentacion"] = pd.to_numeric(
        df_nota_presentacion["Nota Presentacion"], errors="coerce"
    )
    df_nota_presentacion = df_nota_presentacion[df_nota_presentacion["Nota Presentacion"].notna()]
    
    logger.info("📦 Cargando datos del Historial para estimar Notas de Presentación faltantes")
    df_nota_presentacion_estimada = pd.DataFrame()
    notas_examen = pd.DataFrame()
    df_historial = pd.DataFrame(columns=["Curso URL","Codigo_curso","Año","Semestre","Periodo","Promedio","Nota Final"])
    
    try:
        df_historial = load_acta_data(file_name='clean_data.xlsx', sheet_name='Historial')
    except Exception as e:
         logger.exception(f"❌ Error en la carga de datos: {e}.")
             
    df_historial.rename(columns={"Promedio": "Promedio Curso", "Nota Final": "Promedio"}, inplace=True)
    cursos_aprobados = df_historial[(~df_historial["Promedio"].isin(["R","T","E"]))]["Codigo_curso"].unique()         
    notas_examen = df_examen[df_examen["Codigo_curso"].isin(cursos_aprobados)]
    notas_actas = df_historial[(df_historial["Codigo_curso"].isin(df_examen["Codigo_curso"])) & (~df_historial["Promedio"].isin(["R","T","E"]))]#["Promedio"].astype(float).reset_index(drop=True)
    df_nota_presentacion_estimada = pd.merge(notas_examen, notas_actas, on=["Curso URL","Codigo_curso","Año","Semestre"], how="left")   
    m = 0.4
    df_nota_presentacion_estimada["Nota Presentacion estimada"] = (df_nota_presentacion_estimada["Promedio"].astype(float) - m * df_nota_presentacion_estimada["Nota"].astype(float))/(1-m)
    
    
    df_nota_presentacion_estimada = pd.merge(df_nota_presentacion_estimada,df_nota_presentacion, on=["Curso URL","Codigo_curso","Año","Semestre"],how="left")
    df_nota_presentacion_estimada.drop(columns=["Periodo_y", "Periodo", "Evaluación NP"], inplace=True)
    df_nota_presentacion_estimada.rename(columns={"Periodo_x": "Periodo"}, inplace=True)
    
    df_nota_presentacion_estimada["Nota Presentacion estimada"] = np.where(
        df_nota_presentacion_estimada["Nota Presentacion"].notna(),
        df_nota_presentacion_estimada["Nota Presentacion"],        # usa la nota real si existe
        df_nota_presentacion_estimada["Nota Presentacion estimada"] # si no, conserva la estimada
    )
    df_nota_presentacion_estimada["Nota Presentacion estimada"]  = df_nota_presentacion_estimada["Nota Presentacion estimada"].round(2)
    df_nota_presentacion_estimada.drop(columns=["Evaluación","Nota Presentacion"], inplace=True)
    logger.info("ℹ️️Total de Notas de Presentación: {}".format(len(df_nota_presentacion_estimada)))
    logger.info("✅ Cálculo de Notas de Presentación completado.")
    return(df_nota_presentacion_estimada)

def create_df_candidatos_acta_milagrosa(
    df_nota_presentacion_estimada: pd.DataFrame
) -> pd.DataFrame:
    """
    Identify candidate courses for "Acta Milagrosa" cases.

    This function selects courses where the exam grade ("Nota") is
    strictly greater than the final recorded grade ("Promedio").
    These cases are potential "acta milagrosa" candidates, where
    the exam result would allow improving the course outcome.
    The candidates are then sorted by final grade and estimated
    presentation grade.

    Args:
        df_nota_presentacion_estimada (pandas.DataFrame): DataFrame that includes
            actual or estimated presentation notes along with exam and final
            grades. Expected columns include:
            - "Nota" (float): Exam grade.
            - "Promedio" (float): Final grade recorded.
            - "Nota Presentacion estimada" (float): Estimated or actual NP.

    Returns:
        pandas.DataFrame: A filtered and sorted DataFrame containing only
        candidate "acta milagrosa" cases, with the same structure as the input.
        Rows are sorted in ascending order by "Promedio" and then by
        "Nota Presentacion estimada".
    """
    df_candidatos_acta_milagrosa = df_nota_presentacion_estimada[df_nota_presentacion_estimada["Nota"] > df_nota_presentacion_estimada["Promedio"]]
    df_candidatos_acta_milagrosa.sort_values(by=["Promedio","Nota Presentacion estimada"], ascending=[True,True], inplace=True)
    logger.info(f"ℹ️️Total de candidatos a Acta Milagrosa: {len(df_candidatos_acta_milagrosa)}")
    logger.info("✅ Identificación de candidatos a Acta Milagrosa completada.")
    return(df_candidatos_acta_milagrosa)
    
def get_acta_milagrosa_data() -> (pd.DataFrame):
    """
    Identify and build the "Acta Milagrosa" DataFrame.

    This function orchestrates the process of finding the "Acta Milagrosa"
    case: a course where the exam grade is higher than the final course grade,
    and the lowest estimated "Nota de Presentación" is observed. It integrates
    evaluation data, exam records, and historical course data to reconstruct
    the acta with an additional row labeled as "Acta".

    Steps:
        1. Initialize empty DataFrames for evaluaciones and historial with
           the expected schema.
        2. Build exam data with ``create_df_examen``.
        3. Create a DataFrame of presentation notes (actual or estimated)
           with ``create_df_nota_presentacion``.
        4. Identify candidate courses with ``create_df_candidatos_acta_milagrosa``.
        5. Select the candidate course with the minimum "Nota Presentacion estimada".
        6. Extract its corresponding evaluation records from evaluaciones.
        7. Create a new row labeled as "Acta" from the historial and append it
           to the final DataFrame.

    Returns:
        pandas.DataFrame: A DataFrame representing the identified "Acta Milagrosa"
        case. It contains the same columns as the evaluaciones input:
            - "Curso URL"
            - "Codigo_curso"
            - "Año"
            - "Semestre"
            - "Periodo"
            - "Evaluación"
            - "Promedio"

        If no acta can be identified, returns an empty DataFrame with the
        expected schema.

    Raises:
        Exception: Any error during the process is caught and logged.
        In such cases, the function returns an empty DataFrame.
    """
    logger.info("🚀 Iniciando identificación de Acta Milagrosa...")
    df_evaluaciones = pd.DataFrame(columns=["Curso URL","Codigo_curso","Año","Semestre","Periodo","Evaluación","Promedio"])
    df_historial = pd.DataFrame(columns=["Curso URL","Codigo_curso","Año","Semestre","Periodo","Promedio","Nota Final"])
    df_examen = create_df_examen() 
    df_nota_presentacion = create_df_nota_presentacion(df_examen)
    df_candidatos_acta_milagrosa = create_df_candidatos_acta_milagrosa(df_nota_presentacion)
    df_acta_milagrosa = pd.DataFrame(columns=df_evaluaciones.columns)
    try:    
        logger.info("ℹ️️ Identificando Acta Milagrosa...")
        curso_acta_milagrosa = df_candidatos_acta_milagrosa[df_candidatos_acta_milagrosa["Nota Presentacion estimada"] == df_candidatos_acta_milagrosa["Nota Presentacion estimada"].min()]["Codigo_curso"].tolist()[0]
        logger.debug(f"📌curso_acta_milagrosa: {curso_acta_milagrosa}")
        df_acta_milagrosa = df_evaluaciones[df_evaluaciones["Codigo_curso"] == curso_acta_milagrosa]        
        
        row_acta = df_historial[df_historial["Codigo_curso"] == curso_acta_milagrosa]
        row_acta["Evaluación"] = "Acta"
        row_acta = row_acta[["Curso URL","Evaluación","Promedio","Codigo_curso","Año", "Semestre","Periodo"]]
        row_acta.reindex(columns=df_acta_milagrosa.columns)
        
        df_acta_milagrosa = pd.concat([df_acta_milagrosa, row_acta], ignore_index=True)
        logger.info("✅ Acta Milagrosa identificada.")
    except Exception as e:
        logger.exception(f"❌ Error identificando Acta Milagrosa: {e}.")
        
    logger.info(f"ℹ️️ Total de filas en Acta Milagrosa: {len(df_acta_milagrosa)}")
    logger.info("✅ Proceso de identificación de Acta Milagrosa completado.")
    return(df_acta_milagrosa)