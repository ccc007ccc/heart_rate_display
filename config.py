# config.py

import json
import os

CONFIG_FILE = "config.json"

def save_config(config: dict):
    """
    将包含所有设置的字典保存到 config.json 文件。
    """
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def load_config() -> dict:
    """
    从 config.json 文件加载完整的配置。
    如果文件不存在或解析失败，则返回一个空字典。
    """
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    except Exception:
        return {}