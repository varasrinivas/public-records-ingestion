"""
US Suits Medallion Pipeline — Airflow DAG
Orchestrates: Bronze → Quality Gate → Silver → Quality Gate → Gold → BigQuery

Spec-driven by OpenSpec specifications in openspec/specs/.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryInsertJobOperator,
)

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'email_on_failure': True,
}


dag = DAG(
    'us_suits_medallion_pipeline',
    default_args=default_args,
    description='Bronze → Silver → Gold pipeline for US court suits data',
    schedule_interval='0 6 * * *',  # Daily at 6 AM UTC
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['suits', 'medallion', 'pyspark', 'bigquery'],
    max_active_runs=1,
)


# ── TASK FUNCTIONS ──

def run_bronze_ingest(**context):
    """Ingest all state court data into Bronze layer."""
    from src.utils.config import load_config
    from src.utils.spark_session import get_spark
    from src.bronze.ingest import BronzeIngester

    config = load_config()
    spark = get_spark("airflow-bronze-ingest")
    try:
        ingester = BronzeIngester(spark, config)
        results = ingester.ingest_all(context['ds'])
        for r in results:
            if r.get('status') == 'FAILED':
                raise RuntimeError(f"Bronze failed for {r['state']}: {r['error']}")
        context['ti'].xcom_push(key='bronze_results', value=results)
    finally:
        spark.stop()


def run_bronze_quality_gate(**context):
    """Quality gate: validate Bronze data before Silver."""
    from src.utils.config import load_config, get_layer_path
    from src.utils.spark_session import get_spark
    from src.quality.spark_checks import bronze_quality_gate, CheckStatus

    config = load_config()
    spark = get_spark("airflow-bronze-qc")
    bronze_path = str(get_layer_path(config, "bronze"))
    try:
        df = spark.read.parquet(f"{bronze_path}/*/*")
        results = bronze_quality_gate(df)
        failures = [r for r in results if r.status == CheckStatus.FAIL]
        if failures:
            raise RuntimeError(
                f"Bronze quality gate failed: {[r.check_name for r in failures]}"
            )
    finally:
        spark.stop()


def run_silver_canonicalize(**context):
    """Transform Bronze to canonical Silver schema."""
    from src.utils.config import load_config
    from src.utils.spark_session import get_spark
    from src.silver.canonicalize import SilverCanonicalizer

    config = load_config()
    spark = get_spark("airflow-silver")
    try:
        canon = SilverCanonicalizer(spark, config)
        result = canon.run(context['ds'])
        context['ti'].xcom_push(key='silver_results', value=result)
    finally:
        spark.stop()


def run_silver_quality_gate(**context):
    """Quality gate: validate Silver before Gold."""
    from src.utils.config import load_config, get_layer_path
    from src.utils.spark_session import get_spark
    from src.quality.spark_checks import silver_quality_gate, CheckStatus

    config = load_config()
    spark = get_spark("airflow-silver-qc")
    silver_path = str(get_layer_path(config, "silver"))
    try:
        df = spark.read.parquet(f"{silver_path}/suits")
        results = silver_quality_gate(df)
        failures = [r for r in results if r.status == CheckStatus.FAIL]
        if failures:
            raise RuntimeError(
                f"Silver quality gate failed: {[r.check_name for r in failures]}"
            )
    finally:
        spark.stop()


def run_gold_build(**context):
    """Build all Gold best view tables."""
    from src.utils.config import load_config
    from src.utils.spark_session import get_spark
    from src.gold.build_best_view import BestViewBuilder

    config = load_config()
    spark = get_spark("airflow-gold")
    try:
        builder = BestViewBuilder(spark, config)
        results = builder.build_all()
        context['ti'].xcom_push(key='gold_results', value=str(results))
    finally:
        spark.stop()


# ── DAG STRUCTURE ──

start = EmptyOperator(task_id='start', dag=dag)

bronze_ingest = PythonOperator(
    task_id='bronze_ingest_all_states',
    python_callable=run_bronze_ingest,
    dag=dag,
)

bronze_qc = PythonOperator(
    task_id='bronze_quality_gate',
    python_callable=run_bronze_quality_gate,
    dag=dag,
)

silver_transform = PythonOperator(
    task_id='silver_canonicalize',
    python_callable=run_silver_canonicalize,
    dag=dag,
)

silver_qc = PythonOperator(
    task_id='silver_quality_gate',
    python_callable=run_silver_quality_gate,
    dag=dag,
)

gold_build = PythonOperator(
    task_id='gold_build_best_views',
    python_callable=run_gold_build,
    dag=dag,
)

# BigQuery load (from GCS Parquet → BQ tables)
bq_load_suits = BigQueryInsertJobOperator(
    task_id='bq_load_suit_best_view',
    configuration={
        'load': {
            'sourceUris': ['gs://your-bucket/us-suits/gold/suit_best_view/*'],
            'sourceFormat': 'PARQUET',
            'destinationTable': {
                'projectId': 'your-gcp-project',
                'datasetId': 'suits_gold',
                'tableId': 'suit_best_view',
            },
            'writeDisposition': 'WRITE_TRUNCATE',
            'timePartitioning': {
                'type': 'MONTH',
                'field': 'filing_date',
            },
            'clustering': {
                'fields': ['state_code', 'case_type'],
            },
        }
    },
    dag=dag,
)

end = EmptyOperator(task_id='end', dag=dag)

# Dependencies
start >> bronze_ingest >> bronze_qc >> silver_transform >> silver_qc
silver_qc >> gold_build >> bq_load_suits >> end
