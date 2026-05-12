"""Reciprocal Rank Fusion to merge vector and graph result lists."""
from __future__ import annotations

K = 60  # RRF constant


def reciprocal_rank_fusion(
    *result_lists: list[dict],
    score_key: str = "score",
) -> list[dict]:
    scores: dict[str, float] = {}
    items: dict[str, dict] = {}

    for results in result_lists:
        for rank, item in enumerate(results):
            key = item.get("doc_id", "") + str(item.get("chunk_index", ""))
            scores[key] = scores.get(key, 0.0) + 1.0 / (K + rank + 1)
            if key not in items:
                items[key] = item

    fused = sorted(items.values(), key=lambda r: scores[
        r.get("doc_id", "") + str(r.get("chunk_index", ""))
    ], reverse=True)

    for item in fused:
        key = item.get("doc_id", "") + str(item.get("chunk_index", ""))
        item["score"] = scores[key]

    return fused
