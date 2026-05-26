"""
Extractor — BPC (Benefício de Prestação Continuada).
Endpoint: /api-de-dados/bpc  (normal: 400 req/min)
Parâmetros: mesAno, uf, pagina
"""

from __future__ import annotations

from datetime import date
from typing import Generator

from loguru import logger

from extractors.base_extractor import BaseExtractor
from extractors.bolsa_familia import _gerar_meses


UFS_BRASIL = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
]


class BpcExtractor(BaseExtractor):

    nome = "bpc"

    def __init__(self):
        super().__init__("bpc")

    def extract(
        self,
        mes_ano_inicio: str = "200401",
        mes_ano_fim: str | None = None,
        ufs: list[str] | None = None,
    ) -> Generator[list[dict], None, None]:
        """
        Extrai BPC por UF e mês.

        Args:
            mes_ano_inicio: mês/ano inicial (YYYYMM).
            mes_ano_fim:    mês/ano final (padrão: mês atual).
            ufs:            lista de siglas de UF; None = todas.
        """
        if mes_ano_fim is None:
            hoje = date.today()
            mes_ano_fim = f"{hoje.year}{hoje.month:02d}"

        ufs = ufs or UFS_BRASIL
        meses = _gerar_meses(mes_ano_inicio, mes_ano_fim)

        logger.info(f"[{self.nome}] {len(ufs)} UFs × {len(meses)} meses")

        for mes in meses:
            for uf in ufs:
                chave = f"{mes}_{uf}"

                if self.is_already_extracted(chave):
                    continue

                params = {"mesAno": mes, "uf": uf}

                try:
                    for pagina in self.paginate(params):
                        yield pagina
                    self.mark_done(chave)
                except Exception as exc:
                    logger.error(f"[{self.nome}] Falha em {chave}: {exc}")
