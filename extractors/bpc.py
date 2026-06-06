"""
Extractor — BPC (Benefício de Prestação Continuada).
Endpoint: /api-de-dados/bpc-por-municipio  (limites normais: 400/700 req/min)
Parâmetros: mesAno (YYYYMM), codigoIbge, pagina
Granularidade: agregado por município / mês / tipo de benefício.
"""

from __future__ import annotations

from extractors.beneficio_municipio import BeneficioMunicipioExtractor


class BpcExtractor(BeneficioMunicipioExtractor):

    nome = "bpc"
    MES_INICIO_DEFAULT = "200401"

    def __init__(self):
        super().__init__("bpc-por-municipio")
