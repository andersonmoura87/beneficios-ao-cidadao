"""
Utilitário para obter a lista completa de municípios brasileiros via IBGE API.
Resultado cacheado localmente em data/municipios/municipios.json
"""

from __future__ import annotations

import json
from pathlib import Path

import requests
from loguru import logger

IBGE_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
CACHE_PATH = Path("data/municipios/municipios.json")


def listar_municipios(force_refresh: bool = False) -> list[dict]:
    """
    Retorna lista de dicts com {"id": "IBGE_CODE", "nome": "Cidade", "uf": "PR"}.
    Baixa do IBGE na primeira execução e salva em cache local.
    """
    if not force_refresh and CACHE_PATH.exists():
        logger.debug("Carregando municípios do cache local")
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))

    logger.info("Baixando lista de municípios do IBGE...")
    resp = requests.get(IBGE_URL, timeout=30)
    resp.raise_for_status()

    raw = resp.json()
    municipios = [
        {
            "id": str(m["id"]),
            "nome": m["nome"],
            "uf": m["microrregiao"]["mesorregiao"]["UF"]["sigla"],
        }
        for m in raw
    ]

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(municipios, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info(f"{len(municipios):,} municípios carregados e salvos em cache")
    return municipios


def municipios_por_uf(uf: str) -> list[dict]:
    """Filtra municípios por UF (sigla, ex: 'PR')."""
    return [m for m in listar_municipios() if m["uf"] == uf.upper()]


if __name__ == "__main__":
    muns = listar_municipios(force_refresh=True)
    print(f"Total: {len(muns)} municípios")
