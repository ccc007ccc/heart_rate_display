# config.py

import json
import os

CONFIG_FILE = "config.json"

def save_mac(mac: str):
    config = {"mac": mac}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f)

def load_mac() -> str:
    if not os.path.exists(CONFIG_FILE):
        return ''
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("mac", '')
    except Exception:
        return ''
