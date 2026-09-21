from __future__ import annotations

import math

from mmdistance.config import ClusterConfig
from mmdistance.models import Cluster, Detection


def cluster_detections(detections: list[Detection], cfg: ClusterConfig) -> list[Cluster]:
    """Greedy DBSCAN-style clustering in Cartesian space.

    AOP point clouds are sparse, so min_points defaults to 1. Nearby hits of the
    same vehicle still collapse into one object before tracking.
    """
    if not detections:
        return []

    labels = _dbscan(detections, cfg.eps_m, cfg.min_points)
    groups: dict[int, list[Detection]] = {}
    for det, label in zip(detections, labels):
        if label < 0:
            continue
        groups.setdefault(label, []).append(det)
    return [_summarize(group) for group in groups.values()]


def _dbscan(detections: list[Detection], eps: float, min_points: int) -> list[int]:
    n = len(detections)
    labels = [-1] * n
    visited = [False] * n
    cluster_id = 0

    def neighbors(index: int) -> list[int]:
        found = []
        src = detections[index]
        for other, det in enumerate(detections):
            if math.hypot(src.x - det.x, src.y - det.y, src.z - det.z) <= eps:
                found.append(other)
        return found

    for index in range(n):
        if visited[index]:
            continue
        visited[index] = True
        neigh = neighbors(index)
        if len(neigh) < min_points:
            continue
        labels[index] = cluster_id
        seed = list(neigh)
        k = 0
        while k < len(seed):
            point = seed[k]
            if not visited[point]:
                visited[point] = True
                extra = neighbors(point)
                if len(extra) >= min_points:
                    seed.extend(p for p in extra if p not in seed)
            if labels[point] < 0:
                labels[point] = cluster_id
            k += 1
        cluster_id += 1
    return labels


def _summarize(group: list[Detection]) -> Cluster:
    weights = [max(det.snr_db or 1.0, 0.1) for det in group]
    total = sum(weights)

    def weighted(attr: str) -> float:
        return sum(getattr(det, attr) * weight for det, weight in zip(group, weights)) / total

    return Cluster(
        x=weighted("x"),
        y=weighted("y"),
        z=weighted("z"),
        vr=weighted("vr"),
        snr_db=max(det.snr_db or 0.0 for det in group),
        n_points=len(group),
        detections=group,
    )
