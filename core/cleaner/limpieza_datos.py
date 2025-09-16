import pandas as pd
import numpy as np
import os
from pathlib import Path
import logging
from config.logger import setup_logger
from typing import Any
from core.cleaner.acta_milagrosa import get_acta_milagrosa_data

setup_logger() 
logger = logging.getLogger(__name__)
# Emojis: ✅ ❌ ⚠️ 📂 💾 ℹ️️ 🚀 📦 📊 🎨 🖊️ 📌 ➡️ 🎯 🏷️ 📏

def load_scrapped_data(
    settings: dict[str, Any],
    base_path: str
) -> dict[str, pd.DataFrame]:
    """
    Load Excel files from the configured output directory and return their
    contents as a dictionary of DataFrames.

    The function looks for Excel files in the directory defined by
    ``base_path`` combined with ``settings["output_dir"]``. It specifically
    searches for files containing the keywords "ucursos" or "ucampus" in
    their filenames. For each matching file, all sheets are read and stored
    as DataFrames in a dictionary. The resulting dictionaries are merged
    and returned. If the directory does not exist, a warning is logged and
    an empty dictionary is returned.

    Args:
        settings (dict[str, Any]): Dictionary containing configuration
            values. Must include the key ``"output_dir"`` indicating the
            subdirectory where Excel files are located.
        base_path (str): Base path where the output directory resides.

    Returns:
        dict[str, pandas.DataFrame]: A dictionary mapping sheet names to
        DataFrames, combining all sheets found in "ucursos" and "ucampus"
        Excel files. Returns an empty dictionary if no files are found.

    Raises:
        Exception: If there is an error while reading the Excel files.
        The exception will propagate, and no data will be returned.
    """
    salida = Path(settings["output_dir"])
    data_path = os.path.join(base_path,salida)
    ucursos_sheets_df = {}
    ucampus_sheets_df = {} 
    if os.path.exists(data_path):
        for file in os.listdir(data_path):
            if file.endswith('.xlsx') and not file.startswith('~$'):
                file_path = os.path.join(data_path, file)
                if 'ucursos' in file or 'UCURSOS' in file:
                    ucursos_sheets_df = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')                
                if 'ucampus' in file or 'UCAMPUS' in file:
                    ucampus_sheets_df = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
    else:
        logger.info(f"⚠️ Directory '{data_path}' does not exist.")

    df_dict = ucursos_sheets_df | ucampus_sheets_df
    return(df_dict)

def limpiar_recuento(
    df_dict: dict[str, pd.DataFrame]
) -> dict[str, pd.DataFrame]:
    """
    Clean and restructure the "recuento" DataFrame contained in the input
    dictionary, and generate additional subsets by semester.

    This function applies several transformations to the "recuento" table:
    - Removes rows containing the keyword "candidatos" in the "Ramo" column.
    - Splits the "Unnamed: 1" column into two parts: `plan_name` and `count_str`.
    - Extracts the numeric count (N) from strings of the form "X de Y".
    - Builds a new "Plan" column that repeats the plan name across its block.
    - Drops the auxiliary "Unnamed: 1" column.
    - Creates three subsets of the data based on the "Semestre" and "Ramo"
      values:
        * "recuento_semestre_nan_ramo int": Rows where "Semestre" is NaN and
          "Ramo" is numeric, restructured with "Créditos" and "Nota".
        * "recuento_semestre_nan_ramo_str": Rows where "Semestre" is NaN and
          "Ramo" is non-numeric text, restructured into "Plan", "Subplan",
          and "Créditos".
        * "recuento_semestre_ok": Rows where "Semestre" has valid values,
          cleaned and expanded with "Periodo", "Año", "Semestre" (mapped to
          1/2/3), numeric "Nota", and "Codigo_curso".

    Args:
        df_dict (dict[str, pd.DataFrame]): A dictionary of DataFrames that
            must include a key "recuento" containing the recuento table.

    Returns:
        dict[str, pandas.DataFrame]: The updated dictionary including:
            - "recuento": The cleaned and transformed recuento DataFrame.
            - "recuento_semestre_nan_ramo int": Subset with numeric "Ramo"
              and missing "Semestre".
            - "recuento_semestre_nan_ramo_str": Subset with string "Ramo"
              and missing "Semestre".
            - "recuento_semestre_ok": Subset with valid "Semestre" values.

    Raises:
        Exception: If the "recuento" key is missing in `df_dict` or if
        the DataFrame does not have the expected structure (columns such
        as "Ramo", "Semestre", "Créditos", "Nota", "Unnamed: 1").
    """
    ## LIMPIEZA RECUENTO DE CREDITOS
    df = df_dict["recuento"].copy()
    # 1) Eliminar filas con "candidatos" en columna Ramo (sea numérica o texto)
    df = df[~df["Ramo"].astype(str).str.contains(r"\bcandidatos\b", case=False, na=False)]
    # 2) Separar 'Unnamed: 1' por salto de línea, dejando: plan_name y count_str (ej. "Todo 3 de 3")
    parts = df["Unnamed: 1"].astype(str).str.split("\n", n=1, expand=True)
    df["plan_name"] = parts[0].str.strip()
    df["count_str"] = parts[1].str.strip()
    # 3) Extraer N desde la segunda parte (tomamos el número a la IZQUIERDA de "de")
    #    Ej: "10 de 10" -> N = 10
    df["N"] = (
        df["count_str"]
        .str.extract(r"(\d+)\s*de\s*\d+", expand=False)  # 1er grupo: número antes de 'de'
        .astype("Int64")
        .fillna(0)
        .astype(int)
    )
    # 4) Construir la columna Plan repitiendo el nombre del plan N+1 veces
    Plan = []
    current = None
    remaining = 0
    for plan_name, N in df[["plan_name", "N"]].itertuples(index=False, name=None):
        # Si esta fila es cabecera (tiene patrón "N de N"), arranca un bloque nuevo
        if N > 0:
            current = plan_name
            remaining = N + 1  # incluye cabecera
        if remaining > 0 and current is not None:
            Plan.append(current)
            remaining -= 1
        else:
            Plan.append(np.nan)
    df["Plan"] = Plan
    # 5) Eliminar columna auxiliar
    df = df.drop(columns=["Unnamed: 1"])
    df_dict["recuento"] = df
    # 6) Subsets según Semestre
    subset_semestre_nan_ramo_int = df[df["Semestre"].isna() & df["Ramo"].str.isnumeric()].iloc[:, :-4].copy()
    subset_semestre_nan_ramo_int["Nota"] = subset_semestre_nan_ramo_int["Créditos"]
    subset_semestre_nan_ramo_int["Créditos"] = subset_semestre_nan_ramo_int["Ramo"].astype(int)
    subset_semestre_nan_ramo_int.drop(columns=["Ramo"], inplace=True)
    subset_semestre_nan_ramo_str = df[df["Semestre"].isna() & df["Ramo"].apply(lambda x: isinstance(x, str) and not x.isnumeric())].iloc[:, :-5].copy()
    subset_semestre_nan_ramo_str.columns = ["Plan", "Subplan", "Créditos"]
    subset_semestre_ok  = df[df["Semestre"].notna()].iloc[:, :-3].copy()
    subset_semestre_ok["Periodo"] = subset_semestre_ok["Semestre"]
    subset_semestre_ok["Año"] = subset_semestre_ok["Semestre"].str.extract(r"(\d{4})", expand=False).astype(int)
    subset_semestre_ok["Semestre"] = subset_semestre_ok["Semestre"].apply(lambda x: 2 if "Otoño" in str(x) else (1 if "Primavera" in str(x) else (3 if "Verano" in str(x) else np.nan)))
    subset_semestre_ok["Nota"] = (
        subset_semestre_ok["Nota"]
        .astype(str)
        .str.replace(r"\*", "", regex=True)
        .replace("T", "7")
        .replace("", np.nan)
        .apply(lambda x: float(x) if pd.notnull(x) and str(x).replace('.', '', 1) else pd.NA)
        #.astype("Int64")
    )
    subset_semestre_ok["Codigo_curso"] = subset_semestre_ok["Ramo"].apply(lambda x: x.split(" ")[0])
    df_dict["recuento_semestre_nan_ramo int"] = subset_semestre_nan_ramo_int
    df_dict["recuento_semestre_nan_ramo_str"] = subset_semestre_nan_ramo_str
    df_dict["recuento_semestre_ok"] = subset_semestre_ok
    return(df_dict)    

def limpiar_actas_ucursos(
    df_dict: dict[str, pd.DataFrame]
    ) -> dict[str, pd.DataFrame]:
    """
    Clean and restructure the "Actas_ucursos" DataFrame within the input
    dictionary.

    This function pivots the raw acta data extracted from U-Cursos so that
    each indicator becomes a column, removes unnecessary fields, and adds
    derived columns for course code, academic year, semester, and period
    name. The "Periodo" column is formatted as "<Año> <Semestre>" with
    the semester expressed as "Otoño", "Primavera", or "Verano".

    Args:
        df_dict (dict[str, pd.DataFrame]): A dictionary of DataFrames that
            must include a key "Actas_ucursos" with columns:
            - "Curso URL": URL string of the course.
            - "Indicador": Indicator name.
            - "Valor": Indicator value.
            - "Estadísticas del Curso": (dropped in cleaning).

    Returns:
        dict[str, pandas.DataFrame]: The updated dictionary where the
        "Actas_ucursos" DataFrame has been cleaned and enriched with
        the following additional columns:
            - "Codigo_curso": Extracted course code from the URL.
            - "Año": Extracted academic year as integer.
            - "Semestre": Extracted semester as integer (1, 2, or 3).
            - "Periodo": Concatenation of "Año" and semester name.

    Raises:
        Exception: If "Actas_ucursos" is missing from `df_dict` or the
        DataFrame lacks the expected columns.
    """
    ## LIMPIEZA ACTA DE UCURSOS
    df_dict["Actas_ucursos"] = df_dict["Actas_ucursos"].pivot(index="Curso URL", columns="Indicador", values="Valor").reset_index().drop(columns=["Estadísticas del Curso"])
    df_dict["Actas_ucursos"]["Codigo_curso"] = df_dict["Actas_ucursos"]["Curso URL"].apply(lambda x: x.split("/")[-3])
    df_dict["Actas_ucursos"]["Año"] = df_dict["Actas_ucursos"]["Curso URL"].apply(lambda x: x.split("/")[4]).astype(int)
    df_dict["Actas_ucursos"]["Semestre"] = df_dict["Actas_ucursos"]["Curso URL"].apply(lambda x: x.split("/")[5]).astype(int)
    df_dict["Actas_ucursos"]["Periodo"] = df_dict["Actas_ucursos"]["Año"].astype(str) + " " + df_dict["Actas_ucursos"]["Semestre"].apply(lambda x: "Otoño" if str(x)=="1" else("Primavera" if str(x)=="2" else "Verano")).astype(str)
    return(df_dict)

def limpiar_notas_ucursos(
    df_dict: dict[str, pd.DataFrame]
    ) -> dict[str, pd.DataFrame]:
    """
    Clean and enrich the "Notas_ucursos" DataFrame within the input dictionary.

    This function processes the course URLs to extract structured academic
    information. It adds columns for course code, academic year, semester,
    and period name. The "Periodo" column is formatted as "<Año> <Semestre>"
    where the semester is expressed as "Otoño", "Primavera", or "Verano".

    Args:
        df_dict (dict[str, pd.DataFrame]): A dictionary of DataFrames that
            must include a key "Notas_ucursos" with at least the column:
            - "Curso URL": URL string of the course.

    Returns:
        dict[str, pandas.DataFrame]: The updated dictionary where the
        "Notas_ucursos" DataFrame has been enriched with additional columns:
            - "Codigo_curso": Extracted course code from the URL.
            - "Año": Extracted academic year as integer.
            - "Semestre": Extracted semester as integer (1, 2, or 3).
            - "Periodo": Concatenation of "Año" and semester name.

    Raises:
        Exception: If "Notas_ucursos" is missing from `df_dict` or the
        DataFrame lacks the expected "Curso URL" column.
    """
    ## LIMPIEZA NOTAS DE UCURSOS
    df_dict["Notas_ucursos"]["Codigo_curso"] = df_dict["Notas_ucursos"]["Curso URL"].apply(lambda x: x.split("/")[-3])
    df_dict["Notas_ucursos"]["Año"] = df_dict["Notas_ucursos"]["Curso URL"].apply(lambda x: x.split("/")[4]).astype(int)
    df_dict["Notas_ucursos"]["Semestre"] = df_dict["Notas_ucursos"]["Curso URL"].apply(lambda x: x.split("/")[5]).astype(int)
    df_dict["Notas_ucursos"]["Periodo"] = df_dict["Notas_ucursos"]["Año"].astype(str) + " " + df_dict["Notas_ucursos"]["Semestre"].apply(lambda x: "Otoño" if str(x)=="1" else("Primavera" if str(x)=="2" else "Verano")).astype(str)
    return(df_dict)

def limpiar_tabla_notas(
    df_dict: dict[str, pd.DataFrame]
    ) -> dict[str, pd.DataFrame]:
    """
    Clean and enrich the "notas" DataFrame within the input dictionary by
    calculating the CAR (Cumulative Achievement Rate).

    The function processes the "CRA" column, which is expected to be in the
    format "value/total", and computes CAR as the percentage of `value` over
    `total`, rounded to one decimal place. The result is stored in a new
    column "CAR".

    Args:
        df_dict (dict[str, pd.DataFrame]): A dictionary of DataFrames that
            must include a key "notas" with a column:
            - "CRA" (str): Cumulative record string in the format "value/total".

    Returns:
        dict[str, pandas.DataFrame]: The updated dictionary where the
        "notas" DataFrame has an additional column:
            - "CAR" (float): Percentage of completed credits, rounded to
              one decimal place.

    Raises:
        Exception: If "notas" is missing from `df_dict` or if the "CRA"
        column does not follow the expected "value/total" format.
    """
    ## LIMPIEZA TABLA NOTAS
    df_dict["notas"]["CAR"] = df_dict["notas"]["CRA"].apply(lambda x: np.round(float(x.split("/")[0])*100/float(x.split("/")[1]),1))
    return(df_dict)

def limpiar_indicadores_titulo(
    df_dict: dict[str, pd.DataFrame]
    ) -> dict[str, pd.DataFrame]:
    """
    Clean and restructure the "titulo" and "indicadores" DataFrames within
    the input dictionary.

    This function processes the "titulo" DataFrame to extract the exam date
    from the "Examen / Título" column, removes redundant text, and reshapes
    the table into a key-value format with columns "Campo" and "Valor". It
    also renames the columns of the "indicadores" DataFrame to match the same
    key-value structure for consistency.

    Args:
        df_dict (dict[str, pd.DataFrame]): A dictionary of DataFrames that
            must include the keys:
            - "titulo": DataFrame with at least the column "Examen / Título".
            - "indicadores": DataFrame with arbitrary columns to be renamed.

    Returns:
        dict[str, pandas.DataFrame]: The updated dictionary where:
            - "titulo": Reshaped DataFrame with columns ["Campo", "Valor"],
              containing exam information and date.
            - "indicadores": DataFrame with columns renamed to ["Campo", "Valor"].

    Raises:
        Exception: If "titulo" or "indicadores" are missing from `df_dict`,
        or if the "Examen / Título" column does not contain the expected
        format with " Fecha " and " Ingeniería Civil".
    """
    ##LIMPIEZA INDICADORES Y TITULO
    df_dict["titulo"]["Fecha"] = df_dict["titulo"]["Examen / Título"].apply(lambda x: x.split(" Fecha ")[1])
    df_dict["titulo"]["Examen / Título"] = df_dict["titulo"]["Examen / Título"].apply(lambda x: x.split(" Ingeniería Civil")[0])
    df_dict["titulo"] = pd.DataFrame(df_dict["titulo"].iloc[0,:]).reset_index()
    df_dict["titulo"].columns = ["Campo", "Valor"]
    df_dict["indicadores"].columns = ["Campo", "Valor"]
    return(df_dict)

def limpiar_semestre(
    df_dict: dict[str, pd.DataFrame]
    ) -> dict[str, pd.DataFrame]:
    """
    Clean and enrich the "semestre" DataFrame within the input dictionary.

    This function extracts the academic year from the "Periodo" column,
    maps textual semester names to numeric values, and derives a course
    code from the "Curso" column. The transformations produce three
    additional columns: "Año", "Semestre", and "Codigo_curso".

    Args:
        df_dict (dict[str, pd.DataFrame]): A dictionary of DataFrames that
            must include a key "semestre" with at least the columns:
            - "Periodo" (str): String containing the year and semester
              (e.g., "2023 Otoño").
            - "Curso" (str): Course name including a code prefix.

    Returns:
        dict[str, pandas.DataFrame]: The updated dictionary where the
        "semestre" DataFrame has been enriched with:
            - "Año" (int): Extracted four-digit year.
            - "Semestre" (int | float): Mapped semester number
              (2 for Otoño, 1 for Primavera, 3 for Verano, NaN otherwise).
            - "Codigo_curso" (str): Extracted course code from the "Curso" field.

    Raises:
        Exception: If "semestre" is missing from `df_dict` or required
        columns are not present.
    """
    ## LIMPIEZA TABLA SEMESTRE
    df_dict["semestre"]["Año"] = df_dict["semestre"]["Periodo"].str.extract(r"(\d{4})", expand=False).astype(int)
    df_dict["semestre"]["Semestre"] = df_dict["semestre"]["Periodo"].apply(lambda x: 2 if "Otoño" in str(x) else (1 if "Primavera" in str(x) else (3 if "Verano" in str(x) else np.nan)))
    df_dict["semestre"]["Codigo_curso"] = df_dict["semestre"]["Curso"].apply(lambda x: str(x.split("-")[0]))
    return(df_dict)

def limpiar_docencia(
    df_dict: dict[str, pd.DataFrame]
    ) -> dict[str, pd.DataFrame]:
    """
    Clean and enrich the "docencia" DataFrame within the input dictionary.

    This function constructs a new "Periodo" column by concatenating "Año"
    and "Semestre", converts semester names into numeric codes, and ensures
    that the "Año" column is stored as an integer.

    Args:
        df_dict (dict[str, pd.DataFrame]): A dictionary of DataFrames that
            must include a key "docencia" with at least the columns:
            - "Año" (str | int): Academic year.
            - "Semestre" (str): Semester name ("Otoño", "Primavera", "Verano").

    Returns:
        dict[str, pandas.DataFrame]: The updated dictionary where the
        "docencia" DataFrame has been enriched with:
            - "Periodo" (str): Concatenation of year and semester.
            - "Semestre" (int | float): Mapped semester number
              (2 for Otoño, 1 for Primavera, 3 for Verano, NaN otherwise).
            - "Año" (int): Year converted to integer.

    Raises:
        Exception: If "docencia" is missing from `df_dict` or required
        columns are not present.
    """
    ## LIMPIEZA TABLA DOCENCIA
    df_dict["docencia"]["Periodo"] = df_dict["docencia"]["Año"].astype(str) + " " + df_dict["docencia"]["Semestre"].astype(str)
    df_dict["docencia"]["Semestre"] = df_dict["docencia"]["Semestre"].apply(lambda x: 2 if "Otoño" in str(x) else (1 if "Primavera" in str(x) else (3 if "Verano" in str(x) else np.nan)))
    df_dict["docencia"]["Año"] = df_dict["docencia"]["Año"].astype(int)
    return(df_dict)

def limpiar_UB(
    df_dict: dict[str, pd.DataFrame]
    ) -> dict[str, pd.DataFrame]:
    """
    Clean and align the "UB" and "UB_eliminadas" DataFrames within the input dictionary.

    This function standardizes the "UB_eliminadas" table by:
    - Adding a new column "Estado" with the constant value "Eliminada".
    - Reindexing its columns to match the structure of the "UB" DataFrame
      so both tables share the same schema.

    Args:
        df_dict (dict[str, pd.DataFrame]): A dictionary of DataFrames that
            must include the keys:
            - "UB": DataFrame containing active scholarship units (UBs).
            - "UB_eliminadas": DataFrame containing eliminated scholarship units.

    Returns:
        dict[str, pandas.DataFrame]: The updated dictionary where
        "UB_eliminadas" has been aligned with "UB" and enriched with
        the "Estado" column.

    Raises:
        Exception: If either "UB" or "UB_eliminadas" is missing from `df_dict`.
    """
    ## LIMPIEZA UB
    df_dict["UB_eliminadas"]["Estado"] = "Eliminada"
    df_dict["UB_eliminadas"] = df_dict["UB_eliminadas"].reindex(columns=df_dict["UB"].columns)
    return(df_dict)

def creacion_tablas_finales(
    df_dict: dict[str, pd.DataFrame]
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Build the final, curated tables from previously cleaned intermediate DataFrames.

    This function assembles five output tables:
      1) **Evaluaciones**: Copy of ``df_dict["Notas_ucursos"]``.
      2) **Datos**: Vertical concatenation of ``df_dict["titulo"]`` and ``df_dict["indicadores"]``.
      3) **Historial**: Merge between ``df_dict["Actas_ucursos"]`` and
         ``df_dict["recuento_semestre_ok"]`` on ``"Codigo_curso"`` (left join),
         with business rules applied:
            - Set ``Plan = "Reprobado"`` where ``"Nota Final" == "R"``.
            - Set ``Plan = "Eximido"`` where ``"Nota Final" == "T"``.
            - Fill remaining ``Plan`` with ``"No utilizado"``.
            - Drop auxiliary columns, normalize column suffixes, and attach
              ``"Créditos"`` via a merge with ``df_dict["semestre"]`` on
              ``["Codigo_curso", "Periodo"]``.
      4) **UB**: Concatenation of ``df_dict["UB"]`` and ``df_dict["UB_eliminadas"]``.
      5) **Docencia**: Copy of ``df_dict["docencia"]``.

    Args:
        df_dict (dict[str, pd.DataFrame]): Dictionary of intermediate DataFrames.
            Expected keys include:
              - "Notas_ucursos"
              - "titulo"
              - "indicadores"
              - "Actas_ucursos"
              - "recuento_semestre_ok"
              - "semestre"
              - "UB"
              - "UB_eliminadas"
              - "docencia"

    Returns:
        tuple[pandas.DataFrame, pandas.DataFrame, pandas.DataFrame, pandas.DataFrame, pandas.DataFrame]:
            A 5-tuple in the following order:
              - ``Evaluaciones``: Evaluations per course (from "Notas_ucursos").
              - ``Datos``: Key–value style info from title and indicators.
              - ``Historial``: Course history enriched with plan usage and credits.
              - ``UB``: Scholarship units (active + eliminated).
              - ``Docencia``: Teaching activities.

    Raises:
        Exception: If required keys are missing from ``df_dict`` or if expected
        merge columns (e.g., "Codigo_curso", "Periodo", "Nota Final") are absent.
    """
    ## CREACION TABLAS FINALES
    Evaluaciones = df_dict["Notas_ucursos"].copy()
    Datos = pd.concat([df_dict["titulo"], df_dict["indicadores"]], ignore_index=True)
    Historial = pd.merge(
        df_dict["Actas_ucursos"],
        df_dict["recuento_semestre_ok"],
        left_on="Codigo_curso",
        right_on="Codigo_curso",
        how="left"
    )
    Historial[Historial["Nota Final"] == "R"]["Plan"] = "Reprobado"
    Historial[Historial["Nota Final"] == "T"]["Plan"] = "Eximido"
    Historial["Plan"] = Historial["Plan"].fillna("No utilizado") 
    Historial.drop(columns=["Nota","Semestre_y","Periodo_y","Año_y"], inplace=True)
    Historial.columns = [col if not col.endswith(('_x')) else col[:-2] for col in Historial.columns]
    Historial["Créditos"] = pd.merge(Historial,df_dict["semestre"],on=["Codigo_curso","Periodo"])["Creditos"]
    UB = pd.concat([df_dict["UB"], df_dict["UB_eliminadas"]], ignore_index=True)
    Docencia = df_dict["docencia"].copy()
    
    return(Evaluaciones, Datos, Historial, UB, Docencia)

def exportar_tablas_finales(
    Evaluaciones: pd.DataFrame,
    Datos: pd.DataFrame,
    Historial: pd.DataFrame,
    UB: pd.DataFrame,
    Docencia: pd.DataFrame,
    Acta_Milagrosa: pd.DataFrame,
    settings: dict[str, Any],
    base_path: str
) -> None:
    """
    Export the final curated tables to a single Excel file.

    This function writes the provided DataFrames (Evaluaciones, Datos,
    Historial, UB, and Docencia) into separate sheets of an Excel workbook
    named ``clean_data.xlsx``. The output file is saved inside the
    ``settings["output_dir"]`` directory under the specified ``base_path``.
    Sheet names are truncated to 31 characters to comply with Excel limits.

    Args:
        Evaluaciones (pandas.DataFrame): DataFrame containing evaluations
            per course.
        Datos (pandas.DataFrame): DataFrame with title and indicator
            information in key–value format.
        Historial (pandas.DataFrame): DataFrame with academic history,
            plan usage, and credits.
        UB (pandas.DataFrame): DataFrame with scholarship units (active and eliminated).
        Docencia (pandas.DataFrame): DataFrame with teaching activities.
        settings (dict[str, Any]): Configuration dictionary. Must include the
            key ``"output_dir"`` indicating the subdirectory for exports.
        base_path (str): Base path where the output directory resides.

    Returns:
        None

    Raises:
        Exception: If writing to Excel fails due to invalid paths, missing
        permissions, or corrupted DataFrames.
    """
    salida = Path(settings["output_dir"])
    data_path = os.path.join(base_path,salida)
    salida = os.path.join(data_path,"clean_data.xlsx") 
    tablas = {
        "Evaluaciones": Evaluaciones,
        "Datos": Datos,
        "Historial": Historial,
        "UB": UB,
        "Docencia": Docencia,
        "Acta_Milagrosa": Acta_Milagrosa
    }
    with pd.ExcelWriter(salida, engine="xlsxwriter") as writer:
        for nombre, df in tablas.items():
            sheet = nombre[:31]
            df.to_excel(writer, sheet_name=sheet, index=False)

def limpiar_datos(
    settings: dict[str, Any],
    base_path: str
) -> None:        
    """
    Orchestrate the full data cleaning pipeline and export the final results.

    This function coordinates all cleaning steps by sequentially calling
    specialized routines to process raw U-Cursos and U-Campus data. It
    produces intermediate cleaned DataFrames (stored in a dictionary),
    constructs the final curated tables, and exports them into a single
    Excel file.

    Steps:
        1. Load raw Excel files using ``load_scrapped_data``.
        2. Apply cleaning functions to individual tables:
        - ``limpiar_recuento``
        - ``limpiar_actas_ucursos``
        - ``limpiar_notas_ucursos``
        - ``limpiar_tabla_notas``
        - ``limpiar_indicadores_titulo``
        - ``limpiar_semestre``
        - ``limpiar_docencia``
        - ``limpiar_UB``
        3. Generate the final output tables with ``creacion_tablas_finales``:
        - Evaluaciones
        - Datos
        - Historial
        - UB
        - Docencia
        4. Export all final tables into ``clean_data.xlsx`` with
        ``exportar_tablas_finales``.

    Args:
        settings (dict[str, Any]): Configuration dictionary containing at least
            the key ``"output_dir"`` specifying the folder where input/output
            files are located.
        base_path (str): Base path where the output directory resides.

    Returns:
        None

    Raises:
        Exception: If any cleaning step, table creation, or export fails.
        Errors are propagated after being raised in the underlying functions.
    """
    ## LIMPIEZA DE DATOS                  
    df_dict = load_scrapped_data(settings,base_path)
    df_dict = limpiar_recuento(df_dict)
    df_dict = limpiar_actas_ucursos(df_dict)
    df_dict = limpiar_notas_ucursos(df_dict)
    df_dict = limpiar_tabla_notas(df_dict)
    df_dict = limpiar_indicadores_titulo(df_dict)
    df_dict = limpiar_semestre(df_dict)
    df_dict = limpiar_docencia(df_dict)
    df_dict = limpiar_UB(df_dict)
    Evaluaciones, Datos, Historial, UB, Docencia = creacion_tablas_finales(df_dict)
    Acta_Milagrosa = get_acta_milagrosa_data(Evaluaciones, Historial)
    exportar_tablas_finales(Evaluaciones, Datos, Historial, UB, Docencia,Acta_Milagrosa, settings,base_path)