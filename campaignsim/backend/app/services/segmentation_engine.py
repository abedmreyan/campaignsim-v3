"""Customer segmentation (Phase 4).

Clusters a dataset's imported customers on their numeric canonical fields
(age, ltv, order_count, aov, email_open_rate), then asks an LLM to name and
describe each cluster from AGGREGATE statistics only — raw customer rows
never reach a prompt. Segments are written with status='draft' for the user
to review/rename/approve before they can be used for persona synthesis.
"""

import json
from collections import Counter
from typing import Any, Dict, List

import numpy as np
from openai import OpenAI
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from ..config import Config
from ..extensions import db
from ..models.orm import Customer, Dataset, Segment
from ..utils.logger import get_logger

logger = get_logger("campaignsim.services.segmentation_engine")

NUMERIC_FEATURES = ["age", "ltv", "order_count", "aov", "email_open_rate"]
MIN_CUSTOMERS_TO_SEGMENT = 6


def _feature_matrix(customers: List[Customer]) -> np.ndarray:
    rows = []
    for c in customers:
        attrs = c.attributes or {}
        rows.append([float(attrs.get(f) or 0.0) for f in NUMERIC_FEATURES])
    return np.array(rows)


def _pick_k(X: np.ndarray, k_min: int = 3, k_max: int = 8) -> int:
    n = len(X)
    k_max = min(k_max, n - 1)
    if k_max < k_min:
        return max(1, min(k_min, n))

    best_k, best_score = k_min, -1.0
    for k in range(k_min, k_max + 1):
        try:
            labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(X)
            if len(set(labels)) < 2:
                continue
            score = silhouette_score(X, labels)
            if score > best_score:
                best_score, best_k = score, k
        except Exception:
            continue
    return best_k


def cluster_stats(customers: List[Customer]) -> Dict[str, Any]:
    def values(field):
        return [c.attributes.get(field) for c in customers if c.attributes.get(field) is not None]

    def avg(vals):
        return round(sum(vals) / len(vals), 2) if vals else None

    genders = Counter(c.attributes.get("gender") for c in customers if c.attributes.get("gender"))
    locations = Counter(c.attributes.get("location") for c in customers if c.attributes.get("location"))
    statuses = Counter(c.attributes.get("status") for c in customers if c.attributes.get("status"))
    channels: Counter = Counter()
    for c in customers:
        for ch in c.attributes.get("channels_seen") or []:
            channels[ch] += 1

    return {
        "size": len(customers),
        "avg_age": avg(values("age")),
        "avg_ltv": avg(values("ltv")),
        "avg_order_count": avg(values("order_count")),
        "avg_aov": avg(values("aov")),
        "avg_email_open_rate": avg(values("email_open_rate")),
        "top_genders": genders.most_common(3),
        "top_locations": locations.most_common(5),
        "top_statuses": statuses.most_common(3),
        "top_channels": channels.most_common(5),
    }


def _label_clusters_with_llm(cluster_stats: List[Dict[str, Any]]) -> Dict[int, Dict[str, str]]:
    client = OpenAI(api_key=Config.LLM_API_KEY, base_url=Config.LLM_BASE_URL)
    prompt = (
        "You are a marketing segmentation analyst. For each customer cluster below "
        "(described only by aggregate statistics — you never see raw customer rows), "
        "propose a short, memorable segment name (2-4 words) and a one-paragraph "
        "description covering likely traits, motivations, and channel affinity.\n\n"
        f"Clusters (0-indexed):\n{json.dumps(cluster_stats, indent=2)}\n\n"
        'Return JSON: {"segments": [{"index": 0, "name": "...", "description": "..."}, ...]}'
    )
    try:
        response = client.chat.completions.create(
            model=Config.LLM_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.5,
        )
        result = json.loads(response.choices[0].message.content)
        return {item.get("index"): item for item in result.get("segments", [])}
    except Exception as e:
        logger.warning(f"Cluster labeling failed, using generic names: {e}")
        return {}


def segment_dataset(dataset_id, user_id) -> List[Segment]:
    """Cluster this dataset's customers and write draft Segment rows.

    Replaces any previous draft segmentation for this dataset — approved
    segments (status='approved') are left untouched so personas already
    synthesised from them stay valid.
    """
    customers = Customer.query.filter_by(dataset_id=dataset_id, user_id=user_id).all()
    if len(customers) < MIN_CUSTOMERS_TO_SEGMENT:
        raise ValueError(f"Need at least {MIN_CUSTOMERS_TO_SEGMENT} imported customers to segment.")

    X = _feature_matrix(customers)
    X_scaled = StandardScaler().fit_transform(X)
    k = _pick_k(X_scaled)
    model = KMeans(n_clusters=k, n_init=10, random_state=42)
    labels = model.fit_predict(X_scaled)

    clusters: Dict[int, List[Customer]] = {}
    for customer, label in zip(customers, labels):
        clusters.setdefault(int(label), []).append(customer)

    cluster_ids = sorted(clusters.keys())
    stats_list = [cluster_stats(clusters[cid]) for cid in cluster_ids]
    labeled_by_position = _label_clusters_with_llm(stats_list)

    Segment.query.filter_by(dataset_id=dataset_id, user_id=user_id, status="draft").delete()

    segments = []
    for position, cluster_id in enumerate(cluster_ids):
        label_info = labeled_by_position.get(position) or {}
        segment = Segment(
            user_id=user_id,
            dataset_id=dataset_id,
            name=label_info.get("name") or f"Segment {position + 1}",
            description=label_info.get("description") or "",
            method="kmeans",
            definition={
                "features": NUMERIC_FEATURES,
                "centroid": model.cluster_centers_[cluster_id].tolist(),
            },
            size=len(clusters[cluster_id]),
            stats=stats_list[position],
            status="draft",
        )
        db.session.add(segment)
        db.session.flush()  # assign segment.id before tagging its members
        for customer in clusters[cluster_id]:
            customer.segment_id = segment.id
        segments.append(segment)

    dataset = db.session.get(Dataset, dataset_id)
    if dataset:
        dataset.status = "segmented"
    db.session.commit()
    return segments
