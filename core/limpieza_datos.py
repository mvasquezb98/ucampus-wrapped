#datos_ucursos.xlsx
#data_UCAMPUS_19842174K.xlsx

import pandas as pd
import numpy as np
import os
import re

# CARGA DE DATOS
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(base_path,'datos', 'output')
if os.path.exists(data_path):
    for file in os.listdir(data_path):
        if file.endswith('.xlsx') and not file.startswith('~$'):
            if 'ucursos' in file:
                file_path = os.path.join(data_path, file)
                ucursos_sheets_dict = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
                ucursos_sheet_names = list(ucursos_sheets_dict.keys())
            if 'ucampus' in file or 'UCAMPUS' in file:
                file_path = os.path.join(data_path, file)
                ucampus_sheets_dict = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
                ucampus_sheet_names = list(ucampus_sheets_dict.keys())
else:
    print(f"Directory '{data_path}' does not exist.")
    
#dict_keys(['indicadores', 'notas', 'semestre', 'docencia', 'titulo', 'UB', 'UB_eliminadas', 'recuento'])
#dict_keys(['Notas_ucursos', 'Actas_ucursos'])

try:
    df_dict = ucursos_sheets_dict | ucampus_sheets_dict
except NameError:
    print("No se encontraron hojas de cálculo de UCAMPUS o UCURSOS.")

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

## LIMPIEZA ACTA DE UCURSOS
df_dict["Actas_ucursos"] = df_dict["Actas_ucursos"].pivot(index="Curso URL", columns="Indicador", values="Valor").reset_index().drop(columns=["Estadísticas del Curso"])
df_dict["Actas_ucursos"]["Codigo_curso"] = df_dict["Actas_ucursos"]["Curso URL"].apply(lambda x: x.split("/")[-3])
df_dict["Actas_ucursos"]["Año"] = df_dict["Actas_ucursos"]["Curso URL"].apply(lambda x: x.split("/")[4]).astype(int)
df_dict["Actas_ucursos"]["Semestre"] = df_dict["Actas_ucursos"]["Curso URL"].apply(lambda x: x.split("/")[5]).astype(int)
df_dict["Actas_ucursos"]["Periodo"] = df_dict["Actas_ucursos"]["Año"].astype(str) + " " + df_dict["Actas_ucursos"]["Semestre"].apply(lambda x: "Otoño" if str(x)=="1" else("Primavera" if str(x)=="2" else "Verano")).astype(str)

## LIMPIEZA NOTAS DE UCURSOS
df_dict["Notas_ucursos"]["Codigo_curso"] = df_dict["Notas_ucursos"]["Curso URL"].apply(lambda x: x.split("/")[-3])
df_dict["Notas_ucursos"]["Año"] = df_dict["Notas_ucursos"]["Curso URL"].apply(lambda x: x.split("/")[4]).astype(int)
df_dict["Notas_ucursos"]["Semestre"] = df_dict["Notas_ucursos"]["Curso URL"].apply(lambda x: x.split("/")[5]).astype(int)
df_dict["Notas_ucursos"]["Periodo"] = df_dict["Notas_ucursos"]["Año"].astype(str) + " " + df_dict["Notas_ucursos"]["Semestre"].apply(lambda x: "Otoño" if str(x)=="1" else("Primavera" if str(x)=="2" else "Verano")).astype(str)

## LIMPIEZA TABLA NOTAS
df_dict["notas"]["CAR"] = df_dict["notas"]["CRA"].apply(lambda x: np.round(float(x.split("/")[0])*100/float(x.split("/")[1]),1))

##LIMPIEZA INDICADORES Y TITULO
df_dict["titulo"]["Fecha"] = df_dict["titulo"]["Examen / Título"].apply(lambda x: x.split(" Fecha ")[1])
df_dict["titulo"]["Examen / Título"] = df_dict["titulo"]["Examen / Título"].apply(lambda x: x.split(" Ingeniería Civil")[0])
df_dict["titulo"] = pd.DataFrame(df_dict["titulo"].iloc[0,:]).reset_index()
df_dict["titulo"].columns = ["Campo", "Valor"]
df_dict["indicadores"].columns = ["Campo", "Valor"]

## LIMPIEZA TABLA SEMESTRE
df_dict["semestre"]["Año"] = df_dict["semestre"]["Periodo"].str.extract(r"(\d{4})", expand=False).astype(int)
df_dict["semestre"]["Semestre"] = df_dict["semestre"]["Periodo"].apply(lambda x: 2 if "Otoño" in str(x) else (1 if "Primavera" in str(x) else (3 if "Verano" in str(x) else np.nan)))
df_dict["semestre"]["Codigo_curso"] = df_dict["semestre"]["Curso"].apply(lambda x: str(x.split("-")[0]))

## LIMPIEZA TABLA DOCENCIA
df_dict["docencia"]["Periodo"] = df_dict["docencia"]["Año"].astype(str) + " " + df_dict["docencia"]["Semestre"].astype(str)
df_dict["docencia"]["Semestre"] = df_dict["docencia"]["Semestre"].apply(lambda x: 2 if "Otoño" in str(x) else (1 if "Primavera" in str(x) else (3 if "Verano" in str(x) else np.nan)))
df_dict["docencia"]["Año"] = df_dict["docencia"]["Año"].astype(int)

## LIMPIEZA UB
df_dict["UB_eliminadas"]["Estado"] = "Eliminada"
df_dict["UB_eliminadas"] = df_dict["UB_eliminadas"].reindex(columns=df_dict["UB"].columns)

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

# -----------------------------
salida = os.path.join(data_path,"tablas_finales.xlsx") 
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