import pandas as pd
import os

def excel_exporter(file_name, path, df_dict):
    # Guardar en Excel
    final_path = os.path.join(path, f"{file_name}.xlsx")
    with pd.ExcelWriter(final_path, engine='xlsxwriter') as writer:
        for sheet_name, df in df_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)