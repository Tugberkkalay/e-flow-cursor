from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

PROJE_KOKU = Path(__file__).resolve().parent.parent
AYAR_DOSYASI = PROJE_KOKU / "ayarlar.toml"


def yukle(yol: Path | None = None) -> dict[str, Any]:
    yol = yol or AYAR_DOSYASI
    with open(yol, "rb") as f:
        return tomllib.load(f)


def cikti_klasoru(ayar: dict[str, Any]) -> Path:
    klasor = PROJE_KOKU / ayar.get("raporlar", {}).get("cikti_klasoru", "cikti")
    klasor.mkdir(parents=True, exist_ok=True)
    return klasor
