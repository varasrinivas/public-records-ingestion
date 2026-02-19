"""Ingestion metadata generation."""
import uuid
from datetime import datetime, timezone


def generate_batch_id(source: str, date: str) -> str:
    """Generate deterministic batch ID for idempotent ingestion."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source}/{date}"))


def ingestion_metadata(source_system: str, source_table: str, batch_id: str) -> dict:
    """Generate metadata fields for Bronze records."""
    return {
        "_ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
        "_source_system": source_system,
        "_source_table": source_table,
        "_batch_id": batch_id,
    }
