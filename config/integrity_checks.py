import os
import json

def check_project_schema():
    if not os.path.exists("config/settings.json"):
        settings = {
            "headless": True,
            "disable_gpu": False,
            "colab_mode": False,
            "output_dir": "data",
            "log_level": "INFO",
            "default_texture": "assets/textures/texture2.jpg",
            "export_excel": True
            }
        with open("config/settings.json", "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    if not os.path.exists("data"):
        os.makedirs("data")