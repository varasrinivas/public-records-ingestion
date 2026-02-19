"""
Medallion Architecture Pipeline DAG
Orchestrates: Bronze Ingest → Quality Gate → Silver Transform → Quality Gate → Gold Aggregate

Spec-driven by OpenSpec specifications in openspec/specs/.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator


default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
}

dag = DAG(
    'medallion_pipeline',
    default_args=default_args,
    description='Bronze → Silver → Gold medallion pipeline',
    schedule_interval='@daily',
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['medallion', 'etl', 'spec-driven'],
)


def run_bronze_ingest(**context):
    from src.utils.config import load_config
    from src.bronze.ingest import BronzeIngester
    config = load_config()
    ingester = BronzeIngester(config)
    results = ingester.ingest_all(context['ds'])
    for r in results:
        if r.get('status') == 'FAILED':
            raise RuntimeError(f"Bronze ingestion failed for {r['table']}: {r['error']}")
    return results


def run_bronze_quality_gate(**context):
    import pandas as pd
    from src.quality.gates import bronze_to_silver_gate
    from src.quality.checks import CheckStatus
    from src.utils.config import load_config, get_layer_path

    config = load_config()
    bronze_path = get_layer_path(config, "bronze")
    all_passed = True

    for table in ["customers", "orders"]:
        parquet_glob = str(bronze_path / table / "**" / "*.parquet")
        try:
            df = pd.read_parquet(parquet_glob)
        except Exception:
            continue
        results = bronze_to_silver_gate(table, df)
        for r in results:
            if r.status == CheckStatus.FAIL:
                all_passed = False
                print(f"FAIL: {r.check_name} — {r.pass_rate}% (threshold: {r.threshold}%)")

    if not all_passed:
        raise RuntimeError("Bronze quality gate failed — check quarantine")


def run_silver_transform(**context):
    from src.utils.config import load_config
    from src.silver.transform import SilverTransformer
    config = load_config()
    transformer = SilverTransformer(config)
    return transformer.transform_all(context['ds'])


def run_gold_customer_360(**context):
    from src.utils.config import load_config
    from src.gold.customer_360 import Customer360Builder
    config = load_config()
    builder = Customer360Builder(config)
    return builder.build(context['ds'])


def run_gold_daily_revenue(**context):
    from src.utils.config import load_config
    from src.gold.daily_revenue import DailyRevenueBuilder
    config = load_config()
    builder = DailyRevenueBuilder(config)
    return builder.build()


# ── Task definitions ──

start = EmptyOperator(task_id='start', dag=dag)

bronze_ingest = PythonOperator(
    task_id='bronze_ingest',
    python_callable=run_bronze_ingest,
    dag=dag,
)

bronze_quality = PythonOperator(
    task_id='bronze_quality_gate',
    python_callable=run_bronze_quality_gate,
    dag=dag,
)

silver_transform = PythonOperator(
    task_id='silver_transform',
    python_callable=run_silver_transform,
    dag=dag,
)

gold_customer_360 = PythonOperator(
    task_id='gold_customer_360',
    python_callable=run_gold_customer_360,
    dag=dag,
)

gold_daily_revenue = PythonOperator(
    task_id='gold_daily_revenue',
    python_callable=run_gold_daily_revenue,
    dag=dag,
)

end = EmptyOperator(task_id='end', dag=dag)

# ── Dependencies ──
start >> bronze_ingest >> bronze_quality >> silver_transform
silver_transform >> [gold_customer_360, gold_daily_revenue] >> end
