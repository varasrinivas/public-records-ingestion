.PHONY: setup data bronze silver gold pipeline test clean

setup:
	pip install -r requirements.txt

data:
	python sample_data/generate_sample_data.py

bronze: data
	python -m src.bronze.ingest --date 2025-01-15

silver: bronze
	python -m src.silver.transform

gold: silver
	python -m src.gold.customer_360
	python -m src.gold.daily_revenue

pipeline: data bronze silver gold
	@echo "\n✅ Full pipeline complete!"
	@echo "Bronze → Silver → Gold"

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

clean:
	rm -rf data/ .pytest_cache/ __pycache__/ src/__pycache__/
