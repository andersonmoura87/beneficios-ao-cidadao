"""
DAG: BPC + Seguro Defeso — execução mensal consolidada.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

sys.path.insert(0, "/opt/airflow")


DEFAULT_ARGS = {
    "owner": "anderson",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=10),
    "retry_exponential_backoff": True,
    "email_on_failure": True,
    "email": [os.getenv("AIRFLOW_ADMIN_EMAIL", "profandersoncmoura@gmail.com")],
}


def extract_bpc(**context):
    from extractors.bpc import BpcExtractor
    from loaders.minio_loader import MinioLoader
    from loaders.postgres_loader import PostgresLoader
    import pandas as pd

    exec_date: datetime = context["data_interval_start"]
    mes_ano = f"{exec_date.year}{exec_date.month:02d}"

    extractor = BpcExtractor()
    minio = MinioLoader()
    buffer: list[dict] = []
    total = 0

    with PostgresLoader() as pg:
        for pagina in extractor.extract(mes_ano_inicio=mes_ano, mes_ano_fim=mes_ano):
            buffer.extend(pagina)
            total += len(pagina)

            if len(buffer) >= 500:
                partition = {"ano": mes_ano[:4], "mes": mes_ano[4:]}
                minio.upload_parquet(buffer, "bpc", partition)
                pg.load_dataframe("bpc", pd.DataFrame(buffer))
                buffer.clear()

        if buffer:
            partition = {"ano": mes_ano[:4], "mes": mes_ano[4:]}
            minio.upload_parquet(buffer, "bpc", partition)
            pg.load_dataframe("bpc", pd.DataFrame(buffer))

    context["ti"].xcom_push(key="total_bpc", value=total)


def extract_seguro_defeso(**context):
    from extractors.seguro_defeso import SeguroDefEsoExtractor
    from loaders.minio_loader import MinioLoader
    from loaders.postgres_loader import PostgresLoader
    import pandas as pd

    exec_date: datetime = context["data_interval_start"]
    ano = exec_date.year

    extractor = SeguroDefEsoExtractor()
    minio = MinioLoader()
    buffer: list[dict] = []
    total = 0

    with PostgresLoader() as pg:
        for pagina in extractor.extract(ano_inicio=ano, ano_fim=ano):
            buffer.extend(pagina)
            total += len(pagina)

            if len(buffer) >= 500:
                minio.upload_parquet(buffer, "seguro_defeso", {"ano": str(ano)})
                pg.load_dataframe("seguro_defeso", pd.DataFrame(buffer))
                buffer.clear()

        if buffer:
            minio.upload_parquet(buffer, "seguro_defeso", {"ano": str(ano)})
            pg.load_dataframe("seguro_defeso", pd.DataFrame(buffer))

    context["ti"].xcom_push(key="total_seguro_defeso", value=total)


with DAG(
    dag_id="elt_bpc_seguro_defeso",
    description="ELT mensal do BPC e Seguro Defeso",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 8 10 * *",   # todo dia 10 às 08h (após Bolsa Família)
    start_date=datetime(2013, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["beneficios", "bpc", "seguro_defeso", "elt"],
) as dag:

    task_bpc = PythonOperator(
        task_id="extract_bpc",
        python_callable=extract_bpc,
    )

    task_defeso = PythonOperator(
        task_id="extract_seguro_defeso",
        python_callable=extract_seguro_defeso,
    )

    dbt_run = BashOperator(
        task_id="dbt_transform_all",
        bash_command=(
            "cd /opt/airflow/dbt_project && "
            "dbt run --select stg_bpc stg_seguro_defeso mart_beneficios_por_municipio mart_evolucao_temporal mart_ranking_municipios "
            "--profiles-dir /opt/airflow/dbt_project"
        ),
    )

    [task_bpc, task_defeso] >> dbt_run
