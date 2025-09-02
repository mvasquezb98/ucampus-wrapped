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
# Emojis: ✅ ❌ ⚠️ 📂 💾 ℹ️️ logger.info("")

# 📊 Categories and values
labels = ['Strength', 'Charisma', 'Constitution', 'Dexterity', 'Luck', 'Intelligence']
values = [4, 5, 3, 2, 3, 4]
df = pd.DataFrame({'labels': labels, 'values': values})

def plot_radar_chart(df,save_path):
    # ➕ Wrap the data (radar chart needs closed polygon)
    num_vars = len(df["labels"])
    df["angles"] = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    df = pd.concat([df, df.iloc[:1]], ignore_index=True)
    
    # 🎯 Setup the radar chart
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"polar": True})
    ax=cast(PolarAxes, ax)  # tell the type checker this is a PolarAxes

    # 🕸️ Draw the web
    ax.plot(df["angles"], df["values"], color='orange', linewidth=2)
    ax.fill(df["angles"], df["values"], color='orange', alpha=0.5)

    # 🏷️ Category labels
    ax.set_xticks(df["angles"].iloc[:-1])
    ax.set_xticklabels(df["labels"].iloc[:-1])

    # 🔢 Radius ticks
    ax.set_rlabel_position(0)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(['1', '2', '3', '4', '5'])
    ax.set_ylim(0, 5)

    plt.title("Character Stats", size=16, pad=20)
    logger.info("✅ Gráfico de radar creado con éxito.")
    
    # 💾 Save the figure
    img_path = os.path.join(save_path, "radar_plot.svg")
    fig.savefig(img_path, dpi=300, bbox_inches="tight")
    
    plt.close(fig)
    logger.info("💾 Gráfico de radar guardado como 'radar_plot.svg'")