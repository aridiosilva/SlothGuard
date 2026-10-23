"""Settings from the .env file and the environment. Values are never printed by this module."""
from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Optional, Union

PREFIXES = ("AUTH0_", "OLLAMA_")


def load_env(path: Union[str, Path] = ".env") -> dict[str, str]:
    """Parse KEY=VALUE lines. Comments, blank lines and lines without '=' are ignored,
    surrounding quotes are removed, and a missing file gives an empty dict."""
    file = Path(path)
    if not file.exists():
        return {}
    values: dict[str, str] = {}
    with open(file, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def merged_env(
    path: Union[str, Path] = ".env", environ: Optional[Mapping[str, str]] = None
) -> dict[str, str]:
    """File values, overridden by non-empty environment values for the AUTH0_ and OLLAMA_ prefixes."""
    environment = os.environ if environ is None else environ
    values = load_env(path)
    for key, value in environment.items():
        if key.startswith(PREFIXES) and value:
            values[key] = value
    return values
