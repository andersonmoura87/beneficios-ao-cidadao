"""
Extractor — Seguro Defeso por município.
Endpoint: /api-de-dados/seguro-defeso-por-municipio  (limites normais: 400/700 req/min)
Parâmetros: mesAno (YYYYMM), codigoIbge, pagina
Granularidade: agregado por município / mês / tipo de benefício.
"""

from __future__ import annotations

from extractors.beneficio_municipio import BeneficioMunicipioExtractor


class SeguroDefesoExtractor(BeneficioMunicipioExtractor):

    nome = "seguro_defeso"
    MES_INICIO_DEFAULT = "201301"  # dados disponíveis a partir de 2013

    def __init__(self):
        super().__init__("seguro-defeso-por-municipio")
