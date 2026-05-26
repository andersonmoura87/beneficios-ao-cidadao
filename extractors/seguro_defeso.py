"""
Extractor — Seguro Defeso.
Endpoint: /api-de-dados/seguro-defeso-codigo  (RESTRITO: 180 req/min)
Parâmetros: anoInicio, anoFim, pagina
"""

from __future__ import annotations

from datetime import date
from typing import Generator

from loguru import logger

from extractors.base_extractor import BaseExtractor


class SeguroDefEsoExtractor(BaseExtractor):

    nome = "seguro_defeso"

    def __init__(self):
        super().__init__("seguro-defeso-codigo")

    def extract(
        self,
        ano_inicio: int = 2013,
        ano_fim: int | None = None,
    ) -> Generator[list[dict], None, None]:
        """
        Extrai Seguro Defeso por ano.

        Args:
            ano_inicio: ano inicial (dados disponíveis a partir de 2013).
            ano_fim:    ano final (padrão: ano atual).
        """
        if ano_fim is None:
            ano_fim = date.today().year

        anos = list(range(ano_inicio, ano_fim + 1))
        logger.info(f"[{self.nome}] Anos: {anos[0]}–{anos[-1]}")

        for ano in anos:
            chave = str(ano)

            if self.is_already_extracted(chave):
                continue

            params = {"anoInicio": ano, "anoFim": ano}

            try:
                for pagina in self.paginate(params):
                    yield pagina
                self.mark_done(chave)
            except Exception as exc:
                logger.error(f"[{self.nome}] Falha no ano {ano}: {exc}")
