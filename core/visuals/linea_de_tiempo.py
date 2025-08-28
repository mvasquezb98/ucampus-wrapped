import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd

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

def plot_timeline(df):
    # Group descriptions by year
    grouped = df.groupby("year")["desc"].apply(list).reset_index()
    grouped = grouped.sort_values("year")
    grouped["x"] = range(len(grouped))  # Spaced positions: 0, 1, 2...

    # Create plot
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.set_xlim(-0.5, len(grouped) + 0.7)

    ax.set_ylim(0, 5)
    ax.axis("off")

    # Timeline line
    ax.hlines(y=4, xmin=-0.5, xmax=len(grouped) +0.1, color="black")

    # Draw year labels, boxes, and content
    for _, row in grouped.iterrows():
        x = row["x"]
        year = row["year"]
        roles = row["desc"]

        # Ticks and year labels
        ax.vlines(x, 3.8, 4.2, color="black")
        ax.text(x, 4.25, str(year), ha="center", va="bottom", fontsize=10)

        # Box for roles
        box_text = "\n".join(roles)
        height = len(roles) * 0.4 + 0.3
        rect = patches.FancyBboxPatch((x - 0.5, 4 - height - 0.4), 1, height,
                                    boxstyle="round,pad=0.05", edgecolor="black", facecolor="#f5f5f5")
        ax.add_patch(rect)
        ax.text(x, 4 - height / 2 - 0.4, box_text, ha="center", va="center", fontsize=9)

    # Optional: arrow at end of timeline
    ax.arrow(len(grouped) - 0.5 + 0.6, 4, 0.2, 0, head_width=0.05, head_length=0.2, fc='black', ec='black')

    plt.tight_layout()
    plt.show()