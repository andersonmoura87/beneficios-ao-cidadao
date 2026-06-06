"""
Loader — Staging Layer (PostgreSQL).
Lê arquivos Parquet do MinIO e carrega no schema 'raw' do PostgreSQL
usando COPY para máxima performance.
"""

from __future__ import annotations

import io
import os
from typing import Any

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from loguru import logger

from loaders.minio_loader import MinioLoader


DSN = (
    f"host={os.getenv('POSTGRES_HOST', 'localhost')} "
    f"port={os.getenv('POSTGRES_PORT', '5432')} "
    f"dbname={os.getenv('POSTGRES_DB', 'beneficios_db')} "
    f"user={os.getenv('POSTGRES_USER', 'beneficios')} "
    f"password={os.getenv('POSTGRES_PASSWORD', 'beneficios_pass')}"
)

# Mapeamento: nome do benefício → tabela de destino no schema raw
TABLE_MAP = {
    "bolsa_familia":        "raw.bolsa_familia",
    "auxilio_brasil":       "raw.auxilio_brasil",
    "novo_bolsa_familia":   "raw.novo_bolsa_familia",
    "auxilio_emergencial":  "raw.auxilio_emergencial",
    "bpc":                  "raw.bpc",
    "seguro_defeso":        "raw.seguro_defeso",
}


class PostgresLoader:

    def __init__(self):
        self.conn = psycopg2.connect(DSN)
        self.conn.autocommit = False
        self.minio = MinioLoader()

    def _upsert_batch(self, table: str, df: pd.DataFrame, conflict_cols: list[str]):
        """
        Insere ou atualiza registros usando INSERT ... ON CONFLICT DO NOTHING.
        Garante idempotência: reexecuções não duplicam dados.
        """
        if df.empty:
            return

        cols = list(df.columns)
        rows = [tuple(r) for r in df.itertuples(index=False)]

        sql = (
            f"INSERT INTO {table} ({', '.join(cols)}) VALUES %s "
            f"ON CONFLICT ({', '.join(conflict_cols)}) DO NOTHING"
        )

        with self.conn.cursor() as cur:
            execute_values(cur, sql, rows, page_size=1000)
        self.conn.commit()
        logger.info(f"[postgres] {table} → {len(rows):,} linhas inseridas")

    def load_from_minio(self, beneficio: str, prefix: str | None = None):
        """
        Lê todos os Parquet de um benefício no MinIO e carrega no PostgreSQL.
        Processa em chunks para não estourar memória.
        """
        table = TABLE_MAP.get(beneficio)
        if not table:
            raise ValueError(f"Benefício '{beneficio}' não mapeado. Opções: {list(TABLE_MAP)}")

        prefix = prefix or beneficio
        objects = self.minio.list_objects(prefix)

        if not objects:
            logger.warning(f"[{beneficio}] Nenhum objeto encontrado no MinIO com prefixo '{prefix}'")
            return

        logger.info(f"[{beneficio}] {len(objects)} arquivos Parquet a carregar")

        for obj in objects:
            try:
                df = self.minio.download_parquet(obj)
                df = _normalize_columns(df)
                conflict_cols = _get_conflict_cols(beneficio)
                self._upsert_batch(table, df, conflict_cols)
            except Exception as exc:
                logger.error(f"[{beneficio}] Falha ao carregar '{obj}': {exc}")
                self.conn.rollback()

    def load_dataframe(self, beneficio: str, df: pd.DataFrame):
        """Carrega um DataFrame diretamente no PostgreSQL (sem passar pelo MinIO)."""
        table = TABLE_MAP.get(beneficio)
        if not table:
            raise ValueError(f"Benefício '{beneficio}' não mapeado")

        df = _normalize_columns(df)
        conflict_cols = _get_conflict_cols(beneficio)
        self._upsert_batch(table, df, conflict_cols)

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza nomes de colunas: lowercase + underscores."""
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[\s\-/]", "_", regex=True)
        .str.replace(r"[^a-z0-9_]", "", regex=True)
    )
    return df


def _get_conflict_cols(beneficio: str) -> list[str]:
    """
    Coluna que identifica unicamente um registro.

    Os endpoints '-por-municipio' devolvem dados agregados em que o campo `id`
    da API (mapeado para `registro_id`) é a chave única e estável do registro.
    Usá-la garante idempotência em reexecuções para todos os programas.
    """
    return ["registro_id"]
