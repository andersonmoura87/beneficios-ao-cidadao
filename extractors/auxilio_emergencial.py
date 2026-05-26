"""
Extractor — Auxílio Emergencial por município.
Endpoint: /api-de-dados/auxilio-emergencial-por-municipio  (RESTRITO: 180 req/min)
Período disponível: março/2020 a outubro/2021 (programa encerrado).
"""

from __future__ import annotations

from typing import Generator

from loguru import logger

from extractors.base_extractor import BaseExtractor
from extractors.bolsa_familia import _gerar_meses
from extractors.municipios import listar_municipios


class AuxilioEmergencialExtractor(BaseExtractor):

    nome = "auxilio_emergencial"

    # Programa existiu entre 04/2020 e 10/2021
    MES_INICIO_DEFAULT = "202004"
    MES_FIM_DEFAULT = "202110"

    def __init__(self):
        super().__init__("auxilio-emergencial-por-municipio")

    def extract(
        self,
        mes_ano_inicio: str = MES_INICIO_DEFAULT,
        mes_ano_fim: str = MES_FIM_DEFAULT,
        codigos_ibge: list[str] | None = None,
    ) -> Generator[list[dict], None, None]:
        municipios = codigos_ibge or [m["id"] for m in listar_municipios()]
        meses = _gerar_meses(mes_ano_inicio, mes_ano_fim)

        logger.info(
            f"[{self.nome}] {len(municipios)} municípios × {len(meses)} meses"
        )

        for mes in meses:
            for ibge in municipios:
                chave = f"{mes}_{ibge}"

                if self.is_already_extracted(chave):
                    continue

                params = {"mesAno": mes, "codigoIbge": ibge}

                try:
                    for pagina in self.paginate(params):
                        yield pagina
                    self.mark_done(chave)
                except Exception as exc:
                    logger.error(f"[{self.nome}] Falha em {chave}: {exc}")
