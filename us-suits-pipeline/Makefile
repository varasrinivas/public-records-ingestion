.PHONY: setup data bronze silver gold pipeline test clean

setup:
	pip install -r requirements.txt

data:
	python sample_data/generate_state_suits.py

bronze: data
	python -m src.bronze.ingest --date 2025-01-15

silver: bronze
	python -m src.silver.canonicalize --date 2025-01-15

gold: silver
	python -m src.gold.build_best_view --date 2025-01-15

pipeline: data
	python run_pipeline.py --date 2025-01-15

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

clean:
	rm -rf data/ .pytest_cache/ __pycache__/ spark-warehouse/ metastore_db/ derby.log
