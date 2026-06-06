"""
Extractor — Auxílio Brasil por município (transição entre Bolsa Família e Novo Bolsa Família).
Endpoint: /api-de-dados/auxilio-brasil-por-municipio  (limites normais: 400/700 req/min)
Parâmetros: mesAno (YYYYMM), codigoIbge, pagina
Granularidade: agregado por município / mês / tipo de benefício.

O Auxílio Brasil vigorou de novembro/2021 a fevereiro/2023, preenchendo a lacuna
entre o Bolsa Família clássico e o Novo Bolsa Família.
"""

from __future__ import annotations

from extractors.beneficio_municipio import BeneficioMunicipioExtractor


class AuxilioBrasilExtractor(BeneficioMunicipioExtractor):

    nome = "auxilio_brasil"

    # Programa vigorou entre 11/2021 e 02/2023.
    MES_INICIO_DEFAULT = "202111"
    MES_FIM_DEFAULT = "202302"

    def __init__(self):
        super().__init__("auxilio-brasil-por-municipio")
