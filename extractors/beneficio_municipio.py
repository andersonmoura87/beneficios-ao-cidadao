"""
Extractor base para os endpoints '-por-municipio' do Portal da Transparência.

Os quatro programas cobertos (Bolsa Família, Auxílio Emergencial, BPC e
Seguro Defeso) compartilham o mesmo contrato de resposta da API —
`BeneficioPorMunicipioDTO` — e os mesmos parâmetros (mesAno, codigoIbge, pagina).

IMPORTANTE: esses endpoints retornam dados AGREGADOS por município / mês / tipo
de benefício. Não há registros por beneficiário (NIS/CPF) nessas consultas.

Estrutura do DTO:
    id, dataReferencia,
    municipio { codigoIBGE, nomeIBGE, codigoRegiao, nomeRegiao, pais, uf{sigla,nome} },
    tipo { id, descricao, descricaoDetalhada },
    valor, quantidadeBeneficiados
"""

from __future__ import annotations

from datetime import date
from typing import Any, Generator

from loguru import logger

from extractors.base_extractor import BaseExtractor
from extractors.municipios import listar_municipios


def gerar_meses(inicio: str, fim: str) -> list[str]:
    """Gera lista de strings YYYYMM entre dois meses (inclusivo)."""
    ano_i, mes_i = int(inicio[:4]), int(inicio[4:6])
    ano_f, mes_f = int(fim[:4]), int(fim[4:6])

    meses: list[str] = []
    ano, mes = ano_i, mes_i
    while (ano, mes) <= (ano_f, mes_f):
        meses.append(f"{ano}{mes:02d}")
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1
    return meses


# Alias mantido por compatibilidade com imports legados.
_gerar_meses = gerar_meses


class BeneficioMunicipioExtractor(BaseExtractor):
    """
    Base para os endpoints '-por-municipio'. Itera município × mês, pagina,
    achata o DTO aninhado em um dict plano alinhado ao schema 'raw' e faz yield
    de lotes prontos para carga.
    """

    # Sobrescritos por cada programa concreto.
    MES_INICIO_DEFAULT = "200401"
    MES_FIM_DEFAULT: str | None = None  # None → mês corrente

    def extract(
        self,
        mes_ano_inicio: str | None = None,
        mes_ano_fim: str | None = None,
        codigos_ibge: list[str] | None = None,
    ) -> Generator[list[dict], None, None]:
        """
        Extrai o benefício para todos os municípios no intervalo de meses.

        Args:
            mes_ano_inicio: mês/ano inicial (YYYYMM). Padrão: `MES_INICIO_DEFAULT`.
            mes_ano_fim:    mês/ano final (YYYYMM). Padrão: `MES_FIM_DEFAULT` ou mês atual.
            codigos_ibge:   lista de códigos IBGE; None = todos os municípios do Brasil.
        """
        mes_ano_inicio = mes_ano_inicio or self.MES_INICIO_DEFAULT
        if mes_ano_fim is None:
            mes_ano_fim = self.MES_FIM_DEFAULT
        if mes_ano_fim is None:
            hoje = date.today()
            mes_ano_fim = f"{hoje.year}{hoje.month:02d}"

        municipios = codigos_ibge or [m["id"] for m in listar_municipios()]
        meses = gerar_meses(mes_ano_inicio, mes_ano_fim)

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
                        yield [self.flatten(registro, mes) for registro in pagina]
                    self.mark_done(chave)
                except Exception as exc:
                    logger.error(f"[{self.nome}] Falha em {chave}: {exc}")

    @staticmethod
    def flatten(record: dict[str, Any], mes_ano: str) -> dict[str, Any]:
        """
        Achata um `BeneficioPorMunicipioDTO` em um dict plano com chaves
        snake_case alinhadas às colunas do schema 'raw'.

        `mes_ano` (o parâmetro consultado) é injetado como `mes_competencia`,
        que é mais confiável do que reparsear `dataReferencia`.
        """
        municipio = record.get("municipio") or {}
        uf = municipio.get("uf") or {}
        tipo = record.get("tipo") or {}

        return {
            "registro_id": record.get("id"),
            "mes_competencia": mes_ano,
            "data_referencia": record.get("dataReferencia"),
            "codigo_municipio_ibge": municipio.get("codigoIBGE"),
            "nome_municipio": municipio.get("nomeIBGE"),
            "codigo_regiao": municipio.get("codigoRegiao"),
            "nome_regiao": municipio.get("nomeRegiao"),
            "uf": uf.get("sigla"),
            "tipo_id": tipo.get("id"),
            "tipo_descricao": tipo.get("descricao"),
            "tipo_descricao_detalhada": tipo.get("descricaoDetalhada"),
            "valor": record.get("valor"),
            "quantidade_beneficiados": record.get("quantidadeBeneficiados"),
        }
