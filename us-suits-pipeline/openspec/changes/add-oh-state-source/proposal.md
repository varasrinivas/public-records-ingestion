# Proposal: Add Ohio (OH) Court Data Source

## Summary
Add Cuyahoga County (Cleveland) court records as a new state source
to the suits pipeline. Ohio provides tab-delimited CSV files with
a distinct schema requiring new field mappings.

## Motivation
Ohio has the 7th largest state court system. Adding OH expands coverage
and validates the pipeline's ability to onboard new states.

## Scope
- New state schema mapping in `src/schemas/oh_schema.py`
- Sample data generator for OH format
- Bronze ingestion support for tab-delimited CSV
- Silver field mappings for OH → canonical
- Update state config in pipeline_config.yaml
- Unit tests for OH transforms

## Out of Scope
- Other OH counties (Franklin, Hamilton — future)
- Historical backfill beyond 2024
