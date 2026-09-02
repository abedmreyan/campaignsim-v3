"""Dataset intake: CSV/XLSX parsing, LLM-assisted column mapping, and import
into the canonical Customer schema (Phase 4).

Privacy: sample values shown to the mapping-proposal LLM are redacted to
type patterns (<email>, <phone>) before the prompt is built, and any column
the user maps to `external_id` is one-way hashed before a Customer row is
ever written — the raw identity value never reaches the database or a
prompt. See app/models/customer_schema.py for the canonical field list.
"""

import hashlib
import json
import re
from typing import Any, Dict, List, Optional

import pandas as pd
from openai import OpenAI

from ..config import Config
from ..extensions import db
from ..models.customer_schema import CANONICAL_FIELDS, NUMERIC_FIELDS, CanonicalCustomer
from ..models.orm import Customer, Dataset
from ..utils.logger import get_logger

logger = get_logger("campaignsim.services.dataset_mapper")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[\d\-+()\s]{7,20}$")


def read_dataset_file(path: str, source_type: str) -> pd.DataFrame:
    if source_type == "xlsx":
        return pd.read_excel(path, dtype=str)
    return pd.read_csv(path, dtype=str)


def _sample_values(series: "pd.Series", n: int = 5) -> List[str]:
    return series.dropna().astype(str).unique().tolist()[:n]


def _redact(value: str) -> str:
    """Reduce a sample value to a type pattern before it reaches an LLM
    prompt — the model only needs the shape of the data, not the value."""
    if EMAIL_RE.match(value):
        return "<email>"
    if PHONE_RE.match(value):
        return "<phone>"
    if len(value) > 40:
        return value[:40] + "…"
    return value


def propose_mapping(df: "pd.DataFrame") -> Dict[str, Optional[str]]:
    """Ask the LLM to map each source column to a canonical field, or None.
    Returns {source_col: canonical_field_or_None} for every column in df."""
    columns_info = [
        {"column": col, "samples": [_redact(v) for v in _sample_values(df[col])]}
        for col in df.columns
    ]

    client = OpenAI(api_key=Config.LLM_API_KEY, base_url=Config.LLM_BASE_URL)
    prompt = (
        "Map each source column to the best-fitting canonical customer field, or null if none fit.\n\n"
        f"Canonical fields:\n{json.dumps(CANONICAL_FIELDS, indent=2)}\n\n"
        f"Source columns (with redacted sample values):\n{json.dumps(columns_info, indent=2)}\n\n"
        'Return JSON: {"mapping": {"<source_col>": "<canonical_field_or_null>", ...}}. '
        "Use each canonical field at most once — prefer the strongest match. "
        "Map anything that identifies an individual customer (email, phone, account id) to external_id."
    )
    try:
        response = client.chat.completions.create(
            model=Config.LLM_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        result = json.loads(response.choices[0].message.content)
        mapping = result.get("mapping", {})
        return {
            col: (field if field in CANONICAL_FIELDS else None)
            for col, field in mapping.items() if col in df.columns
        }
    except Exception as e:
        logger.warning(f"Mapping proposal failed, returning an empty mapping for review: {e}")
        return {col: None for col in df.columns}


def hash_identity(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()[:32]


def import_dataset(dataset: Dataset, df: "pd.DataFrame", schema_map: Dict[str, Optional[str]]) -> int:
    """Bulk-import rows into Customer per schema_map. Returns imported count."""
    imported = 0
    for _, row in df.iterrows():
        canonical_kwargs: Dict[str, Any] = {}
        extras: Dict[str, Any] = {}
        external_id = None

        for col, field in schema_map.items():
            if col not in row.index or pd.isna(row[col]):
                continue
            value = row[col]
            if field == "external_id":
                external_id = hash_identity(str(value))
            elif field in CANONICAL_FIELDS:
                canonical_kwargs[field] = value
            elif field is None:
                extras[col] = str(value)

        for numeric_field in NUMERIC_FIELDS:
            if numeric_field in canonical_kwargs:
                try:
                    canonical_kwargs[numeric_field] = float(canonical_kwargs[numeric_field])
                except (TypeError, ValueError):
                    canonical_kwargs.pop(numeric_field)

        if isinstance(canonical_kwargs.get("channels_seen"), str):
            canonical_kwargs["channels_seen"] = [
                c.strip() for c in canonical_kwargs["channels_seen"].split(",") if c.strip()
            ]

        canonical_kwargs["extras"] = extras
        try:
            customer = CanonicalCustomer(**canonical_kwargs)
        except Exception as e:
            logger.warning(f"Skipping malformed row during import: {e}")
            continue

        db.session.add(Customer(
            user_id=dataset.user_id,
            dataset_id=dataset.id,
            external_id=external_id,
            attributes=customer.to_attributes(),
        ))
        imported += 1

    dataset.row_count = imported
    dataset.status = "imported"
    db.session.commit()
    return imported
