import pandas as pd

def excel_exporter(file_name,path,df_indicadores, df_cursos, df_semestre, df_dictados, df_examenes, df_UB, df_UB_eliminadas, df_recuento):
    # Save to one Excel file
    final_path = path / f"{file_name}.xlsx"
    with pd.ExcelWriter(final_path, engine='xlsxwriter') as writer:
        df_indicadores.to_excel(writer, sheet_name='indicadores', index=False)
        df_cursos.to_excel(writer, sheet_name='notas', index=False)
        df_semestre.to_excel(writer, sheet_name='semestre', index=False)
        df_dictados.to_excel(writer, sheet_name='docencia', index=False)
        df_examenes.to_excel(writer, sheet_name='titulo', index=False)
        df_UB.to_excel(writer, sheet_name='UB', index=False)
        df_UB_eliminadas.to_excel(writer, sheet_name='UB_eliminadas', index=False)
        df_recuento.to_excel(writer, sheet_name='recuento', index=False)