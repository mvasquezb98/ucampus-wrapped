import pandas as pd
import numpy as np
import os

def load_data(file_name='clean_data.xlsx', sheet_name='Evaluaciones'):
    """
    Load the Acta Milagrosa data from a CSV file.

    Parameters:
    file_path (str): The path to the CSV file containing the Acta Milagrosa data.

    Returns:
    pd.DataFrame: A DataFrame containing the loaded data.
    """
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_path,'datos', 'output',file_name)
    
    try:
        data = pd.read_excel(file_path, sheet_name)
        return data
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

import unicodedata

def limpiar_texto(s):
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

    
def get_acta_milagrosa_data(df):
    """
    Retrieve the Acta Milagrosa data.

    Returns:
    pd.DataFrame: A DataFrame containing the Acta Milagrosa data.
    """
    df_evaluaciones = load_data(file_name='clean_data.xlsx', sheet_name='Evaluaciones')
    df_historial = load_data(file_name='clean_data.xlsx', sheet_name='Historial')
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
    pattern_np = (        
        r"(?:"
        r"NOTA\s+(DE\s+)?PRESENTACI[ÓO]N(\s*\(NP\))?(\s+(A\s+)?EXAMEN)?"
        r"|PROMEDIO\s+PONDERADO\s+PRESENTACI[ÓO]N\s+A\s+EXAMEN"
        r"|SITUACION\s+PRE[- ]?EXAMEN"
        r"|NOTA\s+PRE[- ]?EXAMEN"
        r"|PRE[- ]?EXAMEN"
        r")$"
    )
    
    if df_evaluaciones is not None and df_historial is not None:
        df_evaluaciones.dropna(subset=["Promedio"],inplace=True)
        df_examen = df_evaluaciones.copy()
        df_examen.rename(columns={"Promedio": "Nota"}, inplace=True)
        df_examen["Evaluación"] = df_examen["Evaluación"].apply(lambda x: limpiar_texto(x))
        df_nota_presentacion = df_examen[df_examen["Evaluación"].str.contains(pattern_np, case=False, na=False)]
        df_nota_presentacion = df_nota_presentacion[["Curso URL","Codigo_curso","Año","Semestre","Periodo","Evaluación","Nota"]]
        df_nota_presentacion.rename(columns={"Evaluación": "Evaluación NP", "Nota": "Nota Presentacion"}, inplace=True)
        df_nota_presentacion = (
            df_nota_presentacion.sort_values(["Año", "Semestre"])
                    .drop_duplicates(subset=["Codigo_curso"], keep="last")
        )
        
        df_nota_presentacion = df_nota_presentacion[pd.to_numeric(df_nota_presentacion["Nota Presentacion"], errors="coerce").notna()]
        df_nota_presentacion["Nota Presentacion"] = df_nota_presentacion["Nota Presentacion"].astype(float)
        
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
            print("There are multiple exam entries for the same course. Please check the data.")
        df_historial.rename(columns={"Promedio": "Promedio Curso", "Nota Final": "Promedio"}, inplace=True)
        cursos_aprobados = df_historial[(~df_historial["Promedio"].isin(["R","T","E"]))]["Codigo_curso"].unique()         
        notas_examen = df_examen[df_examen["Codigo_curso"].isin(cursos_aprobados)]
        notas_actas = df_historial[(df_historial["Codigo_curso"].isin(df_examen["Codigo_curso"])) & (~df_historial["Promedio"].isin(["R","T","E"]))]#["Promedio"].astype(float).reset_index(drop=True)
        
        df_final = pd.merge(notas_examen, notas_actas, on=["Curso URL","Codigo_curso","Año","Semestre"], how="left")        
        m = 0.4
        df_final["Nota Presentacion estimada"] = (df_final["Promedio"].astype(float) - m * df_final["Nota"].astype(float))/(1-m)
        df_final = pd.merge(df_final,df_nota_presentacion, on=["Curso URL","Codigo_curso","Año","Semestre"],how="left")
        df_final.drop(columns=["Periodo_y", "Periodo", "Evaluación NP"], inplace=True)
        df_final.rename(columns={"Periodo_x": "Periodo"}, inplace=True)
        
        df_final["Nota Presentacion estimada"] = np.where(
            df_final["Nota Presentacion"].notna(),
            df_final["Nota Presentacion"],        # usa la nota real si existe
            df_final["Nota Presentacion estimada"] # si no, conserva la estimada
        )
        df_final.drop(columns=["Evaluación","Nota Presentacion"], inplace=True)
        df_final = df_final[df_final["Nota"] > df_final["Promedio"]]
        df_final["Nota Presentacion estimada"]  = df_final["Nota Presentacion estimada"].round(2)
        df_final.sort_values(by=["Promedio","Nota Presentacion estimada"], ascending=[True,True], inplace=True)
        
        curso_acta_milagrosa = df_final[df_final["Nota Presentacion estimada"] == df_final["Nota Presentacion estimada"].min()]["Codigo_curso"].tolist()
        curso_acta_milagrosa = curso_acta_milagrosa[0]
        df_acta_milagrosa = df_evaluaciones[df_evaluaciones["Codigo_curso"] == curso_acta_milagrosa]        
        
        row_acta = df_historial[df_historial["Codigo_curso"] == curso_acta_milagrosa]
        row_acta["Evaluación"] = "Acta"
        row_acta = row_acta[["Curso URL","Evaluación","Promedio","Codigo_curso","Año", "Semestre","Periodo"]]
        row_acta.reindex(columns=df_acta_milagrosa.columns)
        
        df_acta_milagrosa = pd.concat([df_acta_milagrosa, row_acta], ignore_index=True)

        return(df_final,df_nota_presentacion,notas_examen,df_acta_milagrosa)
    else:
        raise ValueError("Failed to find Acta Milagrosa.")




