import os
import json
from pathlib import Path

CONFIG_DIR = os.path.join(Path.home(), ".config", "ilo-tunnel")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

class Config:
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self):
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR, exist_ok=True)
            
        if not os.path.exists(CONFIG_FILE):
            return {}
            
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception:
            return False
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        return self.save_config()
