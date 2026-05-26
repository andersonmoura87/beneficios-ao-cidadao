"""
DAG: Extração do Auxílio Emergencial (carga única histórica).
O programa vigorou de 04/2020 a 10/2021 — não há atualizações futuras.
Executado apenas uma vez via trigger manual ou carga inicial.
"""

from __future__ import annotations

import sys
from datetime import timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

sys.path.insert(0, "/opt/airflow")


DEFAULT_ARGS = {
    "owner": "anderson",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=15),
    "retry_exponential_backoff": True,
}


def extract_and_load(**context):
    from extractors.auxilio_emergencial import AuxilioEmergencialExtractor
    from loaders.minio_loader import MinioLoader
    from loaders.postgres_loader import PostgresLoader
    import pandas as pd

    extractor = AuxilioEmergencialExtractor()
    minio = MinioLoader()
    buffer: list[dict] = []
    total = 0

    with PostgresLoader() as pg:
        for pagina in extractor.extract():
            buffer.extend(pagina)
            total += len(pagina)

            if len(buffer) >= 500:
                minio.upload_parquet(buffer, "auxilio_emergencial", {"tipo": "historico"})
                pg.load_dataframe("auxilio_emergencial", pd.DataFrame(buffer))
                buffer.clear()

        if buffer:
            minio.upload_parquet(buffer, "auxilio_emergencial", {"tipo": "historico"})
            pg.load_dataframe("auxilio_emergencial", pd.DataFrame(buffer))

    context["ti"].xcom_push(key="total_registros", value=total)


with DAG(
    dag_id="elt_auxilio_emergencial",
    description="ELT histórico do Auxílio Emergencial COVID-19 (2020–2021)",
    default_args=DEFAULT_ARGS,
    schedule_interval=None,       # somente trigger manual
    start_date=days_ago(1),
    catchup=False,
    max_active_runs=1,
    tags=["beneficios", "auxilio_emergencial", "historico", "elt"],
) as dag:

    extract_load = PythonOperator(
        task_id="extract_and_load",
        python_callable=extract_and_load,
    )

    dbt_run = BashOperator(
        task_id="dbt_transform",
        bash_command=(
            "cd /opt/airflow/dbt_project && "
            "dbt run --select stg_auxilio_emergencial mart_beneficios_por_municipio mart_evolucao_temporal "
            "--profiles-dir /opt/airflow/dbt_project"
        ),
    )

    extract_load >> dbt_run
