"""
Extractor — Auxílio Emergencial por município.
Endpoint: /api-de-dados/auxilio-emergencial-por-municipio  (RESTRITO: 180 req/min)
Parâmetros: mesAno (YYYYMM), codigoIbge, pagina
Período disponível: abril/2020 a outubro/2021 (programa encerrado).
Granularidade: agregado por município / mês / tipo de benefício.
"""

from __future__ import annotations

from extractors.beneficio_municipio import BeneficioMunicipioExtractor


class AuxilioEmergencialExtractor(BeneficioMunicipioExtractor):

    nome = "auxilio_emergencial"

    # Programa vigorou entre 04/2020 e 10/2021.
    MES_INICIO_DEFAULT = "202004"
    MES_FIM_DEFAULT = "202110"

    def __init__(self):
        super().__init__("auxilio-emergencial-por-municipio")
