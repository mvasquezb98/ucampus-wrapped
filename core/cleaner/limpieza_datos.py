import pandas as pd
import numpy as np
import os
from pathlib import Path
import logging
from config.logger import setup_logger

setup_logger() 
logger = logging.getLogger(__name__)
# Emojis: ✅ ❌ ⚠️ 📂 💾 ℹ️️ logger.info("")


def carga_datos(settings,base_path):
    salida = Path(settings["output_dir"])
    data_path = os.path.join(base_path,salida)
    ucursos_sheets_df = pd.DataFrame()
    ucampus_sheets_df = pd.DataFrame() 
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

def limpiar_recuento(df_dict):
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

def limpiar_actas_ucursos(df_dict):
    ## LIMPIEZA ACTA DE UCURSOS
    df_dict["Actas_ucursos"] = df_dict["Actas_ucursos"].pivot(index="Curso URL", columns="Indicador", values="Valor").reset_index().drop(columns=["Estadísticas del Curso"])
    df_dict["Actas_ucursos"]["Codigo_curso"] = df_dict["Actas_ucursos"]["Curso URL"].apply(lambda x: x.split("/")[-3])
    df_dict["Actas_ucursos"]["Año"] = df_dict["Actas_ucursos"]["Curso URL"].apply(lambda x: x.split("/")[4]).astype(int)
    df_dict["Actas_ucursos"]["Semestre"] = df_dict["Actas_ucursos"]["Curso URL"].apply(lambda x: x.split("/")[5]).astype(int)
    df_dict["Actas_ucursos"]["Periodo"] = df_dict["Actas_ucursos"]["Año"].astype(str) + " " + df_dict["Actas_ucursos"]["Semestre"].apply(lambda x: "Otoño" if str(x)=="1" else("Primavera" if str(x)=="2" else "Verano")).astype(str)
    return(df_dict)

def limpiar_notas_ucursos(df_dict):
    ## LIMPIEZA NOTAS DE UCURSOS
    df_dict["Notas_ucursos"]["Codigo_curso"] = df_dict["Notas_ucursos"]["Curso URL"].apply(lambda x: x.split("/")[-3])
    df_dict["Notas_ucursos"]["Año"] = df_dict["Notas_ucursos"]["Curso URL"].apply(lambda x: x.split("/")[4]).astype(int)
    df_dict["Notas_ucursos"]["Semestre"] = df_dict["Notas_ucursos"]["Curso URL"].apply(lambda x: x.split("/")[5]).astype(int)
    df_dict["Notas_ucursos"]["Periodo"] = df_dict["Notas_ucursos"]["Año"].astype(str) + " " + df_dict["Notas_ucursos"]["Semestre"].apply(lambda x: "Otoño" if str(x)=="1" else("Primavera" if str(x)=="2" else "Verano")).astype(str)
    return(df_dict)

def limpiar_tabla_notas(df_dict):
    ## LIMPIEZA TABLA NOTAS
    df_dict["notas"]["CAR"] = df_dict["notas"]["CRA"].apply(lambda x: np.round(float(x.split("/")[0])*100/float(x.split("/")[1]),1))
    return(df_dict)

def limpiar_indicadores_titulo(df_dict):
    ##LIMPIEZA INDICADORES Y TITULO
    df_dict["titulo"]["Fecha"] = df_dict["titulo"]["Examen / Título"].apply(lambda x: x.split(" Fecha ")[1])
    df_dict["titulo"]["Examen / Título"] = df_dict["titulo"]["Examen / Título"].apply(lambda x: x.split(" Ingeniería Civil")[0])
    df_dict["titulo"] = pd.DataFrame(df_dict["titulo"].iloc[0,:]).reset_index()
    df_dict["titulo"].columns = ["Campo", "Valor"]
    df_dict["indicadores"].columns = ["Campo", "Valor"]
    return(df_dict)

def limpiar_semestre(df_dict):
    ## LIMPIEZA TABLA SEMESTRE
    df_dict["semestre"]["Año"] = df_dict["semestre"]["Periodo"].str.extract(r"(\d{4})", expand=False).astype(int)
    df_dict["semestre"]["Semestre"] = df_dict["semestre"]["Periodo"].apply(lambda x: 2 if "Otoño" in str(x) else (1 if "Primavera" in str(x) else (3 if "Verano" in str(x) else np.nan)))
    df_dict["semestre"]["Codigo_curso"] = df_dict["semestre"]["Curso"].apply(lambda x: str(x.split("-")[0]))
    return(df_dict)

def limpiar_docencia(df_dict):
    ## LIMPIEZA TABLA DOCENCIA
    df_dict["docencia"]["Periodo"] = df_dict["docencia"]["Año"].astype(str) + " " + df_dict["docencia"]["Semestre"].astype(str)
    df_dict["docencia"]["Semestre"] = df_dict["docencia"]["Semestre"].apply(lambda x: 2 if "Otoño" in str(x) else (1 if "Primavera" in str(x) else (3 if "Verano" in str(x) else np.nan)))
    df_dict["docencia"]["Año"] = df_dict["docencia"]["Año"].astype(int)
    return(df_dict)

def limpiar_UB(df_dict):
    ## LIMPIEZA UB
    df_dict["UB_eliminadas"]["Estado"] = "Eliminada"
    df_dict["UB_eliminadas"] = df_dict["UB_eliminadas"].reindex(columns=df_dict["UB"].columns)
    return(df_dict)

def creacion_tablas_finales(df_dict):
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

def exportar_tablas_finales(Evaluaciones, Datos, Historial, UB, Docencia, settings,base_path):
    salida = Path(settings["output_dir"])
    data_path = os.path.join(base_path,salida)
    salida = os.path.join(data_path,"clean_data.xlsx") 
    tablas = {
        "Evaluaciones": Evaluaciones,
        "Datos": Datos,
        "Historial": Historial,
        "UB": UB,
        "Docencia": Docencia,
    }
    with pd.ExcelWriter(salida, engine="xlsxwriter") as writer:
        for nombre, df in tablas.items():
            sheet = nombre[:31]
            df.to_excel(writer, sheet_name=sheet, index=False)

def limpiar_datos(settings,base_path):
    ## LIMPIEZA DE DATOS                  
    df_dict = carga_datos(settings,base_path)
    df_dict = limpiar_recuento(df_dict)
    df_dict = limpiar_actas_ucursos(df_dict)
    df_dict = limpiar_notas_ucursos(df_dict)
    df_dict = limpiar_tabla_notas(df_dict)
    df_dict = limpiar_indicadores_titulo(df_dict)
    df_dict = limpiar_semestre(df_dict)
    df_dict = limpiar_docencia(df_dict)
    df_dict = limpiar_UB(df_dict)
    Evaluaciones, Datos, Historial, UB, Docencia = creacion_tablas_finales(df_dict)
    exportar_tablas_finales(Evaluaciones, Datos, Historial, UB, Docencia, settings,base_path)