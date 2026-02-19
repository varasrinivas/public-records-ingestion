"""Pipeline configuration loader."""
from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: str = "config/pipeline_config.yaml") -> dict[str, Any]:
    """Load pipeline configuration from YAML file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(path) as f:
        return yaml.safe_load(f)


def get_layer_path(config: dict, layer: str) -> Path:
    """Get the storage path for a given layer."""
    path = Path(config["paths"][layer])
    path.mkdir(parents=True, exist_ok=True)
    return path
