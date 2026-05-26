"""
Extractor — Bolsa Família por município.
Endpoint: /api-de-dados/bolsa-familia-por-municipio  (RESTRITO: 180 req/min)
Parâmetros: mesAno (YYYYMM), codigoIbge, pagina
"""

from __future__ import annotations

from datetime import date
from typing import Generator

from loguru import logger

from extractors.base_extractor import BaseExtractor
from extractors.municipios import listar_municipios


class BolsaFamiliaExtractor(BaseExtractor):

    nome = "bolsa_familia"

    def __init__(self):
        super().__init__("bolsa-familia-por-municipio")

    def extract(
        self,
        mes_ano_inicio: str = "200401",   # Bolsa Família criado em jan/2004
        mes_ano_fim: str | None = None,
        codigos_ibge: list[str] | None = None,
    ) -> Generator[list[dict], None, None]:
        """
        Extrai dados de Bolsa Família para todos os municípios e meses
        no intervalo [mes_ano_inicio, mes_ano_fim].

        Args:
            mes_ano_inicio: mês/ano inicial no formato YYYYMM.
            mes_ano_fim:    mês/ano final (padrão: mês atual).
            codigos_ibge:   lista de códigos IBGE; None = todos os municípios do Brasil.
        """
        if mes_ano_fim is None:
            hoje = date.today()
            mes_ano_fim = f"{hoje.year}{hoje.month:02d}"

        municipios = codigos_ibge or [m["id"] for m in listar_municipios()]
        meses = _gerar_meses(mes_ano_inicio, mes_ano_fim)

        logger.info(
            f"[{self.nome}] {len(municipios)} municípios × {len(meses)} meses = "
            f"{len(municipios) * len(meses):,} combinações"
        )

        for mes in meses:
            for ibge in municipios:
                chave = f"{mes}_{ibge}"

                if self.is_already_extracted(chave):
                    logger.debug(f"[{self.nome}] {chave} já extraído — pulando")
                    continue

                params = {"mesAno": mes, "codigoIbge": ibge}

                try:
                    for pagina in self.paginate(params):
                        yield pagina
                    self.mark_done(chave)
                except Exception as exc:
                    logger.error(f"[{self.nome}] Falha em {chave}: {exc}")


def _gerar_meses(inicio: str, fim: str) -> list[str]:
    """Gera lista de strings YYYYMM entre dois meses (inclusivo)."""
    ano_i, mes_i = int(inicio[:4]), int(inicio[4:6])
    ano_f, mes_f = int(fim[:4]), int(fim[4:6])

    meses = []
    ano, mes = ano_i, mes_i
    while (ano, mes) <= (ano_f, mes_f):
        meses.append(f"{ano}{mes:02d}")
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1
    return meses
