import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import logging
from config.logger import setup_logger
import os

setup_logger() 
logger = logging.getLogger(__name__)
# Emojis: ✅ ❌ ⚠️ 📂 💾 ℹ️️ 🚀 📦 📊 🎨 🖊️ 📌 ➡️ 🎯 🏷️ 📏

# Input data
data = {
    "year": [2018, 2021, 2021, 2023, 2023, 2023, 2024, 2024, 2024],
    "desc": [
        "Apoyo Rebeauchef",
        "Ayudante IN3401", "Ayudante IN2702",
        "Ayudante IN3401", "Ayudante IN2702", "Ayudante CC2001",
        "Ayudante IN3401", "Ayudante CC2001", "Ayudante CC3702"
    ]
}
df = pd.DataFrame(data)
def plot_timeline(
    df: pd.DataFrame,
    save_path: str
) -> None:
    """
    Generate and save a timeline visualization from a DataFrame.

    The function groups descriptions by year, creates a horizontal timeline,
    draws labeled ticks for each year, and places rounded boxes containing
    the corresponding descriptions. A final arrow is added at the end of the
    timeline to indicate continuity.

    Args:
        df (pandas.DataFrame): DataFrame with at least two columns:
            - "year" (int or str): Year associated with the description.
            - "desc" (str): Description text to display in the timeline.
        save_path (str): Directory where the generated SVG image will be saved.

    Returns:
        None: The function saves the timeline as "radar_plot.svg" in the
        provided directory.

    Raises:
        Exception: If there is an error during plotting or saving the figure.
    """
    logger.info("🚀 Iniciando función plot_timeline()")
    logger.debug(f"📊 DataFrame recibido con {len(df)} filas y columnas: {list(df.columns)}")

    # Group descriptions by year
    logger.info("📦 Agrupando descripciones por año...")
    grouped = df.groupby("year")["desc"].apply(list).reset_index()
    grouped = grouped.sort_values("year")
    grouped["x"] = range(len(grouped))
    logger.debug(f"✅ Agrupación completada: {len(grouped)} años únicos encontrados")

    # Create plot
    logger.info("🎨 Creando figura y ejes de matplotlib...")
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.set_xlim(-0.5, len(grouped) + 0.7)
    ax.set_ylim(0, 5)
    ax.axis("off")

    # Timeline line
    logger.debug("🖊️ Dibujando línea principal de la línea de tiempo")
    ax.hlines(y=4, xmin=-0.5, xmax=len(grouped) + 0.1, color="black")

    # Draw year labels, boxes, and content
    logger.info("📌 Dibujando etiquetas y recuadros por año...")
    for _, row in grouped.iterrows():
        x = row["x"]
        year = row["year"]
        roles = row["desc"]
        logger.debug(f"   ➡️ Año {year} con {len(roles)} roles")

        # Ticks and year labels
        ax.vlines(x, 3.8, 4.2, color="black")
        ax.text(x, 4.25, str(year), ha="center", va="bottom", fontsize=10)

        # Box for roles
        box_text = "\n".join(roles)
        height = len(roles) * 0.4 + 0.3
        rect = patches.FancyBboxPatch(
            (x - 0.5, 4 - height - 0.4), 
            1, 
            height,
            boxstyle="round,pad=0.05", 
            edgecolor="black", 
            facecolor="#f5f5f5"
        )
        ax.add_patch(rect)
        ax.text(x, 4 - height / 2 - 0.4, box_text, ha="center", va="center", fontsize=9)

    # Optional: arrow at end of timeline
    logger.debug("➡️ Dibujando flecha al final de la línea de tiempo")
    ax.arrow(
        len(grouped) - 0.5 + 0.6, 4, 0.2, 0,
        head_width=0.05, head_length=0.2, fc='black', ec='black'
    )

    plt.tight_layout()
    
    # 💾 Save the figure
    img_path = os.path.join(save_path, "radar_plot.svg")
    logger.info(f"💾 Guardando imagen en {img_path}...")
    fig.savefig(img_path, dpi=300, bbox_inches="tight")
    logger.info("✅ Imagen guardada correctamente")