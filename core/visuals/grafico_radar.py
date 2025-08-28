import matplotlib.pyplot as plt
import numpy as np

# 📊 Categories and values
labels = ['Strength', 'Charisma', 'Constitution', 'Dexterity', 'Luck', 'Intelligence']
values = [4, 5, 3, 2, 3, 4]

# ➕ Wrap the data (radar chart needs closed polygon)
num_vars = len(labels)
angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
values += values[:1]      # repeat first value to close the polygon
angles += angles[:1]      # repeat first angle

# 🎯 Setup the radar chart
fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

# 🕸️ Draw the web
ax.plot(angles, values, color='orange', linewidth=2)
ax.fill(angles, values, color='orange', alpha=0.5)

# 🏷️ Category labels
ax.set_xticks(angles[:-1])
ax.set_xticklabels(labels)

# 🔢 Radius ticks
ax.set_rlabel_position(0)
ax.set_yticks([1, 2, 3, 4, 5])
ax.set_yticklabels(['1', '2', '3', '4', '5'])
ax.set_ylim(0, 5)

plt.title("Character Stats", size=16, pad=20)
plt.show()