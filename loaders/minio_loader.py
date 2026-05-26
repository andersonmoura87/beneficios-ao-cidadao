"""
Loader — Raw Layer (MinIO / S3-compatível).
Salva cada batch extraído como Parquet particionado no Data Lake.
Estrutura: s3://beneficios-raw/{beneficio}/ano={YYYY}/mes={MM}/municipio={IBGE}/{uuid}.parquet
"""

from __future__ import annotations

import io
import os
import uuid
from datetime import datetime
from typing import Any

import pandas as pd
from minio import Minio
from minio.error import S3Error
from loguru import logger


class MinioLoader:

    BUCKET_RAW = os.getenv("MINIO_BUCKET_RAW", "beneficios-raw")

    def __init__(self):
        self.client = Minio(
            endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
            secure=False,
        )
        self._ensure_bucket(self.BUCKET_RAW)

    def _ensure_bucket(self, bucket: str):
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)
            logger.info(f"Bucket '{bucket}' criado")

    def upload_parquet(
        self,
        records: list[dict[str, Any]],
        beneficio: str,
        partition: dict[str, str],
    ) -> str:
        """
        Serializa lista de dicts para Parquet e faz upload no MinIO.

        Args:
            records:    lista de registros a salvar.
            beneficio:  nome do programa (ex: 'bolsa_familia').
            partition:  dict com chaves de partição (ex: {'ano': '2024', 'mes': '01'}).

        Returns:
            Caminho do objeto no MinIO.
        """
        if not records:
            logger.debug(f"[{beneficio}] Nenhum registro para upload")
            return ""

        df = pd.DataFrame(records)
        df["_extracted_at"] = datetime.utcnow().isoformat()

        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False, engine="pyarrow", compression="snappy")
        buffer.seek(0)
        size = buffer.getbuffer().nbytes

        partition_path = "/".join(f"{k}={v}" for k, v in partition.items())
        object_name = f"{beneficio}/{partition_path}/{uuid.uuid4().hex}.parquet"

        self.client.put_object(
            bucket_name=self.BUCKET_RAW,
            object_name=object_name,
            data=buffer,
            length=size,
            content_type="application/octet-stream",
        )

        logger.info(f"[{beneficio}] Upload OK → s3://{self.BUCKET_RAW}/{object_name} ({size:,} bytes, {len(records)} registros)")
        return f"s3://{self.BUCKET_RAW}/{object_name}"

    def list_objects(self, prefix: str) -> list[str]:
        """Lista objetos no bucket com determinado prefixo."""
        return [
            obj.object_name
            for obj in self.client.list_objects(self.BUCKET_RAW, prefix=prefix, recursive=True)
        ]

    def download_parquet(self, object_name: str) -> pd.DataFrame:
        """Baixa um objeto Parquet do MinIO e retorna como DataFrame."""
        response = self.client.get_object(self.BUCKET_RAW, object_name)
        return pd.read_parquet(io.BytesIO(response.read()))
