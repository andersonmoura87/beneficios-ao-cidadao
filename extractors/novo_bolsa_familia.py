"""
Extractor — Novo Bolsa Família por município (continuação pós-2021 do programa).
Endpoint: /api-de-dados/novo-bolsa-familia-por-municipio  (limites normais: 400/700 req/min)
Parâmetros: mesAno (YYYYMM), codigoIbge, pagina
Granularidade: agregado por município / mês / tipo de benefício.

O Novo Bolsa Família passou a ser divulgado a partir de março/2023; o programa
clássico (`bolsa-familia-por-municipio`) cobre o histórico até 2021.
"""

from __future__ import annotations

from extractors.beneficio_municipio import BeneficioMunicipioExtractor


class NovoBolsaFamiliaExtractor(BeneficioMunicipioExtractor):

    nome = "novo_bolsa_familia"
    MES_INICIO_DEFAULT = "202303"

    def __init__(self):
        super().__init__("novo-bolsa-familia-por-municipio")
