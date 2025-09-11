import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import logging
from config.logger import setup_logger
import os
from matplotlib.projections.polar import PolarAxes
from typing import cast

setup_logger() 
logger = logging.getLogger(__name__)
# Emojis: ✅ ❌ ⚠️ 📂 💾 ℹ️️ 🚀 📦 📊 🎨 🖊️ 📌 ➡️ 🎯 🏷️ 📏

# Categories and values
labels = ['Strength', 'Charisma', 'Constitution', 'Dexterity', 'Luck', 'Intelligence']
values = [4, 5, 3, 2, 3, 4]
df = pd.DataFrame({'labels': labels, 'values': values})
def plot_radar_chart(
    df: pd.DataFrame,
    save_path: str
) -> None:
    """
    Generate and save a radar (spider) chart from a DataFrame.

    The function creates a radar chart using the categories in the "labels"
    column and the corresponding numeric values in the "values" column. It
    calculates angular positions for each category, draws the polygonal web
    with filled color, configures category and radial labels, and saves the
    chart as an SVG file.

    Args:
        df (pandas.DataFrame): DataFrame containing two required columns:
            - "labels" (str): Names of the categories to display around the chart.
            - "values" (numeric): Numeric values associated with each category.
        save_path (str): Directory where the radar chart SVG file will be saved.

    Returns:
        None: The function saves the chart as "radar_plot.svg" in the given path.

    Raises:
        Exception: If there is an error during figure creation or saving.
    """
    logger.info("🚀 Iniciando función plot_radar_chart()")
    logger.debug(f"📊 DataFrame recibido con {len(df)} filas y columnas: {list(df.columns)}")
    
    # Wrap the data (radar chart needs closed polygon)
    logger.info("📦 Calculando ángulos para cada categoría...")
    num_vars = len(df["labels"])
    df["angles"] = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    df = pd.concat([df, df.iloc[:1]], ignore_index=True)
    logger.debug(f"✅ Ángulos generados: {df['angles'].tolist()}")

    # Setup the radar chart
    logger.info("🎨 Creando figura y ejes polares...")
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"polar": True})
    ax = cast(PolarAxes, ax)

    # Draw the web
    logger.debug("🖊️ Dibujando la malla y el polígono de radar")
    ax.plot(df["angles"], df["values"], color='orange', linewidth=2)
    ax.fill(df["angles"], df["values"], color='orange', alpha=0.5)

    # Category labels
    logger.info("📌 Configurando etiquetas de categorías en el radar")
    ax.set_xticks(df["angles"].iloc[:-1])
    ax.set_xticklabels(df["labels"].iloc[:-1])

    # Radius ticks
    logger.info("📏 Configurando ticks y límites de radio")
    ax.set_rlabel_position(0)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(['1', '2', '3', '4', '5'])
    ax.set_ylim(0, 5)

    plt.title("Character Stats", size=16, pad=20)
    logger.info("✅ Gráfico de radar creado con éxito.")
    
    # Save the figure
    img_path = os.path.join(save_path, "radar_plot.svg")
    logger.info(f"📂 Guardando gráfico en la ruta: {img_path}")
    fig.savefig(img_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info("💾 Gráfico de radar guardado correctamente como 'radar_plot.svg'")