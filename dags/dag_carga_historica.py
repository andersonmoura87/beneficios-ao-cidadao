"""
DAG: Carga histórica completa — execução única via trigger manual.
Orquestra todos os extractors em sequência para não estourar rate limits.
Sequência: municípios IBGE → BPC → Bolsa Família → Auxílio Emergencial → Seguro Defeso → dbt full refresh
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

sys.path.insert(0, "/opt/airflow")


DEFAULT_ARGS = {
    "owner": "anderson",
    "depends_on_past": False,
    "retries": 5,
    "retry_delay": timedelta(minutes=30),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(hours=2),
}


def cache_municipios():
    """Pré-carrega lista de municípios do IBGE e salva em cache."""
    from extractors.municipios import listar_municipios
    municipios = listar_municipios(force_refresh=True)
    return len(municipios)


def extract_bpc_historico():
    from extractors.bpc import BpcExtractor
    from loaders.minio_loader import MinioLoader
    from loaders.postgres_loader import PostgresLoader
    import pandas as pd

    ext = BpcExtractor()
    minio = MinioLoader()
    buf: list[dict] = []

    with PostgresLoader() as pg:
        for pag in ext.extract(mes_ano_inicio="200401"):
            buf.extend(pag)
            if len(buf) >= 1000:
                mes_comp = str(buf[0].get("mes_competencia", "000000"))
                minio.upload_parquet(buf, "bpc", {"ano": mes_comp[:4], "mes": mes_comp[4:]})
                pg.load_dataframe("bpc", pd.DataFrame(buf))
                buf.clear()
        if buf:
            minio.upload_parquet(buf, "bpc", {"tipo": "historico"})
            pg.load_dataframe("bpc", pd.DataFrame(buf))


def extract_bolsa_familia_historico():
    from extractors.bolsa_familia import BolsaFamiliaExtractor
    from loaders.minio_loader import MinioLoader
    from loaders.postgres_loader import PostgresLoader
    import pandas as pd

    ext = BolsaFamiliaExtractor()
    minio = MinioLoader()
    buf: list[dict] = []

    with PostgresLoader() as pg:
        for pag in ext.extract(mes_ano_inicio="200401"):
            buf.extend(pag)
            if len(buf) >= 1000:
                minio.upload_parquet(buf, "bolsa_familia", {"tipo": "historico"})
                pg.load_dataframe("bolsa_familia", pd.DataFrame(buf))
                buf.clear()
        if buf:
            minio.upload_parquet(buf, "bolsa_familia", {"tipo": "historico"})
            pg.load_dataframe("bolsa_familia", pd.DataFrame(buf))


def extract_auxilio_brasil_historico():
    from extractors.auxilio_brasil import AuxilioBrasilExtractor
    from loaders.minio_loader import MinioLoader
    from loaders.postgres_loader import PostgresLoader
    import pandas as pd

    ext = AuxilioBrasilExtractor()
    minio = MinioLoader()
    buf: list[dict] = []

    with PostgresLoader() as pg:
        for pag in ext.extract():
            buf.extend(pag)
            if len(buf) >= 1000:
                minio.upload_parquet(buf, "auxilio_brasil", {"tipo": "historico"})
                pg.load_dataframe("auxilio_brasil", pd.DataFrame(buf))
                buf.clear()
        if buf:
            minio.upload_parquet(buf, "auxilio_brasil", {"tipo": "historico"})
            pg.load_dataframe("auxilio_brasil", pd.DataFrame(buf))


def extract_novo_bolsa_familia_historico():
    from extractors.novo_bolsa_familia import NovoBolsaFamiliaExtractor
    from loaders.minio_loader import MinioLoader
    from loaders.postgres_loader import PostgresLoader
    import pandas as pd

    ext = NovoBolsaFamiliaExtractor()
    minio = MinioLoader()
    buf: list[dict] = []

    with PostgresLoader() as pg:
        for pag in ext.extract(mes_ano_inicio="202303"):
            buf.extend(pag)
            if len(buf) >= 1000:
                minio.upload_parquet(buf, "novo_bolsa_familia", {"tipo": "historico"})
                pg.load_dataframe("novo_bolsa_familia", pd.DataFrame(buf))
                buf.clear()
        if buf:
            minio.upload_parquet(buf, "novo_bolsa_familia", {"tipo": "historico"})
            pg.load_dataframe("novo_bolsa_familia", pd.DataFrame(buf))


def extract_auxilio_historico():
    from extractors.auxilio_emergencial import AuxilioEmergencialExtractor
    from loaders.minio_loader import MinioLoader
    from loaders.postgres_loader import PostgresLoader
    import pandas as pd

    ext = AuxilioEmergencialExtractor()
    minio = MinioLoader()
    buf: list[dict] = []

    with PostgresLoader() as pg:
        for pag in ext.extract():
            buf.extend(pag)
            if len(buf) >= 1000:
                minio.upload_parquet(buf, "auxilio_emergencial", {"tipo": "historico"})
                pg.load_dataframe("auxilio_emergencial", pd.DataFrame(buf))
                buf.clear()
        if buf:
            minio.upload_parquet(buf, "auxilio_emergencial", {"tipo": "historico"})
            pg.load_dataframe("auxilio_emergencial", pd.DataFrame(buf))


def extract_defeso_historico():
    from extractors.seguro_defeso import SeguroDefesoExtractor
    from loaders.minio_loader import MinioLoader
    from loaders.postgres_loader import PostgresLoader
    import pandas as pd

    ext = SeguroDefesoExtractor()
    minio = MinioLoader()
    buf: list[dict] = []

    with PostgresLoader() as pg:
        for pag in ext.extract(mes_ano_inicio="201301"):
            buf.extend(pag)
            if len(buf) >= 1000:
                minio.upload_parquet(buf, "seguro_defeso", {"tipo": "historico"})
                pg.load_dataframe("seguro_defeso", pd.DataFrame(buf))
                buf.clear()
        if buf:
            minio.upload_parquet(buf, "seguro_defeso", {"tipo": "historico"})
            pg.load_dataframe("seguro_defeso", pd.DataFrame(buf))


with DAG(
    dag_id="elt_carga_historica_completa",
    description="Carga histórica de todos os benefícios — executar apenas uma vez",
    default_args=DEFAULT_ARGS,
    schedule_interval=None,   # somente trigger manual
    start_date=datetime(2020, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["beneficios", "historico", "carga-inicial", "elt"],
) as dag:

    t_municipios = PythonOperator(
        task_id="cache_municipios_ibge",
        python_callable=cache_municipios,
    )

    t_bpc = PythonOperator(
        task_id="extract_bpc",
        python_callable=extract_bpc_historico,
    )

    t_bf = PythonOperator(
        task_id="extract_bolsa_familia",
        python_callable=extract_bolsa_familia_historico,
    )

    t_ab = PythonOperator(
        task_id="extract_auxilio_brasil",
        python_callable=extract_auxilio_brasil_historico,
    )

    t_nbf = PythonOperator(
        task_id="extract_novo_bolsa_familia",
        python_callable=extract_novo_bolsa_familia_historico,
    )

    t_ae = PythonOperator(
        task_id="extract_auxilio_emergencial",
        python_callable=extract_auxilio_historico,
    )

    t_sd = PythonOperator(
        task_id="extract_seguro_defeso",
        python_callable=extract_defeso_historico,
    )

    t_dbt = BashOperator(
        task_id="dbt_full_refresh",
        bash_command=(
            "cd /opt/airflow/dbt_project && "
            "dbt run --full-refresh --profiles-dir /opt/airflow/dbt_project && "
            "dbt test --profiles-dir /opt/airflow/dbt_project"
        ),
        execution_timeout=timedelta(hours=4),
    )

    # Sequencial para respeitar rate limits
    t_municipios >> t_bpc >> t_bf >> t_ab >> t_nbf >> t_ae >> t_sd >> t_dbt
