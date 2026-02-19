"""PySpark session factory with pipeline configuration."""
from pyspark.sql import SparkSession
from src.utils.config import load_config


def get_spark(app_name: str | None = None) -> SparkSession:
    """Create or get a configured SparkSession."""
    config = load_config()
    spark_cfg = config.get("spark", {})
    
    builder = SparkSession.builder \
        .appName(app_name or spark_cfg.get("app_name", "us-suits-pipeline")) \
        .master(spark_cfg.get("master", "local[*]"))
    
    for key, value in spark_cfg.get("config", {}).items():
        builder = builder.config(key, value)
    
    # BigQuery connector
    builder = builder.config(
        "spark.jars.packages",
        "com.google.cloud.spark:spark-bigquery-with-dependencies_2.12:0.38.0"
    )
    
    return builder.getOrCreate()
