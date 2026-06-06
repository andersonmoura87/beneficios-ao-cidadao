"""
Extractor — Bolsa Família por município.
Endpoint: /api-de-dados/bolsa-familia-por-municipio  (RESTRITO: 180 req/min)
Parâmetros: mesAno (YYYYMM), codigoIbge, pagina
Granularidade: agregado por município / mês / tipo de benefício.
"""

from __future__ import annotations

from extractors.beneficio_municipio import BeneficioMunicipioExtractor


class BolsaFamiliaExtractor(BeneficioMunicipioExtractor):

    nome = "bolsa_familia"
    MES_INICIO_DEFAULT = "200401"  # Bolsa Família criado em jan/2004

    def __init__(self):
        super().__init__("bolsa-familia-por-municipio")
