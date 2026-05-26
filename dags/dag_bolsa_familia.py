"""
DAG: Extração e carga do Bolsa Família.
Frequência: mensal (todo dia 10 do mês seguinte — dados ficam disponíveis com ~1 semana de atraso).
Fluxo: Extract → Upload MinIO → Load PostgreSQL → dbt transform
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

sys.path.insert(0, "/opt/airflow")


DEFAULT_ARGS = {
    "owner": "anderson",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=10),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(hours=1),
    "email_on_failure": True,
    "email": [os.getenv("AIRFLOW_ADMIN_EMAIL", "profandersoncmoura@gmail.com")],
}


def extract_and_load(**context):
    """Extrai Bolsa Família e carrega no MinIO + PostgreSQL."""
    from extractors.bolsa_familia import BolsaFamiliaExtractor
    from loaders.minio_loader import MinioLoader
    from loaders.postgres_loader import PostgresLoader
    import pandas as pd

    # Determina o mês de referência (mês anterior à data de execução)
    exec_date: datetime = context["data_interval_start"]
    mes_ano = f"{exec_date.year}{exec_date.month:02d}"

    extractor = BolsaFamiliaExtractor()
    minio = MinioLoader()

    batch_size = 500
    buffer: list[dict] = []
    total = 0

    with PostgresLoader() as pg:
        for pagina in extractor.extract(mes_ano_inicio=mes_ano, mes_ano_fim=mes_ano):
            buffer.extend(pagina)
            total += len(pagina)

            if len(buffer) >= batch_size:
                partition = {"ano": mes_ano[:4], "mes": mes_ano[4:]}
                minio.upload_parquet(buffer, "bolsa_familia", partition)
                pg.load_dataframe("bolsa_familia", pd.DataFrame(buffer))
                buffer.clear()

        # flush final
        if buffer:
            partition = {"ano": mes_ano[:4], "mes": mes_ano[4:]}
            minio.upload_parquet(buffer, "bolsa_familia", partition)
            pg.load_dataframe("bolsa_familia", pd.DataFrame(buffer))

    context["ti"].xcom_push(key="total_registros", value=total)


with DAG(
    dag_id="elt_bolsa_familia",
    description="ELT mensal do Bolsa Família (Portal da Transparência)",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 6 10 * *",  # todo dia 10 às 06h
    start_date=datetime(2004, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["beneficios", "bolsa_familia", "elt"],
) as dag:

    extract_load = PythonOperator(
        task_id="extract_and_load",
        python_callable=extract_and_load,
    )

    dbt_run = BashOperator(
        task_id="dbt_transform",
        bash_command=(
            "cd /opt/airflow/dbt_project && "
            "dbt run --select stg_bolsa_familia mart_beneficios_por_municipio mart_evolucao_temporal mart_ranking_municipios "
            "--profiles-dir /opt/airflow/dbt_project"
        ),
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            "cd /opt/airflow/dbt_project && "
            "dbt test --select stg_bolsa_familia "
            "--profiles-dir /opt/airflow/dbt_project"
        ),
    )

    extract_load >> dbt_run >> dbt_test
