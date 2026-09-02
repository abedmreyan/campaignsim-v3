"""Canonical customer schema (Phase 4 — dataset intake).

Every uploaded dataset (CRM export, order history, newsletter list) maps its
source columns onto this schema before import. Identity fields are never
stored raw — see services/dataset_mapper.py, which hashes anything mapped to
`external_id` before a Customer row is ever written. Unmapped source columns
pass through into `extras`, but prompts built from customer data (see
services/segmentation_engine.py) only ever use aggregate statistics computed
over these fields, never a raw row.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Canonical field -> human description, shown to the user during mapping review.
CANONICAL_FIELDS: Dict[str, str] = {
    "external_id": "A unique customer identifier (email, phone, or account ID — will be hashed, never stored raw)",
    "age": "Customer age in years",
    "gender": "Customer gender",
    "location": "City, region, or country",
    "ltv": "Lifetime value (total revenue from this customer)",
    "order_count": "Number of orders/purchases",
    "aov": "Average order value",
    "last_purchase_at": "Date of most recent purchase",
    "email_open_rate": "Email open rate (0.0-1.0)",
    "channels_seen": "Marketing channels this customer has engaged with",
    "created_at": "Date the customer record was created / first seen",
    "status": "Lifecycle status (e.g. active, lapsed, churned)",
}

NUMERIC_FIELDS = {"age", "ltv", "order_count", "aov", "email_open_rate"}


class CanonicalCustomer(BaseModel):
    external_id: Optional[str] = None
    age: Optional[float] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    ltv: Optional[float] = None
    order_count: Optional[float] = None
    aov: Optional[float] = None
    last_purchase_at: Optional[str] = None
    email_open_rate: Optional[float] = None
    channels_seen: Optional[List[str]] = None
    created_at: Optional[str] = None
    status: Optional[str] = None
    extras: Dict[str, Any] = Field(default_factory=dict)

    def to_attributes(self) -> Dict[str, Any]:
        """Everything except external_id (stored on its own hashed column)."""
        data = self.model_dump(exclude={"external_id"}, exclude_none=True)
        extras = data.pop("extras", {})
        data.update(extras)
        return data
