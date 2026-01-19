from functools import lru_cache
import yaml
from pathlib import Path
from typing import Dict, Any

@lru_cache()
def load_vera_rules() -> Dict[str, Any]:
    """
    加载 VERA 规则配置：
    - 来源：config/vera_rules.yaml
    - 使用 lru_cache 避免重复 IO
    """
    # Assuming config/vera_rules.yaml is relative to the project root or we can find it relative to this file
    # This file is in core/, so config/ is one level up and then in config/
    
    # Try absolute path based on known structure or relative path
    # Using relative path from this file's directory: ../config/vera_rules.yaml
    
    base_dir = Path(__file__).resolve().parent.parent
    cfg_path = base_dir / "config" / "vera_rules.yaml"
    
    if not cfg_path.exists():
        # Fallback to verify if running from root
        cfg_path = Path("config/vera_rules.yaml")
    
    if not cfg_path.exists():
        raise FileNotFoundError(f"VERA rules config not found: {cfg_path}")
        
    with cfg_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)
