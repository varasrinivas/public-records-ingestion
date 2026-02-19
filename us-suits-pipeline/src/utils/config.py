"""Pipeline configuration loader."""
from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: str = "config/pipeline_config.yaml") -> dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    with open(path) as f:
        return yaml.safe_load(f)


def get_state_config(config: dict, state_code: str) -> dict:
    """Get configuration for a specific state."""
    states = config.get("states", {})
    if state_code not in states:
        raise ValueError(f"Unknown state: {state_code}. Available: {list(states.keys())}")
    return states[state_code]


def get_layer_path(config: dict, layer: str) -> Path:
    path = Path(config["paths"][layer])
    path.mkdir(parents=True, exist_ok=True)
    return path
